"""Tests for enrollment tracking functions."""

import pytest
from datetime import datetime, timedelta
from trials.enrollment_tracker import (
    parse_enrollment_data,
    calculate_enrollment_urgency,
    format_enrollment_display,
    get_actively_recruiting_sites
)


class TestEnrollmentParsing:
    """Test enrollment data parsing."""

    @pytest.fixture
    def sample_trial_data(self):
        """Sample trial data with enrollment info."""
        return {
            "protocolSection": {
                "statusModule": {
                    "overallStatus": "Recruiting",
                    "lastUpdateSubmitDate": "2025-01-01",
                    "startDateStruct": {"date": "2024-01-01"}
                },
                "designModule": {
                    "enrollmentInfo": {"count": 100}
                },
                "contactsLocationsModule": {
                    "locations": [
                        {
                            "facility": "Hospital A",
                            "city": "Boston",
                            "state": "MA",
                            "status": "Recruiting",
                            "contacts": [{"name": "Dr. Smith", "phone": "617-555-1234"}]
                        },
                        {
                            "facility": "Hospital B",
                            "city": "New York",
                            "state": "NY",
                            "status": "Not yet recruiting"
                        }
                    ]
                }
            }
        }

    def test_parse_basic_enrollment(self, sample_trial_data):
        """Test parsing basic enrollment data."""
        result = parse_enrollment_data(sample_trial_data)

        assert result["target_enrollment"] == 100
        assert result["overall_status"] == "Recruiting"
        assert result["total_sites"] == 2
        assert result["recruiting_sites"] == 1

    def test_parse_enrollment_dates(self, sample_trial_data):
        """Test parsing enrollment dates."""
        result = parse_enrollment_data(sample_trial_data)

        assert result["start_date"] == "2024-01-01"
        assert result["last_update_date"] == "2025-01-01"
        assert result["days_enrolling"] is not None

    def test_parse_site_details(self, sample_trial_data):
        """Test parsing site details."""
        result = parse_enrollment_data(sample_trial_data)

        sites = result["site_details"]
        assert len(sites) == 2

        assert sites[0]["facility"] == "Hospital A"
        assert sites[0]["city"] == "Boston"
        assert sites[0]["state"] == "MA"
        assert sites[0]["status"] == "Recruiting"
        assert sites[0]["contact"] == "Dr. Smith"
        assert sites[0]["phone"] == "617-555-1234"

        assert sites[1]["status"] == "Not yet recruiting"
        assert sites[1]["contact"] is None

    def test_parse_enrollment_velocity(self, sample_trial_data):
        """Test enrollment velocity calculation."""
        result = parse_enrollment_data(sample_trial_data)

        # Should calculate velocity for recruiting trials
        assert result["enrollment_velocity"] is not None
        assert isinstance(result["enrollment_velocity"], (int, float))

    def test_parse_no_enrollment_data(self):
        """Test parsing with minimal data."""
        trial_data = {"protocolSection": {}}
        result = parse_enrollment_data(trial_data)

        assert result["target_enrollment"] == 0
        assert result["overall_status"] == "Unknown"
        assert result["total_sites"] == 0

    def test_parse_no_start_date(self, sample_trial_data):
        """Test parsing without start date."""
        sample_trial_data["protocolSection"]["statusModule"]["startDateStruct"] = {}
        result = parse_enrollment_data(sample_trial_data)

        assert result["days_enrolling"] is None
        assert result["enrollment_velocity"] is None

    def test_parse_invalid_date_format(self, sample_trial_data):
        """Test handling invalid date format."""
        sample_trial_data["protocolSection"]["statusModule"]["startDateStruct"]["date"] = "invalid"
        result = parse_enrollment_data(sample_trial_data)

        assert result["days_enrolling"] is None

    def test_parse_active_not_recruiting(self, sample_trial_data):
        """Test parsing active but not recruiting trial."""
        sample_trial_data["protocolSection"]["statusModule"]["overallStatus"] = "Active, not recruiting"
        result = parse_enrollment_data(sample_trial_data)

        assert result["overall_status"] == "Active, not recruiting"
        assert result["enrollment_velocity"] is not None  # Should still calculate


class TestEnrollmentUrgency:
    """Test enrollment urgency calculation."""

    def test_urgency_closed(self):
        """Test urgency for closed trial."""
        enrollment_data = {
            "overall_status": "Active, not recruiting",
            "recruiting_sites": 0,
            "total_sites": 5
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert urgency == "CLOSED"
        assert "no longer recruiting" in wait_time.lower()

    def test_urgency_inactive(self):
        """Test urgency for inactive trial."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 0,
            "total_sites": 5
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert urgency == "INACTIVE"

    def test_urgency_high_velocity(self):
        """Test high urgency for fast enrollment."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 5,
            "total_sites": 10,
            "enrollment_velocity": 15
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "HIGH" in urgency
        assert "1-2 weeks" in wait_time

    def test_urgency_moderate_velocity(self):
        """Test moderate urgency."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 5,
            "total_sites": 10,
            "enrollment_velocity": 7
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "MODERATE" in urgency
        assert "2-4 weeks" in wait_time

    def test_urgency_low_velocity(self):
        """Test low urgency for slow enrollment."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 5,
            "total_sites": 10,
            "enrollment_velocity": 2
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "LOW" in urgency
        assert "4-8 weeks" in wait_time

    def test_urgency_no_velocity_high_sites(self):
        """Test urgency without velocity data using site ratio."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 8,
            "total_sites": 10,
            "enrollment_velocity": None
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "MODERATE" in urgency

    def test_urgency_no_velocity_low_sites(self):
        """Test urgency with low site ratio."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 2,
            "total_sites": 10,
            "enrollment_velocity": None
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "LOW" in urgency or "UNKNOWN" in urgency

    def test_urgency_unknown(self):
        """Test unknown urgency."""
        enrollment_data = {
            "overall_status": "Recruiting",
            "recruiting_sites": 1,
            "total_sites": 10,
            "enrollment_velocity": None
        }

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)
        assert "UNKNOWN" in urgency or "LOW" in urgency


class TestEnrollmentDisplay:
    """Test enrollment display formatting."""

    def test_format_display_complete(self):
        """Test formatting complete enrollment data."""
        enrollment_data = {
            "target_enrollment": 100,
            "total_sites": 10,
            "recruiting_sites": 8,
            "enrollment_velocity": 5.5,
            "days_enrolling": 120,
            "last_update_date": "2025-01-01",
            "overall_status": "Recruiting"
        }

        result = format_enrollment_display(enrollment_data)

        assert "Enrollment Status" in result
        assert "100 patients" in result
        assert "8 actively recruiting / 10 total" in result
        assert "5.5 patients/month" in result
        assert "120 days" in result
        assert "2025-01-01" in result

    def test_format_display_stale_data(self):
        """Test warning for stale data."""
        old_date = (datetime.now() - timedelta(days=200)).strftime("%Y-%m-%d")

        enrollment_data = {
            "target_enrollment": 100,
            "total_sites": 5,
            "recruiting_sites": 3,
            "last_update_date": old_date,
            "overall_status": "Recruiting"
        }

        result = format_enrollment_display(enrollment_data)

        assert "WARNING" in result
        assert "stale" in result.lower()

    def test_format_display_minimal(self):
        """Test formatting minimal data."""
        enrollment_data = {
            "target_enrollment": 50,
            "total_sites": 5,
            "recruiting_sites": 2,
            "overall_status": "Recruiting"
        }

        result = format_enrollment_display(enrollment_data)

        assert "50 patients" in result
        assert "2 actively recruiting / 5 total" in result

    def test_format_invalid_date(self):
        """Test handling invalid date format."""
        enrollment_data = {
            "target_enrollment": 100,
            "total_sites": 5,
            "recruiting_sites": 3,
            "last_update_date": "invalid-date",
            "overall_status": "Recruiting"
        }

        result = format_enrollment_display(enrollment_data)
        assert "invalid-date" in result


class TestActivelyRecruitingSites:
    """Test filtering actively recruiting sites."""

    def test_get_recruiting_sites(self):
        """Test getting actively recruiting sites."""
        enrollment_data = {
            "site_details": [
                {"facility": "Hospital A", "status": "Recruiting"},
                {"facility": "Hospital B", "status": "Not yet recruiting"},
                {"facility": "Hospital C", "status": "Recruiting"},
                {"facility": "Hospital D", "status": "Completed"}
            ]
        }

        recruiting = get_actively_recruiting_sites(enrollment_data)

        assert len(recruiting) == 2
        assert recruiting[0]["facility"] == "Hospital A"
        assert recruiting[1]["facility"] == "Hospital C"

    def test_no_recruiting_sites(self):
        """Test when no sites are recruiting."""
        enrollment_data = {
            "site_details": [
                {"facility": "Hospital A", "status": "Completed"}
            ]
        }

        recruiting = get_actively_recruiting_sites(enrollment_data)
        assert len(recruiting) == 0

    def test_empty_sites(self):
        """Test with empty site details."""
        enrollment_data = {"site_details": []}

        recruiting = get_actively_recruiting_sites(enrollment_data)
        assert len(recruiting) == 0
