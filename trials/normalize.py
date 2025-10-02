"""Normalize raw clinical trial data into structured format."""

import argparse
import json
from pathlib import Path
from typing import Optional

import pandas as pd

from trials.config import config
from trials.models import ClinicalTrial, NormalizedTrial


def normalize_trial(trial_data: dict) -> Optional[NormalizedTrial]:
    """Normalize a single trial record.

    Args:
        trial_data: Raw trial data from API

    Returns:
        NormalizedTrial object or None if parsing fails
    """
    try:
        trial = ClinicalTrial(**trial_data)

        # Extract countries
        locations = trial.get_locations()
        countries = list(set(loc.get("country", "") for loc in locations if loc.get("country")))

        # Count arms
        arms = trial.get_arms()
        arm_count = len(arms)

        return NormalizedTrial(
            trial_id=trial.get_nct_id(),
            title=trial.get_title(),
            phase=trial.get_phase(),
            status=trial.get_status(),
            start_date=trial.get_start_date(),
            completion_date=trial.get_completion_date(),
            enrollment=trial.get_enrollment(),
            arms=arm_count,
            countries=countries,
            study_type=trial.get_study_type(),
            masking=trial.get_masking(),
            allocation=trial.get_allocation(),
            primary_outcomes=trial.get_primary_outcomes(),
            eligibility_text=trial.get_eligibility_text(),
        )
    except Exception as e:
        print(f"Warning: Failed to normalize trial: {e}")
        return None


def normalize_jsonl_file(input_file: Path) -> pd.DataFrame:
    """Normalize all trials in a JSONL file.

    Args:
        input_file: Path to input JSONL file

    Returns:
        DataFrame with normalized trials
    """
    normalized_trials = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            try:
                trial_data = json.loads(line.strip())
                normalized = normalize_trial(trial_data)
                if normalized:
                    normalized_trials.append(normalized.model_dump())
            except json.JSONDecodeError:
                print(f"Warning: Failed to parse JSON on line {line_num}")
                continue

    df = pd.DataFrame(normalized_trials)
    return df


def normalize_all(
    input_dir: Path = config.RAW_DATA_DIR,
    output_file: Path = config.CLEAN_DATA_DIR / "trials.parquet",
) -> pd.DataFrame:
    """Normalize all JSONL files in the input directory.

    Args:
        input_dir: Directory containing raw JSONL files
        output_file: Path to output Parquet file

    Returns:
        Combined DataFrame with all normalized trials
    """
    config.ensure_dirs()

    # Find all JSONL files
    jsonl_files = list(input_dir.glob("*.jsonl"))

    if not jsonl_files:
        raise ValueError(f"No JSONL files found in {input_dir}")

    print(f"Found {len(jsonl_files)} JSONL file(s) to process")

    # Process all files
    all_dfs = []
    for jsonl_file in jsonl_files:
        print(f"\nProcessing: {jsonl_file.name}")
        df = normalize_jsonl_file(jsonl_file)
        print(f"  Normalized {len(df)} trials")
        all_dfs.append(df)

    # Combine all DataFrames
    combined_df = pd.concat(all_dfs, ignore_index=True)

    # Remove duplicates based on trial_id
    original_count = len(combined_df)
    combined_df = combined_df.drop_duplicates(subset=["trial_id"], keep="first")
    if len(combined_df) < original_count:
        print(f"\nRemoved {original_count - len(combined_df)} duplicate trials")

    print(f"\nTotal unique trials: {len(combined_df)}")

    # Save to Parquet
    combined_df.to_parquet(output_file, index=False)
    print(f"Saved normalized data to: {output_file}")

    # Print summary statistics
    print("\n=== Summary Statistics ===")
    print(f"Total trials: {len(combined_df)}")
    print(f"\nPhase distribution:")
    print(combined_df["phase"].value_counts().head(10))
    print(f"\nStatus distribution:")
    print(combined_df["status"].value_counts().head(10))
    print(f"\nStudy type distribution:")
    print(combined_df["study_type"].value_counts())

    return combined_df


def main() -> None:
    """CLI entry point for normalizing trials."""
    parser = argparse.ArgumentParser(
        description="Normalize raw clinical trial data"
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=config.RAW_DATA_DIR,
        help="Input directory with JSONL files",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.CLEAN_DATA_DIR / "trials.parquet",
        help="Output Parquet file",
    )

    args = parser.parse_args()

    try:
        df = normalize_all(
            input_dir=args.input_dir,
            output_file=args.output,
        )
        print(f"\n✓ Successfully normalized {len(df)} trials")
    except Exception as e:
        print(f"\n✗ Error normalizing trials: {e}")
        raise


if __name__ == "__main__":
    main()
