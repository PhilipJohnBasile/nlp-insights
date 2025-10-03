#!/usr/bin/env python3
"""Enhance clinical data with dose escalation, randomization, and crossover information."""

import json
from pathlib import Path
import pandas as pd
from tqdm import tqdm

from trials.clinical_parser import (
    parse_dose_escalation_info,
    parse_randomization_info,
    parse_crossover_info,
)
from trials.config import config


def enhance_clinical_details():
    """Enhance clinical details with additional parsed information."""

    # Load existing clinical details
    clinical_path = config.CLEAN_DATA_DIR / "clinical_details.parquet"
    if not clinical_path.exists():
        print(f"Clinical details file not found: {clinical_path}")
        return

    clinical_df = pd.read_parquet(clinical_path)
    print(f"Loaded {len(clinical_df)} clinical records")

    # Load eligibility data for crossover parsing
    elig_path = config.CLEAN_DATA_DIR / "eligibility.parquet"
    eligibility_df = pd.read_parquet(elig_path) if elig_path.exists() else None

    # Load raw trial data for full parsing
    raw_data_path = config.DATA_DIR / "trials_raw.json"
    if not raw_data_path.exists():
        print("Raw trials data not found - run fetch_trials.py first")
        return

    with open(raw_data_path, 'r') as f:
        raw_trials = json.load(f)

    # Create a mapping of trial_id to raw data
    trial_raw_map = {}
    for trial_data in raw_trials:
        trial_id = trial_data.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")
        if trial_id:
            trial_raw_map[trial_id] = trial_data

    print(f"Found {len(trial_raw_map)} raw trial records")

    # Add new columns for enhanced data
    enhanced_rows = []

    for idx, row in tqdm(clinical_df.iterrows(), total=len(clinical_df), desc="Enhancing clinical data"):
        trial_id = row["trial_id"]
        enhanced_row = row.to_dict()

        # Get raw trial data
        raw_trial = trial_raw_map.get(trial_id)

        if raw_trial:
            # Parse dose escalation info (for Phase 1 trials)
            if "Phase 1" in str(row.get("phase", "")):
                dose_info = parse_dose_escalation_info(raw_trial)
                enhanced_row["is_dose_escalation"] = dose_info["is_dose_escalation"]
                enhanced_row["is_expansion"] = dose_info["is_expansion"]
                enhanced_row["cohort_type"] = dose_info["cohort_type"]
                enhanced_row["dose_level"] = dose_info["dose_level"]
            else:
                enhanced_row["is_dose_escalation"] = False
                enhanced_row["is_expansion"] = False
                enhanced_row["cohort_type"] = None
                enhanced_row["dose_level"] = None

            # Parse randomization info
            rand_info = parse_randomization_info(raw_trial)
            enhanced_row["is_randomized"] = rand_info["is_randomized"]
            enhanced_row["randomization_ratio"] = rand_info["randomization_ratio"]
            enhanced_row["allocation"] = rand_info["allocation"]
            enhanced_row["masking"] = rand_info["masking"]

            # Parse crossover info
            elig_text = None
            if eligibility_df is not None and trial_id in eligibility_df["trial_id"].values:
                elig_text = eligibility_df[eligibility_df["trial_id"] == trial_id]["eligibility_text"].iloc[0]

            cross_info = parse_crossover_info(elig_text, raw_trial)
            enhanced_row["crossover_allowed"] = cross_info["crossover_allowed"]
            enhanced_row["crossover_details"] = cross_info["crossover_details"]

        enhanced_rows.append(enhanced_row)

    # Create enhanced dataframe
    enhanced_df = pd.DataFrame(enhanced_rows)

    # Save enhanced data
    output_path = config.CLEAN_DATA_DIR / "clinical_details_enhanced.parquet"
    enhanced_df.to_parquet(output_path, index=False)
    print(f"\n✅ Saved enhanced clinical data to {output_path}")

    # Show summary of enhancements
    if "is_dose_escalation" in enhanced_df.columns:
        dose_esc_count = enhanced_df["is_dose_escalation"].sum()
        expansion_count = enhanced_df["is_expansion"].sum()
        print(f"\nDose Escalation trials: {dose_esc_count}")
        print(f"Expansion Cohort trials: {expansion_count}")

    if "is_randomized" in enhanced_df.columns:
        rand_count = enhanced_df["is_randomized"].sum()
        ratio_count = enhanced_df["randomization_ratio"].notna().sum()
        print(f"\nRandomized trials: {rand_count}")
        print(f"Trials with ratio info: {ratio_count}")

    if "crossover_allowed" in enhanced_df.columns:
        cross_yes = (enhanced_df["crossover_allowed"] == True).sum()
        cross_no = (enhanced_df["crossover_allowed"] == False).sum()
        print(f"\nCrossover allowed: {cross_yes}")
        print(f"Crossover not allowed: {cross_no}")

    return enhanced_df


if __name__ == "__main__":
    enhance_clinical_details()