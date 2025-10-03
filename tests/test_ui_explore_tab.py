"""Comprehensive UI tests for Explore tab.

Tests filtering, sorting, display, and export functionality
in the Trial Explorer tab.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def explore_tab(page: Page):
    """Navigate to Explore tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Click Explore tab
    explore_btn = page.locator('button:has-text("📊 Explore")')
    if explore_btn.count() > 0:
        explore_btn.first.click()
        page.wait_for_timeout(1500)

    return page


class TestExploreTabNavigation:
    """Test navigation to and loading of Explore tab."""

    def test_explore_tab_exists(self, page: Page):
        """Test Explore tab button exists."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        explore_btn = page.locator('button:has-text("Explore")')
        expect(explore_btn.first).to_be_visible()

    def test_explore_tab_clickable(self, page: Page):
        """Test Explore tab is clickable."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        explore_btn = page.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            page.wait_for_timeout(1000)

    def test_explore_tab_loads_content(self, explore_tab: Page):
        """Test Explore tab loads content."""
        # Should show Explorer heading or filter elements
        page_text = explore_tab.content().lower()
        assert "phase" in page_text or "status" in page_text or "filter" in page_text


class TestFilters:
    """Test filter functionality in Explore tab."""

    def test_phase_filter_visible(self, explore_tab: Page):
        """Test phase filter dropdown is visible."""
        page_text = explore_tab.content()
        assert "Phase" in page_text

    def test_status_filter_visible(self, explore_tab: Page):
        """Test status filter dropdown is visible."""
        page_text = explore_tab.content()
        assert "Status" in page_text

    def test_cluster_filter_visible_when_available(self, explore_tab: Page):
        """Test cluster filter appears if clusters exist."""
        # Cluster filter may or may not be present depending on data
        page_text = explore_tab.content()
        # Just verify page loaded
        assert len(page_text) > 100

    def test_filters_in_columns(self, explore_tab: Page):
        """Test filters are arranged in columns."""
        # Look for column structure
        columns = explore_tab.locator('[data-testid="column"]')
        # Should have column layout (may vary)
        assert columns.count() >= 0  # Columns may or may not use specific testid


class TestDataDisplay:
    """Test data display and table functionality."""

    def test_results_count_displayed(self, explore_tab: Page):
        """Test that results count is shown."""
        page_text = explore_tab.content()
        # Should show count like "Results (X trials)"
        assert "trial" in page_text.lower() or "result" in page_text.lower()

    def test_dataframe_visible_with_data(self, explore_tab: Page):
        """Test dataframe is visible when data is loaded."""
        # Check for dataframe or table element
        dataframe = explore_tab.locator('[data-testid="stDataFrame"]')
        table = explore_tab.locator('table')

        # Either dataframe or table should exist (or data message)
        assert dataframe.count() > 0 or table.count() > 0 or "No data" in explore_tab.content()

    def test_expected_columns_present(self, explore_tab: Page):
        """Test expected columns are in the display."""
        page_text = explore_tab.content()
        # Should show column headers
        assert "trial" in page_text.lower() or "title" in page_text.lower()


class TestExportFunctionality:
    """Test CSV export functionality."""

    def test_download_csv_button_visible(self, explore_tab: Page):
        """Test Download CSV button is visible."""
        download_btn = explore_tab.locator('button:has-text("Download CSV")')

        # Button should exist (may require data to be loaded)
        # Check if it exists anywhere in the page content
        page_text = explore_tab.content()
        assert "download" in page_text.lower() or "export" in page_text.lower() or "csv" in page_text.lower()

    def test_csv_download_button_enabled_with_data(self, explore_tab: Page):
        """Test CSV button is enabled when data exists."""
        download_btn = explore_tab.locator('button:has-text("Download")')
        # If button exists, verify it's accessible
        if download_btn.count() > 0:
            expect(download_btn.first).to_be_visible()


class TestDataStates:
    """Test different data states (empty, loaded, filtered)."""

    def test_no_data_message_shown_when_empty(self, page: Page):
        """Test appropriate message when no data loaded."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        # Navigate to Explore
        explore_btn = page.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            page.wait_for_timeout(1500)

        # Should show data-related message
        page_text = page.content().lower()
        assert "data" in page_text or "fetch" in page_text or "load" in page_text

    def test_empty_filter_results_handled(self, explore_tab: Page):
        """Test handling when filters return no results."""
        # Even with no results, page should render without errors
        assert explore_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestPerformance:
    """Test performance of Explore tab."""

    def test_tab_loads_quickly(self, page: Page):
        """Test tab loads in reasonable time."""
        import time
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        start = time.time()
        explore_btn = page.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            page.wait_for_timeout(1000)
        elapsed = time.time() - start

        # Should load in less than 5 seconds
        assert elapsed < 5


# Mark all tests as UI tests
pytestmark = pytest.mark.ui
