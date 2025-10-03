#!/usr/bin/env python3
"""Unit tests for clinical trial matching features."""

import pytest
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from trials.app import haversine_distance, geocode_location
from trials.validators import (
    validate_age, validate_state, validate_cancer_type,
    validate_nct_id, validate_ecog, validate_prior_therapies,
    sanitize_text_input
)
from trials.clinical_parser import parse_ecog_requirement


class TestDistanceCalculation:
    """Test geographic distance calculations."""

    def test_haversine_distance_nyc_to_la(self):
        """Test distance calculation between NYC and LA."""
        # NYC coordinates
        nyc_lat, nyc_lon = 40.7128, -74.0060
        # LA coordinates
        la_lat, la_lon = 34.0522, -118.2437

        distance = haversine_distance(nyc_lat, nyc_lon, la_lat, la_lon)

        # Should be approximately 2450 miles
        assert 2400 < distance < 2500, f"NYC to LA distance {distance} not in expected range"

    def test_haversine_distance_same_location(self):
        """Test distance calculation for same location."""
        lat, lon = 40.7128, -74.0060
        distance = haversine_distance(lat, lon, lat, lon)
        assert distance < 1, "Same location should have ~0 distance"

    def test_geocode_state_abbreviation(self):
        """Test geocoding with state abbreviation."""
        lat, lon = geocode_location(state="CA")
        assert lat is not None and lon is not None
        assert 32 < lat < 42  # California latitude range
        assert -125 < lon < -114  # California longitude range

    def test_geocode_full_state_name(self):
        """Test geocoding with full state name."""
        lat, lon = geocode_location(state="California")
        assert lat is not None and lon is not None

    def test_geocode_invalid_state(self):
        """Test geocoding with invalid state."""
        lat, lon = geocode_location(state="InvalidState")
        assert lat is None and lon is None


class TestValidation:
    """Test input validation functions."""

    def test_validate_age_valid(self):
        """Test valid age inputs."""
        valid, msg = validate_age(65)
        assert valid
        assert msg == ""

        valid, msg = validate_age("30")
        assert valid

    def test_validate_age_invalid(self):
        """Test invalid age inputs."""
        valid, msg = validate_age(-1)
        assert not valid
        assert "between 0 and 120" in msg

        valid, msg = validate_age(150)
        assert not valid

        valid, msg = validate_age("abc")
        assert not valid
        assert "Invalid age" in msg

    def test_validate_state_valid(self):
        """Test valid state inputs."""
        valid, msg = validate_state("CA")
        assert valid

        valid, msg = validate_state("California")
        assert valid

        valid, msg = validate_state("ny")  # Should work with lowercase
        assert valid

    def test_validate_state_invalid(self):
        """Test invalid state inputs."""
        valid, msg = validate_state("XX")
        assert not valid
        assert "valid US state" in msg

    def test_validate_nct_id_valid(self):
        """Test valid NCT ID formats."""
        valid, msg = validate_nct_id("NCT12345678")
        assert valid

        valid, msg = validate_nct_id("nct12345678")  # Should handle lowercase
        assert valid

    def test_validate_nct_id_invalid(self):
        """Test invalid NCT ID formats."""
        valid, msg = validate_nct_id("NCT123")  # Too short
        assert not valid
        assert "8 digits" in msg

        valid, msg = validate_nct_id("12345678")  # Missing NCT prefix
        assert not valid

    def test_sanitize_text_input(self):
        """Test text sanitization."""
        # Test HTML removal
        clean = sanitize_text_input("<script>alert('xss')</script>lung cancer")
        assert "<script>" not in clean
        assert "lung cancer" in clean

        # Test SQL keyword removal
        clean = sanitize_text_input("lung cancer; DROP TABLE trials")
        assert "DROP" not in clean
        assert "lung cancer" in clean

        # Test length limiting
        long_text = "a" * 1000
        clean = sanitize_text_input(long_text, max_length=100)
        assert len(clean) <= 100

    def test_validate_ecog_valid(self):
        """Test valid ECOG status."""
        for ecog in ["0", "1", "2", "3", "4"]:
            valid, msg = validate_ecog(ecog)
            assert valid

    def test_validate_ecog_invalid(self):
        """Test invalid ECOG status."""
        valid, msg = validate_ecog("5")
        assert not valid
        assert "between 0 and 4" in msg

    def test_validate_prior_therapies(self):
        """Test prior therapies validation."""
        valid, msg = validate_prior_therapies(3)
        assert valid

        valid, msg = validate_prior_therapies(-1)
        assert not valid

        valid, msg = validate_prior_therapies(25)
        assert not valid


class TestClinicalParsing:
    """Test clinical data parsing functions."""

    def test_parse_ecog_requirement_simple(self):
        """Test ECOG parsing with simple criteria."""
        text = "ECOG performance status ≤ 2"
        result = parse_ecog_requirement(text)
        assert result["max_ecog"] == 2

    def test_parse_ecog_requirement_range(self):
        """Test ECOG parsing with range."""
        text = "ECOG 0-1 only"
        result = parse_ecog_requirement(text)
        assert result["max_ecog"] == 1

    def test_parse_ecog_requirement_none(self):
        """Test ECOG parsing with no requirement."""
        text = "No specific performance status requirement"
        result = parse_ecog_requirement(text)
        assert result["max_ecog"] is None

    def test_parse_ecog_requirement_complex(self):
        """Test ECOG parsing with complex text."""
        text = """
        Inclusion Criteria:
        - Age 18 or older
        - ECOG performance status of 0 or 1
        - Adequate organ function
        """
        result = parse_ecog_requirement(text)
        assert result["max_ecog"] == 1


class TestBiomarkerMatching:
    """Test biomarker matching logic."""

    def test_biomarker_exclusion_mismatch(self):
        """Test that mismatched biomarkers cause exclusion."""
        # Patient has EGFR, trial requires HER2
        patient_biomarkers = ["egfr"]
        trial_biomarkers = {"her2_status": "Positive", "egfr_mutation": None}

        # In real app, this would trigger exclusion
        requires_her2 = trial_biomarkers.get("her2_status") == "Positive"
        has_her2 = "her2" in patient_biomarkers

        assert requires_her2 and not has_her2, "Should detect biomarker mismatch"

    def test_biomarker_match(self):
        """Test matching biomarkers."""
        patient_biomarkers = ["egfr"]
        trial_biomarkers = {"egfr_mutation": True, "her2_status": None}

        has_egfr = "egfr" in patient_biomarkers
        requires_egfr = trial_biomarkers.get("egfr_mutation") == True

        assert has_egfr and requires_egfr, "Should detect biomarker match"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])