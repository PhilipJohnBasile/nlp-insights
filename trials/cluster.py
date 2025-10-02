"""Cluster clinical trials based on design features."""

import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from trials.config import config


def cluster_trials(
    features_file: Path = config.CLEAN_DATA_DIR / "features.parquet",
    output_file: Path = config.CLEAN_DATA_DIR / "clusters.parquet",
    k: int = config.CLUSTERING_K,
    random_seed: int = config.RANDOM_SEED,
) -> pd.DataFrame:
    """Cluster trials based on design features.

    Args:
        features_file: Path to features Parquet file
        output_file: Path to output clusters Parquet file
        k: Number of clusters
        random_seed: Random seed for reproducibility

    Returns:
        DataFrame with trial IDs and cluster labels
    """
    # Load features
    print(f"Loading features from: {features_file}")
    features_df = pd.read_parquet(features_file)
    print(f"Loaded {len(features_df)} trials")

    # Select numeric features for clustering
    feature_cols = [
        "planned_enrollment",
        "num_sites",
        "phase_code",
        "arm_count",
        "randomized_flag",
        "masking_level",
        "duration_days",
    ]

    X = features_df[feature_cols].fillna(0).values

    # Standardize features
    print("Standardizing features...")
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Cluster with KMeans
    print(f"Clustering with k={k}...")
    kmeans = KMeans(n_clusters=k, random_state=random_seed, n_init=10)
    cluster_labels = kmeans.fit_predict(X_scaled)

    # Create output DataFrame
    clusters_df = pd.DataFrame(
        {
            "trial_id": features_df["trial_id"],
            "cluster": cluster_labels,
        }
    )

    # Save to Parquet
    clusters_df.to_parquet(output_file, index=False)
    print(f"Saved cluster labels to: {output_file}")

    # Print cluster statistics
    print("\n=== Cluster Summary ===")
    print(f"Number of clusters: {k}")
    print("\nCluster sizes:")
    print(clusters_df["cluster"].value_counts().sort_index())

    # Merge with features for cluster profiling
    clustered = features_df.merge(clusters_df, on="trial_id")

    print("\n=== Cluster Profiles ===")
    for cluster_id in range(k):
        cluster_data = clustered[clustered["cluster"] == cluster_id]
        print(f"\nCluster {cluster_id} (n={len(cluster_data)}):")
        print(f"  Avg enrollment: {cluster_data['planned_enrollment'].mean():.0f}")
        print(f"  Avg sites: {cluster_data['num_sites'].mean():.1f}")
        print(f"  Avg phase: {cluster_data['phase_code'].mean():.1f}")
        print(f"  Avg arms: {cluster_data['arm_count'].mean():.1f}")
        print(f"  Randomized: {cluster_data['randomized_flag'].mean():.1%}")
        print(f"  Avg duration: {cluster_data['duration_days'].mean():.0f} days")

    return clusters_df


def main() -> None:
    """CLI entry point for clustering trials."""
    parser = argparse.ArgumentParser(
        description="Cluster clinical trials based on design features"
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
        default=config.CLEAN_DATA_DIR / "clusters.parquet",
        help="Output Parquet file",
    )
    parser.add_argument(
        "--k",
        type=int,
        default=config.CLUSTERING_K,
        help="Number of clusters",
    )

    args = parser.parse_args()

    try:
        df = cluster_trials(
            features_file=args.input,
            output_file=args.output,
            k=args.k,
        )
        print(f"\n✓ Successfully clustered {len(df)} trials into {args.k} groups")
    except Exception as e:
        print(f"\n✗ Error clustering trials: {e}")
        raise


if __name__ == "__main__":
    main()
