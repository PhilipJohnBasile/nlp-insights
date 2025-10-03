"""Integration tests for data processing pipeline (fixed version)."""

import pytest
import pandas as pd
import copy
from trials import models


@pytest.fixture
def sample_trial_data():
    """Create sample trial data for testing."""
    return {
        "protocolSection": {
            "identificationModule": {
                "nctId": "NCT12345678",
                "briefTitle": "Test Trial for Advanced NSCLC",
                "officialTitle": "A Phase 2 Trial of Novel Agent"
            },
            "statusModule": {
                "overallStatus": "RECRUITING",
                "startDateStruct": {"date": "2024-01-01"},
                "completionDateStruct": {"date": "2025-12-31"}
            },
            "sponsorCollaboratorsModule": {
                "leadSponsor": {"name": "Test Pharma"}
            },
            "descriptionModule": {
                "briefSummary": "Testing a novel agent in NSCLC patients"
            },
            "designModule": {
                "phases": ["PHASE2"],
                "studyType": "INTERVENTIONAL"
            },
            "armsInterventionsModule": {
                "interventions": [
                    {"name": "Novel Agent", "type": "DRUG"}
                ]
            },
            "eligibilityModule": {
                "eligibilityCriteria": """
                Inclusion Criteria:
                - Age ≥18 years
                - EGFR mutation positive NSCLC
                - ECOG 0-1

                Exclusion Criteria:
                - Brain metastases
                - Prior EGFR TKI
                """,
                "sex": "ALL",
                "minimumAge": "18 Years",
                "maximumAge": "N/A"
            }
        }
    }


@pytest.fixture
def sample_location_data():
    """Create sample location data for testing."""
    return {
        "protocolSection": {
            "contactsLocationsModule": {
                "locations": [
                    {
                        "facility": "Test Hospital",
                        "city": "Boston",
                        "state": "Massachusetts",
                        "country": "United States",
                        "status": "RECRUITING"
                    },
                    {
                        "facility": "Memorial Center",
                        "city": "New York",
                        "state": "New York",
                        "country": "United States",
                        "status": "NOT_YET_RECRUITING"
                    }
                ]
            }
        }
    }


class TestModelNormalization:
    """Test Pydantic model validation and normalization."""

    def test_trial_model_validation(self, sample_trial_data):
        """Test that trial data validates correctly."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)

        assert trial is not None
        assert trial.protocol_section is not None
        assert trial.get_nct_id() == "NCT12345678"
        assert trial.get_status() == "RECRUITING"

    def test_trial_id_extraction(self, sample_trial_data):
        """Test NCT ID extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        nct_id = trial.get_nct_id()

        assert nct_id.startswith("NCT")
        assert len(nct_id) == 11  # NCT + 8 digits

    def test_missing_optional_fields(self):
        """Test handling of missing optional fields."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                    "briefTitle": "Minimal Trial"
                },
                "statusModule": {
                    "overallStatus": "RECRUITING"
                }
            }
        }

        trial = models.ClinicalTrial.model_validate(minimal_data)
        assert trial.get_nct_id() == "NCT00000001"


class TestDataExtraction:
    """Test data extraction from models."""

    def test_extract_basic_fields(self, sample_trial_data):
        """Test basic field extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)

        trial_id = trial.get_nct_id()
        title = trial.get_title()
        status = trial.get_status()
        phase = trial.get_phase()

        assert trial_id == "NCT12345678"
        assert "NSCLC" in title
        assert status == "RECRUITING"
        assert phase == "PHASE2"

    def test_extract_multiple_trials(self, sample_trial_data):
        """Test extracting data from multiple trials."""
        trials_data = [sample_trial_data, copy.deepcopy(sample_trial_data)]
        trials_data[1]["protocolSection"]["identificationModule"]["nctId"] = "NCT87654321"

        trials = [models.ClinicalTrial.model_validate(t) for t in trials_data]
        trial_ids = [t.get_nct_id() for t in trials]

        assert len(trial_ids) == 2
        assert trial_ids[0] != trial_ids[1]

    def test_extract_dates(self, sample_trial_data):
        """Test date field extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        start_date = trial.get_start_date()
        completion_date = trial.get_completion_date()

        assert start_date == "2024-01-01"
        assert completion_date == "2025-12-31"


class TestEligibilityExtraction:
    """Test eligibility criteria extraction."""

    def test_extract_eligibility_text(self, sample_trial_data):
        """Test eligibility text extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        elig_text = trial.get_eligibility_text()

        assert "EGFR mutation" in elig_text
        assert "Inclusion" in elig_text
        assert "Exclusion" in elig_text

    def test_extract_age_requirements(self, sample_trial_data):
        """Test age requirement extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        elig_module = trial.get_eligibility_module()
        min_age = elig_module.get("minimumAge")
        max_age = elig_module.get("maximumAge")

        assert min_age == "18 Years"
        assert max_age == "N/A"

    def test_extract_sex_requirement(self, sample_trial_data):
        """Test sex requirement extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        elig_module = trial.get_eligibility_module()
        sex = elig_module.get("sex")

        assert sex == "ALL"


class TestFeatureExtraction:
    """Test feature extraction from trials."""

    def test_extract_biomarker_features(self, sample_trial_data):
        """Test biomarker feature extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        elig_text = trial.get_eligibility_text()

        # Should detect EGFR mutation requirement
        assert "egfr" in elig_text.lower()

    def test_extract_phase(self, sample_trial_data):
        """Test phase extraction."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        phase = trial.get_phase()

        assert phase == "PHASE2"


class TestRiskAnalysis:
    """Test risk factor analysis."""

    def test_identify_exclusion_criteria(self, sample_trial_data):
        """Test identification of exclusion criteria."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        elig_text = trial.get_eligibility_text()

        # Should identify brain mets and prior therapy exclusions
        assert "brain metastases" in elig_text.lower()
        assert "prior" in elig_text.lower()


class TestLocationProcessing:
    """Test location data processing."""

    def test_extract_locations(self, sample_location_data):
        """Test location extraction."""
        trial = models.ClinicalTrial.model_validate(sample_location_data)
        locations = trial.get_locations()

        assert len(locations) == 2
        assert locations[0]["city"] == "Boston"
        assert locations[1]["city"] == "New York"

    def test_filter_recruiting_sites(self, sample_location_data):
        """Test filtering for recruiting sites."""
        trial = models.ClinicalTrial.model_validate(sample_location_data)
        locations = trial.get_locations()

        recruiting = [loc for loc in locations if loc.get("status") == "RECRUITING"]

        assert len(recruiting) == 1
        assert recruiting[0]["city"] == "Boston"


class TestEndToEndPipeline:
    """Test complete pipeline from raw data to extracted information."""

    def test_complete_trial_processing(self, sample_trial_data):
        """Test processing trial through complete pipeline."""
        # Step 1: Validate with Pydantic
        trial = models.ClinicalTrial.model_validate(sample_trial_data)
        assert trial is not None

        # Step 2: Extract basic fields
        trial_id = trial.get_nct_id()
        title = trial.get_title()
        status = trial.get_status()

        assert trial_id == "NCT12345678"
        assert title is not None
        assert status == "RECRUITING"

        # Step 3: Extract eligibility
        elig_text = trial.get_eligibility_text()
        assert trial_id == "NCT12345678"
        assert len(elig_text) > 0

    def test_dataframe_conversion(self, sample_trial_data):
        """Test conversion to DataFrame format."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)

        # Extract fields manually for DataFrame
        trial_dict = {
            "trial_id": trial.get_nct_id(),
            "title": trial.get_title(),
            "status": trial.get_status(),
            "phase": trial.get_phase()
        }

        df = pd.DataFrame([trial_dict])

        assert len(df) == 1
        assert "trial_id" in df.columns
        assert "title" in df.columns
        assert "status" in df.columns
        assert df.iloc[0]["trial_id"] == "NCT12345678"

    def test_multiple_trials_pipeline(self, sample_trial_data):
        """Test processing multiple trials through pipeline."""
        trials_data = []
        for i in range(5):
            trial_copy = copy.deepcopy(sample_trial_data)
            trial_copy["protocolSection"]["identificationModule"]["nctId"] = f"NCT0000000{i}"
            trials_data.append(trial_copy)

        # Process all trials
        trials = [models.ClinicalTrial.model_validate(t) for t in trials_data]
        trial_dicts = [
            {
                "trial_id": t.get_nct_id(),
                "title": t.get_title(),
                "status": t.get_status(),
                "phase": t.get_phase()
            }
            for t in trials
        ]

        df = pd.DataFrame(trial_dicts)

        assert len(df) == 5
        assert df["trial_id"].nunique() == 5
        assert all(df["status"] == "RECRUITING")


class TestDataQuality:
    """Test data quality and validation."""

    def test_no_duplicate_trial_ids(self, sample_trial_data):
        """Test that duplicate trial IDs are handled."""
        trials_data = [sample_trial_data, copy.deepcopy(sample_trial_data)]

        trials = [models.ClinicalTrial.model_validate(t) for t in trials_data]
        trial_dicts = [
            {
                "trial_id": t.get_nct_id(),
                "title": t.get_title(),
                "status": t.get_status()
            }
            for t in trials
        ]

        df = pd.DataFrame(trial_dicts)

        # Should have duplicate IDs
        assert len(df) == 2
        assert df["trial_id"].nunique() == 1

        # After deduplication
        df_dedup = df.drop_duplicates(subset=["trial_id"])
        assert len(df_dedup) == 1

    def test_required_fields_present(self, sample_trial_data):
        """Test that all required fields are present."""
        trial = models.ClinicalTrial.model_validate(sample_trial_data)

        # Test required methods return values
        assert trial.get_nct_id() is not None
        assert trial.get_title() is not None
        assert trial.get_status() is not None

    def test_handle_null_values(self):
        """Test handling of null/missing values."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT00000001",
                    "briefTitle": "Minimal Trial"
                },
                "statusModule": {
                    "overallStatus": "RECRUITING"
                }
            }
        }

        trial = models.ClinicalTrial.model_validate(minimal_data)

        # Should handle missing optional fields gracefully
        assert trial.get_nct_id() is not None
        assert trial.get_nct_id() == "NCT00000001"
        # Optional fields can be None
        assert trial.get_phase() is None  # No design module


class TestErrorHandling:
    """Test error handling in pipeline."""

    def test_invalid_trial_data(self):
        """Test handling of invalid trial data."""
        invalid_data = {"invalid": "structure"}

        with pytest.raises(Exception):
            models.ClinicalTrial.model_validate(invalid_data)

    def test_missing_required_nct_id(self):
        """Test handling of missing NCT ID."""
        invalid_data = {
            "protocolSection": {
                "identificationModule": {
                    "briefTitle": "No NCT ID Trial"
                }
            }
        }

        # Model validates but get_nct_id() returns empty string
        trial = models.ClinicalTrial.model_validate(invalid_data)
        nct_id = trial.get_nct_id()
        assert nct_id == ""  # Missing NCT ID returns empty string

    def test_empty_trial_list(self):
        """Test handling of empty trial list."""
        trials = []
        trial_dicts = [
            {
                "trial_id": t.get_nct_id(),
                "title": t.get_title()
            }
            for t in trials
        ]

        assert len(trial_dicts) == 0

        df = pd.DataFrame(trial_dicts) if trial_dicts else pd.DataFrame()
        assert len(df) == 0
