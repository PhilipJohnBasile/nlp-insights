"""
Example Analysis Notebook
Convert to .ipynb using: jupytext --to ipynb example_analysis.py
"""

# %% [markdown]
# # Clinical Trials Exploratory Data Analysis
#
# This notebook demonstrates how to perform custom analysis on the clinical trials data.

# %%
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Configure plotting
sns.set_style("whitegrid")
plt.rcParams['figure.figsize'] = (12, 6)

# %% [markdown]
# ## Load Data

# %%
# Load all processed data
trials = pd.read_parquet("../data/clean/trials.parquet")
eligibility = pd.read_parquet("../data/clean/eligibility.parquet")
features = pd.read_parquet("../data/clean/features.parquet")
risks = pd.read_parquet("../data/clean/risks.parquet")
clusters = pd.read_parquet("../data/clean/clusters.parquet")

# Merge everything
df = (trials
      .merge(eligibility, on="trial_id", how="left")
      .merge(features, on="trial_id", how="left")
      .merge(risks, on="trial_id", how="left")
      .merge(clusters, on="trial_id", how="left"))

print(f"Loaded {len(df)} trials")
df.head()

# %% [markdown]
# ## Phase Distribution

# %%
phase_counts = df["phase"].value_counts()
plt.figure(figsize=(10, 6))
phase_counts.plot(kind="bar")
plt.title("Trial Phase Distribution")
plt.xlabel("Phase")
plt.ylabel("Count")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Enrollment Analysis

# %%
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Histogram
axes[0].hist(df["enrollment"].dropna(), bins=50, edgecolor="black")
axes[0].set_xlabel("Enrollment")
axes[0].set_ylabel("Frequency")
axes[0].set_title("Enrollment Distribution")
axes[0].set_xlim(0, 1000)  # Focus on main range

# Box plot by phase
df_phase = df[df["phase"].notna()]
phases_order = ["EARLY_PHASE1", "PHASE1", "PHASE2", "PHASE3", "PHASE4"]
df_phase_filtered = df_phase[df_phase["phase"].isin(phases_order)]

df_phase_filtered.boxplot(column="enrollment", by="phase", ax=axes[1])
axes[1].set_xlabel("Phase")
axes[1].set_ylabel("Enrollment")
axes[1].set_title("Enrollment by Phase")
plt.suptitle("")  # Remove auto-title

plt.tight_layout()
plt.show()

# %% [markdown]
# ## Risk Score Analysis

# %%
fig, axes = plt.subplots(2, 2, figsize=(14, 10))

# Total risk distribution
axes[0, 0].hist(df["total_risk_score"], bins=30, edgecolor="black")
axes[0, 0].set_xlabel("Total Risk Score")
axes[0, 0].set_ylabel("Frequency")
axes[0, 0].set_title("Risk Score Distribution")

# Risk components
risk_components = [
    "small_enrollment_penalty",
    "no_randomization_penalty",
    "single_site_penalty",
    "long_duration_penalty"
]

axes[0, 1].bar(risk_components, [df[c].mean() for c in risk_components])
axes[0, 1].set_ylabel("Average Penalty")
axes[0, 1].set_title("Average Risk Components")
axes[0, 1].tick_params(axis='x', rotation=45)

# Risk vs Enrollment
axes[1, 0].scatter(df["enrollment"], df["total_risk_score"], alpha=0.5)
axes[1, 0].set_xlabel("Enrollment")
axes[1, 0].set_ylabel("Risk Score")
axes[1, 0].set_title("Risk Score vs Enrollment")
axes[1, 0].set_xlim(0, 500)

# Top risk trials
top_risk = df.nlargest(10, "total_risk_score")
axes[1, 1].barh(range(len(top_risk)), top_risk["total_risk_score"])
axes[1, 1].set_yticks(range(len(top_risk)))
axes[1, 1].set_yticklabels([tid[-8:] for tid in top_risk["trial_id"]])
axes[1, 1].set_xlabel("Risk Score")
axes[1, 1].set_title("Top 10 Highest Risk Trials")

plt.tight_layout()
plt.show()

# %% [markdown]
# ## Cluster Analysis

# %%
if "cluster" in df.columns:
    cluster_profile = df.groupby("cluster").agg({
        "enrollment": "mean",
        "num_sites": "mean",
        "arm_count": "mean",
        "randomized_flag": "mean",
        "duration_days": "mean",
        "total_risk_score": "mean",
        "trial_id": "count"
    }).round(1)

    cluster_profile.columns = [
        "Avg Enrollment", "Avg Sites", "Avg Arms",
        "% Randomized", "Avg Duration (days)", "Avg Risk", "Count"
    ]

    print("Cluster Profiles:")
    print(cluster_profile)

    # Visualize cluster sizes
    plt.figure(figsize=(10, 6))
    cluster_sizes = df["cluster"].value_counts().sort_index()
    plt.bar(cluster_sizes.index, cluster_sizes.values)
    plt.xlabel("Cluster")
    plt.ylabel("Number of Trials")
    plt.title("Cluster Sizes")
    plt.show()

# %% [markdown]
# ## Study Status Timeline

# %%
status_counts = df["status"].value_counts()
plt.figure(figsize=(12, 6))
status_counts.plot(kind="barh")
plt.xlabel("Count")
plt.ylabel("Status")
plt.title("Trial Status Distribution")
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Randomization Analysis

# %%
randomization_by_phase = df.groupby("phase")["randomized_flag"].agg(["mean", "count"])
randomization_by_phase.columns = ["Randomization Rate", "Count"]
randomization_by_phase = randomization_by_phase[randomization_by_phase["Count"] >= 5]

fig, ax = plt.subplots(figsize=(10, 6))
randomization_by_phase["Randomization Rate"].plot(kind="bar", ax=ax)
plt.ylabel("Proportion Randomized")
plt.xlabel("Phase")
plt.title("Randomization Rate by Phase")
plt.xticks(rotation=45)
plt.ylim(0, 1)
plt.tight_layout()
plt.show()

# %% [markdown]
# ## Key Findings Summary

# %%
print("=== KEY STATISTICS ===")
print(f"Total trials: {len(df)}")
print(f"Median enrollment: {df['enrollment'].median():.0f}")
print(f"Randomized trials: {df['randomized_flag'].mean():.1%}")
print(f"Average risk score: {df['total_risk_score'].mean():.1f}")
print(f"High risk (>60): {(df['total_risk_score'] > 60).sum()} trials")
print(f"\nMost common phase: {df['phase'].mode()[0]}")
print(f"Most common status: {df['status'].mode()[0]}")

# %% [markdown]
# ## Export High-Risk Trials

# %%
high_risk = df[df["total_risk_score"] > 60].sort_values("total_risk_score", ascending=False)
print(f"\nExporting {len(high_risk)} high-risk trials...")

# Select key columns
export_cols = [
    "trial_id", "title", "phase", "status", "enrollment",
    "randomized_flag", "num_sites", "duration_days",
    "small_enrollment_penalty", "no_randomization_penalty",
    "single_site_penalty", "long_duration_penalty",
    "total_risk_score"
]

high_risk[export_cols].to_csv("../data/clean/high_risk_export.csv", index=False)
print("✓ Exported to data/clean/high_risk_export.csv")
