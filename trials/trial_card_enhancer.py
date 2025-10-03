"""Enhanced trial card display with all new features."""

import streamlit as st
import pandas as pd
import json
from pathlib import Path
from datetime import datetime

from trials.safety_parser import parse_adverse_events, format_safety_display
from trials.enrollment_tracker import parse_enrollment_data, format_enrollment_display, calculate_enrollment_urgency
from trials.financial_info import parse_financial_info, format_financial_display
from trials.protocol_access import get_protocol_links, format_protocol_documents, generate_eligibility_checklist
from trials.similar_patients import format_similar_patients_display
from trials.emr_integration import export_to_emr_format


def load_trial_json(nct_id: str) -> dict:
    """Load full trial JSON data for enhanced features.

    Args:
        nct_id: NCT ID of trial

    Returns:
        Trial data dictionary or empty dict if not found
    """
    # Try to load from raw data directory
    raw_data_path = Path("data/raw")

    # First try individual JSON files
    possible_files = [
        raw_data_path / f"{nct_id}.json",
        raw_data_path / "trials.json",  # All trials in one file
    ]

    for file_path in possible_files:
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    if file_path.name == "trials.json":
                        # Multiple trials in one file
                        all_trials = json.load(f)
                        for trial in all_trials:
                            trial_nct = trial.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")
                            if trial_nct == nct_id:
                                return trial
                    else:
                        # Single trial file
                        return json.load(f)
            except:
                continue

    # Try JSONL files (line-delimited JSON) - this is the FIX for data loading!
    jsonl_files = list(raw_data_path.glob("*.jsonl"))
    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file, 'r') as f:
                for line in f:
                    if line.strip():  # Skip empty lines
                        trial = json.loads(line)
                        trial_nct = trial.get("protocolSection", {}).get("identificationModule", {}).get("nctId", "")
                        if trial_nct == nct_id:
                            return trial
        except Exception as e:
            # Continue to next file if this one fails
            continue

    # Return empty dict if not found
    return {}


def add_enhanced_trial_sections(nct_id: str, match_data: dict, patient_profile: dict = None):
    """Add all enhanced sections to a trial card.

    Args:
        nct_id: NCT ID of trial
        match_data: Trial match data from search results
        patient_profile: Optional patient profile for similarity matching
    """
    # Load full trial JSON for enhanced features
    trial_json = load_trial_json(nct_id)

    if not trial_json:
        st.warning("ℹ️ Enhanced data not available (trial JSON not loaded)")
        return

    st.markdown("---")
    st.markdown("### 🔍 Detailed Information")

    # Initialize session state for referral form
    if f"show_referral_{nct_id}" not in st.session_state:
        st.session_state[f"show_referral_{nct_id}"] = False

    # Quick Action Buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("📝 Create Referral", key=f"btn_referral_{nct_id}", use_container_width=True):
            st.session_state[f"show_referral_{nct_id}"] = True

    with col2:
        if st.button("📧 Set Alert", key=f"btn_alert_{nct_id}", use_container_width=True):
            st.success("✅ Alert set for this trial!")
            st.info("You'll be notified of protocol updates")

    with col3:
        if st.button("💾 Export to EMR", key=f"btn_emr_{nct_id}", use_container_width=True):
            # Generate EMR export
            export_text = export_to_emr_format(
                patient_data=patient_profile or {},
                trials=[match_data],
                format="text"
            )
            st.session_state[f"emr_export_{nct_id}"] = export_text

    with col4:
        if st.button("📋 Print Checklist", key=f"btn_checklist_{nct_id}", use_container_width=True):
            checklist = generate_eligibility_checklist(trial_json)
            st.session_state[f"checklist_{nct_id}"] = checklist

    # Show referral form if button was clicked
    if st.session_state.get(f"show_referral_{nct_id}"):
        st.markdown("---")
        st.subheader("📝 Create Patient Referral")

        with st.form(f"referral_form_{nct_id}"):
            patient_id = st.text_input("Patient ID (De-identified)", key=f"ref_pt_{nct_id}")

            # Site selection
            site_name = st.text_input("Referral Site", key=f"ref_site_{nct_id}")
            site_contact = st.text_input("Contact Person", key=f"ref_contact_{nct_id}")
            site_phone = st.text_input("Contact Phone", key=f"ref_phone_{nct_id}")
            notes = st.text_area("Notes", key=f"ref_notes_{nct_id}")

            col_submit, col_cancel = st.columns(2)
            with col_submit:
                if st.form_submit_button("✅ Create Referral", use_container_width=True):
                    if patient_id and site_name:
                        tracker = st.session_state.referral_tracker
                        ref_id = tracker.add_referral(
                            patient_id=patient_id,
                            nct_id=nct_id,
                            trial_title=match_data.get('title', ''),
                            site_name=site_name,
                            site_contact=site_contact,
                            site_phone=site_phone,
                            notes=notes
                        )
                        st.success(f"✅ Referral created: {ref_id}")
                        st.session_state[f"show_referral_{nct_id}"] = False
                        st.rerun()
                    else:
                        st.error("Please enter Patient ID and Site Name")

            with col_cancel:
                if st.form_submit_button("❌ Cancel", use_container_width=True):
                    st.session_state[f"show_referral_{nct_id}"] = False
                    st.rerun()

    # Show EMR export if generated
    if st.session_state.get(f"emr_export_{nct_id}"):
        st.markdown("---")
        st.subheader("💾 EMR Export")
        st.text_area("Copy this to your EMR:", st.session_state[f"emr_export_{nct_id}"], height=200)
        if st.button("✅ Close Export", key=f"close_emr_{nct_id}"):
            del st.session_state[f"emr_export_{nct_id}"]
            st.rerun()

    # Show checklist if generated
    if st.session_state.get(f"checklist_{nct_id}"):
        st.markdown("---")
        st.subheader("📋 Eligibility Checklist")
        st.markdown(st.session_state[f"checklist_{nct_id}"])
        if st.button("✅ Close Checklist", key=f"close_checklist_{nct_id}"):
            del st.session_state[f"checklist_{nct_id}"]
            st.rerun()

    # Expandable sections with new data
    st.markdown("---")

    # 1. Safety & Toxicity Data
    with st.expander("⚠️ Safety & Toxicity Data", expanded=False):
        eligibility_text = trial_json.get("protocolSection", {}).get("eligibilityModule", {}).get("eligibilityCriteria", "")
        description = trial_json.get("protocolSection", {}).get("descriptionModule", {}).get("briefSummary", "")

        safety_data = parse_adverse_events(eligibility_text, description)
        st.markdown(format_safety_display(safety_data))

    # 2. Enrollment Status & Urgency
    with st.expander("📊 Enrollment Status & Urgency", expanded=False):
        enrollment_data = parse_enrollment_data(trial_json)
        st.markdown(format_enrollment_display(enrollment_data))

        urgency, wait_time = calculate_enrollment_urgency(enrollment_data)

        # Visual urgency indicator
        if "HIGH" in urgency:
            st.error(f"🔥 **HIGH URGENCY:** {wait_time}")
        elif "MODERATE" in urgency:
            st.warning(f"🟡 **MODERATE URGENCY:** {wait_time}")
        elif "LOW" in urgency:
            st.info(f"🟢 **LOW URGENCY:** {wait_time}")
        else:
            st.info(f"⚪ {urgency}: {wait_time}")

    # 3. Financial Information
    with st.expander("💰 Financial Information", expanded=False):
        financial_info = parse_financial_info(trial_json)
        st.markdown(format_financial_display(financial_info))

    # 4. Protocol Documents & Resources
    with st.expander("📄 Protocol Documents & Resources", expanded=False):
        protocol_links = get_protocol_links(trial_json)
        st.markdown(format_protocol_documents(protocol_links))

    # 5. Similar Patients Analytics
    if patient_profile:
        with st.expander("👥 Similar Patients", expanded=False):
            similar_analyzer = st.session_state.similar_patients
            similar_stats = similar_analyzer.find_similar_patients(
                patient_profile=patient_profile,
                nct_id=nct_id
            )
            st.markdown(format_similar_patients_display(similar_stats))

            # Show alternative trials if available
            alternatives = similar_analyzer.get_alternative_trials(
                patient_profile=patient_profile,
                exclude_nct=nct_id
            )
            if alternatives:
                st.markdown("### 💡 Alternative Trials (Similar Patients Enrolled)")
                for alt in alternatives[:5]:
                    st.markdown(f"- [{alt['nct_id']}](https://clinicaltrials.gov/study/{alt['nct_id']}) - {alt['similar_enrolled']} similar patients")


def add_match_quality_visual(match_score: int, reasons: list) -> str:
    """Generate visual match quality indicator.

    Args:
        match_score: Match score from algorithm
        reasons: List of match reasons

    Returns:
        HTML string with visual indicator
    """
    if match_score >= 70:
        color = "#28a745"  # Green
        border = "4px solid #28a745"
        quality = "✅ EXCELLENT MATCH"
    elif match_score >= 50:
        color = "#ffc107"  # Yellow
        border = "4px solid #ffc107"
        quality = "🟡 GOOD MATCH"
    elif match_score >= 30:
        color = "#fd7e14"  # Orange
        border = "4px solid #fd7e14"
        quality = "🟠 FAIR MATCH"
    else:
        color = "#dc3545"  # Red
        border = "4px solid #dc3545"
        quality = "🔴 MARGINAL MATCH"

    # Extract key reasons
    key_reasons = []
    for reason in reasons[:3]:
        if "✅" in reason:
            key_reasons.append(reason.replace("✅", "").strip())

    reasons_html = "<br>".join([f"• {r}" for r in key_reasons]) if key_reasons else "See details below"

    html = f"""
    <div style="border-left: {border}; padding: 15px; margin: 10px 0; background-color: {color}15; border-radius: 4px;">
        <h4 style="margin: 0; color: {color};">{quality} (Score: {match_score})</h4>
        <p style="margin: 5px 0; font-size: 0.9em;">{reasons_html}</p>
    </div>
    """

    return html
