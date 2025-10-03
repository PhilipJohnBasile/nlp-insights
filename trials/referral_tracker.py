"""Referral tracking system for managing patient referrals to clinical trials."""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class ReferralTracker:
    """Manage patient referrals to clinical trials."""

    def __init__(self, data_dir: str = "data/referrals"):
        """Initialize referral tracker.

        Args:
            data_dir: Directory to store referral data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.referrals_file = self.data_dir / "referrals.json"
        self.referrals = self._load_referrals()

    def _load_referrals(self) -> List[Dict]:
        """Load existing referrals from file."""
        if self.referrals_file.exists():
            try:
                with open(self.referrals_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_referrals(self):
        """Save referrals to file."""
        with open(self.referrals_file, 'w') as f:
            json.dump(self.referrals, f, indent=2)

    def add_referral(
        self,
        patient_id: str,
        nct_id: str,
        trial_title: str,
        site_name: str,
        site_contact: Optional[str] = None,
        site_phone: Optional[str] = None,
        notes: Optional[str] = None
    ) -> str:
        """Add a new referral.

        Args:
            patient_id: De-identified patient identifier
            nct_id: NCT ID of the trial
            trial_title: Title of the trial
            site_name: Name of the site
            site_contact: Contact person at site
            site_phone: Phone number for site
            notes: Additional notes

        Returns:
            Referral ID
        """
        referral_id = f"REF{len(self.referrals) + 1:05d}"

        referral = {
            "referral_id": referral_id,
            "patient_id": patient_id,
            "nct_id": nct_id,
            "trial_title": trial_title,
            "site_name": site_name,
            "site_contact": site_contact,
            "site_phone": site_phone,
            "status": "Referred",
            "date_referred": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "notes": notes or "",
            "history": [
                {
                    "date": datetime.now().isoformat(),
                    "status": "Referred",
                    "note": "Initial referral created"
                }
            ]
        }

        self.referrals.append(referral)
        self._save_referrals()

        return referral_id

    def update_referral_status(
        self,
        referral_id: str,
        new_status: str,
        note: Optional[str] = None
    ) -> bool:
        """Update the status of a referral.

        Args:
            referral_id: ID of the referral to update
            new_status: New status (Referred, Contacted, Screening, Enrolled, Screen Failed, Declined)
            note: Optional note about the update

        Returns:
            True if successful, False if referral not found
        """
        for referral in self.referrals:
            if referral["referral_id"] == referral_id:
                referral["status"] = new_status
                referral["last_updated"] = datetime.now().isoformat()

                # Add to history
                history_entry = {
                    "date": datetime.now().isoformat(),
                    "status": new_status,
                    "note": note or f"Status changed to {new_status}"
                }
                referral["history"].append(history_entry)

                self._save_referrals()
                return True

        return False

    def get_referrals_by_patient(self, patient_id: str) -> List[Dict]:
        """Get all referrals for a patient.

        Args:
            patient_id: Patient identifier

        Returns:
            List of referral dictionaries
        """
        return [r for r in self.referrals if r["patient_id"] == patient_id]

    def get_referrals_by_trial(self, nct_id: str) -> List[Dict]:
        """Get all referrals for a trial.

        Args:
            nct_id: NCT ID of trial

        Returns:
            List of referral dictionaries
        """
        return [r for r in self.referrals if r["nct_id"] == nct_id]

    def get_referrals_by_status(self, status: str) -> List[Dict]:
        """Get all referrals with a specific status.

        Args:
            status: Status to filter by

        Returns:
            List of referral dictionaries
        """
        return [r for r in self.referrals if r["status"] == status]

    def get_all_referrals(self) -> List[Dict]:
        """Get all referrals.

        Returns:
            List of all referral dictionaries
        """
        return self.referrals

    def get_referrals_needing_followup(self, days: int = 7) -> List[Dict]:
        """Get referrals that need follow-up.

        Args:
            days: Number of days since last update to consider needing follow-up

        Returns:
            List of referral dictionaries
        """
        from datetime import datetime, timedelta

        cutoff = datetime.now() - timedelta(days=days)
        needing_followup = []

        for referral in self.referrals:
            if referral["status"] in ["Referred", "Contacted", "Screening"]:
                last_updated = datetime.fromisoformat(referral["last_updated"])
                if last_updated < cutoff:
                    needing_followup.append(referral)

        return needing_followup

    def export_to_dataframe(self) -> pd.DataFrame:
        """Export referrals to pandas DataFrame.

        Returns:
            DataFrame with referral data
        """
        if not self.referrals:
            return pd.DataFrame()

        # Flatten the referrals data (excluding history for cleaner export)
        export_data = []
        for r in self.referrals:
            row = {k: v for k, v in r.items() if k != "history"}
            export_data.append(row)

        return pd.DataFrame(export_data)

    def get_summary_stats(self) -> Dict:
        """Get summary statistics about referrals.

        Returns:
            Dictionary with summary stats
        """
        if not self.referrals:
            return {
                "total_referrals": 0,
                "by_status": {},
                "total_patients": 0,
                "total_trials": 0
            }

        status_counts = {}
        for r in self.referrals:
            status = r["status"]
            status_counts[status] = status_counts.get(status, 0) + 1

        unique_patients = len(set(r["patient_id"] for r in self.referrals))
        unique_trials = len(set(r["nct_id"] for r in self.referrals))

        return {
            "total_referrals": len(self.referrals),
            "by_status": status_counts,
            "total_patients": unique_patients,
            "total_trials": unique_trials
        }


# Status options for referrals
REFERRAL_STATUSES = [
    "Referred",
    "Contacted",
    "Screening Scheduled",
    "Screening In Progress",
    "Enrolled",
    "Screen Failed",
    "Patient Declined",
    "Trial Closed"
]
