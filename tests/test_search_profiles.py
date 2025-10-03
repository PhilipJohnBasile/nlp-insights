"""Tests for search profile and history management."""

import json
import pytest
from pathlib import Path
from trials.search_profiles import SearchProfileManager, SearchHistoryManager


class TestSearchProfileManager:
    """Test search profile management."""

    def test_init(self, tmp_path):
        """Test initialization creates directory."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))
        assert manager.data_dir.exists()
        assert manager.profiles_file == manager.data_dir / "search_profiles.json"

    def test_save_profile(self, tmp_path):
        """Test saving a search profile."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        criteria = {
            "age": 65,
            "cancer_type": "Lung Cancer",
            "stage": "IV",
            "EGFR": True
        }

        profile_id = manager.save_profile(
            name="Stage IV NSCLC with EGFR",
            criteria=criteria,
            description="Advanced NSCLC patients with EGFR mutation"
        )

        assert profile_id.startswith("PROF")
        assert len(manager.profiles) == 1
        assert manager.profiles[0]["name"] == "Stage IV NSCLC with EGFR"

    def test_save_multiple_profiles(self, tmp_path):
        """Test saving multiple profiles."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        manager.save_profile("Profile 1", {"age": 65})
        manager.save_profile("Profile 2", {"age": 70})
        manager.save_profile("Profile 3", {"age": 75})

        assert len(manager.profiles) == 3

    def test_profile_id_incrementing(self, tmp_path):
        """Test profile IDs increment correctly."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        id1 = manager.save_profile("Profile 1", {"age": 65})
        id2 = manager.save_profile("Profile 2", {"age": 70})
        id3 = manager.save_profile("Profile 3", {"age": 75})

        assert id1 == "PROF0001"
        assert id2 == "PROF0002"
        assert id3 == "PROF0003"

    def test_load_profile(self, tmp_path):
        """Test loading a profile by ID."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        criteria = {"age": 65, "cancer_type": "Lung Cancer"}
        profile_id = manager.save_profile("Test Profile", criteria)

        loaded = manager.load_profile(profile_id)

        assert loaded is not None
        assert loaded["profile_id"] == profile_id
        assert loaded["name"] == "Test Profile"
        assert loaded["criteria"] == criteria

    def test_load_profile_updates_last_used(self, tmp_path):
        """Test that loading a profile updates last_used."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        profile_id = manager.save_profile("Test", {"age": 65})
        original = manager.profiles[0]["last_used"]

        import time
        time.sleep(0.01)  # Small delay

        loaded = manager.load_profile(profile_id)

        assert loaded["last_used"] != original
        assert loaded["use_count"] == 1

    def test_load_nonexistent_profile(self, tmp_path):
        """Test loading non-existent profile returns None."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        loaded = manager.load_profile("PROF9999")
        assert loaded is None

    def test_delete_profile(self, tmp_path):
        """Test deleting a profile."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        profile_id = manager.save_profile("Test", {"age": 65})
        assert len(manager.profiles) == 1

        result = manager.delete_profile(profile_id)
        assert result is True
        assert len(manager.profiles) == 0

    def test_delete_nonexistent_profile(self, tmp_path):
        """Test deleting non-existent profile returns False."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        result = manager.delete_profile("PROF9999")
        assert result is False

    def test_get_all_profiles(self, tmp_path):
        """Test getting all profiles sorted by last used."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        id1 = manager.save_profile("Profile 1", {"age": 65})
        import time
        time.sleep(0.01)
        id2 = manager.save_profile("Profile 2", {"age": 70})
        time.sleep(0.01)
        id3 = manager.save_profile("Profile 3", {"age": 75})

        all_profiles = manager.get_all_profiles()

        # Should be sorted by last_used (newest first)
        assert len(all_profiles) == 3
        assert all_profiles[0]["profile_id"] == id3
        assert all_profiles[2]["profile_id"] == id1

    def test_get_recent_profiles(self, tmp_path):
        """Test getting recent profiles with limit."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        for i in range(10):
            manager.save_profile(f"Profile {i}", {"age": 65 + i})

        recent = manager.get_recent_profiles(limit=3)

        assert len(recent) == 3
        assert recent[0]["name"] == "Profile 9"  # Most recent

    def test_persistence(self, tmp_path):
        """Test that profiles persist across instances."""
        data_dir = str(tmp_path / "profiles")

        # Create manager and save profile
        manager1 = SearchProfileManager(data_dir=data_dir)
        profile_id = manager1.save_profile("Test", {"age": 65})

        # Create new manager instance
        manager2 = SearchProfileManager(data_dir=data_dir)

        assert len(manager2.profiles) == 1
        loaded = manager2.load_profile(profile_id)
        assert loaded is not None

    def test_save_without_description(self, tmp_path):
        """Test saving profile without description."""
        manager = SearchProfileManager(data_dir=str(tmp_path / "profiles"))

        profile_id = manager.save_profile("Test", {"age": 65})
        loaded = manager.load_profile(profile_id)

        assert loaded["description"] == ""

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from corrupted file returns empty list."""
        data_dir = tmp_path / "profiles"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted JSON file
        profiles_file = data_dir / "search_profiles.json"
        with open(profiles_file, 'w') as f:
            f.write("{ corrupted json }")

        manager = SearchProfileManager(data_dir=str(data_dir))
        assert manager.profiles == []


class TestSearchHistoryManager:
    """Test search history management."""

    def test_init(self, tmp_path):
        """Test initialization creates directory."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))
        assert manager.data_dir.exists()
        assert manager.history_file == manager.data_dir / "search_history.json"

    def test_add_search(self, tmp_path):
        """Test adding a search to history."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        criteria = {"age": 65, "cancer_type": "Lung Cancer"}
        manager.add_search(criteria, results_count=15)

        assert len(manager.history) == 1
        assert manager.history[0]["criteria"] == criteria
        assert manager.history[0]["results_count"] == 15
        assert "search_id" in manager.history[0]
        assert "timestamp" in manager.history[0]

    def test_search_id_generation(self, tmp_path):
        """Test search ID generation."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        manager.add_search({"age": 65}, 10)
        manager.add_search({"age": 70}, 20)

        assert manager.history[0]["search_id"] == "SEARCH00002"
        assert manager.history[1]["search_id"] == "SEARCH00001"

    def test_searches_ordered_newest_first(self, tmp_path):
        """Test searches are ordered newest first."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        manager.add_search({"age": 65}, 10)
        import time
        time.sleep(0.01)
        manager.add_search({"age": 70}, 20)

        # Newest should be first
        assert manager.history[0]["criteria"]["age"] == 70
        assert manager.history[1]["criteria"]["age"] == 65

    def test_history_limit(self, tmp_path):
        """Test history is limited to 50 entries."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        # Add 60 searches
        for i in range(60):
            manager.add_search({"age": 65 + i}, i)

        # Should keep only last 50
        assert len(manager.history) == 50

    def test_get_recent_searches(self, tmp_path):
        """Test getting recent searches."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        for i in range(20):
            manager.add_search({"age": 65 + i}, i)

        recent = manager.get_recent_searches(limit=5)

        assert len(recent) == 5
        # Most recent should be age 84 (65 + 19)
        assert recent[0]["criteria"]["age"] == 84

    def test_clear_history(self, tmp_path):
        """Test clearing all history."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        for i in range(10):
            manager.add_search({"age": 65 + i}, i)

        assert len(manager.history) == 10

        manager.clear_history()

        assert len(manager.history) == 0

    def test_persistence(self, tmp_path):
        """Test that history persists across instances."""
        data_dir = str(tmp_path / "profiles")

        # Create manager and add search
        manager1 = SearchHistoryManager(data_dir=data_dir)
        manager1.add_search({"age": 65}, 10)

        # Create new manager instance
        manager2 = SearchHistoryManager(data_dir=data_dir)

        assert len(manager2.history) == 1
        assert manager2.history[0]["criteria"]["age"] == 65

    def test_load_corrupted_file(self, tmp_path):
        """Test loading from corrupted file returns empty list."""
        data_dir = tmp_path / "profiles"
        data_dir.mkdir(parents=True, exist_ok=True)

        # Create corrupted JSON file
        history_file = data_dir / "search_history.json"
        with open(history_file, 'w') as f:
            f.write("{ corrupted json }")

        manager = SearchHistoryManager(data_dir=str(data_dir))
        assert manager.history == []

    def test_get_recent_searches_default_limit(self, tmp_path):
        """Test get_recent_searches uses default limit of 10."""
        manager = SearchHistoryManager(data_dir=str(tmp_path / "profiles"))

        for i in range(20):
            manager.add_search({"age": 65 + i}, i)

        recent = manager.get_recent_searches()  # No limit specified

        assert len(recent) == 10
