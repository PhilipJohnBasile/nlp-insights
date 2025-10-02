"""Integration tests for the full pipeline."""

import json
from pathlib import Path

import pandas as pd
import pytest

from trials.eligibility import parse_eligibility
from trials.features import extract_features
from trials.models import ClinicalTrial, NormalizedTrial
from trials.normalize import normalize_trial
from trials.risk import calculate_risk_score


@pytest.fixture
def sample_trial_data():
    """Create sample trial data for testing."""
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT00000001",
                "briefTitle": "Test Trial for Breast Cancer",
            },
            "statusModule": {
                "overallStatus": "Recruiting",
                "startDateStruct": {"date": "2023-01-01"},
                "completionDateStruct": {"date": "2025-12-31"},
            },
            "designModule": {
                "studyType": "Interventional",
                "phases": ["Phase 2"],
                "enrollmentInfo": {"count": 100},
                "designInfo": {
                    "allocation": "Randomized",
                    "maskingInfo": {"masking": "Double"},
                },
            },
            "armsInterventionsModule": {
                "armGroups": [
                    {"label": "Treatment", "type": "Experimental"},
                    {"label": "Placebo", "type": "Placebo Comparator"},
                ],
            },
            "eligibilityModule": {
                "eligibilityCriteria": """
                Inclusion Criteria:
                - Age 18 years or older
                - Diagnosed with stage IV breast cancer
                - ECOG performance status 0-1

                Exclusion Criteria:
                - Pregnant or nursing
                - Prior chemotherapy within 6 months
                """,
                "minimumAge": "18 Years",
                "maximumAge": "N/A",
                "sex": "All",
            },
            "contactsLocationsModule": {
                "locations": [
                    {"country": "United States"},
                    {"country": "Canada"},
                ],
            },
            "outcomesModule": {
                "primaryOutcomes": [
                    {"measure": "Overall Survival"},
                ],
            },
        },
    }


def test_full_pipeline(sample_trial_data, tmp_path):
    """Test the full data processing pipeline."""
    # Step 1: Normalize
    normalized = normalize_trial(sample_trial_data)
    assert normalized is not None
    assert normalized.trial_id == "NCT00000001"
    assert normalized.phase == "Phase 2"
    assert normalized.enrollment == 100
    assert normalized.arms == 2

    # Step 2: Parse eligibility
    eligibility = parse_eligibility(
        trial_id=normalized.trial_id,
        eligibility_text=normalized.eligibility_text,
        min_age="18 Years",
    )
    assert eligibility.trial_id == "NCT00000001"
    assert eligibility.min_age == 18.0
    assert len(eligibility.disease_stage_terms) > 0

    # Step 3: Extract features
    df_row = pd.Series(normalized.model_dump())
    features = extract_features(df_row)
    assert features.trial_id == "NCT00000001"
    assert features.planned_enrollment == 100.0
    assert features.randomized_flag == 1
    assert features.phase_code > 0

    # Step 4: Calculate risk
    risk = calculate_risk_score(
        trial_id=features.trial_id,
        enrollment=features.planned_enrollment,
        num_sites=features.num_sites,
        randomized_flag=features.randomized_flag,
        duration_days=features.duration_days,
    )
    assert risk.trial_id == "NCT00000001"
    assert risk.total_risk_score >= 0


def test_clinical_trial_parsing(sample_trial_data):
    """Test parsing of ClinicalTrial model."""
    trial = ClinicalTrial(**sample_trial_data)

    assert trial.get_nct_id() == "NCT00000001"
    assert "Breast Cancer" in trial.get_title()
    assert trial.get_phase() == "Phase 2"
    assert trial.get_status() == "Recruiting"
    assert trial.get_enrollment() == 100
    assert len(trial.get_arms()) == 2
    assert trial.get_allocation() == "Randomized"
    assert len(trial.get_primary_outcomes()) == 1
