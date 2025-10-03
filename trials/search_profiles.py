"""Patient search profile saving and management."""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional


class SearchProfileManager:
    """Manage saved patient search profiles."""

    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize profile manager.

        Args:
            data_dir: Directory to store profile data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.profiles_file = self.data_dir / "search_profiles.json"
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> List[Dict]:
        """Load existing profiles from file."""
        if self.profiles_file.exists():
            try:
                with open(self.profiles_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_profiles(self):
        """Save profiles to file."""
        with open(self.profiles_file, 'w') as f:
            json.dump(self.profiles, f, indent=2)

    def save_profile(
        self,
        name: str,
        criteria: Dict,
        description: Optional[str] = None
    ) -> str:
        """Save a search profile.

        Args:
            name: Profile name
            criteria: Search criteria dictionary
            description: Optional description

        Returns:
            Profile ID
        """
        profile_id = f"PROF{len(self.profiles) + 1:04d}"

        profile = {
            "profile_id": profile_id,
            "name": name,
            "description": description or "",
            "criteria": criteria,
            "created_date": datetime.now().isoformat(),
            "last_used": datetime.now().isoformat(),
            "use_count": 0
        }

        self.profiles.append(profile)
        self._save_profiles()

        return profile_id

    def load_profile(self, profile_id: str) -> Optional[Dict]:
        """Load a profile by ID.

        Args:
            profile_id: Profile ID to load

        Returns:
            Profile dictionary or None if not found
        """
        for profile in self.profiles:
            if profile["profile_id"] == profile_id:
                # Update last used
                profile["last_used"] = datetime.now().isoformat()
                profile["use_count"] += 1
                self._save_profiles()
                return profile

        return None

    def delete_profile(self, profile_id: str) -> bool:
        """Delete a profile.

        Args:
            profile_id: Profile ID to delete

        Returns:
            True if deleted, False if not found
        """
        for i, profile in enumerate(self.profiles):
            if profile["profile_id"] == profile_id:
                self.profiles.pop(i)
                self._save_profiles()
                return True

        return False

    def get_all_profiles(self) -> List[Dict]:
        """Get all profiles sorted by last used.

        Returns:
            List of profile dictionaries
        """
        return sorted(self.profiles, key=lambda x: x["last_used"], reverse=True)

    def get_recent_profiles(self, limit: int = 5) -> List[Dict]:
        """Get recently used profiles.

        Args:
            limit: Number of profiles to return

        Returns:
            List of recent profiles
        """
        sorted_profiles = self.get_all_profiles()
        return sorted_profiles[:limit]


class SearchHistoryManager:
    """Manage search history."""

    def __init__(self, data_dir: str = "data/profiles"):
        """Initialize history manager.

        Args:
            data_dir: Directory to store history data
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.history_file = self.data_dir / "search_history.json"
        self.history = self._load_history()

    def _load_history(self) -> List[Dict]:
        """Load existing history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_history(self):
        """Save history to file."""
        with open(self.history_file, 'w') as f:
            json.dump(self.history, f, indent=2)

    def add_search(self, criteria: Dict, results_count: int):
        """Add a search to history.

        Args:
            criteria: Search criteria used
            results_count: Number of results found
        """
        search = {
            "search_id": f"SEARCH{len(self.history) + 1:05d}",
            "criteria": criteria,
            "results_count": results_count,
            "timestamp": datetime.now().isoformat()
        }

        self.history.insert(0, search)  # Add to beginning

        # Keep only last 50 searches
        self.history = self.history[:50]
        self._save_history()

    def get_recent_searches(self, limit: int = 10) -> List[Dict]:
        """Get recent searches.

        Args:
            limit: Number of searches to return

        Returns:
            List of recent searches
        """
        return self.history[:limit]

    def clear_history(self):
        """Clear all search history."""
        self.history = []
        self._save_history()
