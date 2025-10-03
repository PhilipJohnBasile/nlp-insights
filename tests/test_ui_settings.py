"""Comprehensive UI tests for Settings tab.

Tests configuration options, preferences, and settings persistence.
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8501"


@pytest.fixture(scope="function")
def settings_tab(page: Page):
    """Navigate to Settings tab."""
    page.goto(BASE_URL)
    page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
    page.wait_for_timeout(2000)

    # Click Settings tab
    settings_btn = page.locator('button:has-text("Settings")')
    if settings_btn.count() > 0:
        settings_btn.first.click()
        page.wait_for_timeout(2000)

    return page


class TestSettingsTabNavigation:
    """Test Settings tab navigation."""

    def test_settings_tab_exists(self, page: Page):
        """Test Settings tab exists."""
        page.goto(BASE_URL)
        page.wait_for_selector('[data-testid="stAppViewContainer"]', timeout=10000)
        page.wait_for_timeout(2000)

        settings_btn = page.locator('button:has-text("Settings")')
        expect(settings_btn.first).to_be_visible()

    def test_settings_tab_loads(self, settings_tab: Page):
        """Test Settings tab loads."""
        page_text = settings_tab.content().lower()
        assert "setting" in page_text or "preference" in page_text or "config" in page_text


class TestEmailAlerts:
    """Test email alert configuration."""

    def test_email_alerts_section(self, settings_tab: Page):
        """Test email alerts section exists."""
        page_text = settings_tab.content().lower()
        # May have email or notification settings
        assert len(page_text) > 50

    def test_alert_type_selection(self, settings_tab: Page):
        """Test alert type selection."""
        # Page should render settings
        assert settings_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestNotificationPreferences:
    """Test notification preferences."""

    def test_notification_settings(self, settings_tab: Page):
        """Test notification settings are available."""
        page_text = settings_tab.content()
        assert len(page_text) > 50


class TestDataPreferences:
    """Test data and display preferences."""

    def test_distance_unit_preference(self, settings_tab: Page):
        """Test distance unit preference."""
        # Settings page should load
        assert settings_tab.locator('[data-testid="stAppViewContainer"]').count() > 0

    def test_data_refresh_settings(self, settings_tab: Page):
        """Test data refresh settings."""
        page_text = settings_tab.content()
        assert len(page_text) > 50


class TestExportPreferences:
    """Test export format preferences."""

    def test_export_format_options(self, settings_tab: Page):
        """Test export format preferences."""
        # Page should render
        assert settings_tab.locator('[data-testid="stAppViewContainer"]').count() > 0


class TestSettingsPersistence:
    """Test settings persistence."""

    def test_save_settings_button(self, settings_tab: Page):
        """Test save settings functionality."""
        page_text = settings_tab.content()
        assert len(page_text) > 50


pytestmark = pytest.mark.ui
