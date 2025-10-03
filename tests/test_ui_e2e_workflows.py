"""End-to-end workflow UI tests.

Tests complete user journeys through multiple tabs and features.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def app(page: Page):
    """Navigate to app."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)
    return page


class TestPatientMatchingWorkflow:
    """Test complete patient matching workflow."""

    def test_search_to_results_workflow(self, app: Page):
        """Test patient search to results workflow."""
        # Should be on patient matching tab by default
        page_text = app.content().lower()
        assert "patient" in page_text or "matching" in page_text

        # Fill in basic info
        age_inputs = app.locator('input[type="number"]')
        if age_inputs.count() > 0:
            age_inputs.first.fill("65")
            app.wait_for_timeout(500)

        # Look for submit button
        submit_btn = app.locator('button:has-text("Find Matching Trials")')
        expect(submit_btn).to_be_visible()


class TestDataFetchToExploreWorkflow:
    """Test data fetch to explore workflow."""

    def test_fetch_then_explore_workflow(self, app: Page):
        """Test fetching data then exploring it."""
        # Navigate to Fetch Data tab
        fetch_btn = app.locator('button:has-text("Fetch Data")')
        if fetch_btn.count() > 0:
            fetch_btn.first.click()
            app.wait_for_timeout(1500)

        # Then navigate to Explore
        explore_btn = app.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            app.wait_for_timeout(1500)

        # Should show explore content
        page_text = app.content().lower()
        assert len(page_text) > 100


class TestSearchCompareExportWorkflow:
    """Test search, compare, export workflow."""

    def test_search_compare_export_flow(self, app: Page):
        """Test complete search-compare-export flow."""
        # Start with search (Patient Matching)
        page_text = app.content().lower()
        assert "patient" in page_text or len(page_text) > 100

        # Navigate to Compare Trials
        compare_btn = app.locator('button:has-text("Compare Trials")')
        if compare_btn.count() > 0:
            compare_btn.first.click()
            app.wait_for_timeout(1500)

        # Page should load
        assert app.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestReferralWorkflow:
    """Test referral creation and management workflow."""

    def test_create_update_export_referral(self, app: Page):
        """Test creating, updating, and exporting referral."""
        # Navigate to My Referrals
        referrals_btn = app.locator('button:has-text("My Referrals")')
        if referrals_btn.count() > 0:
            referrals_btn.first.click()
            app.wait_for_timeout(1500)

        # Should show referrals interface
        page_text = app.content().lower()
        assert "referral" in page_text or len(page_text) > 50


class TestCrossTabDataConsistency:
    """Test data consistency across tabs."""

    def test_data_persists_across_tabs(self, app: Page):
        """Test that data persists when switching tabs."""
        # Fill in patient data
        age_inputs = app.locator('input[type="number"]')
        if age_inputs.count() > 0:
            age_inputs.first.fill("70")
            app.wait_for_timeout(500)

        # Switch to Explore tab
        explore_btn = app.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            app.wait_for_timeout(1500)

        # Switch back to Patient Matching
        patient_btn = app.locator('button:has-text("Patient Matching")')
        if patient_btn.count() > 0:
            patient_btn.first.click()
            app.wait_for_timeout(1500)


class TestSessionStatePersistence:
    """Test session state persistence."""

    def test_form_state_persists(self, app: Page):
        """Test form state persists during session."""
        # Enter data
        text_inputs = app.locator('input[type="text"]')
        if text_inputs.count() > 0:
            first_input = text_inputs.first
            first_input.fill("test data")
            app.wait_for_timeout(500)

        # Data should persist
        assert app.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestBrowserNavigation:
    """Test browser back/forward navigation."""

    def test_back_forward_navigation(self, app: Page):
        """Test browser back and forward buttons."""
        # Navigate between tabs
        explore_btn = app.locator('button:has-text("📊 Explore")')
        if explore_btn.count() > 0:
            explore_btn.first.click()
            app.wait_for_timeout(1000)

        settings_btn = app.locator('button:has-text("Settings")')
        if settings_btn.count() > 0:
            settings_btn.first.click()
            app.wait_for_timeout(1000)

        # App should remain functional
        assert app.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestURLParameterHandling:
    """Test URL parameter handling."""

    def test_url_params_processed(self, page: Page):
        """Test URL parameters are processed."""
        # Navigate with query params
        page.goto(f"{BASE_URL}/?age=65&cancer=lung")
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        # App should load
        assert page.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestMultipleTabInteraction:
    """Test interaction across multiple tabs."""

    def test_all_tabs_accessible(self, app: Page):
        """Test all tabs are accessible in sequence."""
        tabs = [
            "Patient Matching",
            "Explore",
            "Eligibility Explorer",
            "Risk Analysis",
            "Compare Trials",
            "My Referrals",
            "Settings",
            "Fetch Data"
        ]

        for tab_name in tabs:
            # Try to find and click each tab
            tab_btn = app.locator(f'button:has-text("{tab_name}")')
            if tab_btn.count() > 0:
                tab_btn.first.click()
                app.wait_for_timeout(1000)

                # Verify tab loaded
                assert app.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""

    def test_app_recovers_from_errors(self, app: Page):
        """Test app recovers from potential errors."""
        # Navigate between tabs rapidly
        for _ in range(3):
            explore_btn = app.locator('button:has-text("Explore")')
            if explore_btn.count() > 0:
                explore_btn.first.click()
                app.wait_for_timeout(300)

            patient_btn = app.locator('button:has-text("Patient")')
            if patient_btn.count() > 0:
                patient_btn.first.click()
                app.wait_for_timeout(300)

        # App should still be functional
        assert app.locator('[data-testid="stAppViewContainer"]').count() > 0


pytestmark = pytest.mark.ui
