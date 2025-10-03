"""Email alert system for clinical trial notifications."""

import json
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Dict, List, Optional
import hashlib


class EmailAlertSystem:
    """Manage email alerts for trial updates."""

    def __init__(self, data_dir: str = "data/alerts"):
        """Initialize email alert system.

        Args:
            data_dir: Directory to store alert subscriptions
        """
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.subscriptions_file = self.data_dir / "subscriptions.json"
        self.subscriptions = self._load_subscriptions()
        self.email_config = self._load_email_config()

    def _load_subscriptions(self) -> List[Dict]:
        """Load existing subscriptions from file."""
        if self.subscriptions_file.exists():
            try:
                with open(self.subscriptions_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []

    def _save_subscriptions(self):
        """Save subscriptions to file."""
        with open(self.subscriptions_file, 'w') as f:
            json.dump(self.subscriptions, f, indent=2)

    def _load_email_config(self) -> Dict:
        """Load email configuration from environment or config file.

        Returns:
            Dict with SMTP config (smtp_server, smtp_port, username, password)
        """
        # In production, load from environment variables or secure config
        # For now, return placeholder that will need to be configured
        return {
            "smtp_server": "smtp.gmail.com",  # Example: Gmail SMTP
            "smtp_port": 587,
            "username": "",  # To be configured
            "password": "",  # To be configured
            "from_email": "noreply@clinicaltrials.app"
        }

    def _hash_email(self, email: str) -> str:
        """Hash email for privacy.

        Args:
            email: Email address

        Returns:
            Hashed email
        """
        return hashlib.sha256(email.encode()).hexdigest()

    def subscribe(
        self,
        email: str,
        alert_types: List[str],
        patient_profile: Optional[Dict] = None,
        trial_filters: Optional[Dict] = None
    ) -> str:
        """Subscribe to email alerts.

        Args:
            email: Email address for alerts
            alert_types: List of alert types (new_trials, protocol_updates, results_published, enrollment_closing)
            patient_profile: Optional patient profile for matching (age, cancer_type, biomarkers, etc.)
            trial_filters: Optional filters (phase, location, etc.)

        Returns:
            Subscription ID
        """
        subscription_id = f"SUB{len(self.subscriptions) + 1:05d}"

        subscription = {
            "subscription_id": subscription_id,
            "email_hash": self._hash_email(email),  # Store hashed for privacy
            "alert_types": alert_types,
            "patient_profile": patient_profile or {},
            "trial_filters": trial_filters or {},
            "active": True,
            "created_date": datetime.now().isoformat(),
            "last_sent": None,
            "total_alerts_sent": 0
        }

        self.subscriptions.append(subscription)
        self._save_subscriptions()

        return subscription_id

    def unsubscribe(self, email: str) -> bool:
        """Unsubscribe an email from all alerts.

        Args:
            email: Email address to unsubscribe

        Returns:
            True if successful, False if not found
        """
        email_hash = self._hash_email(email)
        found = False

        for sub in self.subscriptions:
            if sub["email_hash"] == email_hash:
                sub["active"] = False
                found = True

        if found:
            self._save_subscriptions()

        return found

    def update_subscription(
        self,
        subscription_id: str,
        alert_types: Optional[List[str]] = None,
        patient_profile: Optional[Dict] = None,
        trial_filters: Optional[Dict] = None
    ) -> bool:
        """Update subscription preferences.

        Args:
            subscription_id: Subscription ID to update
            alert_types: Updated alert types
            patient_profile: Updated patient profile
            trial_filters: Updated filters

        Returns:
            True if successful, False if not found
        """
        for sub in self.subscriptions:
            if sub["subscription_id"] == subscription_id:
                if alert_types is not None:
                    sub["alert_types"] = alert_types
                if patient_profile is not None:
                    sub["patient_profile"] = patient_profile
                if trial_filters is not None:
                    sub["trial_filters"] = trial_filters

                self._save_subscriptions()
                return True

        return False

    def get_active_subscriptions(self, alert_type: Optional[str] = None) -> List[Dict]:
        """Get all active subscriptions.

        Args:
            alert_type: Optional filter by alert type

        Returns:
            List of active subscriptions
        """
        active = [s for s in self.subscriptions if s["active"]]

        if alert_type:
            active = [s for s in active if alert_type in s["alert_types"]]

        return active

    def send_alert(
        self,
        email: str,
        subject: str,
        body_html: str,
        subscription_id: Optional[str] = None
    ) -> bool:
        """Send an email alert.

        Args:
            email: Recipient email
            subject: Email subject
            body_html: HTML email body
            subscription_id: Optional subscription ID to track

        Returns:
            True if sent successfully, False otherwise
        """
        # NOTE: This is a placeholder. In production:
        # 1. Validate email configuration
        # 2. Use proper authentication
        # 3. Handle rate limiting
        # 4. Add unsubscribe links
        # 5. Track bounces and failures

        if not self.email_config.get("username") or not self.email_config.get("password"):
            # Email not configured
            print(f"Email alert simulated (not configured): {subject} to {email}")
            return False

        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_config["from_email"]
            msg['To'] = email

            # Add unsubscribe link
            unsubscribe_link = f"https://clinicaltrials.app/unsubscribe?email={email}"
            footer = f"""
            <hr>
            <p style='font-size: 0.8rem; color: #666;'>
            You received this email because you subscribed to clinical trial alerts.
            <a href='{unsubscribe_link}'>Unsubscribe</a>
            </p>
            """
            full_body = body_html + footer

            part = MIMEText(full_body, 'html')
            msg.attach(part)

            with smtplib.SMTP(self.email_config["smtp_server"], self.email_config["smtp_port"]) as server:
                server.starttls()
                server.login(self.email_config["username"], self.email_config["password"])
                server.send_message(msg)

            # Update subscription tracking
            if subscription_id:
                for sub in self.subscriptions:
                    if sub["subscription_id"] == subscription_id:
                        sub["last_sent"] = datetime.now().isoformat()
                        sub["total_alerts_sent"] += 1
                self._save_subscriptions()

            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    def generate_new_trials_email(self, trials: List[Dict], profile: Dict) -> str:
        """Generate HTML email for new matching trials.

        Args:
            trials: List of matching trial dictionaries
            profile: Patient profile used for matching

        Returns:
            HTML email body
        """
        html = f"""
        <html>
        <body style='font-family: Arial, sans-serif; line-height: 1.6; color: #333;'>
            <h2 style='color: #0066cc;'>🔍 New Clinical Trials Matching Your Profile</h2>

            <p>We found <strong>{len(trials)}</strong> new clinical trial(s) that match your criteria:</p>

            <div style='background-color: #f8f9fa; padding: 12px; border-radius: 4px; margin: 16px 0;'>
                <strong>Your Profile:</strong><br>
                Cancer Type: {profile.get('cancer_type', 'Not specified')}<br>
                Age: {profile.get('age', 'Not specified')}<br>
                Location: {profile.get('location', 'Not specified')}
            </div>

            <h3>Matching Trials:</h3>
        """

        for trial in trials[:10]:  # Limit to 10 trials per email
            nct_id = trial.get('nct_id', 'Unknown')
            title = trial.get('title', 'No title')
            phase = trial.get('phase', 'Unknown phase')
            locations = trial.get('locations_count', 0)

            html += f"""
            <div style='border-left: 4px solid #0066cc; padding: 12px; margin: 16px 0; background-color: #f8f9ff;'>
                <h4 style='margin-top: 0;'><a href='https://clinicaltrials.gov/study/{nct_id}' style='color: #0066cc; text-decoration: none;'>{nct_id}</a></h4>
                <p><strong>{title}</strong></p>
                <p style='color: #666; font-size: 0.9rem;'>
                    Phase: {phase} | Sites: {locations}
                </p>
            </div>
            """

        html += """
            <p style='margin-top: 24px;'>
                <a href='https://clinicaltrials.app' style='background-color: #0066cc; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block;'>
                    View All Trials
                </a>
            </p>
        </body>
        </html>
        """

        return html


# Alert types
ALERT_TYPES = [
    "new_trials",            # New trials matching profile
    "protocol_updates",      # Eligibility criteria changes
    "results_published",     # Trial results posted
    "enrollment_closing",    # Trials approaching enrollment targets
    "nearby_sites_opened"    # New sites opened near user location
]
