"""Tests for Pydantic models."""

import pytest
from trials.models import (
    TrialProtocol,
    TrialStatus,
    TrialDesign,
    TrialEnrollment,
    TrialArm,
    TrialEligibility,
    TrialLocation,
    ClinicalTrial,
    NormalizedTrial,
    EligibilityCriteria,
    TrialFeatures,
    TrialRisk
)


class TestTrialProtocol:
    """Test TrialProtocol model."""

    def test_basic_creation(self):
        """Test basic protocol creation."""
        protocol = TrialProtocol(nctId="NCT12345678", briefTitle="Test Trial")
        assert protocol.nct_id == "NCT12345678"
        assert protocol.brief_title == "Test Trial"

    def test_camel_case_alias(self):
        """Test camelCase alias support."""
        protocol = TrialProtocol(nctId="NCT12345678")
        assert protocol.nct_id == "NCT12345678"

    def test_optional_fields(self):
        """Test optional fields."""
        protocol = TrialProtocol(nctId="NCT12345678")
        assert protocol.brief_title is None
        assert protocol.official_title is None


class TestTrialStatus:
    """Test TrialStatus model."""

    def test_basic_creation(self):
        """Test status creation."""
        status = TrialStatus(overallStatus="Recruiting")
        assert status.overall_status == "Recruiting"

    def test_with_dates(self):
        """Test with dates."""
        status = TrialStatus(
            overallStatus="Recruiting",
            startDate="2024-01-01",
            completionDate="2025-12-31"
        )
        assert status.start_date == "2024-01-01"
        assert status.completion_date == "2025-12-31"


class TestTrialDesign:
    """Test TrialDesign model."""

    def test_basic_creation(self):
        """Test design creation."""
        design = TrialDesign(studyType="Interventional")
        assert design.study_type == "Interventional"

    def test_with_phases(self):
        """Test with phases."""
        design = TrialDesign(studyType="Interventional", phases=["Phase 2", "Phase 3"])
        assert len(design.phases) == 2
        assert "Phase 2" in design.phases

    def test_with_allocation(self):
        """Test with allocation."""
        design = TrialDesign(allocation="Randomized", interventionModel="Parallel Assignment")
        assert design.allocation == "Randomized"
        assert design.intervention_model == "Parallel Assignment"


class TestTrialEnrollment:
    """Test TrialEnrollment model."""

    def test_basic_creation(self):
        """Test enrollment creation."""
        enrollment = TrialEnrollment(count=100, type="ESTIMATED")
        assert enrollment.count == 100
        assert enrollment.type == "ESTIMATED"

    def test_optional_fields(self):
        """Test optional fields."""
        enrollment = TrialEnrollment()
        assert enrollment.count is None
        assert enrollment.type is None


class TestTrialArm:
    """Test TrialArm model."""

    def test_basic_creation(self):
        """Test arm creation."""
        arm = TrialArm(label="Experimental", type="Experimental", description="Drug X")
        assert arm.label == "Experimental"
        assert arm.type == "Experimental"
        assert arm.description == "Drug X"


class TestTrialEligibility:
    """Test TrialEligibility model."""

    def test_basic_creation(self):
        """Test eligibility creation."""
        eligibility = TrialEligibility(
            criteria="Age >= 18",
            sex="All",
            minimumAge="18 Years",
            maximumAge="75 Years"
        )
        assert eligibility.criteria == "Age >= 18"
        assert eligibility.sex == "All"
        assert eligibility.minimum_age == "18 Years"
        assert eligibility.maximum_age == "75 Years"

    def test_healthy_volunteers(self):
        """Test healthy volunteers field."""
        eligibility = TrialEligibility(healthyVolunteers="No")
        assert eligibility.healthy_volunteers == "No"


class TestTrialLocation:
    """Test TrialLocation model."""

    def test_basic_creation(self):
        """Test location creation."""
        location = TrialLocation(
            facility="University Hospital",
            city="Boston",
            state="MA",
            country="United States"
        )
        assert location.facility == "University Hospital"
        assert location.city == "Boston"
        assert location.state == "MA"
        assert location.country == "United States"


class TestClinicalTrial:
    """Test ClinicalTrial model."""

    @pytest.fixture
    def sample_trial_data(self):
        """Sample trial data."""
        return {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Test Trial",
                    "officialTitle": "Official Test Trial"
                },
                "statusModule": {
                    "overallStatus": "Recruiting",
                    "lastUpdateSubmitDate": "2025-01-01",
                    "startDateStruct": {"date": "2024-01-01"},
                    "completionDateStruct": {"date": "2026-01-01"}
                },
                "designModule": {
                    "studyType": "Interventional",
                    "phases": ["Phase 2"],
                    "enrollmentInfo": {"count": 100, "type": "ESTIMATED"},
                    "designInfo": {
                        "allocation": "Randomized",
                        "maskingInfo": {"masking": "Double"}
                    }
                },
                "armsInterventionsModule": {
                    "armGroups": [
                        {"label": "Arm 1", "type": "Experimental"},
                        {"label": "Arm 2", "type": "Placebo Comparator"}
                    ]
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Age >= 18 years"
                },
                "contactsLocationsModule": {
                    "locations": [
                        {"facility": "Hospital A", "city": "Boston"},
                        {"facility": "Hospital B", "city": "New York"}
                    ]
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {"measure": "Overall Survival"},
                        {"measure": "Progression-Free Survival"}
                    ]
                }
            }
        }

    def test_basic_creation(self, sample_trial_data):
        """Test trial creation."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.protocol_section is not None

    def test_get_nct_id(self, sample_trial_data):
        """Test NCT ID extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_nct_id() == "NCT12345678"

    def test_get_title(self, sample_trial_data):
        """Test title extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_title() == "Test Trial"

    def test_get_title_fallback(self):
        """Test title fallback to official title."""
        data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "officialTitle": "Official Title Only"
                }
            }
        }
        trial = ClinicalTrial(**data)
        assert trial.get_title() == "Official Title Only"

    def test_get_phase(self, sample_trial_data):
        """Test phase extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_phase() == "Phase 2"

    def test_get_phase_none(self):
        """Test phase when none specified."""
        data = {"protocolSection": {"designModule": {}}}
        trial = ClinicalTrial(**data)
        assert trial.get_phase() is None

    def test_get_status(self, sample_trial_data):
        """Test status extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_status() == "Recruiting"

    def test_get_enrollment(self, sample_trial_data):
        """Test enrollment extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_enrollment() == 100

    def test_get_enrollment_type(self, sample_trial_data):
        """Test enrollment type extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_enrollment_type() == "ESTIMATED"

    def test_get_last_update_date(self, sample_trial_data):
        """Test last update date extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_last_update_date() == "2025-01-01"

    def test_get_last_update_date_fallback(self):
        """Test fallback to statusVerifiedDate."""
        data = {
            "protocolSection": {
                "statusModule": {"statusVerifiedDate": "2024-12-01"}
            }
        }
        trial = ClinicalTrial(**data)
        assert trial.get_last_update_date() == "2024-12-01"

    def test_get_study_type(self, sample_trial_data):
        """Test study type extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_study_type() == "Interventional"

    def test_get_arms(self, sample_trial_data):
        """Test arms extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        arms = trial.get_arms()
        assert len(arms) == 2
        assert arms[0]["label"] == "Arm 1"

    def test_get_arms_empty(self):
        """Test arms when none specified."""
        data = {"protocolSection": {}}
        trial = ClinicalTrial(**data)
        assert trial.get_arms() == []

    def test_get_eligibility_text(self, sample_trial_data):
        """Test eligibility text extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_eligibility_text() == "Age >= 18 years"

    def test_get_eligibility_module(self, sample_trial_data):
        """Test eligibility module extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        module = trial.get_eligibility_module()
        assert "eligibilityCriteria" in module

    def test_get_locations(self, sample_trial_data):
        """Test locations extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        locations = trial.get_locations()
        assert len(locations) == 2
        assert locations[0]["facility"] == "Hospital A"

    def test_get_start_date(self, sample_trial_data):
        """Test start date extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_start_date() == "2024-01-01"

    def test_get_completion_date(self, sample_trial_data):
        """Test completion date extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_completion_date() == "2026-01-01"

    def test_get_completion_date_fallback(self):
        """Test fallback to primaryCompletionDateStruct."""
        data = {
            "protocolSection": {
                "statusModule": {
                    "primaryCompletionDateStruct": {"date": "2025-06-01"}
                }
            }
        }
        trial = ClinicalTrial(**data)
        assert trial.get_completion_date() == "2025-06-01"

    def test_get_allocation(self, sample_trial_data):
        """Test allocation extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_allocation() == "Randomized"

    def test_get_masking(self, sample_trial_data):
        """Test masking extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        assert trial.get_masking() == "Double"

    def test_get_primary_outcomes(self, sample_trial_data):
        """Test primary outcomes extraction."""
        trial = ClinicalTrial(**sample_trial_data)
        outcomes = trial.get_primary_outcomes()
        assert len(outcomes) == 2
        assert "Overall Survival" in outcomes


class TestNormalizedTrial:
    """Test NormalizedTrial model."""

    def test_basic_creation(self):
        """Test normalized trial creation."""
        trial = NormalizedTrial(
            trial_id="NCT12345678",
            title="Test Trial",
            phase="Phase 2",
            status="Recruiting",
            enrollment=100
        )
        assert trial.trial_id == "NCT12345678"
        assert trial.title == "Test Trial"
        assert trial.enrollment == 100

    def test_default_fields(self):
        """Test default field values."""
        trial = NormalizedTrial(trial_id="NCT12345678", title="Test")
        assert trial.arms == 0
        assert trial.countries == []
        assert trial.primary_outcomes == []


class TestEligibilityCriteria:
    """Test EligibilityCriteria model."""

    def test_basic_creation(self):
        """Test eligibility criteria creation."""
        criteria = EligibilityCriteria(
            trial_id="NCT12345678",
            min_age=18.0,
            max_age=75.0,
            sex="All"
        )
        assert criteria.trial_id == "NCT12345678"
        assert criteria.min_age == 18.0
        assert criteria.max_age == 75.0

    def test_with_terms(self):
        """Test with inclusion/exclusion terms."""
        criteria = EligibilityCriteria(
            trial_id="NCT12345678",
            key_inclusion_terms=["EGFR", "Stage IV"],
            key_exclusion_terms=["Pregnant", "HIV"]
        )
        assert len(criteria.key_inclusion_terms) == 2
        assert len(criteria.key_exclusion_terms) == 2


class TestTrialFeatures:
    """Test TrialFeatures model."""

    def test_basic_creation(self):
        """Test trial features creation."""
        features = TrialFeatures(
            trial_id="NCT12345678",
            planned_enrollment=100.0,
            num_sites=10,
            phase_code=2,
            randomized_flag=1
        )
        assert features.trial_id == "NCT12345678"
        assert features.planned_enrollment == 100.0
        assert features.randomized_flag == 1

    def test_default_values(self):
        """Test default values."""
        features = TrialFeatures(trial_id="NCT12345678")
        assert features.planned_enrollment == 0.0
        assert features.num_sites == 0
        assert features.phase_code == 0


class TestTrialRisk:
    """Test TrialRisk model."""

    def test_basic_creation(self):
        """Test trial risk creation."""
        risk = TrialRisk(
            trial_id="NCT12345678",
            small_enrollment_penalty=0.5,
            no_randomization_penalty=0.3,
            total_risk_score=1.2
        )
        assert risk.trial_id == "NCT12345678"
        assert risk.total_risk_score == 1.2

    def test_default_penalties(self):
        """Test default penalty values."""
        risk = TrialRisk(trial_id="NCT12345678")
        assert risk.small_enrollment_penalty == 0.0
        assert risk.total_risk_score == 0.0
