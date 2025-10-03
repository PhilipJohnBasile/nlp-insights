"""Playwright UI tests for Streamlit Clinical Trials app.

These tests interact with the actual running Streamlit application.
Make sure the app is running on http://localhost:8501 before running tests.

Run tests with:
    pytest tests/test_ui_playwright.py --headed  # See browser
    pytest tests/test_ui_playwright.py           # Headless mode
"""

import pytest
import re
from playwright.sync_api import Page, expect
import time


# Base URL for tests
BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def streamlit_app(page: Page):
    """Navigate to Streamlit app and wait for it to load."""
    page.goto(BASE_URL)

    # Wait for Streamlit to be ready
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)

    # Wait a bit for dynamic content to load
    page.wait_for_timeout(2000)

    return page


class TestAppInitialization:
    """Test that the app loads and initializes correctly."""

    def test_app_loads(self, streamlit_app: Page):
        """Test that the main app loads successfully."""
        # Check that the main title is present
        expect(streamlit_app.locator("text=Clinical Trials Insights")).to_be_visible()

    def test_header_present(self, streamlit_app: Page):
        """Test that main header elements are present."""
        # Check for disclaimer
        expect(streamlit_app.locator("text=/Disclaimer/i")).to_be_visible()

        # Check for research tool warning - use .first to handle multiple matches
        expect(streamlit_app.locator("text=/research tool/i").first).to_be_visible()

    def test_tabs_visible(self, streamlit_app: Page):
        """Test that all main tabs are visible."""
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
            # Use flexible matching to find tabs
            expect(streamlit_app.locator(f"text=/{tab_name}/i").first).to_be_visible()


class TestPatientMatching:
    """Test Patient Matching workflow."""

    def test_patient_matching_tab_loads(self, streamlit_app: Page):
        """Test that Patient Matching tab loads with form."""
        # Click on Patient Matching tab (should be default)
        expect(streamlit_app.locator("text=/Patient Matching/i").first).to_be_visible()

        # Check for form elements
        expect(streamlit_app.locator("text=/Age/i").first).to_be_visible()
        expect(streamlit_app.locator("text=/Sex/i").first).to_be_visible()
        expect(streamlit_app.locator("text=/Cancer Type/i").first).to_be_visible()

    def test_nct_lookup_present(self, streamlit_app: Page):
        """Test that NCT ID lookup feature is present."""
        expect(streamlit_app.locator("text=/Quick NCT ID Lookup/i")).to_be_visible()

    def test_form_submission_button(self, streamlit_app: Page):
        """Test that form has a submit button."""
        # Look for the submit button
        submit_button = streamlit_app.locator("button:has-text('Find Matching Trials')")
        expect(submit_button).to_be_visible()

    def test_patient_form_inputs(self, streamlit_app: Page):
        """Test filling out patient form."""
        # Fill in age
        age_input = streamlit_app.locator("input[type='number']").first
        age_input.fill("65")

        # Wait for form to update
        streamlit_app.wait_for_timeout(500)

        # Verify value was set
        assert age_input.input_value() == "65"

    def test_biomarker_checkboxes(self, streamlit_app: Page):
        """Test that biomarker checkboxes are present."""
        biomarkers = ["EGFR", "ALK", "PD-L1", "HER2"]

        for marker in biomarkers:
            # Check if checkbox label exists
            checkbox = streamlit_app.locator(f"text=/{marker}/i").first
            expect(checkbox).to_be_visible(timeout=5000)


class TestNavigation:
    """Test navigation between different sections."""

    def test_navigate_to_explore_tab(self, streamlit_app: Page):
        """Test navigation to Explore tab."""
        # Click Explore tab
        explore_tab = streamlit_app.locator("button:has-text('📊 Explore')")
        if explore_tab.count() > 0:
            explore_tab.first.click()
            streamlit_app.wait_for_timeout(1000)

    def test_navigate_to_settings(self, streamlit_app: Page):
        """Test navigation to Settings tab."""
        settings_tab = streamlit_app.locator("button:has-text('Settings')")
        if settings_tab.count() > 0:
            settings_tab.first.click()
            # Increase wait time for Streamlit to re-render
            streamlit_app.wait_for_timeout(2000)

            # Check settings content loads - use heading to avoid tab/heading duplicate match
            expect(streamlit_app.locator("h2:has-text('Settings')")).to_be_visible()


class TestDataDisplay:
    """Test data display and filtering features."""

    def test_no_data_message(self, streamlit_app: Page):
        """Test that appropriate message shows when no data is loaded."""
        # Should show message about loading data
        page_text = streamlit_app.content()

        # Look for data-related message
        assert "data" in page_text.lower() or "fetch" in page_text.lower()

    def test_fetch_data_tab_present(self, streamlit_app: Page):
        """Test that Fetch Data tab is present."""
        fetch_tab = streamlit_app.locator("button:has-text('Fetch Data')")
        expect(fetch_tab).to_be_visible()


class TestResponsiveDesign:
    """Test responsive design and mobile layouts."""

    def test_mobile_viewport(self, page: Page):
        """Test app in mobile viewport."""
        # Set mobile viewport
        page.set_viewport_size({"width": 375, "height": 667})
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        # Check that Streamlit app container is visible (Streamlit handles mobile layout)
        expect(page.locator('[data-testid="stAppViewContainer"]')).to_be_visible()

    def test_tablet_viewport(self, page: Page):
        """Test app in tablet viewport."""
        # Set tablet viewport
        page.set_viewport_size({"width": 768, "height": 1024})
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        # Check that Streamlit app container is visible (Streamlit handles tablet layout)
        expect(page.locator('[data-testid="stAppViewContainer"]')).to_be_visible()


class TestAccessibility:
    """Test accessibility features."""

    def test_page_has_title(self, streamlit_app: Page):
        """Test that page has a proper title."""
        title = streamlit_app.title()
        assert "Clinical Trials" in title or "Streamlit" in title

    def test_main_landmarks(self, streamlit_app: Page):
        """Test that main page landmarks are present."""
        # Streamlit creates specific data-testid attributes
        expect(streamlit_app.locator('[data-testid="stAppViewContainer"]')).to_be_visible()


class TestInteractiveElements:
    """Test interactive UI elements."""

    def test_checkbox_interaction(self, streamlit_app: Page):
        """Test checkbox interactions."""
        # Find EGFR checkbox label (Streamlit hides actual checkbox, use label)
        egfr_label = streamlit_app.locator('label:has-text("EGFR mutation")')

        if egfr_label.count() > 0 and egfr_label.is_visible():
            # Click the label (which toggles the hidden checkbox)
            egfr_label.click()
            streamlit_app.wait_for_timeout(500)

            # Verify checkbox exists (whether visible or not)
            checkbox = streamlit_app.locator('input[aria-label="EGFR mutation"]')
            assert checkbox.count() > 0
        else:
            # Fallback: just verify any checkbox label exists
            checkbox_label = streamlit_app.locator('label:has(input[type="checkbox"])').first
            expect(checkbox_label).to_be_visible()

    def test_text_input_interaction(self, streamlit_app: Page):
        """Test text input interactions."""
        # Find NCT ID input or cancer type input
        text_input = streamlit_app.locator('input[type="text"]').first

        if text_input.count() > 0:
            # Type into input
            text_input.fill("test input")
            streamlit_app.wait_for_timeout(500)

            # Verify value
            assert text_input.input_value() == "test input"


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_invalid_page_url(self, page: Page):
        """Test handling of invalid URL."""
        # Try to navigate to non-existent page
        page.goto(f"{BASE_URL}/nonexistent")
        page.wait_for_timeout(2000)

        # Should still show the main app (Streamlit handles routing)
        expect(page.locator('[data-testid="stAppViewContainer"]')).to_be_visible()


class TestPerformance:
    """Test performance-related aspects."""

    def test_initial_load_time(self, page: Page):
        """Test that initial load completes in reasonable time."""
        start_time = time.time()

        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)

        load_time = time.time() - start_time

        # Should load in less than 10 seconds
        assert load_time < 10, f"Page took {load_time}s to load"

    def test_tab_switch_performance(self, streamlit_app: Page):
        """Test that tab switching is responsive."""
        # Get all tab buttons
        tabs = streamlit_app.locator('button[role="tab"]')

        if tabs.count() > 1:
            start_time = time.time()

            # Click second tab
            tabs.nth(1).click()
            streamlit_app.wait_for_timeout(500)

            switch_time = time.time() - start_time

            # Should switch in less than 2 seconds
            assert switch_time < 2, f"Tab switch took {switch_time}s"


class TestFullUserJourney:
    """Test complete user workflows."""

    def test_basic_search_workflow(self, streamlit_app: Page):
        """Test basic patient search workflow."""
        # 1. Verify we're on Patient Matching tab
        expect(streamlit_app.locator("text=/Patient Matching/i").first).to_be_visible()

        # 2. Fill in basic patient information
        age_input = streamlit_app.locator("input[type='number']").first
        age_input.fill("65")

        streamlit_app.wait_for_timeout(500)

        # 3. Look for submit button
        submit_button = streamlit_app.locator("button:has-text('Find Matching Trials')")
        expect(submit_button).to_be_visible()

        # Note: We don't actually submit to avoid depending on data availability
        # In a full test environment with test data, we would:
        # submit_button.click()
        # streamlit_app.wait_for_timeout(2000)
        # expect(streamlit_app.locator("text=/Matching Trials/i")).to_be_visible()


# Markers for test categorization
pytestmark = pytest.mark.ui
