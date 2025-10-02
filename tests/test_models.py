"""Tests for Pydantic models."""

from trials.models import (
    ClinicalTrial,
    EligibilityCriteria,
    NormalizedTrial,
    TrialFeatures,
    TrialRisk,
)


def test_normalized_trial_creation():
    """Test creating a NormalizedTrial."""
    trial = NormalizedTrial(
        trial_id="NCT12345678",
        title="Test Trial",
        phase="Phase 2",
        status="Recruiting",
        enrollment=100,
        arms=2,
        countries=["United States"],
    )

    assert trial.trial_id == "NCT12345678"
    assert trial.title == "Test Trial"
    assert trial.enrollment == 100
    assert len(trial.countries) == 1


def test_eligibility_criteria_creation():
    """Test creating EligibilityCriteria."""
    criteria = EligibilityCriteria(
        trial_id="NCT12345678",
        min_age=18.0,
        max_age=65.0,
        sex="All",
        key_inclusion_terms=["diagnosed with cancer"],
        key_exclusion_terms=["pregnant"],
    )

    assert criteria.trial_id == "NCT12345678"
    assert criteria.min_age == 18.0
    assert len(criteria.key_inclusion_terms) == 1


def test_trial_features_creation():
    """Test creating TrialFeatures."""
    features = TrialFeatures(
        trial_id="NCT12345678",
        planned_enrollment=100.0,
        num_sites=5,
        phase_code=3,
        arm_count=2,
        randomized_flag=1,
    )

    assert features.trial_id == "NCT12345678"
    assert features.planned_enrollment == 100.0
    assert features.randomized_flag == 1


def test_trial_risk_creation():
    """Test creating TrialRisk."""
    risk = TrialRisk(
        trial_id="NCT12345678",
        small_enrollment_penalty=20.0,
        no_randomization_penalty=0.0,
        single_site_penalty=10.0,
        long_duration_penalty=5.0,
        total_risk_score=35.0,
    )

    assert risk.trial_id == "NCT12345678"
    assert risk.total_risk_score == 35.0
