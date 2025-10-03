"""Unit tests for input validation utilities."""

import pytest
from trials.validators import (
    validate_age,
    validate_state,
    sanitize_text_input,
    validate_cancer_type,
    validate_nct_id,
    validate_ecog,
    validate_prior_therapies,
    validate_pagination
)


class TestValidateAge:
    """Test cases for age validation."""

    def test_valid_age(self):
        """Test valid age inputs."""
        assert validate_age(25) == (True, "")
        assert validate_age(0) == (True, "")
        assert validate_age(120) == (True, "")
        assert validate_age("65") == (True, "")

    def test_invalid_age_negative(self):
        """Test negative age."""
        is_valid, msg = validate_age(-1)
        assert is_valid is False
        assert "between 0 and 120" in msg

    def test_invalid_age_too_high(self):
        """Test age above maximum."""
        is_valid, msg = validate_age(121)
        assert is_valid is False
        assert "between 0 and 120" in msg

    def test_invalid_age_format(self):
        """Test invalid age format."""
        is_valid, msg = validate_age("abc")
        assert is_valid is False
        assert "Invalid age format" in msg

    def test_invalid_age_none(self):
        """Test None age."""
        is_valid, msg = validate_age(None)
        assert is_valid is False


class TestValidateState:
    """Test cases for state validation."""

    def test_valid_state_abbreviation(self):
        """Test valid state abbreviations."""
        assert validate_state("CA") == (True, "")
        assert validate_state("ca") == (True, "")
        assert validate_state("NY") == (True, "")
        assert validate_state("TX") == (True, "")

    def test_valid_state_full_name(self):
        """Test valid full state names."""
        assert validate_state("California") == (True, "")
        assert validate_state("CALIFORNIA") == (True, "")
        assert validate_state("New York") == (True, "")
        assert validate_state("Texas") == (True, "")

    def test_empty_state(self):
        """Test empty state (should be valid as it's optional)."""
        assert validate_state("") == (True, "")

    def test_invalid_state(self):
        """Test invalid state."""
        is_valid, msg = validate_state("XY")
        assert is_valid is False
        assert "valid US state" in msg

    def test_state_with_whitespace(self):
        """Test state with extra whitespace."""
        assert validate_state("  CA  ") == (True, "")


class TestSanitizeTextInput:
    """Test cases for text input sanitization."""

    def test_sanitize_normal_text(self):
        """Test sanitization of normal text."""
        result = sanitize_text_input("lung cancer")
        assert result == "lung cancer"

    def test_sanitize_html_tags(self):
        """Test removal of HTML tags."""
        result = sanitize_text_input("<script>alert('xss')</script>lung cancer")
        assert "<script>" not in result
        assert "lung cancer" in result

    def test_sanitize_sql_keywords(self):
        """Test removal of SQL keywords."""
        result = sanitize_text_input("DROP TABLE; lung cancer")
        assert "DROP" not in result
        assert "lung cancer" in result

    def test_sanitize_length_limit(self):
        """Test length limitation."""
        long_text = "a" * 1000
        result = sanitize_text_input(long_text, max_length=100)
        assert len(result) <= 100

    def test_sanitize_empty_string(self):
        """Test empty string."""
        result = sanitize_text_input("")
        assert result == ""

    def test_sanitize_special_chars(self):
        """Test removal of dangerous special characters."""
        result = sanitize_text_input("lung cancer <>&")
        assert "<" not in result or "&" not in result


class TestValidateCancerType:
    """Test cases for cancer type validation."""

    def test_valid_common_cancer(self):
        """Test valid common cancer types."""
        assert validate_cancer_type("lung cancer") == (True, "")
        assert validate_cancer_type("breast cancer") == (True, "")
        assert validate_cancer_type("prostate cancer") == (True, "")

    def test_valid_uncommon_cancer(self):
        """Test valid uncommon cancer types."""
        is_valid, msg = validate_cancer_type("rare sarcoma")
        assert is_valid is True

    def test_empty_cancer_type(self):
        """Test empty cancer type."""
        is_valid, msg = validate_cancer_type("")
        assert is_valid is False
        assert "required" in msg

    def test_too_short_cancer_type(self):
        """Test cancer type that's too short."""
        is_valid, msg = validate_cancer_type("ab")
        assert is_valid is False
        assert "at least 3 characters" in msg

    def test_cancer_type_with_sql_injection(self):
        """Test cancer type with SQL injection attempt."""
        # Sanitization should handle this
        is_valid, msg = validate_cancer_type("lung DROP TABLE")
        # Should still be valid after sanitization
        assert is_valid is True


class TestValidateNctId:
    """Test cases for NCT ID validation."""

    def test_valid_nct_id(self):
        """Test valid NCT IDs."""
        assert validate_nct_id("NCT12345678") == (True, "")
        assert validate_nct_id("nct12345678") == (True, "")
        assert validate_nct_id("NCT00000001") == (True, "")

    def test_empty_nct_id(self):
        """Test empty NCT ID (should be valid as it's optional)."""
        assert validate_nct_id("") == (True, "")

    def test_invalid_nct_id_format(self):
        """Test invalid NCT ID formats."""
        is_valid, msg = validate_nct_id("NCT1234567")  # 7 digits
        assert is_valid is False
        assert "NCT followed by 8 digits" in msg

    def test_invalid_nct_id_no_prefix(self):
        """Test NCT ID without prefix."""
        is_valid, msg = validate_nct_id("12345678")
        assert is_valid is False

    def test_invalid_nct_id_letters(self):
        """Test NCT ID with letters in number part."""
        is_valid, msg = validate_nct_id("NCTABCD1234")
        assert is_valid is False

    def test_nct_id_with_whitespace(self):
        """Test NCT ID with whitespace."""
        assert validate_nct_id("  NCT12345678  ") == (True, "")


class TestValidateEcog:
    """Test cases for ECOG validation."""

    def test_valid_ecog(self):
        """Test valid ECOG values."""
        assert validate_ecog("0") == (True, "")
        assert validate_ecog("1") == (True, "")
        assert validate_ecog("2") == (True, "")
        assert validate_ecog("3") == (True, "")
        assert validate_ecog("4") == (True, "")

    def test_empty_ecog(self):
        """Test empty ECOG (should be valid as it's optional)."""
        assert validate_ecog("") == (True, "")

    def test_invalid_ecog_range(self):
        """Test ECOG values outside valid range."""
        is_valid, msg = validate_ecog("5")
        assert is_valid is False
        assert "between 0 and 4" in msg

        is_valid, msg = validate_ecog("-1")
        assert is_valid is False

    def test_invalid_ecog_format(self):
        """Test invalid ECOG format."""
        is_valid, msg = validate_ecog("abc")
        assert is_valid is False
        assert "Invalid ECOG format" in msg


class TestValidatePriorTherapies:
    """Test cases for prior therapies validation."""

    def test_valid_prior_therapies(self):
        """Test valid number of prior therapies."""
        assert validate_prior_therapies(0) == (True, "")
        assert validate_prior_therapies(5) == (True, "")
        assert validate_prior_therapies(20) == (True, "")
        assert validate_prior_therapies("10") == (True, "")

    def test_invalid_prior_therapies_negative(self):
        """Test negative number of prior therapies."""
        is_valid, msg = validate_prior_therapies(-1)
        assert is_valid is False
        assert "between 0 and 20" in msg

    def test_invalid_prior_therapies_too_high(self):
        """Test too many prior therapies."""
        is_valid, msg = validate_prior_therapies(21)
        assert is_valid is False
        assert "between 0 and 20" in msg

    def test_invalid_prior_therapies_format(self):
        """Test invalid format."""
        is_valid, msg = validate_prior_therapies("abc")
        assert is_valid is False
        assert "Invalid number format" in msg


class TestValidatePagination:
    """Test cases for pagination validation."""

    def test_valid_page(self):
        """Test valid page numbers."""
        assert validate_pagination(0, 10) == 0
        assert validate_pagination(5, 10) == 5
        assert validate_pagination(9, 10) == 9

    def test_page_negative(self):
        """Test negative page number."""
        assert validate_pagination(-1, 10) == 0
        assert validate_pagination(-5, 10) == 0

    def test_page_too_high(self):
        """Test page number beyond total pages."""
        assert validate_pagination(10, 10) == 9
        assert validate_pagination(15, 10) == 9

    def test_page_zero_total(self):
        """Test with zero total pages."""
        assert validate_pagination(5, 0) == 5  # Should return as-is when no pages


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_none_inputs(self):
        """Test None inputs where applicable."""
        assert validate_state(None) == (False, "Please enter a valid US state (e.g., CA or California)")
        assert validate_ecog(None) == (True, "")

    def test_unicode_inputs(self):
        """Test unicode character handling."""
        result = sanitize_text_input("café ☕ cancer")
        # Should handle unicode gracefully

    def test_very_long_inputs(self):
        """Test very long inputs."""
        long_cancer = "a" * 10000
        is_valid, msg = validate_cancer_type(long_cancer)
        # Should be sanitized to max length
        assert is_valid is True

    def test_mixed_case_inputs(self):
        """Test mixed case handling."""
        assert validate_state("CaLiFoRnIa") == (True, "")
        assert validate_nct_id("nCt12345678") == (True, "")


class TestSecurityValidation:
    """Test security-related validation."""

    def test_xss_prevention(self):
        """Test XSS attack prevention."""
        malicious = '<img src=x onerror="alert(1)">'
        result = sanitize_text_input(malicious)
        assert "<img" not in result
        assert "onerror" not in result

    def test_sql_injection_prevention(self):
        """Test SQL injection prevention."""
        malicious = "'; DROP TABLE trials; --"
        result = sanitize_text_input(malicious)
        assert "DROP" not in result

    def test_script_tag_removal(self):
        """Test script tag removal."""
        malicious = "<script>window.location='evil.com'</script>"
        result = sanitize_text_input(malicious)
        assert "<script>" not in result
        assert "evil.com" not in result or "<script>" not in result
