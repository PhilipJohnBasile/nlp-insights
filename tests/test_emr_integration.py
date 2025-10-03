"""Tests for EMR integration utilities."""

import pytest
import json
from trials.emr_integration import (
    export_to_emr_format,
    import_from_csv,
    generate_referral_letter,
    get_emr_integration_instructions
)


class TestEMRExport:
    """Test EMR export functions."""

    @pytest.fixture
    def patient_data(self):
        """Sample patient data."""
        return {
            "age": 65,
            "cancer_type": "Lung Cancer",
            "stage": "IV",
            "ecog": 1,
            "prior_therapies": "Carboplatin/Pemetrexed",
            "PDL1": True,
            "EGFR": True
        }

    @pytest.fixture
    def sample_trials(self):
        """Sample trial data."""
        return [
            {
                "nct_id": "NCT12345678",
                "title": "Study of Drug X in Lung Cancer",
                "phase": "Phase 3",
                "status": "Recruiting",
                "nearest_site": {
                    "facility": "University Hospital",
                    "city": "Boston",
                    "state": "MA",
                    "distance": 5.2,
                    "phone": "617-555-1234"
                }
            },
            {
                "nct_id": "NCT87654321",
                "title": "Immunotherapy Trial",
                "phase": "Phase 2",
                "status": "Recruiting"
            }
        ]

    def test_export_text_format(self, patient_data, sample_trials):
        """Test text format export."""
        result = export_to_emr_format(patient_data, sample_trials, format="text")

        assert "CLINICAL TRIAL SEARCH RESULTS" in result
        assert "Age: 65" in result
        assert "Lung Cancer" in result
        assert "Stage: IV" in result
        assert "ECOG: 1" in result
        assert "PDL1" in result
        assert "EGFR" in result
        assert "NCT12345678" in result
        assert "University Hospital" in result
        assert "Boston, MA" in result
        assert "617-555-1234" in result

    def test_export_text_limits_trials(self, patient_data):
        """Test text export limits to 10 trials."""
        trials = [{"nct_id": f"NCT{i:08d}", "title": f"Trial {i}"} for i in range(20)]
        result = export_to_emr_format(patient_data, trials, format="text")

        assert "NCT00000000" in result
        assert "NCT00000009" in result
        assert "NCT00000010" not in result

    def test_export_csv_format(self, patient_data, sample_trials):
        """Test CSV format export."""
        result = export_to_emr_format(patient_data, sample_trials, format="csv")

        assert "NCT_ID,Title,Phase,Status" in result
        assert "NCT12345678" in result
        assert "Drug X in Lung Cancer" in result
        assert "Phase 3" in result
        assert "University Hospital" in result

    def test_export_csv_truncates_long_title(self, patient_data):
        """Test CSV export truncates long titles."""
        trials = [{
            "nct_id": "NCT12345678",
            "title": "A" * 150,  # Very long title
            "phase": "Phase 2"
        }]

        result = export_to_emr_format(patient_data, trials, format="csv")
        lines = result.split("\n")
        data_line = lines[1]

        # Should be truncated to 100 chars
        assert len(data_line.split(",")[1]) <= 102  # Allow for quotes

    def test_export_json_format(self, patient_data, sample_trials):
        """Test JSON format export."""
        result = export_to_emr_format(patient_data, sample_trials, format="json")

        data = json.loads(result)
        assert "export_timestamp" in data
        assert "patient_criteria" in data
        assert "matching_trials" in data

        assert data["patient_criteria"]["age"] == 65
        assert len(data["matching_trials"]) == 2
        assert data["matching_trials"][0]["nct_id"] == "NCT12345678"

    def test_export_default_format(self, patient_data, sample_trials):
        """Test default format is text."""
        result_default = export_to_emr_format(patient_data, sample_trials)
        result_text = export_to_emr_format(patient_data, sample_trials, format="text")

        assert result_default == result_text

    def test_export_invalid_format_defaults_to_text(self, patient_data, sample_trials):
        """Test invalid format defaults to text."""
        result = export_to_emr_format(patient_data, sample_trials, format="invalid")
        assert "CLINICAL TRIAL SEARCH RESULTS" in result

    def test_export_minimal_patient_data(self):
        """Test export with minimal patient data."""
        patient_data = {}
        trials = [{"nct_id": "NCT12345678", "title": "Test"}]

        result = export_to_emr_format(patient_data, trials, format="text")
        assert "PATIENT CRITERIA:" in result
        assert "NCT12345678" in result

    def test_export_no_nearest_site(self, patient_data):
        """Test export when trial has no nearest_site."""
        trials = [{
            "nct_id": "NCT12345678",
            "title": "Test Trial",
            "phase": "Phase 2",
            "status": "Recruiting"
        }]

        result = export_to_emr_format(patient_data, trials, format="text")
        assert "NCT12345678" in result
        assert "Test Trial" in result


class TestEMRImport:
    """Test EMR import functions."""

    def test_import_from_csv(self):
        """Test importing patient data from CSV."""
        csv_content = """Patient_ID,Age,Cancer_Type,Stage,ECOG,Biomarkers
PT001,65,Lung Cancer,IV,1,"EGFR,PDL1"
PT002,58,Breast Cancer,III,0,HER2"""

        patients = import_from_csv(csv_content)

        assert len(patients) == 2

        assert patients[0]["patient_id"] == "PT001"
        assert patients[0]["age"] == 65
        assert patients[0]["cancer_type"] == "Lung Cancer"
        assert patients[0]["stage"] == "IV"
        assert patients[0]["ecog"] == "1"
        assert "EGFR" in patients[0]["biomarkers"]
        assert "PDL1" in patients[0]["biomarkers"]

        assert patients[1]["patient_id"] == "PT002"
        assert patients[1]["age"] == 58

    def test_import_missing_age(self):
        """Test import handles missing age."""
        csv_content = """Patient_ID,Age,Cancer_Type
PT001,,Lung Cancer"""

        patients = import_from_csv(csv_content)
        assert patients[0]["age"] is None

    def test_import_no_biomarkers(self):
        """Test import handles no biomarkers."""
        csv_content = """Patient_ID,Age,Biomarkers
PT001,65,"""

        patients = import_from_csv(csv_content)
        assert patients[0]["biomarkers"] == []


class TestReferralLetter:
    """Test referral letter generation."""

    @pytest.fixture
    def patient_data(self):
        """Sample patient data."""
        return {
            "age": 65,
            "cancer_type": "Lung Cancer",
            "stage": "IV",
            "ecog": 1,
            "prior_therapies": "Carboplatin/Pemetrexed",
            "PDL1": True,
            "EGFR": True
        }

    @pytest.fixture
    def trial_data(self):
        """Sample trial data."""
        return {
            "nct_id": "NCT12345678",
            "title": "Study of Drug X in Advanced Lung Cancer",
            "phase": "Phase 3"
        }

    def test_generate_referral_letter(self, patient_data, trial_data):
        """Test generating referral letter."""
        letter = generate_referral_letter(
            patient_data,
            trial_data,
            "Dr. John Smith"
        )

        assert "Date:" in letter
        assert "Trial Coordinator" in letter
        assert "NCT12345678" in letter
        assert "Study of Drug X" in letter
        assert "Phase 3" in letter
        assert "Age: 65" in letter
        assert "Lung Cancer" in letter
        assert "Stage IV" in letter
        assert "ECOG Performance Status: 1" in letter
        assert "Carboplatin/Pemetrexed" in letter
        assert "PDL1" in letter  # No hyphen in output
        assert "EGFR" in letter
        assert "Dr. John Smith" in letter

    def test_referral_letter_minimal_data(self):
        """Test referral letter with minimal data."""
        patient_data = {"cancer_type": "Lung Cancer"}
        trial_data = {"nct_id": "NCT12345678"}

        letter = generate_referral_letter(
            patient_data,
            trial_data,
            "Dr. Smith"
        )

        assert "NCT12345678" in letter
        assert "Lung Cancer" in letter
        assert "Dr. Smith" in letter

    def test_referral_letter_biomarker_formatting(self):
        """Test biomarker names are formatted correctly."""
        patient_data = {
            "cancer_type": "Lung Cancer",
            "MSI_HIGH": True,
            "TMB_HIGH": True
        }

        trial_data = {"nct_id": "NCT12345678"}

        letter = generate_referral_letter(patient_data, trial_data, "Dr. Smith")

        assert "MSI-HIGH" in letter
        assert "TMB-HIGH" in letter

    def test_referral_letter_no_biomarkers(self):
        """Test referral letter when no biomarkers present."""
        patient_data = {
            "age": 65,
            "cancer_type": "Lung Cancer"
        }

        trial_data = {"nct_id": "NCT12345678"}

        letter = generate_referral_letter(patient_data, trial_data, "Dr. Smith")

        assert "Biomarker Status" not in letter


class TestEMRInstructions:
    """Test EMR integration instructions."""

    def test_get_instructions(self):
        """Test getting EMR integration instructions."""
        instructions = get_emr_integration_instructions()

        assert isinstance(instructions, str)
        assert "EMR Integration" in instructions
        assert "Text Format" in instructions
        assert "CSV Format" in instructions
        assert "JSON Format" in instructions
        assert "CSV Import Template" in instructions
        assert "Patient_ID,Age,Cancer_Type" in instructions
