"""Tests for clustering and risk scoring modules."""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from trials.cluster import cluster_trials
from trials.risk import calculate_risk_score, score_all_trials


class TestClusterTrials:
    """Test trial clustering functionality."""

    def test_basic_clustering(self, tmp_path):
        """Test basic clustering with sample data."""
        # Create sample features
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": ["NCT001", "NCT002", "NCT003", "NCT004", "NCT005"],
            "planned_enrollment": [100, 200, 50, 150, 80],
            "num_sites": [3, 5, 1, 4, 2],
            "phase_code": [2, 3, 1, 2, 2],
            "arm_count": [2, 3, 1, 2, 2],
            "randomized_flag": [1, 1, 0, 1, 1],
            "masking_level": [2, 2, 0, 1, 2],
            "duration_days": [365, 730, 180, 450, 300]
        })
        features_df.to_parquet(features_file, index=False)

        # Cluster
        output_file = tmp_path / "clusters.parquet"
        result_df = cluster_trials(
            features_file=features_file,
            output_file=output_file,
            k=3,
            random_seed=42
        )

        # Verify
        assert len(result_df) == 5
        assert "trial_id" in result_df.columns
        assert "cluster" in result_df.columns
        assert output_file.exists()

    def test_cluster_labels_range(self, tmp_path):
        """Test cluster labels are in correct range."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": [f"NCT{i:03d}" for i in range(20)],
            "planned_enrollment": np.random.randint(10, 200, 20),
            "num_sites": np.random.randint(1, 10, 20),
            "phase_code": np.random.randint(1, 4, 20),
            "arm_count": np.random.randint(1, 5, 20),
            "randomized_flag": np.random.randint(0, 2, 20),
            "masking_level": np.random.randint(0, 3, 20),
            "duration_days": np.random.randint(100, 1000, 20)
        })
        features_df.to_parquet(features_file, index=False)

        output_file = tmp_path / "clusters.parquet"
        result_df = cluster_trials(features_file, output_file, k=5, random_seed=42)

        # Cluster labels should be 0-4 for k=5
        assert result_df["cluster"].min() >= 0
        assert result_df["cluster"].max() < 5

    def test_reproducible_clustering(self, tmp_path):
        """Test that clustering is reproducible with same random seed."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": [f"NCT{i:03d}" for i in range(10)],
            "planned_enrollment": [100, 200, 50, 150, 80, 120, 90, 180, 60, 140],
            "num_sites": [3, 5, 1, 4, 2, 3, 2, 5, 1, 4],
            "phase_code": [2, 3, 1, 2, 2, 3, 1, 2, 1, 3],
            "arm_count": [2, 3, 1, 2, 2, 3, 1, 2, 1, 3],
            "randomized_flag": [1, 1, 0, 1, 1, 1, 0, 1, 0, 1],
            "masking_level": [2, 2, 0, 1, 2, 2, 0, 1, 0, 2],
            "duration_days": [365, 730, 180, 450, 300, 600, 200, 500, 150, 650]
        })
        features_df.to_parquet(features_file, index=False)

        # Cluster twice with same seed
        output1 = tmp_path / "clusters1.parquet"
        result1 = cluster_trials(features_file, output1, k=3, random_seed=42)

        output2 = tmp_path / "clusters2.parquet"
        result2 = cluster_trials(features_file, output2, k=3, random_seed=42)

        # Results should be identical
        pd.testing.assert_frame_equal(result1, result2)

    def test_handles_missing_values(self, tmp_path):
        """Test clustering handles NaN values."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": ["NCT001", "NCT002", "NCT003"],
            "planned_enrollment": [100, np.nan, 50],
            "num_sites": [3, 5, np.nan],
            "phase_code": [2, np.nan, 1],
            "arm_count": [2, 3, 1],
            "randomized_flag": [1, 1, 0],
            "masking_level": [2, 2, 0],
            "duration_days": [365, 730, 180]
        })
        features_df.to_parquet(features_file, index=False)

        output_file = tmp_path / "clusters.parquet"
        result_df = cluster_trials(features_file, output_file, k=2, random_seed=42)

        # Should complete without errors
        assert len(result_df) == 3


class TestCalculateRiskScore:
    """Test risk score calculation."""

    def test_low_risk_trial(self):
        """Test low risk trial (good design)."""
        risk = calculate_risk_score(
            trial_id="NCT12345678",
            enrollment=200,  # Good enrollment
            num_sites=10,    # Multi-site
            randomized_flag=1,  # Randomized
            duration_days=365   # Reasonable duration
        )

        assert risk.trial_id == "NCT12345678"
        assert risk.small_enrollment_penalty == 0.0
        assert risk.no_randomization_penalty == 0.0
        assert risk.single_site_penalty == 0.0
        assert risk.long_duration_penalty == 0.0
        assert risk.total_risk_score == 0.0

    def test_small_enrollment_penalty(self):
        """Test small enrollment penalty calculation."""
        # Very small enrollment
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=10,
            num_sites=5,
            randomized_flag=1,
            duration_days=365
        )

        assert risk.small_enrollment_penalty > 0
        assert risk.total_risk_score > 0

    def test_zero_enrollment_penalty(self):
        """Test zero enrollment gets maximum penalty."""
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=0,
            num_sites=5,
            randomized_flag=1,
            duration_days=365
        )

        assert risk.small_enrollment_penalty == 50.0

    def test_no_randomization_penalty(self):
        """Test non-randomized trial penalty."""
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=5,
            randomized_flag=0,  # Not randomized
            duration_days=365
        )

        assert risk.no_randomization_penalty == 30.0
        assert risk.total_risk_score >= 30.0

    def test_single_site_penalty(self):
        """Test single site penalty."""
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=1,  # Single site
            randomized_flag=1,
            duration_days=365
        )

        assert risk.single_site_penalty > 0
        assert risk.total_risk_score > 0

    def test_zero_sites_penalty(self):
        """Test zero sites gets maximum site penalty."""
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=0,
            randomized_flag=1,
            duration_days=365
        )

        assert risk.single_site_penalty == 20.0

    def test_few_sites_penalty(self):
        """Test 2-3 sites gets moderate penalty."""
        risk2 = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=2,
            randomized_flag=1,
            duration_days=365
        )

        risk3 = calculate_risk_score(
            trial_id="NCT002",
            enrollment=200,
            num_sites=3,
            randomized_flag=1,
            duration_days=365
        )

        assert risk2.single_site_penalty == 5.0
        assert risk3.single_site_penalty == 5.0

    def test_long_duration_penalty(self):
        """Test long duration penalty."""
        # Very long trial (5 years = 1825 days)
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=5,
            randomized_flag=1,
            duration_days=1825
        )

        assert risk.long_duration_penalty > 0
        assert risk.total_risk_score > 0

    def test_long_duration_capped(self):
        """Test long duration penalty is capped at 30."""
        # Extremely long trial (20 years)
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=200,
            num_sites=5,
            randomized_flag=1,
            duration_days=7300
        )

        assert risk.long_duration_penalty <= 30.0

    def test_high_risk_trial(self):
        """Test high risk trial (multiple risk factors)."""
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=0,       # Max penalty: 50
            num_sites=0,        # Max penalty: 20
            randomized_flag=0,  # Penalty: 30
            duration_days=5000  # High penalty: ~27.4
        )

        # Total should be close to max (130)
        assert risk.total_risk_score > 100
        assert risk.small_enrollment_penalty == 50.0
        assert risk.no_randomization_penalty == 30.0
        assert risk.single_site_penalty == 20.0

    def test_moderate_enrollment(self):
        """Test enrollment just below threshold."""
        # Test enrollment = 40 (threshold is 50 by default)
        risk = calculate_risk_score(
            trial_id="NCT001",
            enrollment=40,
            num_sites=5,
            randomized_flag=1,
            duration_days=365
        )

        # Should have some penalty but not max
        assert 0 < risk.small_enrollment_penalty < 50.0


class TestScoreAllTrials:
    """Test batch risk scoring."""

    def test_score_all_trials(self, tmp_path):
        """Test scoring multiple trials."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": ["NCT001", "NCT002", "NCT003"],
            "planned_enrollment": [200, 10, 0],
            "num_sites": [10, 1, 0],
            "randomized_flag": [1, 0, 0],
            "duration_days": [365, 730, 2000]
        })
        features_df.to_parquet(features_file, index=False)

        output_file = tmp_path / "risks.parquet"
        risks_df = score_all_trials(features_file, output_file)

        # Verify
        assert len(risks_df) == 3
        assert "trial_id" in risks_df.columns
        assert "total_risk_score" in risks_df.columns
        assert output_file.exists()

    def test_risk_scores_vary(self, tmp_path):
        """Test that risk scores vary appropriately."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": ["LOW_RISK", "HIGH_RISK"],
            "planned_enrollment": [200, 0],
            "num_sites": [10, 0],
            "randomized_flag": [1, 0],
            "duration_days": [365, 5000]
        })
        features_df.to_parquet(features_file, index=False)

        output_file = tmp_path / "risks.parquet"
        risks_df = score_all_trials(features_file, output_file)

        low_risk = risks_df[risks_df["trial_id"] == "LOW_RISK"].iloc[0]
        high_risk = risks_df[risks_df["trial_id"] == "HIGH_RISK"].iloc[0]

        # High risk should have much higher score
        assert high_risk["total_risk_score"] > low_risk["total_risk_score"]
        assert low_risk["total_risk_score"] < 10  # Low risk ~0
        assert high_risk["total_risk_score"] > 100  # High risk ~130

    def test_all_penalty_columns_present(self, tmp_path):
        """Test that all penalty columns are in output."""
        features_file = tmp_path / "features.parquet"
        features_df = pd.DataFrame({
            "trial_id": ["NCT001"],
            "planned_enrollment": [100],
            "num_sites": [5],
            "randomized_flag": [1],
            "duration_days": [365]
        })
        features_df.to_parquet(features_file, index=False)

        output_file = tmp_path / "risks.parquet"
        risks_df = score_all_trials(features_file, output_file)

        required_cols = [
            "trial_id",
            "small_enrollment_penalty",
            "no_randomization_penalty",
            "single_site_penalty",
            "long_duration_penalty",
            "total_risk_score"
        ]

        for col in required_cols:
            assert col in risks_df.columns
