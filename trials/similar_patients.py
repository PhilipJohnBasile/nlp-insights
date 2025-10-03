"""Similar patients analysis for clinical trial matching."""

import json
from pathlib import Path
from typing import Dict, List, Optional
import pandas as pd


class SimilarPatientsAnalyzer:
    """Analyze similar patient enrollment patterns."""

    def __init__(self, data_dir: str = "data/patient_analytics"):
        """Initialize analyzer.

        Args:
            data_dir: Directory to store anonymized patient data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.enrollments_file = self.data_dir / "enrollments_anonymized.json"
        self.enrollments = self._load_enrollments()

    def _load_enrollments(self) -> List[Dict]:
        """Load anonymized enrollment data."""
        if self.enrollments_file.exists():
            try:
                with open(self.enrollments_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_enrollments(self):
        """Save enrollment data."""
        with open(self.enrollments_file, 'w') as f:
            json.dump(self.enrollments, f, indent=2)

    def record_enrollment(
        self,
        nct_id: str,
        patient_profile: Dict,
        outcome: str
    ):
        """Record an anonymized enrollment.

        Args:
            nct_id: Trial NCT ID
            patient_profile: Anonymized patient characteristics
            outcome: 'enrolled', 'screen_failed', 'declined'
        """
        record = {
            "nct_id": nct_id,
            "profile": {
                "age_range": self._bucket_age(patient_profile.get("age")),
                "cancer_type": patient_profile.get("cancer_type"),
                "stage": patient_profile.get("stage"),
                "prior_lines": patient_profile.get("prior_lines"),
                "ecog": patient_profile.get("ecog"),
                "biomarkers": patient_profile.get("biomarkers", [])
            },
            "outcome": outcome,
            "timestamp": pd.Timestamp.now().isoformat()
        }

        self.enrollments.append(record)
        self._save_enrollments()

    def _bucket_age(self, age: Optional[int]) -> Optional[str]:
        """Convert age to range for privacy.

        Args:
            age: Age in years

        Returns:
            Age range string
        """
        if age is None:
            return None

        if age < 40:
            return "18-39"
        elif age < 50:
            return "40-49"
        elif age < 60:
            return "50-59"
        elif age < 70:
            return "60-69"
        else:
            return "70+"

    def find_similar_patients(self, patient_profile: Dict, nct_id: Optional[str] = None) -> Dict:
        """Find similar patients and their outcomes.

        Args:
            patient_profile: Current patient's profile
            nct_id: Optional specific trial to analyze

        Returns:
            Dictionary with similar patient statistics
        """
        age_range = self._bucket_age(patient_profile.get("age"))
        cancer_type = patient_profile.get("cancer_type", "").lower()
        ecog = patient_profile.get("ecog")

        # Filter for similar patients
        similar = []
        for enrollment in self.enrollments:
            prof = enrollment["profile"]

            # Match criteria
            age_match = prof.get("age_range") == age_range
            cancer_match = prof.get("cancer_type", "").lower() == cancer_type
            ecog_match = prof.get("ecog") == ecog

            # Require at least 2 of 3 matches
            match_score = sum([age_match, cancer_match, ecog_match])

            if match_score >= 2:
                if nct_id is None or enrollment["nct_id"] == nct_id:
                    similar.append(enrollment)

        if not similar:
            return {
                "total_similar": 0,
                "enrolled": 0,
                "screen_failed": 0,
                "declined": 0,
                "success_rate": None
            }

        # Calculate statistics
        outcomes = [e["outcome"] for e in similar]
        enrolled = outcomes.count("enrolled")
        screen_failed = outcomes.count("screen_failed")
        declined = outcomes.count("declined")

        total = len(similar)
        success_rate = (enrolled / total * 100) if total > 0 else None

        return {
            "total_similar": total,
            "enrolled": enrolled,
            "screen_failed": screen_failed,
            "declined": declined,
            "success_rate": success_rate
        }

    def get_alternative_trials(self, patient_profile: Dict, exclude_nct: Optional[str] = None) -> List[Dict]:
        """Get trials where similar patients enrolled.

        Args:
            patient_profile: Patient profile
            exclude_nct: NCT ID to exclude (usually current trial)

        Returns:
            List of trials with enrollment counts
        """
        similar_analysis = self.find_similar_patients(patient_profile)

        # Count enrollments by trial
        trial_counts = {}
        for enrollment in self.enrollments:
            if enrollment["outcome"] == "enrolled":
                nct = enrollment["nct_id"]
                if nct != exclude_nct:
                    trial_counts[nct] = trial_counts.get(nct, 0) + 1

        # Sort by count
        sorted_trials = sorted(trial_counts.items(), key=lambda x: x[1], reverse=True)

        return [{"nct_id": nct, "similar_enrolled": count} for nct, count in sorted_trials[:10]]


def format_similar_patients_display(stats: Dict) -> str:
    """Format similar patients statistics for display.

    Args:
        stats: Output from find_similar_patients

    Returns:
        Formatted markdown string
    """
    if stats["total_similar"] == 0:
        return """### 👥 Similar Patients

ℹ️ No similar patient data available yet.

As more patients use this system, we'll show you anonymized data about patients with similar profiles."""

    sections = []
    sections.append("### 👥 Similar Patients")
    sections.append("")
    sections.append(f"**{stats['total_similar']}** patients with similar profiles have been referred")
    sections.append("")

    # Success rate
    if stats["success_rate"] is not None:
        sections.append(f"**Success Rate:** {stats['success_rate']:.1f}% enrolled")
        sections.append("")

    # Breakdown
    sections.append("**Outcomes:**")
    sections.append(f"- ✅ Enrolled: {stats['enrolled']}")
    sections.append(f"- ❌ Screen Failed: {stats['screen_failed']}")
    sections.append(f"- ⏸️ Declined: {stats['declined']}")

    sections.append("")
    sections.append("_Note: Data is anonymized and aggregated for privacy_")

    return "\n".join(sections)
