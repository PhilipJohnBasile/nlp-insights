"""Tests for eligibility parsing functions."""

import pytest
from trials.eligibility import (
    parse_age,
    extract_inclusion_exclusion,
    extract_disease_stages,
    parse_eligibility
)


class TestParseAge:
    """Test age parsing function."""

    def test_parse_years(self):
        """Test parsing years."""
        assert parse_age("18 Years") == 18.0
        assert parse_age("65 years") == 65.0
        assert parse_age("75 YEARS") == 75.0

    def test_parse_months(self):
        """Test parsing months."""
        assert parse_age("6 Months") == 0.5
        assert parse_age("24 months") == 2.0
        assert parse_age("18 MONTHS") == 1.5

    def test_parse_weeks(self):
        """Test parsing weeks."""
        assert parse_age("52 Weeks") == 1.0
        assert parse_age("26 weeks") == 0.5

    def test_parse_days(self):
        """Test parsing days."""
        assert parse_age("365 Days") == 1.0
        assert parse_age("730 days") == 2.0

    def test_parse_decimal_values(self):
        """Test parsing decimal values."""
        assert parse_age("18.5 Years") == 18.5
        assert parse_age("6.5 months") == pytest.approx(0.542, rel=0.01)

    def test_parse_na_values(self):
        """Test N/A and None values."""
        assert parse_age("N/A") is None
        assert parse_age("n/a") is None
        assert parse_age("NONE") is None
        assert parse_age(None) is None
        assert parse_age("") is None

    def test_parse_no_number(self):
        """Test strings without numbers."""
        assert parse_age("No age limit") is None
        assert parse_age("Adult") is None

    def test_parse_default_to_years(self):
        """Test default assumption is years."""
        assert parse_age("18") == 18.0
        assert parse_age("65") == 65.0


class TestExtractInclusionExclusion:
    """Test inclusion/exclusion extraction."""

    def test_basic_extraction(self):
        """Test basic extraction."""
        text = """
        Inclusion Criteria:
        - Age >= 18 years
        - Confirmed diagnosis of cancer

        Exclusion Criteria:
        - Pregnant or nursing women
        - Active infection requiring treatment
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) >= 1
        assert any("18 years" in item for item in inclusion)
        assert len(exclusion) >= 1
        assert any("Pregnant" in item for item in exclusion)

    def test_case_insensitive(self):
        """Test case insensitive matching."""
        text = """
        INCLUSION CRITERIA:
        - Patient must be 18 or older

        EXCLUSION CRITERIA:
        - Prior treatment with study drug
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) >= 1
        assert len(exclusion) >= 1

    def test_numbered_list(self):
        """Test numbered list parsing."""
        text = """
        Inclusion Criteria:
        1. Age >= 18 years old
        2. ECOG performance status 0-1

        Exclusion Criteria:
        1) Pregnant women
        2) Active CNS metastases
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) >= 1
        assert len(exclusion) >= 1

    def test_bullet_point_variations(self):
        """Test different bullet point styles."""
        text = """
        Inclusion Criteria:
        • Age requirement met
        * Diagnosis confirmed
        - Treatment naive

        Exclusion Criteria:
        • Pregnancy test positive
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) >= 1
        assert len(exclusion) >= 1

    def test_empty_text(self):
        """Test empty or None text."""
        inclusion, exclusion = extract_inclusion_exclusion(None)
        assert inclusion == []
        assert exclusion == []

        inclusion, exclusion = extract_inclusion_exclusion("")
        assert inclusion == []
        assert exclusion == []

    def test_only_inclusion(self):
        """Test text with only inclusion criteria."""
        text = """
        Inclusion Criteria:
        - Age >= 18 years
        - Confirmed diagnosis
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) >= 1
        assert len(exclusion) == 0

    def test_only_exclusion(self):
        """Test text with only exclusion criteria."""
        text = """
        Exclusion Criteria:
        - Pregnant women
        - Active infection
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) == 0
        assert len(exclusion) >= 1

    def test_filters_short_items(self):
        """Test that short items (< 10 chars) are filtered."""
        text = """
        Inclusion Criteria:
        - Age >= 18 years and confirmed diagnosis
        - Yes
        - No

        Exclusion Criteria:
        - Pregnant or nursing women
        - N/A
        """
        inclusion, exclusion = extract_inclusion_exclusion(text)

        # Should not include "Yes", "No", "N/A"
        assert all(len(item) > 10 for item in inclusion)
        assert all(len(item) > 10 for item in exclusion)

    def test_limits_to_20_terms(self):
        """Test limit to 20 terms."""
        # Create text with 25 inclusion items
        items = "\n".join([f"- Inclusion criterion number {i}" for i in range(25)])
        text = f"Inclusion Criteria:\n{items}\n\nExclusion Criteria:\n- Exclusion item"

        inclusion, exclusion = extract_inclusion_exclusion(text)

        assert len(inclusion) <= 20


class TestExtractDiseaseStages:
    """Test disease stage extraction."""

    def test_roman_numeral_stages(self):
        """Test Roman numeral stages."""
        text = "Patients with Stage IV cancer or Stage III disease"
        stages = extract_disease_stages(text)

        assert any("iv" in s.lower() for s in stages)
        assert any("iii" in s.lower() for s in stages)

    def test_numeric_stages(self):
        """Test numeric stages."""
        text = "Stage 1, Stage 2, or Stage 3 disease"
        stages = extract_disease_stages(text)

        assert len(stages) >= 1

    def test_stage_subdivisions(self):
        """Test stage subdivisions (a, b, c)."""
        text = "Stage IIIa or Stage IVb disease"
        stages = extract_disease_stages(text)

        assert any("iiia" in s.lower() for s in stages)

    def test_metastatic(self):
        """Test metastatic detection."""
        text = "Metastatic cancer or metastatic disease"
        stages = extract_disease_stages(text)

        assert any("metastatic" in s.lower() for s in stages)

    def test_locally_advanced(self):
        """Test locally advanced detection."""
        text = "Locally advanced or locally recurrent disease"
        stages = extract_disease_stages(text)

        assert any("locally advanced" in s.lower() for s in stages)

    def test_early_stage(self):
        """Test early stage detection."""
        text = "Early stage cancer eligible"
        stages = extract_disease_stages(text)

        assert any("early stage" in s.lower() for s in stages)

    def test_advanced_disease(self):
        """Test advanced disease detection."""
        text = "Advanced cancer or advanced disease"
        stages = extract_disease_stages(text)

        assert any("advanced" in s.lower() for s in stages)

    def test_recurrent_refractory(self):
        """Test recurrent and refractory detection."""
        text = "Recurrent or refractory disease"
        stages = extract_disease_stages(text)

        assert any("recurrent" in s.lower() for s in stages)
        assert any("refractory" in s.lower() for s in stages)

    def test_empty_text(self):
        """Test empty text."""
        assert extract_disease_stages(None) == []
        assert extract_disease_stages("") == []

    def test_no_duplicates(self):
        """Test no duplicate stages."""
        text = "Stage IV disease, stage IV cancer, Stage IV patients"
        stages = extract_disease_stages(text)

        # Should deduplicate
        stage_iv_count = sum(1 for s in stages if "iv" in s.lower())
        assert stage_iv_count == 1

    def test_limits_to_10_stages(self):
        """Test limit to 10 stages."""
        text = "Stage I, Stage II, Stage III, Stage IV, metastatic, advanced, recurrent, refractory, locally advanced, early stage, other stage"
        stages = extract_disease_stages(text)

        assert len(stages) <= 10


class TestParseEligibility:
    """Test complete eligibility parsing."""

    def test_basic_parsing(self):
        """Test basic eligibility parsing."""
        text = """
        Inclusion Criteria:
        - Age >= 18 years
        - Stage IV cancer

        Exclusion Criteria:
        - Pregnant women
        """

        criteria = parse_eligibility(
            trial_id="NCT12345678",
            eligibility_text=text,
            min_age="18 Years",
            max_age="75 Years",
            sex="All"
        )

        assert criteria.trial_id == "NCT12345678"
        assert criteria.min_age == 18.0
        assert criteria.max_age == 75.0
        assert criteria.sex == "All"
        assert len(criteria.key_inclusion_terms) >= 1
        assert len(criteria.key_exclusion_terms) >= 1
        assert len(criteria.disease_stage_terms) >= 1

    def test_with_none_ages(self):
        """Test with None ages."""
        criteria = parse_eligibility(
            trial_id="NCT12345678",
            eligibility_text="Test",
            min_age=None,
            max_age=None
        )

        assert criteria.min_age is None
        assert criteria.max_age is None

    def test_with_na_ages(self):
        """Test with N/A ages."""
        criteria = parse_eligibility(
            trial_id="NCT12345678",
            eligibility_text="Test",
            min_age="N/A",
            max_age="N/A"
        )

        assert criteria.min_age is None
        assert criteria.max_age is None

    def test_with_empty_eligibility_text(self):
        """Test with empty eligibility text."""
        criteria = parse_eligibility(
            trial_id="NCT12345678",
            eligibility_text=None
        )

        assert criteria.key_inclusion_terms == []
        assert criteria.key_exclusion_terms == []
        assert criteria.disease_stage_terms == []

    def test_comprehensive_example(self):
        """Test comprehensive example."""
        text = """
        Inclusion Criteria:
        1. Age 18 years or older
        2. Histologically confirmed Stage IV non-small cell lung cancer
        3. ECOG performance status 0-1
        4. Adequate organ function

        Exclusion Criteria:
        1. Pregnant or nursing women
        2. Active brain metastases
        3. Prior treatment with study drug
        4. Uncontrolled medical conditions
        """

        criteria = parse_eligibility(
            trial_id="NCT99999999",
            eligibility_text=text,
            min_age="18 Years",
            max_age="N/A",
            sex="All"
        )

        assert criteria.trial_id == "NCT99999999"
        assert criteria.min_age == 18.0
        assert criteria.max_age is None
        assert len(criteria.key_inclusion_terms) >= 3
        assert len(criteria.key_exclusion_terms) >= 3
        assert any("stage iv" in s.lower() for s in criteria.disease_stage_terms)


class TestParseAllEligibility:
    """Test batch eligibility parsing."""

    def test_parse_all_with_mock_data(self, tmp_path, monkeypatch):
        """Test parse_all_eligibility with mock data."""
        import pandas as pd
        from trials.eligibility import parse_all_eligibility

        # Create mock input file
        input_file = tmp_path / "trials.parquet"
        output_file = tmp_path / "eligibility.parquet"

        # Mock data
        trials_data = pd.DataFrame([
            {
                "trial_id": "NCT12345678",
                "eligibility_text": "Inclusion: Age >= 18\nExclusion: Pregnant"
            },
            {
                "trial_id": "NCT87654321",
                "eligibility_text": "Inclusion: Stage IV\nExclusion: Active infection"
            }
        ])
        trials_data.to_parquet(input_file, index=False)

        # Run parsing
        result_df = parse_all_eligibility(input_file, output_file)

        # Verify results
        assert len(result_df) == 2
        assert output_file.exists()
        assert "trial_id" in result_df.columns
