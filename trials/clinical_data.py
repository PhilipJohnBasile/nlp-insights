"""Extract clinical-specific data for oncology use cases."""

import json
from pathlib import Path
from typing import Any

import pandas as pd

from trials.config import config


def extract_interventions(trial_data: dict) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Extract intervention/drug information from trial.

    Args:
        trial_data: Raw trial data from API

    Returns:
        Tuple of (intervention list, intervention summary dict)
    """
    protocol = trial_data.get("protocolSection", {})
    arms_module = protocol.get("armsInterventionsModule", {})
    interventions = arms_module.get("interventions", [])

    result = []
    drug_count = 0
    drug_names = []

    for intervention in interventions:
        interv_type = intervention.get("type", "")
        interv_name = intervention.get("name", "")

        result.append({
            "type": interv_type,
            "name": interv_name,
            "description": intervention.get("description", ""),
        })

        # Count drugs (not procedures, devices, etc)
        if interv_type == "DRUG":
            drug_count += 1
            drug_names.append(interv_name)

    # Determine if combination therapy
    is_combination = drug_count > 1

    summary = {
        "num_drugs": drug_count,
        "is_combination": is_combination,
        "drug_names": drug_names,
    }

    return result, summary


def extract_locations(trial_data: dict) -> list[dict[str, Any]]:
    """Extract site location information from trial.

    Args:
        trial_data: Raw trial data from API

    Returns:
        List of location dictionaries with geocoding
    """
    protocol = trial_data.get("protocolSection", {})
    contacts_module = protocol.get("contactsLocationsModule", {})
    locations = contacts_module.get("locations", [])

    result = []
    for loc in locations:
        geo = loc.get("geoPoint", {})

        # Extract contact information
        contacts = loc.get("contacts", [])
        contact_name = None
        contact_phone = None
        contact_email = None

        if contacts:
            # Usually first contact is study coordinator
            contact = contacts[0]
            contact_name = contact.get("name")
            contact_phone = contact.get("phone")
            contact_email = contact.get("email")

        result.append({
            "facility": loc.get("facility", ""),
            "city": loc.get("city", ""),
            "state": loc.get("state", ""),
            "zip": loc.get("zip", ""),
            "country": loc.get("country", ""),
            "status": loc.get("status", ""),
            "latitude": geo.get("lat"),
            "longitude": geo.get("lon"),
            "contact_name": contact_name,
            "contact_phone": contact_phone,
            "contact_email": contact_email,
        })

    return result


def extract_sponsor_info(trial_data: dict) -> dict[str, str]:
    """Extract sponsor and collaborator information.

    Args:
        trial_data: Raw trial data from API

    Returns:
        Dictionary with sponsor information
    """
    protocol = trial_data.get("protocolSection", {})
    sponsor_module = protocol.get("sponsorCollaboratorsModule", {})
    lead_sponsor = sponsor_module.get("leadSponsor", {})

    return {
        "sponsor_name": lead_sponsor.get("name", ""),
        "sponsor_class": lead_sponsor.get("class", ""),  # INDUSTRY, NIH, OTHER, etc.
    }


def extract_outcomes(trial_data: dict) -> dict[str, list[str]]:
    """Extract primary and secondary outcomes/endpoints.

    Args:
        trial_data: Raw trial data from API

    Returns:
        Dictionary with primary and secondary outcome lists
    """
    protocol = trial_data.get("protocolSection", {})
    outcomes_module = protocol.get("outcomesModule", {})

    primary = outcomes_module.get("primaryOutcomes", [])
    secondary = outcomes_module.get("secondaryOutcomes", [])

    return {
        "primary_outcomes": [o.get("measure", "") for o in primary],
        "secondary_outcomes": [o.get("measure", "") for o in secondary],
    }


def extract_conditions(trial_data: dict) -> list[str]:
    """Extract disease conditions/indications.

    Args:
        trial_data: Raw trial data from API

    Returns:
        List of conditions
    """
    protocol = trial_data.get("protocolSection", {})
    conditions_module = protocol.get("conditionsModule", {})
    return conditions_module.get("conditions", [])


def extract_phase(trial_data: dict) -> str:
    """Extract trial phase (Phase I, II, III, IV).

    Args:
        trial_data: Raw trial data from API

    Returns:
        Phase string (e.g., "Phase 2" or "Phase 1/Phase 2")
    """
    protocol = trial_data.get("protocolSection", {})
    design_module = protocol.get("designModule", {})
    phases = design_module.get("phases", [])

    if not phases:
        return "Not Applicable"

    # Clean up phase names (PHASE2 -> Phase 2)
    cleaned_phases = []
    for phase in phases:
        phase_str = phase.replace("PHASE", "Phase ").replace("NA", "Not Applicable")
        cleaned_phases.append(phase_str)

    return "/".join(cleaned_phases)


def extract_arms_info(trial_data: dict) -> dict[str, Any]:
    """Extract information about treatment arms and comparators.

    Args:
        trial_data: Raw trial data from API

    Returns:
        Dictionary with arm information
    """
    protocol = trial_data.get("protocolSection", {})
    arms_module = protocol.get("armsInterventionsModule", {})
    arm_groups = arms_module.get("armGroups", [])

    arms_list = []
    has_control = False
    has_placebo = False

    for arm in arm_groups:
        arm_type = arm.get("type", "")
        arm_label = arm.get("label", "")
        arm_desc = arm.get("description", "")

        arms_list.append({
            "label": arm_label,
            "type": arm_type,
            "description": arm_desc
        })

        # Check for control/placebo arms
        if arm_type in ["PLACEBO_COMPARATOR", "SHAM_COMPARATOR"]:
            has_placebo = True
        elif arm_type in ["ACTIVE_COMPARATOR", "NO_INTERVENTION"]:
            has_control = True

    # Determine study design
    if len(arms_list) == 1:
        study_design = "Single Arm"
    elif has_placebo:
        study_design = "Placebo-Controlled"
    elif has_control:
        study_design = "Active-Controlled"
    else:
        study_design = f"{len(arms_list)} Arms"

    return {
        "num_arms": len(arms_list),
        "arms": arms_list,
        "study_design": study_design,
        "has_placebo": has_placebo,
        "has_active_control": has_control,
    }


def create_clinical_dataframes(input_file: Path) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Extract clinical data from JSONL file into separate dataframes.

    Args:
        input_file: Path to JSONL file with raw trial data

    Returns:
        Tuple of (interventions_df, locations_df, clinical_details_df)
    """
    interventions_list = []
    locations_list = []
    clinical_details_list = []

    with open(input_file, "r", encoding="utf-8") as f:
        for line in f:
            trial = json.loads(line)
            nct_id = trial.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")

            if not nct_id:
                continue

            # Extract interventions
            interventions, intervention_summary = extract_interventions(trial)
            for intervention in interventions:
                interventions_list.append({
                    "trial_id": nct_id,
                    **intervention
                })

            # Extract locations
            locations = extract_locations(trial)
            for location in locations:
                locations_list.append({
                    "trial_id": nct_id,
                    **location
                })

            # Extract clinical details
            sponsor_info = extract_sponsor_info(trial)
            outcomes = extract_outcomes(trial)
            conditions = extract_conditions(trial)
            phase = extract_phase(trial)
            arms_info = extract_arms_info(trial)

            clinical_details_list.append({
                "trial_id": nct_id,
                "sponsor_name": sponsor_info["sponsor_name"],
                "sponsor_class": sponsor_info["sponsor_class"],
                "conditions": conditions,
                "primary_outcomes": outcomes["primary_outcomes"],
                "secondary_outcomes": outcomes["secondary_outcomes"],
                "phase": phase,
                "num_arms": arms_info["num_arms"],
                "study_design": arms_info["study_design"],
                "has_placebo": arms_info["has_placebo"],
                "has_active_control": arms_info["has_active_control"],
                "arms": arms_info["arms"],
                "num_drugs": intervention_summary["num_drugs"],
                "is_combination": intervention_summary["is_combination"],
                "drug_names": intervention_summary["drug_names"],
            })

    interventions_df = pd.DataFrame(interventions_list)
    locations_df = pd.DataFrame(locations_list)
    clinical_details_df = pd.DataFrame(clinical_details_list)

    return interventions_df, locations_df, clinical_details_df


def main():
    """Extract clinical data from all raw JSONL files."""
    print("Extracting clinical data from raw files...")

    all_interventions = []
    all_locations = []
    all_clinical_details = []

    for jsonl_file in config.RAW_DATA_DIR.glob("*.jsonl"):
        print(f"Processing {jsonl_file.name}...")
        interventions_df, locations_df, clinical_details_df = create_clinical_dataframes(jsonl_file)

        all_interventions.append(interventions_df)
        all_locations.append(locations_df)
        all_clinical_details.append(clinical_details_df)

    # Combine all dataframes
    if all_interventions:
        final_interventions = pd.concat(all_interventions, ignore_index=True)
        final_locations = pd.concat(all_locations, ignore_index=True)
        final_clinical_details = pd.concat(all_clinical_details, ignore_index=True)

        # Remove duplicates
        final_interventions = final_interventions.drop_duplicates()
        final_locations = final_locations.drop_duplicates()
        final_clinical_details = final_clinical_details.drop_duplicates(subset=["trial_id"])

        # Save to parquet
        output_dir = config.CLEAN_DATA_DIR
        final_interventions.to_parquet(output_dir / "interventions.parquet", index=False)
        final_locations.to_parquet(output_dir / "locations.parquet", index=False)
        final_clinical_details.to_parquet(output_dir / "clinical_details.parquet", index=False)

        print(f"\n✅ Saved {len(final_interventions)} interventions")
        print(f"✅ Saved {len(final_locations)} locations")
        print(f"✅ Saved {len(final_clinical_details)} clinical details")
    else:
        print("No data to process!")


if __name__ == "__main__":
    main()
