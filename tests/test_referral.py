"""Tests for referral tracking system."""

import pytest
import json
from pathlib import Path
from datetime import datetime, timedelta
from trials.referral_tracker import ReferralTracker, REFERRAL_STATUSES
import tempfile
import shutil
import pandas as pd


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def tracker(temp_dir):
    """Create referral tracker with temporary directory."""
    return ReferralTracker(data_dir=temp_dir)


class TestReferralTracker:
    """Test ReferralTracker class."""

    def test_initialization(self, tracker, temp_dir):
        """Test tracker initializes correctly."""
        assert tracker.data_dir == Path(temp_dir)
        assert tracker.data_dir.exists()
        assert tracker.referrals_file.name == "referrals.json"
        assert isinstance(tracker.referrals, list)

    def test_add_referral_basic(self, tracker):
        """Test adding basic referral."""
        ref_id = tracker.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="University Hospital"
        )

        assert ref_id.startswith("REF")
        assert len(tracker.referrals) == 1

        ref = tracker.referrals[0]
        assert ref["referral_id"] == ref_id
        assert ref["patient_id"] == "PT001"
        assert ref["nct_id"] == "NCT12345678"
        assert ref["trial_title"] == "Test Trial"
        assert ref["site_name"] == "University Hospital"
        assert ref["status"] == "Referred"

    def test_add_referral_with_contact(self, tracker):
        """Test adding referral with contact info."""
        ref_id = tracker.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="Hospital",
            site_contact="Dr. Smith",
            site_phone="555-1234",
            notes="Patient interested"
        )

        ref = tracker.referrals[0]
        assert ref["site_contact"] == "Dr. Smith"
        assert ref["site_phone"] == "555-1234"
        assert ref["notes"] == "Patient interested"

    def test_add_referral_creates_history(self, tracker):
        """Test referral creation adds history entry."""
        ref_id = tracker.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="Hospital"
        )

        ref = tracker.referrals[0]
        assert "history" in ref
        assert len(ref["history"]) == 1
        assert ref["history"][0]["status"] == "Referred"
        assert "Initial referral" in ref["history"][0]["note"]

    def test_referral_persistence(self, temp_dir):
        """Test referrals persist to disk."""
        tracker1 = ReferralTracker(data_dir=temp_dir)
        ref_id = tracker1.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="Hospital"
        )

        # Create new instance and verify data loaded
        tracker2 = ReferralTracker(data_dir=temp_dir)
        assert len(tracker2.referrals) == 1
        assert tracker2.referrals[0]["referral_id"] == ref_id

    def test_update_referral_status(self, tracker):
        """Test updating referral status."""
        ref_id = tracker.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="Hospital"
        )

        result = tracker.update_referral_status(
            referral_id=ref_id,
            new_status="Contacted",
            note="Called coordinator"
        )

        assert result is True

        ref = tracker.referrals[0]
        assert ref["status"] == "Contacted"
        assert len(ref["history"]) == 2
        assert ref["history"][1]["status"] == "Contacted"
        assert ref["history"][1]["note"] == "Called coordinator"

    def test_update_referral_not_found(self, tracker):
        """Test updating non-existent referral."""
        result = tracker.update_referral_status(
            referral_id="REFXXXXX",
            new_status="Contacted"
        )
        assert result is False

    def test_update_referral_without_note(self, tracker):
        """Test updating status without custom note."""
        ref_id = tracker.add_referral(
            patient_id="PT001",
            nct_id="NCT12345678",
            trial_title="Test Trial",
            site_name="Hospital"
        )

        tracker.update_referral_status(ref_id, "Enrolled")

        ref = tracker.referrals[0]
        assert "Status changed to Enrolled" in ref["history"][1]["note"]

    def test_get_referrals_by_patient(self, tracker):
        """Test getting referrals for a patient."""
        tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        tracker.add_referral("PT001", "NCT87654321", "Trial 2", "Hospital B")
        tracker.add_referral("PT002", "NCT11111111", "Trial 3", "Hospital C")

        pt001_refs = tracker.get_referrals_by_patient("PT001")
        assert len(pt001_refs) == 2

        pt002_refs = tracker.get_referrals_by_patient("PT002")
        assert len(pt002_refs) == 1

    def test_get_referrals_by_trial(self, tracker):
        """Test getting referrals for a trial."""
        tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        tracker.add_referral("PT002", "NCT12345678", "Trial 1", "Hospital A")
        tracker.add_referral("PT003", "NCT87654321", "Trial 2", "Hospital B")

        trial1_refs = tracker.get_referrals_by_trial("NCT12345678")
        assert len(trial1_refs) == 2

        trial2_refs = tracker.get_referrals_by_trial("NCT87654321")
        assert len(trial2_refs) == 1

    def test_get_referrals_by_status(self, tracker):
        """Test getting referrals by status."""
        ref1 = tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        ref2 = tracker.add_referral("PT002", "NCT87654321", "Trial 2", "Hospital B")
        ref3 = tracker.add_referral("PT003", "NCT11111111", "Trial 3", "Hospital C")

        tracker.update_referral_status(ref2, "Enrolled")

        referred = tracker.get_referrals_by_status("Referred")
        assert len(referred) == 2

        enrolled = tracker.get_referrals_by_status("Enrolled")
        assert len(enrolled) == 1

    def test_get_all_referrals(self, tracker):
        """Test getting all referrals."""
        tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        tracker.add_referral("PT002", "NCT87654321", "Trial 2", "Hospital B")

        all_refs = tracker.get_all_referrals()
        assert len(all_refs) == 2

    def test_get_referrals_needing_followup(self, tracker):
        """Test getting referrals needing follow-up."""
        ref1 = tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        ref2 = tracker.add_referral("PT002", "NCT87654321", "Trial 2", "Hospital B")

        # Update ref1 to old date
        old_date = (datetime.now() - timedelta(days=10)).isoformat()
        tracker.referrals[0]["last_updated"] = old_date

        # Update ref2 status to Enrolled (shouldn't need follow-up)
        tracker.update_referral_status(ref2, "Enrolled")

        needing_followup = tracker.get_referrals_needing_followup(days=7)
        assert len(needing_followup) == 1
        assert needing_followup[0]["referral_id"] == ref1

    def test_get_referrals_needing_followup_custom_days(self, tracker):
        """Test follow-up with custom days threshold."""
        ref1 = tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")

        old_date = (datetime.now() - timedelta(days=5)).isoformat()
        tracker.referrals[0]["last_updated"] = old_date

        # Should need follow-up with 3 day threshold
        needing_followup = tracker.get_referrals_needing_followup(days=3)
        assert len(needing_followup) == 1

        # Should NOT need follow-up with 7 day threshold
        needing_followup = tracker.get_referrals_needing_followup(days=7)
        assert len(needing_followup) == 0

    def test_export_to_dataframe(self, tracker):
        """Test exporting to pandas DataFrame."""
        tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        tracker.add_referral("PT002", "NCT87654321", "Trial 2", "Hospital B")

        df = tracker.export_to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert "patient_id" in df.columns
        assert "nct_id" in df.columns
        assert "status" in df.columns
        assert "history" not in df.columns  # Should be excluded

    def test_export_empty_dataframe(self, tracker):
        """Test exporting when no referrals exist."""
        df = tracker.export_to_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_get_summary_stats(self, tracker):
        """Test getting summary statistics."""
        ref1 = tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")
        ref2 = tracker.add_referral("PT001", "NCT87654321", "Trial 2", "Hospital B")
        ref3 = tracker.add_referral("PT002", "NCT12345678", "Trial 1", "Hospital A")

        tracker.update_referral_status(ref2, "Enrolled")

        stats = tracker.get_summary_stats()

        assert stats["total_referrals"] == 3
        assert stats["by_status"]["Referred"] == 2
        assert stats["by_status"]["Enrolled"] == 1
        assert stats["total_patients"] == 2
        assert stats["total_trials"] == 2

    def test_get_summary_stats_empty(self, tracker):
        """Test summary stats with no referrals."""
        stats = tracker.get_summary_stats()

        assert stats["total_referrals"] == 0
        assert stats["by_status"] == {}
        assert stats["total_patients"] == 0
        assert stats["total_trials"] == 0

    def test_load_corrupt_file(self, temp_dir):
        """Test loading with corrupt referrals file."""
        refs_file = Path(temp_dir) / "referrals.json"
        refs_file.write_text("{invalid json")

        tracker = ReferralTracker(data_dir=temp_dir)
        assert tracker.referrals == []

    def test_referral_statuses_constant(self):
        """Test REFERRAL_STATUSES constant."""
        assert len(REFERRAL_STATUSES) == 8
        assert "Referred" in REFERRAL_STATUSES
        assert "Contacted" in REFERRAL_STATUSES
        assert "Screening Scheduled" in REFERRAL_STATUSES
        assert "Enrolled" in REFERRAL_STATUSES
        assert "Screen Failed" in REFERRAL_STATUSES
        assert "Patient Declined" in REFERRAL_STATUSES

    def test_multiple_status_updates(self, tracker):
        """Test multiple status updates create full history."""
        ref_id = tracker.add_referral("PT001", "NCT12345678", "Trial 1", "Hospital A")

        tracker.update_referral_status(ref_id, "Contacted")
        tracker.update_referral_status(ref_id, "Screening Scheduled")
        tracker.update_referral_status(ref_id, "Enrolled")

        ref = tracker.referrals[0]
        assert len(ref["history"]) == 4  # Initial + 3 updates
        assert ref["history"][-1]["status"] == "Enrolled"
        assert ref["status"] == "Enrolled"
