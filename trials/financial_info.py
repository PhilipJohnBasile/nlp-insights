"""Parse and display financial and insurance information for clinical trials."""

import re
from typing import Dict, Optional


def parse_financial_info(trial_data: Dict) -> Dict:
    """Extract financial information from trial data.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Dictionary with financial information
    """
    sponsor_module = trial_data.get("protocolSection", {}).get("sponsorCollaboratorsModule", {})
    description_module = trial_data.get("protocolSection", {}).get("descriptionModule", {})

    sponsor_info = sponsor_module.get("leadSponsor", {})
    sponsor_name = sponsor_info.get("name", "Unknown")
    sponsor_class = sponsor_info.get("class", "Unknown")

    # Get description text for parsing
    brief_summary = description_module.get("briefSummary", "")
    detailed_desc = description_module.get("detailedDescription", "")
    full_text = (brief_summary + " " + detailed_desc).lower()

    # Parse coverage information
    covers_soc = _check_standard_of_care_coverage(full_text)
    travel_reimbursement = _check_travel_reimbursement(full_text)

    # Determine likely coverage based on sponsor
    likely_coverage = _estimate_coverage_by_sponsor(sponsor_class, sponsor_name)

    return {
        "sponsor_name": sponsor_name,
        "sponsor_class": sponsor_class,
        "covers_standard_of_care": covers_soc,
        "travel_reimbursement": travel_reimbursement,
        "likely_coverage": likely_coverage
    }


def _check_standard_of_care_coverage(text: str) -> Optional[bool]:
    """Check if trial mentions standard of care coverage.

    Args:
        text: Trial description text (lowercased)

    Returns:
        True/False/None if mentioned/not mentioned/unclear
    """
    positive_patterns = [
        r'sponsor.*covers?.*standard of care',
        r'standard of care.*provided',
        r'no cost.*standard of care',
        r'sponsor.*pays?.*standard of care'
    ]

    negative_patterns = [
        r'standard of care.*not covered',
        r'insurance.*standard of care',
        r'patient.*responsible.*standard of care'
    ]

    for pattern in positive_patterns:
        if re.search(pattern, text):
            return True

    for pattern in negative_patterns:
        if re.search(pattern, text):
            return False

    return None


def _check_travel_reimbursement(text: str) -> Optional[bool]:
    """Check if trial offers travel reimbursement.

    Args:
        text: Trial description text (lowercased)

    Returns:
        True/False/None if offered/not offered/unclear
    """
    positive_patterns = [
        r'travel.*reimburs',
        r'lodging.*provided',
        r'transportation.*assistance',
        r'mileage.*reimburs'
    ]

    for pattern in positive_patterns:
        if re.search(pattern, text):
            return True

    return None


def _estimate_coverage_by_sponsor(sponsor_class: str, sponsor_name: str) -> str:
    """Estimate likely coverage based on sponsor type.

    Args:
        sponsor_class: Sponsor classification (Industry, NIH, Other, etc.)
        sponsor_name: Name of sponsor

    Returns:
        Description of likely coverage
    """
    if sponsor_class == "INDUSTRY":
        return "Industry-sponsored trials typically cover study drug and study-related procedures. Standard of care may be covered."
    elif sponsor_class == "NIH":
        return "NIH-sponsored trials often provide study intervention at no cost. Standard of care typically billed to insurance."
    elif sponsor_class in ["FED", "OTHER_GOV"]:
        return "Government-sponsored trials usually provide study interventions at no cost."
    elif "NETWORK" in sponsor_class or "NCI" in sponsor_name.upper():
        return "Cancer center network trials typically cover study-related costs. Standard of care billed to insurance."
    else:
        return "Contact site for specific coverage details."


def format_financial_display(financial_info: Dict) -> str:
    """Format financial information for UI display.

    Args:
        financial_info: Output from parse_financial_info

    Returns:
        Formatted markdown string
    """
    sections = []

    sections.append("### 💰 Financial Information")
    sections.append("")

    # Sponsor
    sponsor = financial_info.get("sponsor_name", "Unknown")
    sponsor_class = financial_info.get("sponsor_class", "Unknown")
    sections.append(f"**Sponsor:** {sponsor} ({sponsor_class})")
    sections.append("")

    # Likely coverage
    likely = financial_info.get("likely_coverage", "")
    if likely:
        sections.append(f"**Likely Coverage:** {likely}")
        sections.append("")

    # Standard of care
    soc = financial_info.get("covers_standard_of_care")
    if soc is True:
        sections.append("✅ **Standard of Care:** Likely covered by sponsor")
    elif soc is False:
        sections.append("⚠️ **Standard of Care:** Billed to insurance")
    else:
        sections.append("ℹ️ **Standard of Care:** Contact site for details")

    # Travel reimbursement
    travel = financial_info.get("travel_reimbursement")
    if travel:
        sections.append("✅ **Travel:** Reimbursement may be available")
    else:
        sections.append("ℹ️ **Travel:** Contact site regarding reimbursement")

    sections.append("")
    sections.append("💡 **Important:** Coverage varies by site. Always verify financial details with the trial coordinator before enrolling.")

    return "\n".join(sections)


def get_financial_assistance_resources() -> str:
    """Return list of financial assistance resources.

    Returns:
        Formatted markdown with resources
    """
    return """
### 📋 Financial Assistance Resources

**Patient Assistance Programs:**
- [Cancer Financial Assistance Coalition](https://www.cancerfac.org/)
- [Patient Advocate Foundation](https://www.patientadvocate.org/)
- [CancerCare](https://www.cancercare.org/)

**Travel Assistance:**
- [Corporate Angel Network](https://www.corpangelnetwork.org/) - Free air travel
- [Mercy Medical Angels](https://www.mercymedicalangels.org/) - Travel assistance
- [Joe's House](https://www.joeshouse.org/) - Lodging near treatment centers

**Insurance Assistance:**
- [Healthcare.gov](https://www.healthcare.gov/) - Health insurance marketplace
- [Medicare](https://www.medicare.gov/) - Federal health insurance
- [State Medicaid Programs](https://www.medicaid.gov/state-overviews/index.html)

**Drug Assistance:**
- [NeedyMeds](https://www.needymeds.org/) - Medication assistance programs
- [RxAssist](https://www.rxassist.org/) - Prescription assistance
- [Partnership for Prescription Assistance](https://www.pparx.org/)
"""
