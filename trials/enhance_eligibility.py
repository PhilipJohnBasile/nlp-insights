"""Enhance eligibility data with clinical features."""

import pandas as pd
from trials.config import config
from trials.clinical_parser import (
    split_inclusion_exclusion,
    parse_treatment_line,
    check_common_exclusions,
    parse_biomarker_requirements,
    parse_prior_lines_limit,
    parse_washout_period,
    parse_required_tests,
    parse_ecog_requirement,
)


def main():
    """Enhance eligibility data with parsed clinical features."""
    print("Enhancing eligibility data with clinical features...")

    # Load existing data
    trials_df = pd.read_parquet(config.CLEAN_DATA_DIR / "trials.parquet")
    eligibility_df = pd.read_parquet(config.CLEAN_DATA_DIR / "eligibility.parquet")

    #  Merge to get eligibility text
    merged = eligibility_df.merge(
        trials_df[["trial_id", "eligibility_text"]],
        on="trial_id",
        how="left"
    )

    enhanced_rows = []

    for _, row in merged.iterrows():
        trial_id = row["trial_id"]
        eligibility_text = row.get("eligibility_text")

        # Split inclusion/exclusion
        inclusion_text, exclusion_text = split_inclusion_exclusion(eligibility_text)

        # Parse treatment line
        treatment_info = parse_treatment_line(eligibility_text)

        # Check common exclusions
        exclusions = check_common_exclusions(eligibility_text)

        # Parse biomarker requirements
        biomarkers = parse_biomarker_requirements(eligibility_text)

        # Parse prior lines limit
        prior_lines_limit = parse_prior_lines_limit(eligibility_text)

        # Parse washout period
        washout_period = parse_washout_period(eligibility_text)

        # Parse required tests
        required_tests = parse_required_tests(eligibility_text)

        # Parse ECOG requirement
        ecog_req = parse_ecog_requirement(eligibility_text)

        enhanced_rows.append({
            "trial_id": trial_id,
            "min_age": row.get("min_age"),
            "max_age": row.get("max_age"),
            "sex": row.get("sex"),
            "inclusion_text": inclusion_text,
            "exclusion_text": exclusion_text,
            "treatment_line": treatment_info["treatment_line"],
            "prior_therapy_required": treatment_info["prior_therapy_required"],
            "treatment_naive_allowed": treatment_info["treatment_naive_allowed"],
            "brain_mets_excluded": exclusions.get("brain_mets_excluded"),
            "prior_immunotherapy_excluded": exclusions.get("prior_immunotherapy_excluded"),
            "autoimmune_excluded": exclusions.get("autoimmune_excluded"),
            "hiv_excluded": exclusions.get("hiv_excluded"),
            "hepatitis_excluded": exclusions.get("hepatitis_excluded"),
            "organ_dysfunction_excluded": exclusions.get("organ_dysfunction_excluded"),
            "biomarker_requirements": biomarkers,
            "prior_lines_limit": prior_lines_limit,
            "washout_period": washout_period,
            "required_tests": required_tests,
            "max_ecog": ecog_req["max_ecog"],
        })

    enhanced_df = pd.DataFrame(enhanced_rows)

    # Save enhanced eligibility
    output_path = config.CLEAN_DATA_DIR / "eligibility_enhanced.parquet"
    enhanced_df.to_parquet(output_path, index=False)

    print(f"✅ Saved {len(enhanced_df)} enhanced eligibility records")
    print(f"\nNew columns:")
    print(f"  - inclusion_text (separated)")
    print(f"  - exclusion_text (separated)")
    print(f"  - treatment_line (1st/2nd/3rd+)")
    print(f"  - prior_therapy_required")
    print(f"  - treatment_naive_allowed")
    print(f"  - brain_mets_excluded")
    print(f"  - prior_immunotherapy_excluded")
    print(f"  - autoimmune_excluded")
    print(f"  - hiv_excluded")
    print(f"  - hepatitis_excluded")
    print(f"  - organ_dysfunction_excluded")

    # Show sample
    print(f"\nSample treatment lines:")
    print(enhanced_df["treatment_line"].value_counts())


if __name__ == "__main__":
    main()
