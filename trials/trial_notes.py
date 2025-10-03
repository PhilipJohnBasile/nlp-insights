"""Trial notes and annotations system."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class TrialNotesManager:
    """Manage personal notes and annotations for trials."""

    def __init__(self, data_dir: str = "data/notes"):
        """Initialize notes manager.

        Args:
            data_dir: Directory to store notes data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.notes_file = self.data_dir / "trial_notes.json"
        self.notes = self._load_notes()

    def _load_notes(self) -> Dict:
        """Load existing notes from file."""
        if self.notes_file.exists():
            try:
                with open(self.notes_file, 'r') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_notes(self):
        """Save notes to file."""
        with open(self.notes_file, 'w') as f:
            json.dump(self.notes, f, indent=2)

    def add_note(self, nct_id: str, note_text: str, note_type: str = "general"):
        """Add a note to a trial.

        Args:
            nct_id: NCT ID of trial
            note_text: Note content
            note_type: Type of note (general, concern, positive, question)
        """
        if nct_id not in self.notes:
            self.notes[nct_id] = {
                "nct_id": nct_id,
                "notes": [],
                "starred": False,
                "flagged": False,
                "tags": []
            }

        note = {
            "note_id": f"NOTE{len(self.notes[nct_id]['notes']) + 1:04d}",
            "text": note_text,
            "type": note_type,
            "timestamp": datetime.now().isoformat()
        }

        self.notes[nct_id]["notes"].append(note)
        self._save_notes()

    def get_notes(self, nct_id: str) -> Optional[Dict]:
        """Get all notes for a trial.

        Args:
            nct_id: NCT ID of trial

        Returns:
            Notes dictionary or None if no notes
        """
        return self.notes.get(nct_id)

    def star_trial(self, nct_id: str, starred: bool = True):
        """Star/favorite a trial.

        Args:
            nct_id: NCT ID of trial
            starred: True to star, False to unstar
        """
        if nct_id not in self.notes:
            self.notes[nct_id] = {
                "nct_id": nct_id,
                "notes": [],
                "starred": starred,
                "flagged": False,
                "tags": []
            }
        else:
            self.notes[nct_id]["starred"] = starred

        self._save_notes()

    def flag_trial(self, nct_id: str, flagged: bool = True):
        """Flag a trial for concern/review.

        Args:
            nct_id: NCT ID of trial
            flagged: True to flag, False to unflag
        """
        if nct_id not in self.notes:
            self.notes[nct_id] = {
                "nct_id": nct_id,
                "notes": [],
                "starred": False,
                "flagged": flagged,
                "tags": []
            }
        else:
            self.notes[nct_id]["flagged"] = flagged

        self._save_notes()

    def add_tags(self, nct_id: str, tags: List[str]):
        """Add tags to a trial.

        Args:
            nct_id: NCT ID of trial
            tags: List of tags to add
        """
        if nct_id not in self.notes:
            self.notes[nct_id] = {
                "nct_id": nct_id,
                "notes": [],
                "starred": False,
                "flagged": False,
                "tags": tags
            }
        else:
            # Merge tags without duplicates
            existing_tags = set(self.notes[nct_id].get("tags", []))
            new_tags = existing_tags.union(set(tags))
            self.notes[nct_id]["tags"] = list(new_tags)

        self._save_notes()

    def get_starred_trials(self) -> List[str]:
        """Get list of starred trial NCT IDs.

        Returns:
            List of NCT IDs
        """
        return [nct_id for nct_id, data in self.notes.items() if data.get("starred", False)]

    def get_flagged_trials(self) -> List[str]:
        """Get list of flagged trial NCT IDs.

        Returns:
            List of NCT IDs
        """
        return [nct_id for nct_id, data in self.notes.items() if data.get("flagged", False)]

    def get_trials_by_tag(self, tag: str) -> List[str]:
        """Get trials with a specific tag.

        Args:
            tag: Tag to search for

        Returns:
            List of NCT IDs
        """
        return [nct_id for nct_id, data in self.notes.items() if tag in data.get("tags", [])]

    def delete_note(self, nct_id: str, note_id: str) -> bool:
        """Delete a specific note.

        Args:
            nct_id: NCT ID of trial
            note_id: Note ID to delete

        Returns:
            True if deleted, False if not found
        """
        if nct_id in self.notes:
            notes_list = self.notes[nct_id]["notes"]
            for i, note in enumerate(notes_list):
                if note["note_id"] == note_id:
                    notes_list.pop(i)
                    self._save_notes()
                    return True

        return False
