"""EMR integration utilities for clinical trial matching."""

import json
from datetime import datetime
from typing import Dict, List, Optional
import csv
from io import StringIO


def export_to_emr_format(patient_data: Dict, trials: List[Dict], format: str = "text") -> str:
    """Export patient matching data in EMR-friendly format.

    Args:
        patient_data: Patient information
        trials: List of matching trials
        format: Output format ('text', 'csv', 'json')

    Returns:
        Formatted string for EMR
    """
    if format == "text":
        return _export_text_format(patient_data, trials)
    elif format == "csv":
        return _export_csv_format(trials)
    elif format == "json":
        return _export_json_format(patient_data, trials)
    else:
        return _export_text_format(patient_data, trials)


def _export_text_format(patient_data: Dict, trials: List[Dict]) -> str:
    """Export as plain text for copy/paste into EMR notes.

    Args:
        patient_data: Patient information
        trials: List of matching trials

    Returns:
        Formatted text
    """
    lines = []
    lines.append("=" * 60)
    lines.append("CLINICAL TRIAL SEARCH RESULTS")
    lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("=" * 60)
    lines.append("")

    # Patient summary
    lines.append("PATIENT CRITERIA:")
    if patient_data.get("age"):
        lines.append(f"  Age: {patient_data['age']}")
    if patient_data.get("cancer_type"):
        lines.append(f"  Cancer Type: {patient_data['cancer_type']}")
    if patient_data.get("stage"):
        lines.append(f"  Stage: {patient_data['stage']}")
    if patient_data.get("ecog"):
        lines.append(f"  ECOG: {patient_data['ecog']}")
    if patient_data.get("prior_therapies"):
        lines.append(f"  Prior Therapies: {patient_data['prior_therapies']}")

    biomarkers = []
    for marker in ["PDL1", "EGFR", "ALK", "ROS1", "BRAF", "HER2", "BRCA", "MSI_HIGH", "TMB_HIGH", "NTRK"]:
        if patient_data.get(marker):
            biomarkers.append(marker.replace("_", "-"))
    if biomarkers:
        lines.append(f"  Biomarkers: {', '.join(biomarkers)}")

    lines.append("")
    lines.append(f"MATCHING TRIALS FOUND: {len(trials)}")
    lines.append("")

    # List trials
    for i, trial in enumerate(trials[:10], 1):
        lines.append(f"{i}. {trial.get('nct_id', 'N/A')}")
        lines.append(f"   Title: {trial.get('title', 'N/A')}")
        lines.append(f"   Phase: {trial.get('phase', 'N/A')}")
        lines.append(f"   Status: {trial.get('status', 'N/A')}")

        # Location info
        if trial.get("nearest_site"):
            site = trial["nearest_site"]
            lines.append(f"   Site: {site.get('facility', 'N/A')}, {site.get('city', '')}, {site.get('state', '')}")
            if site.get('distance'):
                lines.append(f"   Distance: {site['distance']:.1f} miles")
            if site.get('phone'):
                lines.append(f"   Phone: {site['phone']}")

        lines.append(f"   ClinicalTrials.gov: https://clinicaltrials.gov/study/{trial.get('nct_id', '')}")
        lines.append("")

    lines.append("=" * 60)
    lines.append("NEXT STEPS:")
    lines.append("1. Review full eligibility criteria with patient")
    lines.append("2. Contact trial coordinator at preferred site")
    lines.append("3. Obtain patient consent for referral")
    lines.append("4. Complete referral documentation")
    lines.append("=" * 60)

    return "\n".join(lines)


def _export_csv_format(trials: List[Dict]) -> str:
    """Export trials as CSV for EMR import.

    Args:
        trials: List of matching trials

    Returns:
        CSV string
    """
    output = StringIO()
    fieldnames = ["NCT_ID", "Title", "Phase", "Status", "Site", "City", "State", "Distance_Miles", "Phone", "URL"]
    writer = csv.DictWriter(output, fieldnames=fieldnames)

    writer.writeheader()
    for trial in trials:
        site = trial.get("nearest_site", {})
        row = {
            "NCT_ID": trial.get("nct_id", ""),
            "Title": trial.get("title", "")[:100],  # Truncate long titles
            "Phase": trial.get("phase", ""),
            "Status": trial.get("status", ""),
            "Site": site.get("facility", ""),
            "City": site.get("city", ""),
            "State": site.get("state", ""),
            "Distance_Miles": site.get("distance", ""),
            "Phone": site.get("phone", ""),
            "URL": f"https://clinicaltrials.gov/study/{trial.get('nct_id', '')}"
        }
        writer.writerow(row)

    return output.getvalue()


def _export_json_format(patient_data: Dict, trials: List[Dict]) -> str:
    """Export as JSON for structured EMR integration.

    Args:
        patient_data: Patient information
        trials: List of matching trials

    Returns:
        JSON string
    """
    export_data = {
        "export_timestamp": datetime.now().isoformat(),
        "patient_criteria": patient_data,
        "matching_trials": []
    }

    for trial in trials:
        trial_export = {
            "nct_id": trial.get("nct_id"),
            "title": trial.get("title"),
            "phase": trial.get("phase"),
            "status": trial.get("status"),
            "url": f"https://clinicaltrials.gov/study/{trial.get('nct_id', '')}",
            "sites": trial.get("sites", [])
        }
        export_data["matching_trials"].append(trial_export)

    return json.dumps(export_data, indent=2)


def import_from_csv(csv_content: str) -> List[Dict]:
    """Import patient data from CSV file (common EMR export format).

    Args:
        csv_content: CSV file content as string

    Returns:
        List of patient dictionaries
    """
    patients = []
    reader = csv.DictReader(StringIO(csv_content))

    for row in reader:
        patient = {
            "patient_id": row.get("Patient_ID", ""),
            "age": int(row.get("Age", 0)) if row.get("Age") else None,
            "cancer_type": row.get("Cancer_Type", ""),
            "stage": row.get("Stage", ""),
            "ecog": row.get("ECOG", ""),
            "biomarkers": row.get("Biomarkers", "").split(",") if row.get("Biomarkers") else []
        }
        patients.append(patient)

    return patients


def generate_referral_letter(patient_data: Dict, trial: Dict, physician_name: str) -> str:
    """Generate a referral letter template for trial coordinators.

    Args:
        patient_data: Patient information
        trial: Trial information
        physician_name: Referring physician name

    Returns:
        Formatted referral letter
    """
    today = datetime.now().strftime("%B %d, %Y")

    letter = f"""
Date: {today}

To: Trial Coordinator
Re: Patient Referral for Clinical Trial {trial.get('nct_id', '')}

Dear Trial Coordinator,

I am writing to refer a patient who may be eligible for your clinical trial:

TRIAL INFORMATION:
- NCT ID: {trial.get('nct_id', '')}
- Title: {trial.get('title', '')}
- Phase: {trial.get('phase', '')}

PATIENT SUMMARY:
"""

    if patient_data.get("age"):
        letter += f"- Age: {patient_data['age']} years\n"
    if patient_data.get("cancer_type"):
        letter += f"- Diagnosis: {patient_data['cancer_type']}"
        if patient_data.get("stage"):
            letter += f", Stage {patient_data['stage']}"
        letter += "\n"
    if patient_data.get("ecog"):
        letter += f"- ECOG Performance Status: {patient_data['ecog']}\n"
    if patient_data.get("prior_therapies"):
        letter += f"- Prior Therapies: {patient_data['prior_therapies']}\n"

    # Biomarkers
    biomarkers = []
    for marker in ["PDL1", "EGFR", "ALK", "ROS1", "BRAF", "HER2", "BRCA", "MSI_HIGH", "TMB_HIGH"]:
        if patient_data.get(marker):
            biomarkers.append(marker.replace("_", "-"))
    if biomarkers:
        letter += f"- Biomarker Status: {', '.join(biomarkers)}\n"

    letter += f"""

Based on my review of the eligibility criteria, I believe this patient may be a good candidate for the trial. I would appreciate if you could:

1. Review the patient's eligibility
2. Contact me to discuss any questions
3. Schedule a screening visit if appropriate

Please feel free to contact me at your earliest convenience.

Sincerely,
{physician_name}

---
This referral was generated using the Clinical Trials Matching System.
Full eligibility criteria should be verified before enrollment.
"""

    return letter


def get_emr_integration_instructions() -> str:
    """Get instructions for EMR integration.

    Returns:
        Markdown formatted instructions
    """
    return """### 🏥 EMR Integration Guide

**Export Options:**

1. **Text Format** - Copy/paste into EMR progress notes
   - Simple formatted text
   - Includes all trial details
   - Ready for clinical documentation

2. **CSV Format** - Import into EMR structured data
   - Spreadsheet-compatible
   - One row per trial
   - Can be linked to patient chart

3. **JSON Format** - For automated EMR integration
   - Structured data format
   - API-friendly
   - Programmatic access

**How to Use:**

1. Complete patient matching search
2. Select trials to export
3. Choose your preferred format
4. Click "Export to EMR Format"
5. Copy or download the result
6. Paste into your EMR system

**CSV Import Template:**

Your EMR can export patient data using this CSV format:

```
Patient_ID,Age,Cancer_Type,Stage,ECOG,Biomarkers
PT001,65,Lung Cancer,IV,1,EGFR,PDL1
PT002,58,Breast Cancer,III,0,HER2,BRCA
```

Upload this CSV to batch-process multiple patients.

**Tips:**
- Always verify data before committing to EMR
- Follow your institution's data privacy policies
- Keep audit trail of trial referrals
- Update EMR when enrollment status changes
"""
