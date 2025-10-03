"""Advanced clinical parsing for oncologist-friendly features."""

import re
from typing import Optional


def split_inclusion_exclusion(eligibility_text: Optional[str]) -> tuple[str, str]:
    """Split eligibility text into inclusion and exclusion sections.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Tuple of (inclusion_text, exclusion_text)
    """
    if not eligibility_text:
        return "", ""

    text = eligibility_text

    # Look for "Inclusion Criteria:" and "Exclusion Criteria:" sections
    inclusion_match = re.search(
        r"inclusion\s+criteria:?\s*(.*?)(?=exclusion\s+criteria:|$)",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    exclusion_match = re.search(
        r"exclusion\s+criteria:?\s*(.*?)$",
        text,
        re.IGNORECASE | re.DOTALL,
    )

    inclusion_text = inclusion_match.group(1).strip() if inclusion_match else ""
    exclusion_text = exclusion_match.group(1).strip() if exclusion_match else ""

    # If no clear sections, try to infer
    if not inclusion_text and not exclusion_text:
        # Everything is probably inclusion if no exclusion section
        inclusion_text = text
        exclusion_text = ""

    return inclusion_text, exclusion_text


def parse_treatment_line(eligibility_text: Optional[str]) -> dict:
    """Determine treatment line requirements.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Dictionary with treatment line info
    """
    if not eligibility_text:
        return {
            "treatment_line": "Unknown",
            "prior_therapy_required": False,
            "treatment_naive_allowed": True,
        }

    text = eligibility_text.lower()

    # Check for treatment naive / first line
    if any(phrase in text for phrase in [
        "treatment naive",
        "treatment-naive",
        "no prior systemic",
        "first-line",
        "first line",
        "previously untreated",
    ]):
        return {
            "treatment_line": "1st line",
            "prior_therapy_required": False,
            "treatment_naive_allowed": True,
        }

    # Check for second line
    if any(phrase in text for phrase in [
        "second-line",
        "second line",
        "2nd line",
        "one prior",
        "1 prior",
        "failed first",
    ]):
        return {
            "treatment_line": "2nd line",
            "prior_therapy_required": True,
            "treatment_naive_allowed": False,
        }

    # Check for third+ line / heavily pretreated
    if any(phrase in text for phrase in [
        "third-line",
        "third line",
        "3rd line",
        "two or more prior",
        ">=2 prior",
        "heavily pretreated",
        "relapsed or refractory",
        "salvage",
    ]):
        return {
            "treatment_line": "3rd+ line",
            "prior_therapy_required": True,
            "treatment_naive_allowed": False,
        }

    # Check for "previously treated" without specific line
    if any(phrase in text for phrase in [
        "previously treated",
        "prior therapy",
        "prior treatment",
        "received prior",
    ]):
        return {
            "treatment_line": "Previously treated",
            "prior_therapy_required": True,
            "treatment_naive_allowed": False,
        }

    # Default: unclear
    return {
        "treatment_line": "Any line",
        "prior_therapy_required": False,
        "treatment_naive_allowed": True,
    }


def check_common_exclusions(eligibility_text: Optional[str]) -> dict:
    """Check for common exclusion criteria.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Dictionary with boolean flags for common exclusions
    """
    if not eligibility_text:
        return {}

    text = eligibility_text.lower()

    # Get exclusion section
    _, exclusion_text = split_inclusion_exclusion(eligibility_text)
    exclusion_lower = exclusion_text.lower() if exclusion_text else text

    results = {}

    # Brain metastases - check "allowed" first to avoid false positives
    if any(phrase in text for phrase in [
        "brain metastases allowed",
        "treated brain mets allowed",
        "stable brain metastases allowed",
        "brain mets treated",
    ]):
        results["brain_mets_excluded"] = False
    elif any(phrase in exclusion_lower for phrase in [
        "brain metastases",
        "brain mets",
        "cns metastases",
        "central nervous system metastases",
        "untreated brain",
    ]):
        results["brain_mets_excluded"] = True
    else:
        results["brain_mets_excluded"] = None  # Unclear

    # Prior immunotherapy - more comprehensive patterns
    if any(phrase in exclusion_lower for phrase in [
        "prior pd-1",
        "prior pd-l1",
        "prior immune checkpoint",
        "prior immunotherapy",
        "previous anti-pd",
        "prior checkpoint inhibitor",
        "previous immunotherapy",
        "prior immune",
        "prior treatment with pd-1",
        "prior treatment with pd-l1",
        "previous pd-1",
        "previous pd-l1",
    ]):
        results["prior_immunotherapy_excluded"] = True
    # Check if explicitly allowed
    elif any(phrase in text for phrase in [
        "prior immunotherapy allowed",
        "previous immunotherapy permitted",
    ]):
        results["prior_immunotherapy_excluded"] = False
    else:
        results["prior_immunotherapy_excluded"] = False  # Default: not excluded

    # Autoimmune disease
    if any(phrase in exclusion_lower for phrase in [
        "autoimmune disease",
        "autoimmune disorder",
        "active autoimmune",
    ]):
        results["autoimmune_excluded"] = True
    else:
        results["autoimmune_excluded"] = False

    # HIV
    if any(phrase in exclusion_lower for phrase in [
        "hiv",
        "human immunodeficiency virus",
    ]):
        results["hiv_excluded"] = True
    else:
        results["hiv_excluded"] = False

    # Hepatitis
    if any(phrase in exclusion_lower for phrase in [
        "hepatitis",
        "hbv",
        "hcv",
    ]):
        results["hepatitis_excluded"] = True
    else:
        results["hepatitis_excluded"] = False

    # Organ dysfunction
    if any(phrase in exclusion_lower for phrase in [
        "organ dysfunction",
        "hepatic impairment",
        "renal impairment",
        "cardiac dysfunction",
    ]):
        results["organ_dysfunction_excluded"] = True
    else:
        results["organ_dysfunction_excluded"] = False

    return results


def parse_biomarker_requirements(eligibility_text: Optional[str]) -> dict:
    """Parse specific biomarker requirements and cutoffs.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Dictionary with biomarker details
    """
    if not eligibility_text:
        return {}

    text = eligibility_text.lower()
    biomarkers = {}

    # PD-L1 expression levels
    pdl1_match = re.search(r'pd-?l1.*?[≥>=]+\s*(\d+)%', text)
    if pdl1_match:
        biomarkers['pdl1_cutoff'] = f"≥{pdl1_match.group(1)}%"
    elif 'pd-l1' in text or 'pdl1' in text:
        biomarkers['pdl1_required'] = True

    # HER2 status
    if any(phrase in text for phrase in ['her2+', 'her2 positive', 'her2-positive']):
        biomarkers['her2_status'] = 'Positive'
    elif any(phrase in text for phrase in ['her2-', 'her2 negative', 'her2-negative']):
        biomarkers['her2_status'] = 'Negative'

    # EGFR mutations
    if any(phrase in text for phrase in ['egfr mutation', 'egfr-mutant', 'egfr+', 'exon 19', 'l858r', 't790m']):
        biomarkers['egfr_mutation'] = True
        if 'exon 19' in text:
            biomarkers['egfr_specific'] = 'Exon 19 deletion'
        elif 'l858r' in text:
            biomarkers['egfr_specific'] = 'L858R'
        elif 't790m' in text:
            biomarkers['egfr_specific'] = 'T790M'

    # ALK rearrangement
    if any(phrase in text for phrase in ['alk+', 'alk positive', 'alk rearrangement', 'alk fusion']):
        biomarkers['alk_rearrangement'] = True

    # ROS1 rearrangement
    if any(phrase in text for phrase in ['ros1+', 'ros1 positive', 'ros1 rearrangement', 'ros1 fusion']):
        biomarkers['ros1_rearrangement'] = True

    # BRCA mutations
    if any(phrase in text for phrase in ['brca1', 'brca2', 'brca mutation', 'brca+']):
        biomarkers['brca_mutation'] = True

    # MSI/MMR status
    if any(phrase in text for phrase in ['msi-h', 'microsatellite instability-high', 'msi high']):
        biomarkers['msi_status'] = 'MSI-High'
    elif any(phrase in text for phrase in ['dmmr', 'mmr deficient', 'mismatch repair deficient']):
        biomarkers['mmr_status'] = 'Deficient'

    # TMB (Tumor Mutational Burden)
    tmb_match = re.search(r'tmb.*?[≥>=]+\s*(\d+)', text)
    if tmb_match:
        biomarkers['tmb_cutoff'] = f"≥{tmb_match.group(1)}"

    # IDH mutation (gliomas)
    if any(phrase in text for phrase in ['idh1', 'idh2', 'idh mutation', 'idh-mutant']):
        biomarkers['idh_mutation'] = True

    # MGMT methylation (gliomas)
    if any(phrase in text for phrase in ['mgmt methylated', 'mgmt methylation']):
        biomarkers['mgmt_methylated'] = True

    return biomarkers


def parse_prior_lines_limit(eligibility_text: Optional[str]) -> Optional[int]:
    """Parse maximum number of prior therapy lines allowed.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Maximum number of prior lines, or None if no limit specified
    """
    if not eligibility_text:
        return None

    text = eligibility_text.lower()
    _, exclusion_text = split_inclusion_exclusion(eligibility_text)
    exclusion_lower = exclusion_text.lower() if exclusion_text else ""

    # Look for "no more than X prior" patterns
    patterns = [
        r'no more than (\d+) prior',
        r'maximum (\d+) prior',
        r'[≤<=]\s*(\d+) prior',
        r'up to (\d+) prior',
        r'(\d+)-(\d+)\s+prior',  # e.g., "1-2 prior therapies"
        r'after\s+\d+-(\d+)\s+prior',  # e.g., "after 1-2 prior"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # For range patterns (group 2), use the max value
            if len(match.groups()) > 1 and match.group(2):
                return int(match.group(2))
            return int(match.group(1))

    # Check exclusion section for ">X prior lines"
    exclude_patterns = [
        r'>(\d+) prior',
        r'more than (\d+) prior',
        r'greater than (\d+) prior',
    ]

    for pattern in exclude_patterns:
        match = re.search(pattern, exclusion_lower)
        if match:
            return int(match.group(1))

    return None


def parse_washout_period(eligibility_text: Optional[str]) -> Optional[str]:
    """Parse washout period requirements.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Washout period string (e.g., "2 weeks", "4 weeks") or None
    """
    if not eligibility_text:
        return None

    text = eligibility_text.lower()

    # Look for washout patterns
    patterns = [
        r'(\d+)\s*week[s]?\s+(?:since|from|after).*?(?:prior|last|previous)\s+(?:therapy|treatment|chemotherapy)',
        r'washout.*?(\d+)\s*week[s]?',
        r'(\d+)\s*week[s]?\s+washout',
        r'completed.*?therapy.*?(\d+)\s*week[s]?\s+(?:prior|before)',
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            weeks = match.group(1)
            return f"{weeks} weeks"

    # Look for day-based washout
    patterns_days = [
        r'(\d+)\s*day[s]?\s+(?:since|from|after).*?(?:prior|last|previous)',
        r'washout.*?(\d+)\s*day[s]?',
        r'(\d+)\s*day[s]?\s+washout',
        r'washout\s+(?:period\s+)?(?:of\s+)?(\d+)\s*day[s]?',
    ]

    for pattern in patterns_days:
        match = re.search(pattern, text)
        if match:
            days = match.group(1)
            return f"{days} days"

    return None


def parse_required_tests(eligibility_text: Optional[str]) -> list[str]:
    """Parse required labs and diagnostic tests.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        List of required tests
    """
    if not eligibility_text:
        return []

    text = eligibility_text.lower()
    required_tests = []

    # Common required tests
    if any(phrase in text for phrase in ['tissue biopsy', 'fresh biopsy', 'tumor biopsy required']):
        required_tests.append('Fresh tumor biopsy')
    elif any(phrase in text for phrase in ['archival tissue', 'archived tissue', 'ffpe']):
        required_tests.append('Archival tissue')

    if any(phrase in text for phrase in ['pet scan', 'pet-ct', 'fdg-pet']):
        required_tests.append('PET scan')

    if any(phrase in text for phrase in ['mri brain', 'brain mri', 'mri of the brain']):
        required_tests.append('Brain MRI')

    if any(phrase in text for phrase in ['ct scan', 'computed tomography']):
        required_tests.append('CT scan')

    if any(phrase in text for phrase in ['echocardiogram', 'echo', 'muga scan', 'lvef']):
        required_tests.append('Cardiac function test (Echo/MUGA)')

    if any(phrase in text for phrase in ['bone marrow biopsy', 'bone marrow aspir']):
        required_tests.append('Bone marrow biopsy')

    if any(phrase in text for phrase in ['liquid biopsy', 'ctdna', 'circulating tumor dna']):
        required_tests.append('Liquid biopsy (ctDNA)')

    if any(phrase in text for phrase in ['molecular testing', 'genomic profiling', 'next-generation sequencing', 'ngs']):
        required_tests.append('Genomic profiling/NGS')

    return required_tests


def parse_dose_escalation_info(trial_data: dict) -> dict:
    """Parse dose escalation vs expansion cohort information.

    Args:
        trial_data: Full trial JSON data

    Returns:
        Dictionary with dose escalation info
    """
    result = {
        "is_dose_escalation": False,
        "is_expansion": False,
        "cohort_type": None,
        "dose_level": None
    }

    # Check in title and description
    text_fields = [
        trial_data.get("protocolSection", {}).get("identificationModule", {}).get("briefTitle", ""),
        trial_data.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary", ""),
        trial_data.get("protocolSection", {}).get("descriptionModule", {}).get("detailedDescription", "")
    ]

    combined_text = " ".join([str(t) for t in text_fields if t]).lower()

    # Dose escalation patterns
    if any(phrase in combined_text for phrase in [
        "dose escalation", "dose-escalation", "3+3 design", "mtd", "maximum tolerated dose",
        "dose finding", "dose-finding", "phase 1a", "phase ia"
    ]):
        result["is_dose_escalation"] = True
        result["cohort_type"] = "Dose Escalation"

        # Try to find dose level
        import re
        dose_match = re.search(r"dose level (\d+)", combined_text)
        if dose_match:
            result["dose_level"] = f"Level {dose_match.group(1)}"

    # Expansion cohort patterns
    if any(phrase in combined_text for phrase in [
        "expansion cohort", "expansion phase", "dose expansion", "phase 1b", "phase ib",
        "recommended phase 2 dose", "rp2d", "expansion arm"
    ]):
        result["is_expansion"] = True
        result["cohort_type"] = "Expansion Cohort" if not result["is_dose_escalation"] else "Dose Escalation + Expansion"

    return result


def parse_randomization_info(trial_data: dict) -> dict:
    """Parse randomization ratio and design.

    Args:
        trial_data: Full trial JSON data

    Returns:
        Dictionary with randomization info
    """
    result = {
        "is_randomized": False,
        "randomization_ratio": None,
        "allocation": None,
        "masking": None
    }

    design = trial_data.get("protocolSection", {}).get("designModule", {})

    # Check if randomized
    allocation = design.get("designInfo", {}).get("allocation")
    if allocation and allocation.upper() == "RANDOMIZED":
        result["is_randomized"] = True
        result["allocation"] = allocation

        # Check masking/blinding
        masking_info = design.get("designInfo", {}).get("maskingInfo", {})
        result["masking"] = masking_info.get("masking", "None")

        # Try to find ratio in description
        desc = trial_data.get("protocolSection", {}).get("descriptionModule", {}).get("detailedDescription", "")
        if desc:
            import re
            # Look for patterns like "2:1", "1:1:1", etc.
            ratio_match = re.search(r"(\d+:\d+(?::\d+)*)\s*(?:ratio|randomization)", desc.lower())
            if ratio_match:
                result["randomization_ratio"] = ratio_match.group(1)
            # Also check for percentage patterns
            elif "1:1" in desc:
                result["randomization_ratio"] = "1:1"
            elif "2:1" in desc:
                result["randomization_ratio"] = "2:1"
            elif "3:1" in desc:
                result["randomization_ratio"] = "3:1"

    return result


def parse_crossover_info(eligibility_text: Optional[str], trial_data: dict = None) -> dict:
    """Parse crossover allowance information.

    Args:
        eligibility_text: Eligibility criteria text
        trial_data: Full trial JSON data

    Returns:
        Dictionary with crossover info
    """
    result = {
        "crossover_allowed": None,
        "crossover_details": None
    }

    # Combine relevant text fields
    text_to_check = (eligibility_text or "").lower()

    if trial_data:
        desc = trial_data.get("protocolSection", {}).get("descriptionModule", {})
        text_to_check += " " + str(desc.get("briefSummary", "")).lower()
        text_to_check += " " + str(desc.get("detailedDescription", "")).lower()

    # Check for crossover patterns
    if any(phrase in text_to_check for phrase in [
        "crossover allowed", "cross-over allowed", "may crossover", "may cross over",
        "crossover to", "cross over to", "switch to active", "unblinding"
    ]):
        result["crossover_allowed"] = True
        result["crossover_details"] = "Crossover to active treatment allowed"
    elif any(phrase in text_to_check for phrase in [
        "no crossover", "crossover not", "not allowed to cross", "no cross-over"
    ]):
        result["crossover_allowed"] = False
        result["crossover_details"] = "No crossover allowed"

    return result


def parse_ecog_requirement(eligibility_text: Optional[str]) -> dict:
    """Parse ECOG performance status requirements.

    Args:
        eligibility_text: Full eligibility criteria text

    Returns:
        Dictionary with ECOG requirements (max_ecog: int or None)
    """
    if not eligibility_text:
        return {"max_ecog": None}

    text = eligibility_text.lower()

    # Look for ECOG patterns
    patterns = [
        r'ecog\s+(?:performance\s+)?status\s+(?:of\s+)?[≤<=]\s*(\d)',
        r'ecog\s+(?:ps\s+)?[≤<=]\s*(\d)',
        r'ecog\s+0-(\d)',
        r'ecog\s+(?:ps\s+)?0-(\d)',
        r'ecog\s+0\s+or\s+(\d)',
        r'ecog\s+(?:performance\s+)?status\s+(?:of\s+)?0\s+or\s+(\d)',
        r'ecog\s+0,\s*1(?:,\s*(\d))?',
        r'ecog\s+(?:performance\s+)?status\s+0-(\d)',
    ]

    max_ecog = None
    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            # Find the last group that has a value
            for group in match.groups():
                if group and group.isdigit():
                    try:
                        max_ecog = int(group)
                        break
                    except (ValueError, TypeError):
                        continue
            if max_ecog is not None:
                break

    # Also check for explicit ECOG 0-1 only
    if max_ecog is None:
        if 'ecog 0-1' in text or 'ecog 0 or 1' in text or 'ecog ps 0-1' in text:
            max_ecog = 1
        elif 'ecog 0-2' in text or 'ecog ps 0-2' in text:
            max_ecog = 2

    return {"max_ecog": max_ecog}


def extract_contact_from_location(location_data: dict) -> dict:
    """Extract contact information from location data.

    Args:
        location_data: Raw location data from API

    Returns:
        Dictionary with contact information
    """
    contacts = location_data.get("contacts", [])

    result = {
        "contact_name": None,
        "contact_phone": None,
        "contact_email": None,
        "contact_role": None,
    }

    if contacts:
        # Get first contact (usually study coordinator)
        contact = contacts[0]
        result["contact_name"] = contact.get("name")
        result["contact_phone"] = contact.get("phone")
        result["contact_email"] = contact.get("email")
        result["contact_role"] = contact.get("role")

    return result
