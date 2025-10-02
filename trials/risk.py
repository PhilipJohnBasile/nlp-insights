"""Risk scoring for clinical trials."""

import argparse
from pathlib import Path

import pandas as pd

from trials.config import config
from trials.models import TrialRisk


def calculate_risk_score(
    trial_id: str,
    enrollment: float,
    num_sites: int,
    randomized_flag: int,
    duration_days: float,
) -> TrialRisk:
    """Calculate risk score for a trial.

    Risk components:
    - Small enrollment penalty: Higher risk for trials with fewer participants
    - No randomization penalty: Higher risk for non-randomized trials
    - Single site penalty: Higher risk for single-site trials
    - Long duration penalty: Higher risk for very long trials

    Args:
        trial_id: Trial NCT ID
        enrollment: Planned enrollment count
        num_sites: Number of sites/countries
        randomized_flag: 1 if randomized, 0 otherwise
        duration_days: Trial duration in days

    Returns:
        TrialRisk object with component and total scores
    """
    # Small enrollment penalty (0-50 points)
    # Penalty increases as enrollment gets smaller
    if enrollment < config.SMALL_ENROLLMENT_THRESHOLD:
        if enrollment == 0:
            small_enrollment_penalty = 50.0
        else:
            small_enrollment_penalty = (
                50.0 * (config.SMALL_ENROLLMENT_THRESHOLD - enrollment) /
                config.SMALL_ENROLLMENT_THRESHOLD
            )
    else:
        small_enrollment_penalty = 0.0

    # No randomization penalty (30 points if not randomized)
    no_randomization_penalty = 30.0 if randomized_flag == 0 else 0.0

    # Single/few site penalty (0-20 points)
    if num_sites == 0:
        single_site_penalty = 20.0
    elif num_sites == 1:
        single_site_penalty = float(config.SINGLE_SITE_PENALTY)
    elif num_sites <= 3:
        single_site_penalty = 5.0
    else:
        single_site_penalty = 0.0

    # Long duration penalty (0-30 points)
    # Penalty for trials longer than threshold
    if duration_days > config.LONG_DURATION_DAYS:
        # Cap at 30 points for extremely long trials
        excess_days = duration_days - config.LONG_DURATION_DAYS
        long_duration_penalty = min(30.0, (excess_days / 365.0) * 10.0)
    else:
        long_duration_penalty = 0.0

    # Total risk score (max 130 points)
    total_risk_score = (
        small_enrollment_penalty +
        no_randomization_penalty +
        single_site_penalty +
        long_duration_penalty
    )

    return TrialRisk(
        trial_id=trial_id,
        small_enrollment_penalty=small_enrollment_penalty,
        no_randomization_penalty=no_randomization_penalty,
        single_site_penalty=single_site_penalty,
        long_duration_penalty=long_duration_penalty,
        total_risk_score=total_risk_score,
    )


def score_all_trials(
    features_file: Path = config.CLEAN_DATA_DIR / "features.parquet",
    output_file: Path = config.CLEAN_DATA_DIR / "risks.parquet",
) -> pd.DataFrame:
    """Calculate risk scores for all trials.

    Args:
        features_file: Path to features Parquet file
        output_file: Path to output risks Parquet file

    Returns:
        DataFrame with risk scores
    """
    # Load features
    print(f"Loading features from: {features_file}")
    features_df = pd.read_parquet(features_file)
    print(f"Loaded {len(features_df)} trials")

    # Calculate risk scores
    print("Calculating risk scores...")
    risks = []

    for _, row in features_df.iterrows():
        risk = calculate_risk_score(
            trial_id=row["trial_id"],
            enrollment=row["planned_enrollment"],
            num_sites=row["num_sites"],
            randomized_flag=row["randomized_flag"],
            duration_days=row["duration_days"],
        )
        risks.append(risk.model_dump())

    risks_df = pd.DataFrame(risks)

    # Save to Parquet
    risks_df.to_parquet(output_file, index=False)
    print(f"Saved risk scores to: {output_file}")

    # Print summary
    print("\n=== Risk Score Summary ===")
    print(risks_df["total_risk_score"].describe())

    print("\n=== Highest Risk Trials ===")
    top_risks = risks_df.nlargest(10, "total_risk_score")
    for _, row in top_risks.iterrows():
        print(f"\n{row['trial_id']}: Total Risk = {row['total_risk_score']:.1f}")
        print(f"  Small enrollment: {row['small_enrollment_penalty']:.1f}")
        print(f"  No randomization: {row['no_randomization_penalty']:.1f}")
        print(f"  Single site: {row['single_site_penalty']:.1f}")
        print(f"  Long duration: {row['long_duration_penalty']:.1f}")

    return risks_df


def main() -> None:
    """CLI entry point for risk scoring."""
    parser = argparse.ArgumentParser(
        description="Calculate risk scores for clinical trials"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=config.CLEAN_DATA_DIR / "features.parquet",
        help="Input Parquet file with features",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=config.CLEAN_DATA_DIR / "risks.parquet",
        help="Output Parquet file",
    )

    args = parser.parse_args()

    try:
        df = score_all_trials(
            features_file=args.input,
            output_file=args.output,
        )
        print(f"\n✓ Successfully scored {len(df)} trials")
    except Exception as e:
        print(f"\n✗ Error scoring trials: {e}")
        raise


if __name__ == "__main__":
    main()
