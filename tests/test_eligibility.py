"""Tests for eligibility parsing."""

from trials.eligibility import (
    extract_disease_stages,
    extract_inclusion_exclusion,
    parse_age,
)


def test_parse_age_years():
    """Test parsing age in years."""
    assert parse_age("18 Years") == 18.0
    assert parse_age("65 years") == 65.0


def test_parse_age_months():
    """Test parsing age in months."""
    assert parse_age("12 Months") == 1.0
    assert parse_age("24 months") == 2.0


def test_parse_age_invalid():
    """Test parsing invalid age."""
    assert parse_age("N/A") is None
    assert parse_age("") is None
    assert parse_age(None) is None


def test_extract_inclusion_exclusion():
    """Test extracting inclusion and exclusion criteria."""
    text = """
    Inclusion Criteria:
    - Age 18 or older
    - Diagnosed with cancer

    Exclusion Criteria:
    - Pregnant or nursing
    - Prior chemotherapy
    """

    inclusion, exclusion = extract_inclusion_exclusion(text)

    assert len(inclusion) > 0
    assert len(exclusion) > 0
    assert any("18" in item or "Age" in item for item in inclusion)


def test_extract_disease_stages():
    """Test extracting disease stage terms."""
    text = "Patients with stage IV metastatic breast cancer or locally advanced disease"

    stages = extract_disease_stages(text)

    assert len(stages) > 0
    assert any("metastatic" in s.lower() for s in stages)
