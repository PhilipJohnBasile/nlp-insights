"""Parse and structure eligibility criteria from clinical trials."""

import argparse
import re
from pathlib import Path
from typing import Optional

import pandas as pd

from trials.config import config
from trials.models import EligibilityCriteria


def parse_age(age_str: Optional[str]) -> Optional[float]:
    """Parse age string to numeric years.

    Args:
        age_str: Age string like "18 Years", "6 Months", "N/A"

    Returns:
        Age in years or None
    """
    if not age_str or age_str.upper() in ("N/A", "NONE"):
        return None

    age_str = age_str.strip().lower()

    # Extract number
    match = re.search(r"(\d+(?:\.\d+)?)", age_str)
    if not match:
        return None

    value = float(match.group(1))

    # Convert to years
    if "month" in age_str:
        return value / 12.0
    elif "week" in age_str:
        return value / 52.0
    elif "day" in age_str:
        return value / 365.0
    else:  # Assume years
        return value


def extract_inclusion_exclusion(
    criteria_text: Optional[str],
) -> tuple[list[str], list[str]]:
    """Extract inclusion and exclusion criteria from text.

    Args:
        criteria_text: Raw eligibility criteria text

    Returns:
        Tuple of (inclusion_terms, exclusion_terms)
    """
    if not criteria_text:
        return [], []

    inclusion_terms = []
    exclusion_terms = []

    # Split by sections
    inclusion_match = re.search(
        r"inclusion\s+criteria:?(.*?)(?=exclusion\s+criteria:|$)",
        criteria_text,
        re.IGNORECASE | re.DOTALL,
    )
    exclusion_match = re.search(
        r"exclusion\s+criteria:?(.*?)$",
        criteria_text,
        re.IGNORECASE | re.DOTALL,
    )

    # Extract inclusion criteria
    if inclusion_match:
        inclusion_text = inclusion_match.group(1)
        # Split by bullet points or numbered lists
        items = re.split(r"\n\s*[-•*\d]+[\.\)]\s*", inclusion_text)
        inclusion_terms = [
            item.strip()
            for item in items
            if item.strip() and len(item.strip()) > 10
        ]

    # Extract exclusion criteria
    if exclusion_match:
        exclusion_text = exclusion_match.group(1)
        items = re.split(r"\n\s*[-•*\d]+[\.\)]\s*", exclusion_text)
        exclusion_terms = [
            item.strip()
            for item in items
            if item.strip() and len(item.strip()) > 10
        ]

    # Limit to top terms
    return inclusion_terms[:20], exclusion_terms[:20]


def extract_disease_stages(criteria_text: Optional[str]) -> list[str]:
    """Extract disease stage mentions from criteria text.

    Args:
        criteria_text: Raw eligibility criteria text

    Returns:
        List of disease stage terms
    """
    if not criteria_text:
        return []

    stage_patterns = [
        r"stage\s+[I1V2v3i4]+[abc]?",
        r"metastatic",
        r"locally\s+advanced",
        r"early\s+stage",
        r"advanced",
        r"recurrent",
        r"refractory",
    ]

    stages = []
    criteria_lower = criteria_text.lower()

    for pattern in stage_patterns:
        matches = re.finditer(pattern, criteria_lower, re.IGNORECASE)
        for match in matches:
            stage = match.group(0).strip()
            if stage not in stages:
                stages.append(stage)

    return stages[:10]


def parse_eligibility(
    trial_id: str,
    eligibility_text: Optional[str],
    min_age: Optional[str] = None,
    max_age: Optional[str] = None,
    sex: Optional[str] = None,
) -> EligibilityCriteria:
    """Parse eligibility criteria for a trial.

    Args:
        trial_id: Trial NCT ID
        eligibility_text: Raw eligibility criteria text
        min_age: Minimum age string
        max_age: Maximum age string
        sex: Sex eligibility

    Returns:
        Parsed eligibility criteria
    """
    # Parse ages
    min_age_years = parse_age(min_age)
    max_age_years = parse_age(max_age)

    # Extract terms
    inclusion, exclusion = extract_inclusion_exclusion(eligibility_text)
    stages = extract_disease_stages(eligibility_text)

    return EligibilityCriteria(
        trial_id=trial_id,
        min_age=min_age_years,
        max_age=max_age_years,
        sex=sex,
        key_inclusion_terms=inclusion,
        key_exclusion_terms=exclusion,
        disease_stage_terms=stages,
    )


def parse_all_eligibility(
    trials_file: Path = config.CLEAN_DATA_DIR / "trials.parquet",
    output_file: Path = config.CLEAN_DATA_DIR / "eligibility.parquet",
) -> pd.DataFrame:
    """Parse eligibility criteria for all trials.

    Args:
        trials_file: Path to normalized trials Parquet file
        output_file: Path to output eligibility Parquet file

    Returns:
        DataFrame with parsed eligibility criteria
    """
    # Load normalized trials
    print(f"Loading trials from: {trials_file}")
    trials_df = pd.read_parquet(trials_file)
    print(f"Loaded {len(trials_df)} trials")

    # Parse eligibility for each trial
    eligibility_records = []

    for _, row in trials_df.iterrows():
        criteria = parse_eligibility(
            trial_id=row["trial_id"],
            eligibility_text=row.get("eligibility_text"),
        )
        eligibility_records.append(criteria.model_dump())

    eligibility_df = pd.DataFrame(eligibility_records)

    # Save to Parquet
    eligibility_df.to_parquet(output_file, index=False)
    print(f"Saved eligibility data to: {output_file}")

    # Print summary
    print("\n=== Eligibility Summary ===")
    print(f"Total trials: {len(eligibility_df)}")
    print(f"Trials with age restrictions: {eligibility_df['min_age'].notna().sum()}")
    print(f"Trials with sex restrictions: {eligibility_df['sex'].notna().sum()}")
    print(f"Average inclusion criteria: {eligibility_df['key_inclusion_terms'].apply(len).mean():.1f}")
    print(f"Average exclusion criteria: {eligibility_df['key_exclusion_terms'].apply(len).mean():.1f}")

    return eligibility_df


def main() -> None:
    """CLI entry point for parsing eligibility criteria."""
    parser = argparse.ArgumentParser(
        description="Parse eligibility criteria from clinical trials"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=config.CLEAN_DATA_DIR / "trials.parquet",
        help="Input Parquet file with normalized trials",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.CLEAN_DATA_DIR / "eligibility.parquet",
        help="Output Parquet file",
    )

    args = parser.parse_args()

    try:
        df = parse_all_eligibility(
            trials_file=args.input,
            output_file=args.output,
        )
        print(f"\n✓ Successfully parsed eligibility for {len(df)} trials")
    except Exception as e:
        print(f"\n✗ Error parsing eligibility: {e}")
        raise


if __name__ == "__main__":
    main()
