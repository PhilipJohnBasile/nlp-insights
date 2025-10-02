"""Feature engineering for clinical trial clustering and analysis."""

import argparse
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

from trials.config import config
from trials.models import TrialFeatures


def parse_date(date_str: Optional[str]) -> Optional[datetime]:
    """Parse date string to datetime.

    Args:
        date_str: Date string in various formats

    Returns:
        Datetime object or None
    """
    if not date_str or pd.isna(date_str):
        return None

    # Try common formats
    formats = [
        "%Y-%m-%d",
        "%Y-%m",
        "%Y",
        "%B %Y",
        "%B %d, %Y",
    ]

    for fmt in formats:
        try:
            return datetime.strptime(str(date_str), fmt)
        except ValueError:
            continue

    return None


def calculate_duration_days(
    start_date: Optional[str],
    completion_date: Optional[str],
) -> float:
    """Calculate trial duration in days.

    Args:
        start_date: Start date string
        completion_date: Completion date string

    Returns:
        Duration in days or 0.0 if dates cannot be parsed
    """
    start = parse_date(start_date)
    end = parse_date(completion_date)

    if start and end and end > start:
        return (end - start).days

    return 0.0


def encode_phase(phase: Optional[str]) -> int:
    """Encode phase as numeric code.

    Args:
        phase: Phase string (e.g., "Phase 1", "Phase 2")

    Returns:
        Numeric phase code (0-4)
    """
    if not phase or pd.isna(phase):
        return 0

    phase_lower = str(phase).lower()

    if "early phase 1" in phase_lower or "phase 0" in phase_lower:
        return 1
    elif "phase 1" in phase_lower:
        return 2
    elif "phase 2" in phase_lower:
        return 3
    elif "phase 3" in phase_lower:
        return 4
    elif "phase 4" in phase_lower:
        return 5

    return 0


def encode_masking(masking: Optional[str]) -> int:
    """Encode masking level as numeric code.

    Args:
        masking: Masking description

    Returns:
        Masking level (0-4)
    """
    if not masking or pd.isna(masking):
        return 0

    masking_lower = str(masking).lower()

    if "quadruple" in masking_lower:
        return 4
    elif "triple" in masking_lower:
        return 3
    elif "double" in masking_lower:
        return 2
    elif "single" in masking_lower:
        return 1

    return 0


def extract_features(row: pd.Series) -> TrialFeatures:
    """Extract features from a trial record.

    Args:
        row: DataFrame row with trial data

    Returns:
        TrialFeatures object
    """
    # Enrollment
    enrollment = row.get("enrollment", 0)
    if pd.isna(enrollment):
        enrollment = 0

    # Duration
    duration = calculate_duration_days(
        row.get("start_date"),
        row.get("completion_date"),
    )

    # Phase
    phase_code = encode_phase(row.get("phase"))

    # Arms
    arm_count = row.get("arms", 0)
    if pd.isna(arm_count):
        arm_count = 0

    # Allocation
    allocation = str(row.get("allocation", "")).lower()
    randomized_flag = 1 if "randomized" in allocation else 0

    # Study type / intervention model
    parallel_flag = 0
    # This would need to check intervention_model if available in the data

    # Masking
    masking_level = encode_masking(row.get("masking"))

    # Sites (count countries as proxy for sites)
    countries = row.get("countries", [])
    try:
        if pd.isna(countries):
            num_sites = 0
        elif isinstance(countries, (list, tuple)):
            num_sites = len(countries)
        elif hasattr(countries, '__len__'):
            num_sites = len(countries) if len(countries) > 0 else 0
        else:
            num_sites = 0
    except (TypeError, ValueError):
        # If pd.isna fails on array-like, check differently
        if isinstance(countries, (list, tuple)):
            num_sites = len(countries)
        elif hasattr(countries, '__len__'):
            num_sites = len(countries)
        else:
            num_sites = 0

    return TrialFeatures(
        trial_id=row["trial_id"],
        planned_enrollment=float(enrollment),
        num_sites=num_sites,
        phase_code=phase_code,
        arm_count=int(arm_count),
        randomized_flag=randomized_flag,
        parallel_flag=parallel_flag,
        masking_level=masking_level,
        duration_days=duration,
    )


def build_features(
    trials_file: Path = config.CLEAN_DATA_DIR / "trials.parquet",
    output_file: Path = config.CLEAN_DATA_DIR / "features.parquet",
) -> pd.DataFrame:
    """Build feature matrix for all trials.

    Args:
        trials_file: Path to normalized trials Parquet file
        output_file: Path to output features Parquet file

    Returns:
        DataFrame with trial features
    """
    # Load normalized trials
    print(f"Loading trials from: {trials_file}")
    trials_df = pd.read_parquet(trials_file)
    print(f"Loaded {len(trials_df)} trials")

    # Extract features
    print("Extracting features...")
    features = []

    for _, row in trials_df.iterrows():
        trial_features = extract_features(row)
        features.append(trial_features.model_dump())

    features_df = pd.DataFrame(features)

    # Save to Parquet
    features_df.to_parquet(output_file, index=False)
    print(f"Saved features to: {output_file}")

    # Print summary
    print("\n=== Feature Summary ===")
    print(features_df.describe())

    return features_df


def main() -> None:
    """CLI entry point for building features."""
    parser = argparse.ArgumentParser(
        description="Build feature matrix for clinical trials"
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
        default=config.CLEAN_DATA_DIR / "features.parquet",
        help="Output Parquet file",
    )

    args = parser.parse_args()

    try:
        df = build_features(
            trials_file=args.input,
            output_file=args.output,
        )
        print(f"\n✓ Successfully built features for {len(df)} trials")
    except Exception as e:
        print(f"\n✗ Error building features: {e}")
        raise


if __name__ == "__main__":
    main()
