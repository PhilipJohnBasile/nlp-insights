"""Protocol document access and management."""

import re
from typing import Dict, List, Optional


def get_protocol_links(trial_data: Dict) -> Dict[str, str]:
    """Extract links to protocol documents from trial data.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Dictionary with document links
    """
    nct_id = trial_data.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")

    links = {}

    # Standard ClinicalTrials.gov links
    if nct_id:
        links["trial_page"] = f"https://clinicaltrials.gov/study/{nct_id}"
        links["full_text"] = f"https://clinicaltrials.gov/study/{nct_id}?tab=table"
        links["history"] = f"https://clinicaltrials.gov/study/{nct_id}?tab=history"

    # Check for document section
    doc_module = trial_data.get("protocolSection", {}).get("referencesModule", {})

    # Available IPD (Individual Participant Data) documents
    ipd_module = trial_data.get("protocolSection", {}).get("ipdSharingStatementModule", {})
    ipd_sharing = ipd_module.get("ipdSharing", "NO")

    if ipd_sharing in ["YES", "YES_WITH_RESTRICTION"]:
        ipd_plan = ipd_module.get("description", "")
        ipd_url = ipd_module.get("url")

        if ipd_url:
            links["ipd_sharing"] = ipd_url

        # Common IPD document types
        ipd_info_types = ipd_module.get("infoTypes", [])
        if "STUDY_PROTOCOL" in ipd_info_types:
            links["protocol_available"] = "Contact sponsor for study protocol"
        if "SAP" in ipd_info_types:
            links["sap_available"] = "Statistical Analysis Plan available"
        if "ICF" in ipd_info_types:
            links["icf_available"] = "Informed Consent Form available"

    # References and publications
    references = doc_module.get("references", [])
    if references:
        links["publications"] = [ref.get("pmid") or ref.get("citation") for ref in references[:5]]

    return links


def format_protocol_documents(links: Dict[str, str]) -> str:
    """Format protocol document links for display.

    Args:
        links: Dictionary from get_protocol_links

    Returns:
        Formatted markdown string
    """
    sections = []

    sections.append("### 📄 Protocol Documents & Resources")
    sections.append("")

    # Main trial page
    if "trial_page" in links:
        sections.append(f"**📋 [View Full Trial Details]({links['trial_page']})**")

    if "full_text" in links:
        sections.append(f"**📊 [View Tabular Data]({links['full_text']})**")

    if "history" in links:
        sections.append(f"**📅 [View Update History]({links['history']})**")

    sections.append("")

    # IPD Sharing
    if "ipd_sharing" in links:
        sections.append("**📑 Data Sharing:**")
        sections.append(f"- [IPD Sharing Plan]({links['ipd_sharing']})")

    if "protocol_available" in links:
        sections.append(f"- ✅ {links['protocol_available']}")
    if "sap_available" in links:
        sections.append(f"- ✅ {links['sap_available']}")
    if "icf_available" in links:
        sections.append(f"- ✅ {links['icf_available']}")

    # Publications
    if "publications" in links and links["publications"]:
        sections.append("")
        sections.append("**📚 Related Publications:**")
        for pub in links["publications"]:
            if pub and str(pub).startswith("PMID"):
                pmid = pub.replace("PMID:", "").strip()
                sections.append(f"- [PubMed {pmid}](https://pubmed.ncbi.nlm.nih.gov/{pmid}/)")
            elif pub:
                sections.append(f"- {pub}")

    sections.append("")
    sections.append("💡 **To request full protocol:** Contact the trial coordinator at the site")

    return "\n".join(sections)


def generate_eligibility_checklist(trial_data: Dict) -> str:
    """Generate a printable eligibility checklist.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Formatted markdown checklist
    """
    eligibility_module = trial_data.get("protocolSection", {}).get("eligibilityModule", {})
    criteria_text = eligibility_module.get("eligibilityCriteria", "")

    if not criteria_text:
        return "Eligibility criteria not available"

    # Parse inclusion and exclusion
    sections = []
    sections.append("# Eligibility Checklist")
    sections.append("")

    # Try to split into inclusion and exclusion
    text_lower = criteria_text.lower()

    inclusion_match = re.search(r'inclusion criteria:?\s*(.*?)(?=exclusion criteria|$)',
                                 criteria_text, re.IGNORECASE | re.DOTALL)
    exclusion_match = re.search(r'exclusion criteria:?\s*(.*?)$',
                                 criteria_text, re.IGNORECASE | re.DOTALL)

    if inclusion_match:
        sections.append("## ✅ Inclusion Criteria (Patient MUST meet these)")
        sections.append("")
        inclusion_text = inclusion_match.group(1).strip()

        # Extract bullet points
        bullets = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)', inclusion_text, re.DOTALL)
        if not bullets:
            # Try numbered list
            bullets = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', inclusion_text, re.DOTALL)

        for bullet in bullets[:15]:  # Limit to 15 items
            clean = bullet.strip().replace('\n', ' ')
            sections.append(f"- [ ] {clean}")
        sections.append("")

    if exclusion_match:
        sections.append("## ❌ Exclusion Criteria (Patient MUST NOT have these)")
        sections.append("")
        exclusion_text = exclusion_match.group(1).strip()

        # Extract bullet points
        bullets = re.findall(r'[-•]\s*(.+?)(?=\n[-•]|\n\n|$)', exclusion_text, re.DOTALL)
        if not bullets:
            bullets = re.findall(r'\d+\.\s*(.+?)(?=\n\d+\.|\n\n|$)', exclusion_text, re.DOTALL)

        for bullet in bullets[:15]:
            clean = bullet.strip().replace('\n', ' ')
            sections.append(f"- [ ] {clean}")

    # Add age and sex criteria
    sections.append("")
    sections.append("## 📋 Demographics")

    min_age = eligibility_module.get("minimumAge", "N/A")
    max_age = eligibility_module.get("maximumAge", "N/A")
    sex = eligibility_module.get("sex", "ALL")

    sections.append(f"- [ ] Age: {min_age} to {max_age}")
    sections.append(f"- [ ] Sex: {sex}")

    return "\n".join(sections)


def get_consent_form_info(trial_data: Dict) -> str:
    """Get information about informed consent forms.

    Args:
        trial_data: Full trial data dictionary

    Returns:
        Information about consent process
    """
    return """### 📝 Informed Consent Information

**What to expect:**
1. Site coordinator will review full consent form with you
2. Ask questions about any parts you don't understand
3. You'll have time to review with family before signing
4. You can withdraw consent at any time

**Key questions to ask:**
- What are the potential risks and benefits?
- What are my alternatives if I don't participate?
- Will my medical information be kept private?
- Can I stop participating at any time?
- What costs will I be responsible for?
- What happens if I'm injured during the study?

**Before your appointment:**
- Bring a list of current medications
- Bring recent lab reports if available
- Consider bringing a family member for support
- Write down any questions you have

💡 **Tip:** Request a copy of the informed consent form in advance to review at home.
"""
