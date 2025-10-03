"""Tests for trial normalization functions."""

import pytest
import json
import pandas as pd
from pathlib import Path
from trials.normalize import (
    normalize_trial,
    normalize_jsonl_file
)


class TestNormalizeTrial:
    """Test single trial normalization."""

    @pytest.fixture
    def sample_trial_data(self):
        """Sample trial data."""
        return {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Test Trial"
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
                        {"label": "Arm 1"},
                        {"label": "Arm 2"}
                    ]
                },
                "contactsLocationsModule": {
                    "locations": [
                        {"facility": "Hospital A", "country": "United States"},
                        {"facility": "Hospital B", "country": "Canada"},
                        {"facility": "Hospital C", "country": "United States"}
                    ]
                },
                "eligibilityModule": {
                    "eligibilityCriteria": "Age >= 18"
                },
                "outcomesModule": {
                    "primaryOutcomes": [
                        {"measure": "Overall Survival"}
                    ]
                }
            }
        }

    def test_basic_normalization(self, sample_trial_data):
        """Test basic trial normalization."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized is not None
        assert normalized.trial_id == "NCT12345678"
        assert normalized.title == "Test Trial"
        assert normalized.phase == "Phase 2"
        assert normalized.status == "Recruiting"

    def test_dates_extraction(self, sample_trial_data):
        """Test date extraction."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized.start_date == "2024-01-01"
        assert normalized.completion_date == "2026-01-01"
        assert normalized.last_updated == "2025-01-01"

    def test_enrollment_info(self, sample_trial_data):
        """Test enrollment information."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized.enrollment == 100
        assert normalized.enrollment_type == "ESTIMATED"

    def test_arms_count(self, sample_trial_data):
        """Test arm counting."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized.arms == 2

    def test_countries_extraction(self, sample_trial_data):
        """Test countries extraction and deduplication."""
        normalized = normalize_trial(sample_trial_data)

        assert len(normalized.countries) == 2
        assert "United States" in normalized.countries
        assert "Canada" in normalized.countries

    def test_study_design(self, sample_trial_data):
        """Test study design extraction."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized.study_type == "Interventional"
        assert normalized.allocation == "Randomized"
        assert normalized.masking == "Double"

    def test_eligibility_text(self, sample_trial_data):
        """Test eligibility text extraction."""
        normalized = normalize_trial(sample_trial_data)

        assert normalized.eligibility_text == "Age >= 18"

    def test_primary_outcomes(self, sample_trial_data):
        """Test primary outcomes extraction."""
        normalized = normalize_trial(sample_trial_data)

        assert len(normalized.primary_outcomes) == 1
        assert "Overall Survival" in normalized.primary_outcomes

    def test_minimal_data(self):
        """Test with minimal data."""
        minimal_data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT99999999",
                    "briefTitle": "Minimal Trial"
                }
            }
        }

        normalized = normalize_trial(minimal_data)

        assert normalized is not None
        assert normalized.trial_id == "NCT99999999"
        assert normalized.title == "Minimal Trial"
        assert normalized.phase is None
        assert normalized.arms == 0
        assert normalized.countries == []

    def test_invalid_data_returns_none(self):
        """Test that invalid data returns None."""
        invalid_data = {"invalid": "structure"}
        normalized = normalize_trial(invalid_data)

        assert normalized is None

    def test_missing_locations(self):
        """Test trial without locations."""
        data = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT12345678",
                    "briefTitle": "Test"
                }
            }
        }

        normalized = normalize_trial(data)
        assert normalized.countries == []

    def test_locations_without_country(self, sample_trial_data):
        """Test locations without country field."""
        sample_trial_data["protocolSection"]["contactsLocationsModule"]["locations"] = [
            {"facility": "Hospital", "city": "Boston"}
        ]

        normalized = normalize_trial(sample_trial_data)
        # Should filter out empty country strings
        assert "" not in normalized.countries


class TestNormalizeJsonlFile:
    """Test JSONL file normalization."""

    def test_normalize_jsonl_file(self, tmp_path):
        """Test normalizing a JSONL file."""
        # Create test JSONL file
        jsonl_file = tmp_path / "trials.jsonl"

        trials = [
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT11111111",
                        "briefTitle": "Trial 1"
                    }
                }
            },
            {
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT22222222",
                        "briefTitle": "Trial 2"
                    }
                }
            }
        ]

        with open(jsonl_file, "w") as f:
            for trial in trials:
                f.write(json.dumps(trial) + "\n")

        # Normalize
        df = normalize_jsonl_file(jsonl_file)

        assert len(df) == 2
        assert "trial_id" in df.columns
        assert "title" in df.columns
        assert df["trial_id"].tolist() == ["NCT11111111", "NCT22222222"]

    def test_handles_invalid_json(self, tmp_path):
        """Test handling of invalid JSON lines."""
        jsonl_file = tmp_path / "trials.jsonl"

        with open(jsonl_file, "w") as f:
            # Valid JSON
            f.write(json.dumps({
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT11111111",
                        "briefTitle": "Valid Trial"
                    }
                }
            }) + "\n")
            # Invalid JSON
            f.write("{ invalid json }\n")
            # Another valid JSON
            f.write(json.dumps({
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT22222222",
                        "briefTitle": "Another Valid"
                    }
                }
            }) + "\n")

        df = normalize_jsonl_file(jsonl_file)

        # Should skip the invalid line
        assert len(df) == 2

    def test_handles_failed_normalization(self, tmp_path):
        """Test handling of trials that fail normalization."""
        jsonl_file = tmp_path / "trials.jsonl"

        with open(jsonl_file, "w") as f:
            # Valid trial
            f.write(json.dumps({
                "protocolSection": {
                    "identificationModule": {
                        "nctId": "NCT11111111",
                        "briefTitle": "Valid"
                    }
                }
            }) + "\n")
            # Invalid structure (will fail normalization)
            f.write(json.dumps({"invalid": "structure"}) + "\n")

        df = normalize_jsonl_file(jsonl_file)

        # Should only include successfully normalized trial
        assert len(df) == 1
        assert df["trial_id"].iloc[0] == "NCT11111111"

    def test_empty_file(self, tmp_path):
        """Test with empty file."""
        jsonl_file = tmp_path / "empty.jsonl"
        jsonl_file.write_text("")

        df = normalize_jsonl_file(jsonl_file)

        assert len(df) == 0
        assert isinstance(df, pd.DataFrame)


class TestNormalizeAll:
    """Test batch normalization."""

    def test_normalize_all(self, tmp_path, monkeypatch):
        """Test normalizing all files in directory."""
        from trials.normalize import normalize_all
        import pandas as pd

        # Create input directory with JSONL files
        input_dir = tmp_path / "raw"
        input_dir.mkdir()
        output_file = tmp_path / "normalized.parquet"

        # Create two JSONL files
        file1 = input_dir / "trials_1.jsonl"
        file2 = input_dir / "trials_2.jsonl"

        trial1 = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT11111111",
                    "briefTitle": "Trial 1"
                }
            }
        }

        trial2 = {
            "protocolSection": {
                "identificationModule": {
                    "nctId": "NCT22222222",
                    "briefTitle": "Trial 2"
                }
            }
        }

        file1.write_text(json.dumps(trial1))
        file2.write_text(json.dumps(trial2))

        # Run normalization
        df = normalize_all(input_dir, output_file)

        # Verify
        assert len(df) == 2
        assert output_file.exists()

        # Verify saved parquet can be read
        saved_df = pd.read_parquet(output_file)
        assert len(saved_df) == 2
