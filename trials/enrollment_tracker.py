"""Track and analyze enrollment status for clinical trials."""

import re
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple


def parse_enrollment_data(trial_data: Dict) -> Dict:
    """Extract enrollment information from trial data.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Dictionary with enrollment metrics
    """
    status_module = trial_data.get("protocolSection", {}).get("statusModule", {})
    design_module = trial_data.get("protocolSection", {}).get("designModule", {})

    # Basic enrollment data
    enrollment = design_module.get("enrollmentInfo", {})
    target_enrollment = enrollment.get("count", 0)

    # Status information
    overall_status = status_module.get("overallStatus", "Unknown")
    last_update_date = status_module.get("lastUpdateSubmitDate")
    start_date = status_module.get("startDateStruct", {}).get("date")

    # Calculate enrollment velocity if possible
    velocity = None
    days_enrolling = None

    if start_date and overall_status in ["Recruiting", "Active, not recruiting"]:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            now = datetime.now()
            days_enrolling = (now - start).days

            # Estimate enrollment rate (simplified - would need actual enrollment data)
            # This is a placeholder calculation
            if days_enrolling > 0 and target_enrollment > 0:
                # Assume 50% enrollment if actively recruiting (very rough estimate)
                estimated_enrolled = target_enrollment * 0.5 if overall_status == "Recruiting" else target_enrollment * 0.8
                velocity = estimated_enrolled / (days_enrolling / 30)  # patients per month
        except:
            pass

    # Parse sites information
    locations = trial_data.get("protocolSection", {}).get("contactsLocationsModule", {}).get("locations", [])
    total_sites = len(locations)

    recruiting_sites = 0
    site_details = []

    for location in locations:
        loc_status = location.get("status", "Unknown")
        if loc_status == "Recruiting":
            recruiting_sites += 1

        site_info = {
            "facility": location.get("facility", "Unknown"),
            "city": location.get("city", ""),
            "state": location.get("state", ""),
            "status": loc_status,
            "contact": location.get("contacts", [{}])[0].get("name") if location.get("contacts") else None,
            "phone": location.get("contacts", [{}])[0].get("phone") if location.get("contacts") else None
        }
        site_details.append(site_info)

    return {
        "target_enrollment": target_enrollment,
        "overall_status": overall_status,
        "total_sites": total_sites,
        "recruiting_sites": recruiting_sites,
        "enrollment_velocity": velocity,  # patients per month estimate
        "days_enrolling": days_enrolling,
        "last_update_date": last_update_date,
        "start_date": start_date,
        "site_details": site_details
    }


def calculate_enrollment_urgency(enrollment_data: Dict) -> Tuple[str, str]:
    """Determine enrollment urgency level and wait time estimate.

    Args:
        enrollment_data: Output from parse_enrollment_data

    Returns:
        Tuple of (urgency_level, wait_time_estimate)
    """
    velocity = enrollment_data.get("enrollment_velocity")
    recruiting_sites = enrollment_data.get("recruiting_sites", 0)
    total_sites = enrollment_data.get("total_sites", 1)
    status = enrollment_data.get("overall_status", "")

    # Determine urgency
    if status == "Active, not recruiting":
        return "CLOSED", "Trial is no longer recruiting"

    if recruiting_sites == 0:
        return "INACTIVE", "No sites actively recruiting"

    if velocity and velocity > 10:
        urgency = "🔥 HIGH"
        wait_estimate = "1-2 weeks (fast enrollment)"
    elif velocity and velocity > 5:
        urgency = "🟡 MODERATE"
        wait_estimate = "2-4 weeks (steady enrollment)"
    elif velocity and velocity > 0:
        urgency = "🟢 LOW"
        wait_estimate = "4-8 weeks (slow enrollment)"
    else:
        # No velocity data, use site ratio as proxy
        site_ratio = recruiting_sites / total_sites if total_sites > 0 else 0

        if site_ratio > 0.7:
            urgency = "🟡 MODERATE"
            wait_estimate = "2-4 weeks (many sites recruiting)"
        elif site_ratio > 0.3:
            urgency = "🟢 LOW"
            wait_estimate = "4-8 weeks (limited sites)"
        else:
            urgency = "⚪ UNKNOWN"
            wait_estimate = "Contact site for availability"

    return urgency, wait_estimate


def format_enrollment_display(enrollment_data: Dict) -> str:
    """Format enrollment data for UI display.

    Args:
        enrollment_data: Output from parse_enrollment_data

    Returns:
        Formatted markdown string
    """
    urgency, wait_time = calculate_enrollment_urgency(enrollment_data)

    sections = []

    # Header with urgency
    sections.append(f"### 📊 Enrollment Status: {urgency}")
    sections.append(f"**Estimated Wait Time:** {wait_time}")
    sections.append("")

    # Target enrollment
    target = enrollment_data.get("target_enrollment", "Unknown")
    sections.append(f"**Target Enrollment:** {target} patients")

    # Sites
    total_sites = enrollment_data.get("total_sites", 0)
    recruiting_sites = enrollment_data.get("recruiting_sites", 0)
    sections.append(f"**Sites:** {recruiting_sites} actively recruiting / {total_sites} total")

    # Velocity if available
    velocity = enrollment_data.get("enrollment_velocity")
    if velocity:
        sections.append(f"**Enrollment Rate:** ~{velocity:.1f} patients/month")

    # Days enrolling
    days = enrollment_data.get("days_enrolling")
    if days:
        sections.append(f"**Time Enrolling:** {days} days")

    # Last update
    last_update = enrollment_data.get("last_update_date")
    if last_update:
        try:
            update_dt = datetime.strptime(last_update, "%Y-%m-%d")
            days_since = (datetime.now() - update_dt).days
            sections.append(f"**Last Updated:** {last_update} ({days_since} days ago)")

            if days_since > 180:
                sections.append("⚠️ **WARNING:** Data may be stale (>6 months old)")
        except:
            sections.append(f"**Last Updated:** {last_update}")

    return "\n".join(sections)


def get_actively_recruiting_sites(enrollment_data: Dict) -> list:
    """Filter for sites currently recruiting.

    Args:
        enrollment_data: Output from parse_enrollment_data

    Returns:
        List of sites with Recruiting status
    """
    all_sites = enrollment_data.get("site_details", [])
    return [site for site in all_sites if site.get("status") == "Recruiting"]
