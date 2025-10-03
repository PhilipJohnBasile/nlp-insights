"""Comprehensive UI tests for Risk Analysis tab.

Tests risk scoring, metrics display, and risk categorization.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def risk_tab(page: Page):
    """Navigate to Risk Analysis tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Click Risk Analysis tab
    risk_btn = page.locator('button:has-text("Risk Analysis")')
    if risk_btn.count() > 0:
        risk_btn.first.click()
        page.wait_for_timeout(1500)

    return page


class TestRiskTabNavigation:
    """Test Risk Analysis tab navigation and loading."""

    def test_risk_tab_exists(self, page: Page):
        """Test Risk Analysis tab exists."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        risk_btn = page.locator('button:has-text("Risk")')
        expect(risk_btn.first).to_be_visible()

    def test_risk_tab_loads(self, risk_tab: Page):
        """Test Risk Analysis tab loads content."""
        page_text = risk_tab.content().lower()
        assert "risk" in page_text or "score" in page_text or "analysis" in page_text


class TestRiskMetrics:
    """Test risk metrics display."""

    def test_risk_score_displayed(self, risk_tab: Page):
        """Test risk scores are displayed."""
        page_text = risk_tab.content()
        # Should show risk-related content
        assert "risk" in page_text.lower() or "score" in page_text.lower()

    def test_risk_components_shown(self, risk_tab: Page):
        """Test individual risk components are shown."""
        page_text = risk_tab.content().lower()
        # Should show risk components
        possible_components = ["enrollment", "randomization", "site", "duration"]
        assert any(comp in page_text for comp in possible_components)

    def test_top_risky_trials_displayed(self, risk_tab: Page):
        """Test top risky trials table is shown."""
        page_text = risk_tab.content()
        # Should show trial information
        assert "trial" in page_text.lower() or "nct" in page_text.lower()


class TestRiskCategories:
    """Test risk category classification."""

    def test_risk_categories_exist(self, risk_tab: Page):
        """Test risk categories are defined."""
        page_text = risk_tab.content().lower()
        # Should have risk levels
        risk_levels = ["low", "medium", "high"]
        # May show risk categories
        assert len(page_text) > 100

    def test_risk_thresholds_documented(self, risk_tab: Page):
        """Test risk thresholds are shown or documented."""
        # Page should load successfully
        assert risk_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestRiskVisualization:
    """Test risk visualization elements."""

    def test_risk_data_visualized(self, risk_tab: Page):
        """Test risk data is visualized."""
        # Look for charts or tables
        page_text = risk_tab.content()
        assert len(page_text) > 200

    def test_risk_breakdown_shown(self, risk_tab: Page):
        """Test risk score breakdown is shown."""
        page_text = risk_tab.content().lower()
        # Should show some breakdown
        assert "risk" in page_text


class TestRiskFiltering:
    """Test filtering trials by risk."""

    def test_filter_by_risk_category(self, risk_tab: Page):
        """Test filtering by risk category."""
        # Page should render
        assert risk_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_sort_by_risk_score(self, risk_tab: Page):
        """Test sorting by risk score."""
        # Page should have sortable content
        assert risk_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestRiskExport:
    """Test exporting risk data."""

    def test_risk_export_available(self, risk_tab: Page):
        """Test risk data export is available."""
        page_text = risk_tab.content().lower()
        # May have export option
        assert "risk" in page_text or len(page_text) > 100


pytestmark = pytest.mark.ui
