"""Tests for financial information parsing and display."""

import pytest
from trials.financial_info import (
    parse_financial_info,
    _check_standard_of_care_coverage,
    _check_travel_reimbursement,
    _estimate_coverage_by_sponsor,
    format_financial_display,
    get_financial_assistance_resources
)


class TestParseFinancialInfo:
    """Test financial information parsing."""

    def test_parse_basic_info(self):
        """Test parsing basic financial information."""
        trial_data = {
            "protocolSection": {
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {
                        "name": "Pharma Corp",
                        "class": "INDUSTRY"
                    }
                },
                "descriptionModule": {
                    "briefSummary": "This is a trial",
                    "detailedDescription": "Trial details"
                }
            }
        }

        result = parse_financial_info(trial_data)

        assert result["sponsor_name"] == "Pharma Corp"
        assert result["sponsor_class"] == "INDUSTRY"
        assert "Industry-sponsored" in result["likely_coverage"]

    def test_parse_with_soc_coverage(self):
        """Test parsing with standard of care coverage mentioned."""
        trial_data = {
            "protocolSection": {
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Test", "class": "INDUSTRY"}
                },
                "descriptionModule": {
                    "briefSummary": "Sponsor covers standard of care procedures.",
                    "detailedDescription": ""
                }
            }
        }

        result = parse_financial_info(trial_data)
        assert result["covers_standard_of_care"] is True

    def test_parse_with_travel_reimbursement(self):
        """Test parsing with travel reimbursement mentioned."""
        trial_data = {
            "protocolSection": {
                "sponsorCollaboratorsModule": {
                    "leadSponsor": {"name": "Test", "class": "OTHER"}
                },
                "descriptionModule": {
                    "briefSummary": "",
                    "detailedDescription": "Travel reimbursement available for participants."
                }
            }
        }

        result = parse_financial_info(trial_data)
        assert result["travel_reimbursement"] is True

    def test_parse_empty_data(self):
        """Test parsing with minimal data."""
        trial_data = {"protocolSection": {}}

        result = parse_financial_info(trial_data)

        assert result["sponsor_name"] == "Unknown"
        assert result["sponsor_class"] == "Unknown"
        assert result["covers_standard_of_care"] is None
        assert result["travel_reimbursement"] is None


class TestCheckStandardOfCareCoverage:
    """Test standard of care coverage detection."""

    def test_positive_coverage(self):
        """Test detecting positive standard of care coverage."""
        text = "sponsor covers standard of care procedures"
        assert _check_standard_of_care_coverage(text) is True

        text = "standard of care provided at no cost"
        assert _check_standard_of_care_coverage(text) is True

        text = "sponsor pays for standard of care"
        assert _check_standard_of_care_coverage(text) is True

    def test_negative_coverage(self):
        """Test detecting no standard of care coverage."""
        text = "standard of care not covered by sponsor"
        assert _check_standard_of_care_coverage(text) is False

        text = "patient responsible for standard of care costs"
        assert _check_standard_of_care_coverage(text) is False

        text = "insurance will be billed for standard of care"
        assert _check_standard_of_care_coverage(text) is False

    def test_no_mention(self):
        """Test when standard of care is not mentioned."""
        text = "this is a clinical trial description"
        assert _check_standard_of_care_coverage(text) is None


class TestCheckTravelReimbursement:
    """Test travel reimbursement detection."""

    def test_travel_mentioned(self):
        """Test detecting travel reimbursement mention."""
        text = "travel reimbursement available"
        assert _check_travel_reimbursement(text) is True

        text = "lodging provided for out-of-town patients"
        assert _check_travel_reimbursement(text) is True

        text = "transportation assistance available"
        assert _check_travel_reimbursement(text) is True

        text = "mileage reimbursement provided"
        assert _check_travel_reimbursement(text) is True

    def test_no_travel_mention(self):
        """Test when travel is not mentioned."""
        text = "this is a clinical trial description"
        assert _check_travel_reimbursement(text) is None


class TestEstimateCoverageBySponsor:
    """Test coverage estimation by sponsor type."""

    def test_industry_sponsor(self):
        """Test industry sponsor coverage."""
        result = _estimate_coverage_by_sponsor("INDUSTRY", "Pharma Corp")
        assert "Industry-sponsored" in result
        assert "study drug" in result

    def test_nih_sponsor(self):
        """Test NIH sponsor coverage."""
        result = _estimate_coverage_by_sponsor("NIH", "National Institutes of Health")
        assert "NIH-sponsored" in result
        assert "no cost" in result
        assert "insurance" in result

    def test_federal_sponsor(self):
        """Test federal sponsor coverage."""
        result = _estimate_coverage_by_sponsor("FED", "Federal Agency")
        assert "Government-sponsored" in result
        assert "no cost" in result

    def test_other_gov_sponsor(self):
        """Test other government sponsor coverage."""
        result = _estimate_coverage_by_sponsor("OTHER_GOV", "State Department")
        assert "Government-sponsored" in result

    def test_nci_network(self):
        """Test NCI network coverage."""
        result = _estimate_coverage_by_sponsor("OTHER", "NCI Network")
        assert "Cancer center network" in result
        assert "insurance" in result

    def test_network_sponsor(self):
        """Test network sponsor coverage."""
        result = _estimate_coverage_by_sponsor("NETWORK_GROUP", "Trial Network")
        assert "network trials" in result

    def test_unknown_sponsor(self):
        """Test unknown sponsor type."""
        result = _estimate_coverage_by_sponsor("UNKNOWN", "Unknown Org")
        assert "Contact site" in result


class TestFormatFinancialDisplay:
    """Test financial information formatting."""

    def test_basic_display(self):
        """Test basic financial display formatting."""
        financial_info = {
            "sponsor_name": "Pharma Corp",
            "sponsor_class": "INDUSTRY",
            "likely_coverage": "Industry coverage details",
            "covers_standard_of_care": None,
            "travel_reimbursement": None
        }

        result = format_financial_display(financial_info)

        assert "### 💰 Financial Information" in result
        assert "Pharma Corp" in result
        assert "INDUSTRY" in result
        assert "Industry coverage details" in result
        assert "Contact site for details" in result

    def test_display_with_soc_covered(self):
        """Test display when standard of care is covered."""
        financial_info = {
            "sponsor_name": "Test",
            "sponsor_class": "OTHER",
            "likely_coverage": "",
            "covers_standard_of_care": True,
            "travel_reimbursement": None
        }

        result = format_financial_display(financial_info)
        assert "✅ **Standard of Care:** Likely covered" in result

    def test_display_with_soc_not_covered(self):
        """Test display when standard of care is not covered."""
        financial_info = {
            "sponsor_name": "Test",
            "sponsor_class": "OTHER",
            "likely_coverage": "",
            "covers_standard_of_care": False,
            "travel_reimbursement": None
        }

        result = format_financial_display(financial_info)
        assert "⚠️ **Standard of Care:** Billed to insurance" in result

    def test_display_with_travel(self):
        """Test display with travel reimbursement."""
        financial_info = {
            "sponsor_name": "Test",
            "sponsor_class": "OTHER",
            "likely_coverage": "",
            "covers_standard_of_care": None,
            "travel_reimbursement": True
        }

        result = format_financial_display(financial_info)
        assert "✅ **Travel:** Reimbursement may be available" in result

    def test_display_without_travel(self):
        """Test display without travel reimbursement."""
        financial_info = {
            "sponsor_name": "Test",
            "sponsor_class": "OTHER",
            "likely_coverage": "",
            "covers_standard_of_care": None,
            "travel_reimbursement": False
        }

        result = format_financial_display(financial_info)
        assert "Contact site regarding reimbursement" in result

    def test_display_important_notice(self):
        """Test display includes important notice."""
        financial_info = {
            "sponsor_name": "Test",
            "sponsor_class": "OTHER",
            "likely_coverage": "",
            "covers_standard_of_care": None,
            "travel_reimbursement": None
        }

        result = format_financial_display(financial_info)
        assert "💡 **Important:**" in result
        assert "Always verify" in result


class TestGetFinancialAssistanceResources:
    """Test financial assistance resources."""

    def test_resources_content(self):
        """Test that resources are returned."""
        result = get_financial_assistance_resources()

        # Check sections
        assert "Financial Assistance Resources" in result
        assert "Patient Assistance Programs" in result
        assert "Travel Assistance" in result
        assert "Insurance Assistance" in result
        assert "Drug Assistance" in result

    def test_resources_links(self):
        """Test that resource links are included."""
        result = get_financial_assistance_resources()

        # Check some key links
        assert "cancerfac.org" in result
        assert "patientadvocate.org" in result
        assert "cancercare.org" in result
        assert "corpangelnetwork.org" in result
        assert "medicare.gov" in result
        assert "needymeds.org" in result

    def test_resources_formatting(self):
        """Test resources are properly formatted."""
        result = get_financial_assistance_resources()

        # Should have markdown headers
        assert "###" in result
        assert "**" in result
        assert "- [" in result  # Markdown links