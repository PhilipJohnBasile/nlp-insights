"""Tests for similar patients analysis."""

import json
import pytest
from pathlib import Path
from trials.similar_patients import (
    SimilarPatientsAnalyzer,
    format_similar_patients_display
)


class TestSimilarPatientsAnalyzer:
    """Test similar patients analysis."""

    def test_init(self, tmp_path):
        """Test initialization creates directory."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))
        assert analyzer.data_dir.exists()
        assert analyzer.enrollments_file == analyzer.data_dir / "enrollments_anonymized.json"

    def test_record_enrollment(self, tmp_path):
        """Test recording an enrollment."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient = {
            "age": 65,
            "cancer_type": "Lung Cancer",
            "stage": "IV",
            "prior_lines": 2,
            "ecog": 1,
            "biomarkers": ["EGFR", "PDL1"]
        }

        analyzer.record_enrollment("NCT12345678", patient, "enrolled")

        assert len(analyzer.enrollments) == 1
        enrollment = analyzer.enrollments[0]
        assert enrollment["nct_id"] == "NCT12345678"
        assert enrollment["outcome"] == "enrolled"
        assert enrollment["profile"]["age_range"] == "60-69"
        assert enrollment["profile"]["cancer_type"] == "Lung Cancer"

    def test_bucket_age(self, tmp_path):
        """Test age bucketing for privacy."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        assert analyzer._bucket_age(None) is None
        assert analyzer._bucket_age(25) == "18-39"
        assert analyzer._bucket_age(39) == "18-39"
        assert analyzer._bucket_age(40) == "40-49"
        assert analyzer._bucket_age(49) == "40-49"
        assert analyzer._bucket_age(50) == "50-59"
        assert analyzer._bucket_age(59) == "50-59"
        assert analyzer._bucket_age(60) == "60-69"
        assert analyzer._bucket_age(69) == "60-69"
        assert analyzer._bucket_age(70) == "70+"
        assert analyzer._bucket_age(85) == "70+"

    def test_find_similar_patients_no_data(self, tmp_path):
        """Test finding similar patients with no data."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}
        stats = analyzer.find_similar_patients(patient)

        assert stats["total_similar"] == 0
        assert stats["enrolled"] == 0
        assert stats["screen_failed"] == 0
        assert stats["declined"] == 0
        assert stats["success_rate"] is None

    def test_find_similar_patients_with_matches(self, tmp_path):
        """Test finding similar patients with matches."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        # Record several enrollments
        patient1 = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}
        patient2 = {"age": 66, "cancer_type": "Lung Cancer", "ecog": 1}
        patient3 = {"age": 67, "cancer_type": "Lung Cancer", "ecog": 2}
        patient4 = {"age": 45, "cancer_type": "Breast Cancer", "ecog": 1}

        analyzer.record_enrollment("NCT001", patient1, "enrolled")
        analyzer.record_enrollment("NCT002", patient2, "screen_failed")
        analyzer.record_enrollment("NCT003", patient3, "enrolled")
        analyzer.record_enrollment("NCT004", patient4, "declined")

        # Search for similar to patient1
        search_patient = {"age": 64, "cancer_type": "Lung Cancer", "ecog": 1}
        stats = analyzer.find_similar_patients(search_patient)

        # Should match patients 1 and 2 (same age range, cancer type, ECOG)
        assert stats["total_similar"] >= 2
        assert stats["enrolled"] >= 1
        assert stats["success_rate"] is not None

    def test_find_similar_patients_with_specific_trial(self, tmp_path):
        """Test finding similar patients for a specific trial."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient1 = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}
        patient2 = {"age": 66, "cancer_type": "Lung Cancer", "ecog": 1}

        analyzer.record_enrollment("NCT001", patient1, "enrolled")
        analyzer.record_enrollment("NCT002", patient2, "enrolled")

        search_patient = {"age": 64, "cancer_type": "Lung Cancer", "ecog": 1}

        # Search for NCT001 only
        stats = analyzer.find_similar_patients(search_patient, nct_id="NCT001")
        assert stats["total_similar"] == 1
        assert stats["enrolled"] == 1

    def test_match_score_calculation(self, tmp_path):
        """Test that match score requires 2 of 3 criteria."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        # Base patient
        base_patient = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}
        analyzer.record_enrollment("NCT001", base_patient, "enrolled")

        # Test cases
        # 3/3 match - should match
        search1 = {"age": 66, "cancer_type": "Lung Cancer", "ecog": 1}
        stats1 = analyzer.find_similar_patients(search1)
        assert stats1["total_similar"] == 1

        # 2/3 match (different ECOG) - should match
        search2 = {"age": 67, "cancer_type": "Lung Cancer", "ecog": 2}
        stats2 = analyzer.find_similar_patients(search2)
        assert stats2["total_similar"] == 1

        # 1/3 match (only cancer type) - should NOT match
        search3 = {"age": 45, "cancer_type": "Lung Cancer", "ecog": 3}
        stats3 = analyzer.find_similar_patients(search3)
        assert stats3["total_similar"] == 0

    def test_get_alternative_trials(self, tmp_path):
        """Test getting alternative trials."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}

        # Record enrollments in different trials
        analyzer.record_enrollment("NCT001", patient, "enrolled")
        analyzer.record_enrollment("NCT001", patient, "enrolled")
        analyzer.record_enrollment("NCT002", patient, "enrolled")
        analyzer.record_enrollment("NCT003", patient, "screen_failed")

        alternatives = analyzer.get_alternative_trials(patient, exclude_nct="NCT004")

        # Should return trials sorted by enrollment count
        assert len(alternatives) >= 2
        assert alternatives[0]["nct_id"] == "NCT001"  # 2 enrollments
        assert alternatives[0]["similar_enrolled"] == 2
        assert alternatives[1]["nct_id"] == "NCT002"  # 1 enrollment
        assert alternatives[1]["similar_enrolled"] == 1

    def test_get_alternative_trials_excludes_current(self, tmp_path):
        """Test that alternative trials exclude current trial."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}

        analyzer.record_enrollment("NCT001", patient, "enrolled")
        analyzer.record_enrollment("NCT002", patient, "enrolled")

        alternatives = analyzer.get_alternative_trials(patient, exclude_nct="NCT001")

        # NCT001 should be excluded
        nct_ids = [alt["nct_id"] for alt in alternatives]
        assert "NCT001" not in nct_ids
        assert "NCT002" in nct_ids

    def test_persistence(self, tmp_path):
        """Test data persistence across instances."""
        data_dir = str(tmp_path / "analytics")

        # Create analyzer and record enrollment
        analyzer1 = SimilarPatientsAnalyzer(data_dir=data_dir)
        patient = {"age": 65, "cancer_type": "Lung Cancer", "ecog": 1}
        analyzer1.record_enrollment("NCT001", patient, "enrolled")

        # Create new analyzer instance
        analyzer2 = SimilarPatientsAnalyzer(data_dir=data_dir)

        assert len(analyzer2.enrollments) == 1
        assert analyzer2.enrollments[0]["nct_id"] == "NCT001"

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from corrupted file returns empty list."""
        data_dir = tmp_path / "analytics"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted JSON file
        enrollments_file = data_dir / "enrollments_anonymized.json"
        with open(enrollments_file, 'w') as f:
            f.write("{ corrupted json }")

        analyzer = SimilarPatientsAnalyzer(data_dir=str(data_dir))
        assert analyzer.enrollments == []

    def test_enrollment_timestamp(self, tmp_path):
        """Test that enrollments have timestamps."""
        analyzer = SimilarPatientsAnalyzer(data_dir=str(tmp_path / "analytics"))

        patient = {"age": 65, "cancer_type": "Lung Cancer"}
        analyzer.record_enrollment("NCT001", patient, "enrolled")

        assert "timestamp" in analyzer.enrollments[0]


class TestFormatSimilarPatientsDisplay:
    """Test formatting of similar patients display."""

    def test_no_similar_patients(self):
        """Test display when no similar patients found."""
        stats = {
            "total_similar": 0,
            "enrolled": 0,
            "screen_failed": 0,
            "declined": 0,
            "success_rate": None
        }

        result = format_similar_patients_display(stats)

        assert "### 👥 Similar Patients" in result
        assert "No similar patient data available" in result
        assert "As more patients use this system" in result

    def test_similar_patients_found(self):
        """Test display with similar patients."""
        stats = {
            "total_similar": 10,
            "enrolled": 6,
            "screen_failed": 2,
            "declined": 2,
            "success_rate": 60.0
        }

        result = format_similar_patients_display(stats)

        assert "### 👥 Similar Patients" in result
        assert "**10** patients with similar profiles" in result
        assert "**Success Rate:** 60.0% enrolled" in result
        assert "✅ Enrolled: 6" in result
        assert "❌ Screen Failed: 2" in result
        assert "⏸️ Declined: 2" in result

    def test_privacy_note(self):
        """Test privacy note is included."""
        stats = {
            "total_similar": 5,
            "enrolled": 3,
            "screen_failed": 1,
            "declined": 1,
            "success_rate": 60.0
        }

        result = format_similar_patients_display(stats)
        assert "anonymized and aggregated for privacy" in result

    def test_no_success_rate(self):
        """Test display when success rate is None."""
        stats = {
            "total_similar": 5,
            "enrolled": 0,
            "screen_failed": 3,
            "declined": 2,
            "success_rate": None
        }

        result = format_similar_patients_display(stats)
        # Should not show success rate
        assert "Success Rate:" not in result or "None" not in result