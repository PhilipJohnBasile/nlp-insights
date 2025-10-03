"""Tests for email alert system."""

import json
import pytest
from pathlib import Path
from datetime import datetime
from trials.email_alerts import EmailAlertSystem, ALERT_TYPES
import tempfile
import shutil


@pytest.fixture
def temp_dir():
    """Create temporary directory for test data."""
    temp = tempfile.mkdtemp()
    yield temp
    shutil.rmtree(temp)


@pytest.fixture
def alert_system(temp_dir):
    """Create email alert system with temporary directory."""
    return EmailAlertSystem(data_dir=temp_dir)


class TestEmailAlertSystem:
    """Test EmailAlertSystem class."""

    def test_initialization(self, alert_system, temp_dir):
        """Test system initializes correctly."""
        assert alert_system.data_dir == Path(temp_dir)
        assert alert_system.data_dir.exists()
        assert alert_system.subscriptions_file.exists() or not alert_system.subscriptions
        assert isinstance(alert_system.email_config, dict)

    def test_email_config_structure(self, alert_system):
        """Test email config has required fields."""
        config = alert_system.email_config
        assert "smtp_server" in config
        assert "smtp_port" in config
        assert "from_email" in config

    def test_hash_email(self, alert_system):
        """Test email hashing for privacy."""
        email = "test@example.com"
        hashed = alert_system._hash_email(email)
        assert isinstance(hashed, str)
        assert len(hashed) == 64  # SHA256 hex digest
        assert hashed != email

        # Same email should produce same hash
        assert alert_system._hash_email(email) == hashed

        # Different email should produce different hash
        assert alert_system._hash_email("other@example.com") != hashed

    def test_subscribe_basic(self, alert_system):
        """Test basic subscription."""
        sub_id = alert_system.subscribe(
            email="patient@example.com",
            alert_types=["new_trials"]
        )

        assert sub_id.startswith("SUB")
        assert len(alert_system.subscriptions) == 1

        sub = alert_system.subscriptions[0]
        assert sub["subscription_id"] == sub_id
        assert sub["alert_types"] == ["new_trials"]
        assert sub["active"] is True
        assert "created_date" in sub

    def test_subscribe_with_profile(self, alert_system):
        """Test subscription with patient profile."""
        profile = {
            "age": 65,
            "cancer_type": "Lung Cancer",
            "biomarkers": ["EGFR"]
        }

        sub_id = alert_system.subscribe(
            email="patient@example.com",
            alert_types=["new_trials", "results_published"],
            patient_profile=profile
        )

        sub = alert_system.subscriptions[0]
        assert sub["patient_profile"] == profile
        assert len(sub["alert_types"]) == 2

    def test_subscribe_with_filters(self, alert_system):
        """Test subscription with trial filters."""
        filters = {
            "phase": ["Phase 3"],
            "location": "California"
        }

        sub_id = alert_system.subscribe(
            email="patient@example.com",
            alert_types=["new_trials"],
            trial_filters=filters
        )

        sub = alert_system.subscriptions[0]
        assert sub["trial_filters"] == filters

    def test_subscribe_persistence(self, temp_dir):
        """Test subscriptions persist to disk."""
        system1 = EmailAlertSystem(data_dir=temp_dir)
        sub_id = system1.subscribe(
            email="test@example.com",
            alert_types=["new_trials"]
        )

        # Create new instance and verify data loaded
        system2 = EmailAlertSystem(data_dir=temp_dir)
        assert len(system2.subscriptions) == 1
        assert system2.subscriptions[0]["subscription_id"] == sub_id

    def test_unsubscribe(self, alert_system):
        """Test unsubscribing from alerts."""
        email = "patient@example.com"
        alert_system.subscribe(email=email, alert_types=["new_trials"])

        result = alert_system.unsubscribe(email)
        assert result is True
        assert alert_system.subscriptions[0]["active"] is False

    def test_unsubscribe_not_found(self, alert_system):
        """Test unsubscribing non-existent email."""
        result = alert_system.unsubscribe("nonexistent@example.com")
        assert result is False

    def test_update_subscription(self, alert_system):
        """Test updating subscription preferences."""
        sub_id = alert_system.subscribe(
            email="test@example.com",
            alert_types=["new_trials"]
        )

        result = alert_system.update_subscription(
            subscription_id=sub_id,
            alert_types=["new_trials", "protocol_updates"],
            patient_profile={"age": 70}
        )

        assert result is True
        sub = alert_system.subscriptions[0]
        assert len(sub["alert_types"]) == 2
        assert sub["patient_profile"]["age"] == 70

    def test_update_subscription_not_found(self, alert_system):
        """Test updating non-existent subscription."""
        result = alert_system.update_subscription(
            subscription_id="SUBXXXXX",
            alert_types=["new_trials"]
        )
        assert result is False

    def test_get_active_subscriptions(self, alert_system):
        """Test getting active subscriptions."""
        alert_system.subscribe("user1@example.com", ["new_trials"])
        alert_system.subscribe("user2@example.com", ["results_published"])
        alert_system.subscribe("user3@example.com", ["new_trials"])
        alert_system.unsubscribe("user3@example.com")

        active = alert_system.get_active_subscriptions()
        assert len(active) == 2

    def test_get_active_subscriptions_by_type(self, alert_system):
        """Test filtering active subscriptions by alert type."""
        alert_system.subscribe("user1@example.com", ["new_trials"])
        alert_system.subscribe("user2@example.com", ["results_published"])
        alert_system.subscribe("user3@example.com", ["new_trials", "results_published"])

        new_trials_subs = alert_system.get_active_subscriptions("new_trials")
        assert len(new_trials_subs) == 2

        results_subs = alert_system.get_active_subscriptions("results_published")
        assert len(results_subs) == 2

    def test_send_alert_no_config(self, alert_system):
        """Test sending alert without email configuration."""
        result = alert_system.send_alert(
            email="test@example.com",
            subject="Test Alert",
            body_html="<p>Test content</p>"
        )
        assert result is False

    def test_send_alert_with_subscription_tracking(self, alert_system, monkeypatch):
        """Test alert tracks subscription stats."""
        # Mock SMTP to avoid actual email sending
        def mock_smtp_init(self, *args, **kwargs):
            pass

        class MockSMTP:
            def __init__(self, *args, **kwargs):
                pass
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def starttls(self):
                pass
            def login(self, *args):
                pass
            def send_message(self, msg):
                pass

        monkeypatch.setattr("smtplib.SMTP", MockSMTP)

        # Configure email
        alert_system.email_config["username"] = "test@example.com"
        alert_system.email_config["password"] = "password"

        sub_id = alert_system.subscribe("user@example.com", ["new_trials"])

        result = alert_system.send_alert(
            email="user@example.com",
            subject="Test",
            body_html="<p>Test</p>",
            subscription_id=sub_id
        )

        assert result is True
        sub = alert_system.subscriptions[0]
        assert sub["total_alerts_sent"] == 1
        assert sub["last_sent"] is not None

    def test_generate_new_trials_email(self, alert_system):
        """Test generating new trials email HTML."""
        trials = [
            {
                "nct_id": "NCT12345678",
                "title": "Test Trial for Lung Cancer",
                "phase": "Phase 3",
                "locations_count": 15
            }
        ]

        profile = {
            "cancer_type": "Lung Cancer",
            "age": 65,
            "location": "California"
        }

        html = alert_system.generate_new_trials_email(trials, profile)

        assert "NCT12345678" in html
        assert "Test Trial for Lung Cancer" in html
        assert "Phase 3" in html
        assert "Lung Cancer" in html
        assert "California" in html
        assert "<html>" in html
        assert "</html>" in html

    def test_generate_email_limits_trials(self, alert_system):
        """Test email limits to 10 trials."""
        trials = [{"nct_id": f"NCT{i:08d}", "title": f"Trial {i}"} for i in range(20)]
        profile = {"cancer_type": "Lung Cancer"}

        html = alert_system.generate_new_trials_email(trials, profile)

        # Should only include first 10
        assert "NCT00000000" in html
        assert "NCT00000009" in html
        assert "NCT00000010" not in html

    def test_load_subscriptions_with_corrupt_file(self, temp_dir):
        """Test loading with corrupt subscriptions file."""
        # Create corrupt JSON file
        subs_file = Path(temp_dir) / "subscriptions.json"
        subs_file.write_text("{invalid json")

        system = EmailAlertSystem(data_dir=temp_dir)
        assert system.subscriptions == []

    def test_alert_types_constant(self):
        """Test ALERT_TYPES constant is defined."""
        assert len(ALERT_TYPES) == 5
        assert "new_trials" in ALERT_TYPES
        assert "protocol_updates" in ALERT_TYPES
        assert "results_published" in ALERT_TYPES
        assert "enrollment_closing" in ALERT_TYPES
        assert "nearby_sites_opened" in ALERT_TYPES

    def test_multiple_subscriptions_same_email(self, alert_system):
        """Test multiple subscriptions for same email."""
        email = "patient@example.com"

        sub1 = alert_system.subscribe(email, ["new_trials"])
        sub2 = alert_system.subscribe(email, ["results_published"])

        assert len(alert_system.subscriptions) == 2
        assert sub1 != sub2

    def test_unsubscribe_affects_all_emails(self, alert_system):
        """Test unsubscribe deactivates all subscriptions for an email."""
        email = "patient@example.com"

        alert_system.subscribe(email, ["new_trials"])
        alert_system.subscribe(email, ["results_published"])

        result = alert_system.unsubscribe(email)
        assert result is True

        active = alert_system.get_active_subscriptions()
        assert len(active) == 0
