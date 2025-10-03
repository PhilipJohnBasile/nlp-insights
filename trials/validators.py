#!/usr/bin/env python3
"""Input validation utilities for clinical trials app."""

import re
from typing import Optional, Any
import pandas as pd


def validate_age(age: Any) -> tuple[bool, str]:
    """Validate patient age input."""
    try:
        age_int = int(age)
        if age_int < 0 or age_int > 120:
            return False, "Age must be between 0 and 120"
        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid age format"


def validate_state(state: str) -> tuple[bool, str]:
    """Validate US state input."""
    if state is None:
        return False, "Please enter a valid US state (e.g., CA or California)"
    if not state:
        return True, ""  # Empty string is optional

    valid_states = {
        "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
        "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
        "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
        "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
        "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY", "DC"
    }

    state_upper = state.upper().strip()
    if len(state_upper) == 2 and state_upper in valid_states:
        return True, ""

    # Check full state names
    state_names = {
        "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
        "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT",
        "DELAWARE": "DE", "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI",
        "IDAHO": "ID", "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA",
        "KANSAS": "KS", "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME",
        "MARYLAND": "MD", "MASSACHUSETTS": "MA", "MICHIGAN": "MI",
        "MINNESOTA": "MN", "MISSISSIPPI": "MS", "MISSOURI": "MO",
        "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
        "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM",
        "NEW YORK": "NY", "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND",
        "OHIO": "OH", "OKLAHOMA": "OK", "OREGON": "OR", "PENNSYLVANIA": "PA",
        "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC", "SOUTH DAKOTA": "SD",
        "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT", "VERMONT": "VT",
        "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
        "WISCONSIN": "WI", "WYOMING": "WY"
    }

    if state_upper in state_names:
        return True, ""

    return False, "Please enter a valid US state (e.g., CA or California)"


def sanitize_text_input(text: str, max_length: int = 500) -> str:
    """Sanitize user text input to prevent XSS and SQL injection."""
    if not text:
        return ""

    # Remove any HTML tags
    text = re.sub(r'<[^>]+>', '', text)

    # Remove any SQL keywords
    sql_keywords = ["DROP", "DELETE", "INSERT", "UPDATE", "SELECT", "UNION"]
    for keyword in sql_keywords:
        text = re.sub(rf'\b{keyword}\b', '', text, flags=re.IGNORECASE)

    # Limit length
    text = text[:max_length]

    # Basic character whitelist
    text = re.sub(r'[^\w\s\-.,;:()\'"]', '', text)

    return text.strip()


def validate_cancer_type(cancer_type: str) -> tuple[bool, str]:
    """Validate cancer type input."""
    if not cancer_type:
        return False, "Cancer type is required"

    cancer_type_clean = sanitize_text_input(cancer_type, max_length=100)

    # Check for minimum length
    if len(cancer_type_clean) < 3:
        return False, "Cancer type must be at least 3 characters"

    # Check for common patterns
    common_cancers = [
        "lung", "breast", "prostate", "colon", "melanoma", "lymphoma",
        "leukemia", "pancreatic", "brain", "liver", "kidney", "bladder",
        "ovarian", "cervical", "thyroid", "myeloma", "sarcoma", "glioblastoma"
    ]

    # Just warn if not a common type, don't reject
    found_common = any(cancer in cancer_type_clean.lower() for cancer in common_cancers)
    if not found_common:
        return True, ""  # Still valid, just uncommon

    return True, ""


def validate_nct_id(nct_id: str) -> tuple[bool, str]:
    """Validate NCT ID format."""
    if not nct_id:
        return True, ""  # NCT ID is optional

    # Clean the input
    nct_id = nct_id.strip().upper()

    # Check format: NCT followed by 8 digits
    pattern = r'^NCT\d{8}$'
    if not re.match(pattern, nct_id):
        return False, "NCT ID must be in format NCT12345678 (NCT followed by 8 digits)"

    return True, ""


def validate_ecog(ecog: str) -> tuple[bool, str]:
    """Validate ECOG performance status."""
    if not ecog or ecog == "":
        return True, ""  # ECOG is optional

    try:
        ecog_int = int(ecog)
        if ecog_int < 0 or ecog_int > 4:
            return False, "ECOG must be between 0 and 4"
        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid ECOG format"


def validate_prior_therapies(num_therapies: Any) -> tuple[bool, str]:
    """Validate number of prior therapies."""
    try:
        num = int(num_therapies)
        if num < 0 or num > 20:
            return False, "Number of prior therapies must be between 0 and 20"
        return True, ""
    except (ValueError, TypeError):
        return False, "Invalid number format"


def validate_pagination(page_num: int, total_pages: int) -> int:
    """Validate and fix pagination values."""
    if page_num < 0:
        return 0
    if page_num >= total_pages and total_pages > 0:
        return total_pages - 1
    return page_num