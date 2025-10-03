"""Playwright configuration for Streamlit UI testing."""

import os
from pathlib import Path

# Base URL for the Streamlit app
BASE_URL = os.getenv("STREAMLIT_URL", "http://localhost:8501")

# Playwright configuration
PLAYWRIGHT_CONFIG = {
    "base_url": BASE_URL,
    "timeout": 30000,  # 30 seconds default timeout
    "slow_mo": 100,  # Slow down operations by 100ms for visibility (optional)
    "headless": os.getenv("HEADLESS", "true").lower() == "true",
    "browser": "chromium",
    "viewport": {"width": 1280, "height": 720},
    "screenshot": "only-on-failure",
    "video": "retain-on-failure",
}

# Test data directory
TEST_DATA_DIR = Path(__file__).parent / "tests" / "ui_test_data"

# Screenshots directory
SCREENSHOTS_DIR = Path(__file__).parent / "tests" / "screenshots"
SCREENSHOTS_DIR.mkdir(parents=True, exist_ok=True)

# Videos directory
VIDEOS_DIR = Path(__file__).parent / "tests" / "videos"
VIDEOS_DIR.mkdir(parents=True, exist_ok=True)
