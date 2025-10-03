"""Tests for trial notes and annotations system."""

import json
import pytest
from pathlib import Path
from trials.trial_notes import TrialNotesManager


class TestTrialNotesManager:
    """Test trial notes management."""

    def test_init(self, tmp_path):
        """Test initialization creates directory."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))
        assert manager.data_dir.exists()
        assert manager.notes_file == manager.data_dir / "trial_notes.json"

    def test_add_note(self, tmp_path):
        """Test adding a note to a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT12345678", "This trial looks promising", "positive")

        notes = manager.get_notes("NCT12345678")
        assert notes is not None
        assert len(notes["notes"]) == 1
        assert notes["notes"][0]["text"] == "This trial looks promising"
        assert notes["notes"][0]["type"] == "positive"

    def test_add_multiple_notes(self, tmp_path):
        """Test adding multiple notes to same trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT12345678", "Note 1", "general")
        manager.add_note("NCT12345678", "Note 2", "concern")
        manager.add_note("NCT12345678", "Note 3", "question")

        notes = manager.get_notes("NCT12345678")
        assert len(notes["notes"]) == 3

    def test_note_id_generation(self, tmp_path):
        """Test note IDs are generated correctly."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "First note")
        manager.add_note("NCT001", "Second note")
        manager.add_note("NCT001", "Third note")

        notes = manager.get_notes("NCT001")
        assert notes["notes"][0]["note_id"] == "NOTE0001"
        assert notes["notes"][1]["note_id"] == "NOTE0002"
        assert notes["notes"][2]["note_id"] == "NOTE0003"

    def test_note_timestamp(self, tmp_path):
        """Test notes have timestamps."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "Test note")

        notes = manager.get_notes("NCT001")
        assert "timestamp" in notes["notes"][0]

    def test_default_note_type(self, tmp_path):
        """Test default note type is 'general'."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "Test note")  # No type specified

        notes = manager.get_notes("NCT001")
        assert notes["notes"][0]["type"] == "general"

    def test_get_notes_nonexistent(self, tmp_path):
        """Test getting notes for trial with no notes."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        notes = manager.get_notes("NCT99999999")
        assert notes is None

    def test_star_trial(self, tmp_path):
        """Test starring a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.star_trial("NCT001", starred=True)

        notes = manager.get_notes("NCT001")
        assert notes["starred"] is True

    def test_unstar_trial(self, tmp_path):
        """Test unstarring a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.star_trial("NCT001", starred=True)
        manager.star_trial("NCT001", starred=False)

        notes = manager.get_notes("NCT001")
        assert notes["starred"] is False

    def test_star_trial_with_existing_notes(self, tmp_path):
        """Test starring trial that already has notes."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "Test note")
        manager.star_trial("NCT001", starred=True)

        notes = manager.get_notes("NCT001")
        assert notes["starred"] is True
        assert len(notes["notes"]) == 1

    def test_flag_trial(self, tmp_path):
        """Test flagging a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.flag_trial("NCT001", flagged=True)

        notes = manager.get_notes("NCT001")
        assert notes["flagged"] is True

    def test_unflag_trial(self, tmp_path):
        """Test unflagging a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.flag_trial("NCT001", flagged=True)
        manager.flag_trial("NCT001", flagged=False)

        notes = manager.get_notes("NCT001")
        assert notes["flagged"] is False

    def test_add_tags(self, tmp_path):
        """Test adding tags to a trial."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_tags("NCT001", ["immunotherapy", "phase-2"])

        notes = manager.get_notes("NCT001")
        assert "immunotherapy" in notes["tags"]
        assert "phase-2" in notes["tags"]

    def test_add_tags_no_duplicates(self, tmp_path):
        """Test adding duplicate tags."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_tags("NCT001", ["immunotherapy", "phase-2"])
        manager.add_tags("NCT001", ["phase-2", "EGFR"])  # phase-2 is duplicate

        notes = manager.get_notes("NCT001")
        assert len(notes["tags"]) == 3  # Only 3 unique tags
        assert "immunotherapy" in notes["tags"]
        assert "phase-2" in notes["tags"]
        assert "EGFR" in notes["tags"]

    def test_get_starred_trials(self, tmp_path):
        """Test getting list of starred trials."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.star_trial("NCT001", starred=True)
        manager.star_trial("NCT002", starred=True)
        manager.star_trial("NCT003", starred=False)

        starred = manager.get_starred_trials()
        assert len(starred) == 2
        assert "NCT001" in starred
        assert "NCT002" in starred
        assert "NCT003" not in starred

    def test_get_flagged_trials(self, tmp_path):
        """Test getting list of flagged trials."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.flag_trial("NCT001", flagged=True)
        manager.flag_trial("NCT002", flagged=False)
        manager.flag_trial("NCT003", flagged=True)

        flagged = manager.get_flagged_trials()
        assert len(flagged) == 2
        assert "NCT001" in flagged
        assert "NCT003" in flagged
        assert "NCT002" not in flagged

    def test_get_trials_by_tag(self, tmp_path):
        """Test getting trials by tag."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_tags("NCT001", ["immunotherapy", "phase-2"])
        manager.add_tags("NCT002", ["immunotherapy", "phase-3"])
        manager.add_tags("NCT003", ["chemotherapy", "phase-2"])

        immuno_trials = manager.get_trials_by_tag("immunotherapy")
        assert len(immuno_trials) == 2
        assert "NCT001" in immuno_trials
        assert "NCT002" in immuno_trials

        phase2_trials = manager.get_trials_by_tag("phase-2")
        assert len(phase2_trials) == 2
        assert "NCT001" in phase2_trials
        assert "NCT003" in phase2_trials

    def test_delete_note(self, tmp_path):
        """Test deleting a specific note."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "Note 1")
        manager.add_note("NCT001", "Note 2")
        manager.add_note("NCT001", "Note 3")

        notes_before = manager.get_notes("NCT001")
        note_id = notes_before["notes"][1]["note_id"]  # Delete middle note

        result = manager.delete_note("NCT001", note_id)
        assert result is True

        notes_after = manager.get_notes("NCT001")
        assert len(notes_after["notes"]) == 2
        assert notes_after["notes"][0]["text"] == "Note 1"
        assert notes_after["notes"][1]["text"] == "Note 3"

    def test_delete_nonexistent_note(self, tmp_path):
        """Test deleting non-existent note."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        result = manager.delete_note("NCT001", "NOTE9999")
        assert result is False

    def test_delete_note_from_nonexistent_trial(self, tmp_path):
        """Test deleting note from trial with no notes."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        result = manager.delete_note("NCT99999999", "NOTE0001")
        assert result is False

    def test_persistence(self, tmp_path):
        """Test that notes persist across instances."""
        data_dir = str(tmp_path / "notes")

        # Create manager and add data
        manager1 = TrialNotesManager(data_dir=data_dir)
        manager1.add_note("NCT001", "Test note")
        manager1.star_trial("NCT001", starred=True)
        manager1.add_tags("NCT001", ["test-tag"])

        # Create new manager instance
        manager2 = TrialNotesManager(data_dir=data_dir)

        notes = manager2.get_notes("NCT001")
        assert len(notes["notes"]) == 1
        assert notes["starred"] is True
        assert "test-tag" in notes["tags"]

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from corrupted file returns empty dict."""
        data_dir = tmp_path / "notes"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted JSON file
        notes_file = data_dir / "trial_notes.json"
        with open(notes_file, 'w') as f:
            f.write("{ corrupted json }")

        manager = TrialNotesManager(data_dir=str(data_dir))
        assert manager.notes == {}

    def test_initial_trial_structure(self, tmp_path):
        """Test initial trial structure when first created."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "First note")

        notes = manager.get_notes("NCT001")
        assert notes["nct_id"] == "NCT001"
        assert notes["starred"] is False
        assert notes["flagged"] is False
        assert notes["tags"] == []

    def test_multiple_trials(self, tmp_path):
        """Test managing notes for multiple trials."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "Note for trial 1")
        manager.add_note("NCT002", "Note for trial 2")
        manager.add_note("NCT003", "Note for trial 3")

        assert manager.get_notes("NCT001") is not None
        assert manager.get_notes("NCT002") is not None
        assert manager.get_notes("NCT003") is not None

    def test_note_types(self, tmp_path):
        """Test different note types."""
        manager = TrialNotesManager(data_dir=str(tmp_path / "notes"))

        manager.add_note("NCT001", "General info", "general")
        manager.add_note("NCT001", "Safety concern", "concern")
        manager.add_note("NCT001", "Looks promising", "positive")
        manager.add_note("NCT001", "Need to verify", "question")

        notes = manager.get_notes("NCT001")
        assert notes["notes"][0]["type"] == "general"
        assert notes["notes"][1]["type"] == "concern"
        assert notes["notes"][2]["type"] == "positive"
        assert notes["notes"][3]["type"] == "question"
