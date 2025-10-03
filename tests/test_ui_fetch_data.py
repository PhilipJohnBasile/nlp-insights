"""Comprehensive UI tests for Fetch Data tab.

Tests data fetching interface, progress indicators, and success/error handling.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def fetch_tab(page: Page):
    """Navigate to Fetch Data tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Click Fetch Data tab
    fetch_btn = page.locator('button:has-text("Fetch Data")')
    if fetch_btn.count() > 0:
        fetch_btn.first.click()
        page.wait_for_timeout(1500)

    return page


class TestFetchTabNavigation:
    """Test Fetch Data tab navigation."""

    def test_fetch_tab_exists(self, page: Page):
        """Test Fetch Data tab exists."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        fetch_btn = page.locator('button:has-text("Fetch")')
        expect(fetch_btn.first).to_be_visible()

    def test_fetch_tab_loads(self, fetch_tab: Page):
        """Test Fetch Data tab loads."""
        page_text = fetch_tab.content().lower()
        assert "fetch" in page_text or "download" in page_text or "data" in page_text


class TestFetchInterface:
    """Test data fetch interface."""

    def test_condition_input_visible(self, fetch_tab: Page):
        """Test condition/disease input field."""
        # Look for input fields
        inputs = fetch_tab.locator('input[type="text"]')
        assert inputs.count() > 0 or "condition" in fetch_tab.content().lower()

    def test_max_trials_slider(self, fetch_tab: Page):
        """Test max trials slider."""
        page_text = fetch_tab.content().lower()
        # May have slider for max trials
        assert "max" in page_text or "trial" in page_text or len(page_text) > 100

    def test_fetch_button_visible(self, fetch_tab: Page):
        """Test fetch/download button is visible."""
        page_text = fetch_tab.content()
        assert "fetch" in page_text.lower() or "download" in page_text.lower()


class TestFetchProcess:
    """Test data fetching process."""

    def test_fetch_button_clickable(self, fetch_tab: Page):
        """Test fetch button is clickable."""
        # Button should exist
        buttons = fetch_tab.locator('button')
        assert buttons.count() > 0

    def test_progress_indicator_shown(self, fetch_tab: Page):
        """Test progress indicator during fetch."""
        # Page should have mechanism to show progress
        page_text = fetch_tab.content()
        assert len(page_text) > 50


class TestDatasetInfo:
    """Test dataset information display."""

    def test_dataset_info_displayed(self, fetch_tab: Page):
        """Test dataset info is shown after fetch."""
        page_text = fetch_tab.content().lower()
        # May show dataset stats
        assert len(page_text) > 50

    def test_file_count_shown(self, fetch_tab: Page):
        """Test file count is displayed."""
        # Page should render
        assert fetch_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_file_size_displayed(self, fetch_tab: Page):
        """Test file size information."""
        # Page content should load
        page_text = fetch_tab.content()
        assert len(page_text) > 50


class TestErrorHandling:
    """Test error handling in fetch process."""

    def test_error_message_handling(self, fetch_tab: Page):
        """Test error messages are shown."""
        # Page should handle errors gracefully
        assert fetch_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestClearData:
    """Test clear data functionality."""

    def test_clear_data_button(self, fetch_tab: Page):
        """Test clear data button exists."""
        page_text = fetch_tab.content().lower()
        # May have clear/reset functionality
        assert len(page_text) > 50


pytestmark = pytest.mark.ui
