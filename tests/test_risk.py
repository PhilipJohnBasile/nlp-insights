"""Tests for risk scoring."""

from trials.risk import calculate_risk_score


def test_risk_score_high_risk():
    """Test risk score for high-risk trial."""
    # Small enrollment, not randomized, single site, long duration
    risk = calculate_risk_score(
        trial_id="NCT00000001",
        enrollment=10.0,
        num_sites=1,
        randomized_flag=0,
        duration_days=1000.0,
    )

    assert risk.trial_id == "NCT00000001"
    assert risk.small_enrollment_penalty > 0
    assert risk.no_randomization_penalty == 30.0
    assert risk.single_site_penalty > 0
    assert risk.long_duration_penalty > 0
    assert risk.total_risk_score > 50


def test_risk_score_low_risk():
    """Test risk score for low-risk trial."""
    # Large enrollment, randomized, many sites, normal duration
    risk = calculate_risk_score(
        trial_id="NCT00000002",
        enrollment=500.0,
        num_sites=20,
        randomized_flag=1,
        duration_days=365.0,
    )

    assert risk.trial_id == "NCT00000002"
    assert risk.small_enrollment_penalty == 0
    assert risk.no_randomization_penalty == 0
    assert risk.single_site_penalty == 0
    assert risk.long_duration_penalty == 0
    assert risk.total_risk_score == 0


def test_risk_score_medium_risk():
    """Test risk score for medium-risk trial."""
    # Small enrollment but randomized, few sites
    risk = calculate_risk_score(
        trial_id="NCT00000003",
        enrollment=30.0,
        num_sites=3,
        randomized_flag=1,
        duration_days=500.0,
    )

    assert risk.trial_id == "NCT00000003"
    assert risk.small_enrollment_penalty > 0
    assert risk.no_randomization_penalty == 0
    assert 0 < risk.total_risk_score < 50
