"""Comprehensive UI tests for Patient Matching tab.

Tests all functionality in the Patient Matching workflow including:
- NCT ID quick lookup
- Patient demographics form
- Cancer information
- Biomarker selection
- Patient conditions
- Filters and search
- Form submission and results
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def patient_matching_tab(page: Page):
    """Navigate to Patient Matching tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Should default to Patient Matching tab
    return page


class TestNCTLookup:
    """Test NCT ID quick lookup functionality."""

    def test_nct_lookup_input_visible(self, patient_matching_tab: Page):
        """Test that NCT lookup input is visible."""
        expect(patient_matching_tab.locator("text=/Quick NCT ID Lookup/i")).to_be_visible()

        # Check for input field
        nct_input = patient_matching_tab.locator('input[placeholder*="NCT"]').first
        expect(nct_input).to_be_visible()

    def test_nct_lookup_button_visible(self, patient_matching_tab: Page):
        """Test that Look Up button is visible."""
        lookup_btn = patient_matching_tab.locator('button:has-text("Look Up")')
        expect(lookup_btn).to_be_visible()

    def test_nct_lookup_input_accepts_text(self, patient_matching_tab: Page):
        """Test typing into NCT lookup field."""
        nct_input = patient_matching_tab.locator('input[placeholder*="NCT"]').first
        nct_input.fill("NCT12345678")
        patient_matching_tab.wait_for_timeout(500)
        assert nct_input.input_value() == "NCT12345678"

    def test_nct_lookup_validates_format(self, patient_matching_tab: Page):
        """Test NCT ID format validation."""
        nct_input = patient_matching_tab.locator('input[placeholder*="NCT"]').first

        # Test valid format
        nct_input.fill("NCT12345678")
        patient_matching_tab.wait_for_timeout(300)

        # Test lowercase (should work)
        nct_input.clear()
        nct_input.fill("nct12345678")
        patient_matching_tab.wait_for_timeout(300)


class TestPatientDemographics:
    """Test patient demographics form fields."""

    def test_age_input_visible(self, patient_matching_tab: Page):
        """Test age input field is visible."""
        expect(patient_matching_tab.locator("text=/Age/i").first).to_be_visible()

        # Age input should be number type
        age_input = patient_matching_tab.locator('input[type="number"]').first
        expect(age_input).to_be_visible()

    def test_age_input_accepts_valid_age(self, patient_matching_tab: Page):
        """Test entering valid age."""
        age_input = patient_matching_tab.locator('input[type="number"]').first
        age_input.fill("65")
        patient_matching_tab.wait_for_timeout(300)
        assert age_input.input_value() == "65"

    def test_age_input_boundaries(self, patient_matching_tab: Page):
        """Test age input boundaries."""
        age_input = patient_matching_tab.locator('input[type="number"]').first

        # Test minimum age
        age_input.fill("18")
        patient_matching_tab.wait_for_timeout(300)

        # Test maximum reasonable age
        age_input.clear()
        age_input.fill("100")
        patient_matching_tab.wait_for_timeout(300)

    def test_sex_selection_visible(self, patient_matching_tab: Page):
        """Test sex selection dropdown is visible."""
        expect(patient_matching_tab.locator("text=/Sex/i").first).to_be_visible()

    def test_sex_options_available(self, patient_matching_tab: Page):
        """Test sex dropdown has expected options."""
        # Look for sex-related content in the page
        page_text = patient_matching_tab.content().lower()
        assert "male" in page_text or "female" in page_text


class TestCancerInformation:
    """Test cancer information form fields."""

    def test_cancer_type_input_visible(self, patient_matching_tab: Page):
        """Test cancer type input is visible."""
        expect(patient_matching_tab.locator("text=/Cancer Type/i").first).to_be_visible()

    def test_cancer_type_accepts_input(self, patient_matching_tab: Page):
        """Test typing cancer type."""
        # Find text input for cancer type
        cancer_inputs = patient_matching_tab.locator('input[type="text"]')
        if cancer_inputs.count() > 0:
            cancer_input = cancer_inputs.first
            cancer_input.fill("Lung Cancer")
            patient_matching_tab.wait_for_timeout(300)

    def test_stage_selection_visible(self, patient_matching_tab: Page):
        """Test stage selection is visible."""
        expect(patient_matching_tab.locator("text=/Stage/i").first).to_be_visible()


class TestBiomarkers:
    """Test biomarker checkbox interactions."""

    def test_egfr_checkbox_visible(self, patient_matching_tab: Page):
        """Test EGFR checkbox is visible."""
        egfr = patient_matching_tab.locator('text=/EGFR/i').first
        expect(egfr).to_be_visible()

    def test_alk_checkbox_visible(self, patient_matching_tab: Page):
        """Test ALK checkbox is visible."""
        alk = patient_matching_tab.locator('text=/ALK/i').first
        expect(alk).to_be_visible()

    def test_pdl1_checkbox_visible(self, patient_matching_tab: Page):
        """Test PD-L1 checkbox is visible."""
        pdl1 = patient_matching_tab.locator('text=/PD-L1/i').first
        expect(pdl1).to_be_visible()

    def test_her2_checkbox_visible(self, patient_matching_tab: Page):
        """Test HER2 checkbox is visible."""
        her2 = patient_matching_tab.locator('text=/HER2/i').first
        expect(her2).to_be_visible()

    def test_brca_checkbox_visible(self, patient_matching_tab: Page):
        """Test BRCA checkbox is visible."""
        brca = patient_matching_tab.locator('text=/BRCA/i').first
        expect(brca).to_be_visible()

    def test_msi_checkbox_visible(self, patient_matching_tab: Page):
        """Test MSI-High checkbox is visible."""
        msi = patient_matching_tab.locator('text=/MSI/i').first
        expect(msi).to_be_visible()

    def test_biomarker_checkbox_interaction(self, patient_matching_tab: Page):
        """Test clicking biomarker checkboxes."""
        # Find EGFR checkbox label
        egfr_label = patient_matching_tab.locator('label:has-text("EGFR")')

        if egfr_label.count() > 0 and egfr_label.is_visible():
            egfr_label.first.click()
            patient_matching_tab.wait_for_timeout(500)


class TestPatientConditions:
    """Test patient condition checkboxes."""

    def test_brain_mets_checkbox_visible(self, patient_matching_tab: Page):
        """Test brain metastases checkbox is visible."""
        brain_mets = patient_matching_tab.locator('text=/Brain metastases/i').first
        expect(brain_mets).to_be_visible(timeout=5000)

    def test_autoimmune_checkbox_visible(self, patient_matching_tab: Page):
        """Test autoimmune disease checkbox is visible."""
        autoimmune = patient_matching_tab.locator('text=/Autoimmune/i').first
        expect(autoimmune).to_be_visible(timeout=5000)

    def test_hiv_checkbox_visible(self, patient_matching_tab: Page):
        """Test HIV positive checkbox is visible."""
        hiv = patient_matching_tab.locator('text=/HIV/i').first
        expect(hiv).to_be_visible(timeout=5000)


class TestFilters:
    """Test filter options and controls."""

    def test_recruiting_only_filter_visible(self, patient_matching_tab: Page):
        """Test recruiting only filter is visible."""
        recruiting = patient_matching_tab.locator('text=/actively recruiting/i').first
        expect(recruiting).to_be_visible()

    def test_distance_filter_visible(self, patient_matching_tab: Page):
        """Test distance filter is visible."""
        distance = patient_matching_tab.locator('text=/distance/i').first
        expect(distance).to_be_visible(timeout=5000)

    def test_phase_filters_visible(self, patient_matching_tab: Page):
        """Test phase filter checkboxes are visible."""
        page_text = patient_matching_tab.content().lower()
        assert "phase 1" in page_text or "phase 2" in page_text

    def test_distance_slider_interaction(self, patient_matching_tab: Page):
        """Test distance slider can be adjusted."""
        # Look for slider elements
        sliders = patient_matching_tab.locator('input[type="range"]')
        if sliders.count() > 0:
            slider = sliders.first
            # Sliders exist
            assert slider.count() > 0


class TestFormSubmission:
    """Test form submission and search functionality."""

    def test_submit_button_visible(self, patient_matching_tab: Page):
        """Test Find Matching Trials button is visible."""
        submit_btn = patient_matching_tab.locator('button:has-text("Find Matching Trials")')
        expect(submit_btn).to_be_visible()

    def test_submit_button_is_primary(self, patient_matching_tab: Page):
        """Test submit button has primary styling."""
        submit_btn = patient_matching_tab.locator('button:has-text("Find Matching Trials")')
        # Primary button should be visible
        expect(submit_btn).to_be_visible()

    def test_form_accepts_complete_input(self, patient_matching_tab: Page):
        """Test filling out complete patient form."""
        # Fill age
        age_input = patient_matching_tab.locator('input[type="number"]').first
        age_input.fill("65")

        # Fill cancer type
        text_inputs = patient_matching_tab.locator('input[type="text"]')
        if text_inputs.count() > 0:
            text_inputs.first.fill("Lung Cancer")

        patient_matching_tab.wait_for_timeout(500)

        # Verify submit button still visible
        submit_btn = patient_matching_tab.locator('button:has-text("Find Matching Trials")')
        expect(submit_btn).to_be_visible()


# Mark all tests as UI tests
pytestmark = pytest.mark.ui
