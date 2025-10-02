"""Fetch clinical trial data from ClinicalTrials.gov."""

import argparse
import json
from datetime import datetime
from pathlib import Path

from trials.client import ClinicalTrialsClient
from trials.config import config


def fetch_trials(
    condition: str,
    max_studies: int = 2000,
    output_dir: Path = config.RAW_DATA_DIR,
) -> Path:
    """Fetch clinical trials for a specific condition.

    Args:
        condition: Disease or condition to search for
        max_studies: Maximum number of studies to fetch
        output_dir: Directory to save raw data

    Returns:
        Path to the output JSONL file
    """
    config.ensure_dirs()

    client = ClinicalTrialsClient()
    print(f"Fetching trials for condition: {condition}")
    print(f"Maximum studies: {max_studies}")

    # Fetch studies
    studies = client.search_all(
        condition=condition,
        max_studies=max_studies,
        page_size=1000,
        use_cache=True,
    )

    print(f"\nTotal studies fetched: {len(studies)}")

    # Generate output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    safe_condition = "".join(
        c if c.isalnum() or c in " -_" else "_" for c in condition
    ).replace(" ", "_")
    output_file = output_dir / f"{safe_condition}_{timestamp}.jsonl"

    # Save as JSONL
    with open(output_file, "w", encoding="utf-8") as f:
        for study in studies:
            f.write(json.dumps(study) + "\n")

    print(f"\nSaved {len(studies)} studies to: {output_file}")
    return output_file


def main() -> None:
    """CLI entry point for fetching trials."""
    parser = argparse.ArgumentParser(
        description="Fetch clinical trials from ClinicalTrials.gov"
    )
    parser.add_argument(
        "--condition",
        type=str,
        required=True,
        help="Disease or condition to search for (e.g., 'breast cancer')",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=2000,
        help="Maximum number of studies to fetch (default: 2000)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=config.RAW_DATA_DIR,
        help="Output directory for raw data",
    )

    args = parser.parse_args()

    try:
        output_file = fetch_trials(
            condition=args.condition,
            max_studies=args.max,
            output_dir=args.output_dir,
        )
        print(f"\n✓ Successfully fetched trials to {output_file}")
    except Exception as e:
        print(f"\n✗ Error fetching trials: {e}")
        raise


if __name__ == "__main__":
    main()
