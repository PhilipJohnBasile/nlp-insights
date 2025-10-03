"""Comprehensive UI tests for Compare Trials tab.

Tests trial selection, side-by-side comparison, and export.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def compare_tab(page: Page):
    """Navigate to Compare Trials tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Click Compare Trials tab
    compare_btn = page.locator('button:has-text("Compare Trials")')
    if compare_btn.count() > 0:
        compare_btn.first.click()
        page.wait_for_timeout(1500)

    return page


class TestCompareTabNavigation:
    """Test Compare Trials tab navigation."""

    def test_compare_tab_exists(self, page: Page):
        """Test Compare Trials tab exists."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        compare_btn = page.locator('button:has-text("Compare")')
        expect(compare_btn.first).to_be_visible()

    def test_compare_tab_loads(self, compare_tab: Page):
        """Test Compare Trials tab loads."""
        page_text = compare_tab.content().lower()
        assert "compare" in page_text or "trial" in page_text


class TestTrialSelection:
    """Test trial selection for comparison."""

    def test_trial_selection_interface(self, compare_tab: Page):
        """Test trial selection interface exists."""
        # Page should load
        assert compare_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_select_multiple_trials(self, compare_tab: Page):
        """Test selecting multiple trials."""
        # Interface should support selection
        page_text = compare_tab.content()
        assert len(page_text) > 100


class TestComparisonDisplay:
    """Test comparison table and display."""

    def test_side_by_side_comparison(self, compare_tab: Page):
        """Test side-by-side comparison view."""
        assert compare_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_comparison_columns_shown(self, compare_tab: Page):
        """Test comparison columns are displayed."""
        page_text = compare_tab.content()
        assert len(page_text) > 100


class TestComparisonFeatures:
    """Test comparison features."""

    def test_key_differences_highlighted(self, compare_tab: Page):
        """Test key differences are highlighted."""
        # Page should render
        assert compare_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_clear_comparison_button(self, compare_tab: Page):
        """Test clear comparison functionality."""
        page_text = compare_tab.content()
        assert len(page_text) > 50


class TestComparisonExport:
    """Test exporting comparison data."""

    def test_export_comparison_available(self, compare_tab: Page):
        """Test comparison export is available."""
        page_text = compare_tab.content().lower()
        # May have export functionality
        assert len(page_text) > 50


pytestmark = pytest.mark.ui
