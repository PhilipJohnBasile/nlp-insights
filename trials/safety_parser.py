"""Parse safety and toxicity data from clinical trials."""

import re
from typing import Dict, List, Optional


def parse_adverse_events(eligibility_text: Optional[str], description: Optional[str] = None) -> Dict:
    """Extract common adverse events and dose-limiting toxicities from trial text.

    Args:
        eligibility_text: Eligibility criteria text
        description: Trial description text

    Returns:
        Dictionary with toxicity information
    """
    result = {
        "common_aes": [],
        "dose_limiting_toxicities": [],
        "grade_3_4_events": [],
        "safety_monitoring": []
    }

    if not eligibility_text and not description:
        return result

    # Combine texts
    full_text = ""
    if eligibility_text:
        full_text += eligibility_text.lower() + " "
    if description:
        full_text += description.lower()

    # Common adverse event patterns
    ae_patterns = [
        r'adverse\s+events?[:\s]+([^.]+)',
        r'toxicit(?:y|ies)[:\s]+([^.]+)',
        r'side\s+effects?[:\s]+([^.]+)',
        r'common\s+(?:aes?|adverse\s+events?)[:\s]+([^.]+)'
    ]

    for pattern in ae_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            # Extract individual AEs from the match
            events = re.split(r'[,;]', match)
            for event in events[:5]:  # Limit to first 5
                clean_event = event.strip()
                if len(clean_event) > 5 and len(clean_event) < 100:
                    result["common_aes"].append(clean_event)

    # Dose-limiting toxicity patterns
    dlt_patterns = [
        r'dose[- ]limiting\s+toxicit(?:y|ies)[:\s]+([^.]+)',
        r'dlt[:\s]+([^.]+)',
        r'maximum\s+tolerated\s+dose.*?toxicit(?:y|ies)[:\s]+([^.]+)'
    ]

    for pattern in dlt_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            events = re.split(r'[,;]', match)
            for event in events[:3]:
                clean_event = event.strip()
                if len(clean_event) > 5 and len(clean_event) < 100:
                    result["dose_limiting_toxicities"].append(clean_event)

    # Grade 3-4 events
    grade_patterns = [
        r'grade\s+[34][+]?\s+(?:aes?|events?|toxicit(?:y|ies))[:\s]+([^.]+)',
        r'grade\s+≥\s*3\s+(?:aes?|events?)[:\s]+([^.]+)',
        r'grade\s+3-4\s+(?:adverse\s+events?|aes?|toxicit(?:y|ies))[:\s]+([^.]+)',
        r'grade\s+3-4\s+(?:[\w-]+\s+)(?:adverse\s+events?|aes?)\s+(?:occurred)[:\s]*([^.]+)',
        r'grade\s+3\s+or\s+4\s+(?:aes?|adverse\s+events?)[:\s]*([^.]+)',
        r'serious\s+adverse\s+events?[:\s]+([^.]+)',
        r'severe\s+(?:aes?|adverse\s+events?)[:\s]+([^.]+)'
    ]

    for pattern in grade_patterns:
        matches = re.findall(pattern, full_text)
        for match in matches:
            events = re.split(r'[,;]', match)
            for event in events[:5]:
                clean_event = event.strip()
                if len(clean_event) > 5 and len(clean_event) < 100:
                    result["grade_3_4_events"].append(clean_event)

    # Safety monitoring requirements
    monitoring_patterns = [
        r'(?:ekg|ecg|electrocardiogram)',
        r'cardiac\s+monitoring',
        r'liver\s+function\s+tests?',
        r'renal\s+function',
        r'blood\s+counts?',
        r'laboratory\s+monitoring'
    ]

    for pattern in monitoring_patterns:
        if re.search(pattern, full_text):
            result["safety_monitoring"].append(pattern.replace(r'\s+', ' ').replace('?', ''))

    # Deduplicate
    result["common_aes"] = list(set(result["common_aes"]))[:10]
    result["dose_limiting_toxicities"] = list(set(result["dose_limiting_toxicities"]))[:5]
    result["grade_3_4_events"] = list(set(result["grade_3_4_events"]))[:10]
    result["safety_monitoring"] = list(set(result["safety_monitoring"]))

    return result


def format_safety_display(safety_data: Dict) -> str:
    """Format safety data for display in UI.

    Args:
        safety_data: Dictionary from parse_adverse_events

    Returns:
        Formatted HTML string for display
    """
    sections = []

    if safety_data.get("dose_limiting_toxicities"):
        dlts = ", ".join(safety_data["dose_limiting_toxicities"])
        sections.append(f"**⚠️ Dose-Limiting Toxicities:** {dlts}")

    if safety_data.get("grade_3_4_events"):
        grade34 = ", ".join(safety_data["grade_3_4_events"])
        sections.append(f"**🔴 Grade 3-4 Events:** {grade34}")

    if safety_data.get("common_aes"):
        common = ", ".join(safety_data["common_aes"])
        sections.append(f"**💊 Common AEs:** {common}")

    if safety_data.get("safety_monitoring"):
        monitoring = ", ".join(safety_data["safety_monitoring"])
        sections.append(f"**🔬 Monitoring Required:** {monitoring}")

    if not sections:
        return "ℹ️ Safety data not available in trial documentation"

    return "\n\n".join(sections)


def extract_toxicity_from_results(trial_data: Dict) -> Optional[Dict]:
    """Extract toxicity data from trial results if available.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Dictionary with results-based toxicity data or None
    """
    # This would parse actual results data if available
    # For now, returns None as most recruiting trials don't have results yet

    results_section = trial_data.get("resultsSection", {})
    if not results_section:
        return None

    adverse_events = results_section.get("adverseEventsModule", {})
    if not adverse_events:
        return None

    # Parse frequency table if available
    frequency_threshold = adverse_events.get("frequencyThreshold")
    events_list = adverse_events.get("eventGroups", [])

    parsed_results = {
        "frequency_threshold": frequency_threshold,
        "reported_events": []
    }

    for event_group in events_list:
        title = event_group.get("title", "")
        deaths = event_group.get("deathsNumAffected", 0)
        serious = event_group.get("seriousNumAffected", 0)

        if deaths or serious:
            parsed_results["reported_events"].append({
                "group": title,
                "deaths": deaths,
                "serious": serious
            })

    return parsed_results if parsed_results["reported_events"] else None
