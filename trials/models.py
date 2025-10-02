"""Pydantic models for clinical trial data."""

from datetime import date
from typing import Any, Optional

from pydantic import BaseModel, Field


class TrialProtocol(BaseModel):
    """Raw protocol information from ClinicalTrials.gov."""

    nct_id: str = Field(alias="nctId")
    brief_title: Optional[str] = Field(default=None, alias="briefTitle")
    official_title: Optional[str] = Field(default=None, alias="officialTitle")

    class Config:
        populate_by_name = True


class TrialStatus(BaseModel):
    """Trial status information."""

    overall_status: Optional[str] = Field(default=None, alias="overallStatus")
    start_date: Optional[str] = Field(default=None, alias="startDate")
    completion_date: Optional[str] = Field(default=None, alias="completionDate")

    class Config:
        populate_by_name = True


class TrialDesign(BaseModel):
    """Trial design information."""

    study_type: Optional[str] = Field(default=None, alias="studyType")
    phases: Optional[list[str]] = Field(default=None)
    allocation: Optional[str] = Field(default=None)
    intervention_model: Optional[str] = Field(default=None, alias="interventionModel")
    masking: Optional[dict[str, Any]] = Field(default=None)

    class Config:
        populate_by_name = True


class TrialEnrollment(BaseModel):
    """Enrollment information."""

    count: Optional[int] = None
    type: Optional[str] = None


class TrialArm(BaseModel):
    """Trial arm/group information."""

    label: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None


class TrialEligibility(BaseModel):
    """Eligibility criteria."""

    criteria: Optional[str] = None
    sex: Optional[str] = None
    minimum_age: Optional[str] = Field(default=None, alias="minimumAge")
    maximum_age: Optional[str] = Field(default=None, alias="maximumAge")
    healthy_volunteers: Optional[str] = Field(default=None, alias="healthyVolunteers")

    class Config:
        populate_by_name = True


class TrialLocation(BaseModel):
    """Trial location information."""

    facility: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None


class ClinicalTrial(BaseModel):
    """Complete clinical trial data from API."""

    protocol_section: dict[str, Any] = Field(alias="protocolSection")

    class Config:
        populate_by_name = True

    def get_nct_id(self) -> str:
        """Extract NCT ID."""
        return self.protocol_section.get("identificationModule", {}).get("nctId", "")

    def get_title(self) -> str:
        """Extract trial title."""
        ident = self.protocol_section.get("identificationModule", {})
        return ident.get("briefTitle") or ident.get("officialTitle", "")

    def get_phase(self) -> Optional[str]:
        """Extract phase."""
        design = self.protocol_section.get("designModule", {})
        phases = design.get("phases", [])
        return phases[0] if phases else None

    def get_status(self) -> Optional[str]:
        """Extract overall status."""
        status = self.protocol_section.get("statusModule", {})
        return status.get("overallStatus")

    def get_enrollment(self) -> Optional[int]:
        """Extract enrollment count."""
        design = self.protocol_section.get("designModule", {})
        enrollment = design.get("enrollmentInfo", {})
        return enrollment.get("count")

    def get_study_type(self) -> Optional[str]:
        """Extract study type."""
        design = self.protocol_section.get("designModule", {})
        return design.get("studyType")

    def get_arms(self) -> list[dict[str, Any]]:
        """Extract arm/group information."""
        arms_module = self.protocol_section.get("armsInterventionsModule", {})
        return arms_module.get("armGroups", [])

    def get_eligibility_text(self) -> Optional[str]:
        """Extract eligibility criteria text."""
        eligibility = self.protocol_section.get("eligibilityModule", {})
        return eligibility.get("eligibilityCriteria")

    def get_eligibility_module(self) -> dict[str, Any]:
        """Extract full eligibility module."""
        return self.protocol_section.get("eligibilityModule", {})

    def get_locations(self) -> list[dict[str, Any]]:
        """Extract location information."""
        locations = self.protocol_section.get("contactsLocationsModule", {})
        return locations.get("locations", [])

    def get_start_date(self) -> Optional[str]:
        """Extract start date."""
        status = self.protocol_section.get("statusModule", {})
        start = status.get("startDateStruct", {})
        return start.get("date")

    def get_completion_date(self) -> Optional[str]:
        """Extract completion date."""
        status = self.protocol_section.get("statusModule", {})
        completion = status.get("completionDateStruct", {}) or status.get(
            "primaryCompletionDateStruct", {}
        )
        return completion.get("date")

    def get_allocation(self) -> Optional[str]:
        """Extract allocation type."""
        design = self.protocol_section.get("designModule", {})
        return design.get("designInfo", {}).get("allocation")

    def get_masking(self) -> Optional[str]:
        """Extract masking information."""
        design = self.protocol_section.get("designModule", {})
        masking = design.get("designInfo", {}).get("maskingInfo", {})
        return masking.get("masking")

    def get_primary_outcomes(self) -> list[str]:
        """Extract primary outcome measures."""
        outcomes = self.protocol_section.get("outcomesModule", {})
        primary = outcomes.get("primaryOutcomes", [])
        return [o.get("measure", "") for o in primary]


class NormalizedTrial(BaseModel):
    """Normalized trial data for analysis."""

    trial_id: str
    title: str
    phase: Optional[str] = None
    status: Optional[str] = None
    start_date: Optional[str] = None
    completion_date: Optional[str] = None
    enrollment: Optional[int] = None
    arms: int = 0
    countries: list[str] = Field(default_factory=list)
    study_type: Optional[str] = None
    masking: Optional[str] = None
    allocation: Optional[str] = None
    primary_outcomes: list[str] = Field(default_factory=list)
    eligibility_text: Optional[str] = None


class EligibilityCriteria(BaseModel):
    """Parsed eligibility criteria."""

    trial_id: str
    min_age: Optional[float] = None
    max_age: Optional[float] = None
    sex: Optional[str] = None
    key_inclusion_terms: list[str] = Field(default_factory=list)
    key_exclusion_terms: list[str] = Field(default_factory=list)
    disease_stage_terms: list[str] = Field(default_factory=list)


class TrialFeatures(BaseModel):
    """Engineered features for clustering and analysis."""

    trial_id: str
    planned_enrollment: float = 0.0
    num_sites: int = 0
    phase_code: int = 0
    arm_count: int = 0
    randomized_flag: int = 0
    parallel_flag: int = 0
    masking_level: int = 0
    duration_days: float = 0.0


class TrialRisk(BaseModel):
    """Risk assessment for a trial."""

    trial_id: str
    small_enrollment_penalty: float = 0.0
    no_randomization_penalty: float = 0.0
    single_site_penalty: float = 0.0
    long_duration_penalty: float = 0.0
    total_risk_score: float = 0.0
