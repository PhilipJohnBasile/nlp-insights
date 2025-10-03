"""Streamlit app for exploring clinical trials data."""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path
from math import radians, sin, cos, sqrt, atan2

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from trials.config import config

# Import new feature modules
from trials.safety_parser import parse_adverse_events, format_safety_display
from trials.enrollment_tracker import parse_enrollment_data, format_enrollment_display
from trials.referral_tracker import ReferralTracker, REFERRAL_STATUSES
from trials.mobile_styles import get_mobile_css
from trials.email_alerts import EmailAlertSystem, ALERT_TYPES
from trials.financial_info import parse_financial_info, format_financial_display, get_financial_assistance_resources
from trials.protocol_access import get_protocol_links, format_protocol_documents, generate_eligibility_checklist
from trials.similar_patients import SimilarPatientsAnalyzer, format_similar_patients_display
from trials.emr_integration import export_to_emr_format, get_emr_integration_instructions
from trials.trial_card_enhancer import add_enhanced_trial_sections, add_match_quality_visual


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points on Earth using Haversine formula.

    Args:
        lat1, lon1: Latitude and longitude of first point
        lat2, lon2: Latitude and longitude of second point

    Returns:
        Distance in miles
    """
    R = 3959  # Earth's radius in miles

    lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    distance = R * c

    return distance


def geocode_location(city: str = None, state: str = None, zip_code: str = None) -> tuple:
    """Simple geocoding using approximate US state/city centers.

    Returns:
        Tuple of (latitude, longitude) or (None, None) if not found
    """
    # Simple US state center coordinates
    state_centers = {
        "AL": (32.806671, -86.791130), "AK": (61.370716, -152.404419),
        "AZ": (33.729759, -111.431221), "AR": (34.969704, -92.373123),
        "CA": (36.116203, -119.681564), "CO": (39.059811, -105.311104),
        "CT": (41.597782, -72.755371), "DE": (39.318523, -75.507141),
        "FL": (27.766279, -81.686783), "GA": (33.040619, -83.643074),
        "HI": (21.094318, -157.498337), "ID": (44.240459, -114.478828),
        "IL": (40.349457, -88.986137), "IN": (39.849426, -86.258278),
        "IA": (42.011539, -93.210526), "KS": (38.526600, -96.726486),
        "KY": (37.668140, -84.670067), "LA": (31.169546, -91.867805),
        "ME": (44.693947, -69.381927), "MD": (39.063946, -76.802101),
        "MA": (42.230171, -71.530106), "MI": (43.326618, -84.536095),
        "MN": (45.694454, -93.900192), "MS": (32.741646, -89.678696),
        "MO": (38.456085, -92.288368), "MT": (46.921925, -110.454353),
        "NE": (41.125370, -98.268082), "NV": (38.313515, -117.055374),
        "NH": (43.452492, -71.563896), "NJ": (40.298904, -74.521011),
        "NM": (34.840515, -106.248482), "NY": (42.165726, -74.948051),
        "NC": (35.630066, -79.806419), "ND": (47.528912, -99.784012),
        "OH": (40.388783, -82.764915), "OK": (35.565342, -96.928917),
        "OR": (44.572021, -122.070938), "PA": (40.590752, -77.209755),
        "RI": (41.680893, -71.511780), "SC": (33.856892, -80.945007),
        "SD": (44.299782, -99.438828), "TN": (35.747845, -86.692345),
        "TX": (31.054487, -97.563461), "UT": (40.150032, -111.862434),
        "VT": (44.045876, -72.710686), "VA": (37.769337, -78.169968),
        "WA": (47.400902, -121.490494), "WV": (38.491226, -80.954453),
        "WI": (44.268543, -89.616508), "WY": (42.755966, -107.302490),
        "DC": (38.907192, -77.036871)
    }

    # Try state lookup
    if state:
        state_upper = state.upper()
        if state_upper in state_centers:
            return state_centers[state_upper]
        # Try full state name to abbreviation
        state_names = {
            "ALABAMA": "AL", "ALASKA": "AK", "ARIZONA": "AZ", "ARKANSAS": "AR",
            "CALIFORNIA": "CA", "COLORADO": "CO", "CONNECTICUT": "CT", "DELAWARE": "DE",
            "FLORIDA": "FL", "GEORGIA": "GA", "HAWAII": "HI", "IDAHO": "ID",
            "ILLINOIS": "IL", "INDIANA": "IN", "IOWA": "IA", "KANSAS": "KS",
            "KENTUCKY": "KY", "LOUISIANA": "LA", "MAINE": "ME", "MARYLAND": "MD",
            "MASSACHUSETTS": "MA", "MICHIGAN": "MI", "MINNESOTA": "MN", "MISSISSIPPI": "MS",
            "MISSOURI": "MO", "MONTANA": "MT", "NEBRASKA": "NE", "NEVADA": "NV",
            "NEW HAMPSHIRE": "NH", "NEW JERSEY": "NJ", "NEW MEXICO": "NM", "NEW YORK": "NY",
            "NORTH CAROLINA": "NC", "NORTH DAKOTA": "ND", "OHIO": "OH", "OKLAHOMA": "OK",
            "OREGON": "OR", "PENNSYLVANIA": "PA", "RHODE ISLAND": "RI", "SOUTH CAROLINA": "SC",
            "SOUTH DAKOTA": "SD", "TENNESSEE": "TN", "TEXAS": "TX", "UTAH": "UT",
            "VERMONT": "VT", "VIRGINIA": "VA", "WASHINGTON": "WA", "WEST VIRGINIA": "WV",
            "WISCONSIN": "WI", "WYOMING": "WY"
        }
        if state_upper in state_names:
            return state_centers[state_names[state_upper]]

    return (None, None)


# Page config
st.set_page_config(
    page_title="Clinical Trials Insights",
    page_icon="🔬",
    layout="wide",
)

# Fix dark mode styling
st.markdown("""
<style>
    /* Fix form background in dark mode */
    [data-testid="stForm"] {
        background-color: transparent !important;
    }

    /* Ensure text inputs are visible in dark mode */
    [data-testid="stForm"] input,
    [data-testid="stForm"] select,
    [data-testid="stForm"] textarea {
        background-color: var(--background-color) !important;
        color: var(--text-color) !important;
    }

    /* Fix subheaders in forms for dark mode */
    [data-testid="stForm"] h3,
    [data-testid="stForm"] h4 {
        color: var(--text-color) !important;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(ttl=60)  # Cache for 60 seconds to allow refresh after data fetch
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all processed data files.

    Returns:
        Tuple of (trials, eligibility, features, risks, clinical_details, locations) DataFrames
    """
    trials = pd.read_parquet(config.CLEAN_DATA_DIR / "trials.parquet")

    # Try to load enhanced eligibility first, fallback to regular
    enhanced_elig_file = config.CLEAN_DATA_DIR / "eligibility_enhanced.parquet"
    if enhanced_elig_file.exists():
        eligibility = pd.read_parquet(enhanced_elig_file)
    else:
        eligibility = pd.read_parquet(config.CLEAN_DATA_DIR / "eligibility.parquet")

    features = pd.read_parquet(config.CLEAN_DATA_DIR / "features.parquet")
    risks = pd.read_parquet(config.CLEAN_DATA_DIR / "risks.parquet")

    # Load clinical details (phase, endpoints, arms, etc.)
    clinical_details = pd.read_parquet(config.CLEAN_DATA_DIR / "clinical_details.parquet")

    # Load locations (for site info and contacts)
    locations = pd.read_parquet(config.CLEAN_DATA_DIR / "locations.parquet")

    # Merge cluster data if available
    cluster_file = config.CLEAN_DATA_DIR / "clusters.parquet"
    if cluster_file.exists():
        clusters = pd.read_parquet(cluster_file)
        trials = trials.merge(clusters, on="trial_id", how="left")

    return trials, eligibility, features, risks, clinical_details, locations


def highlight_terms(text: str, terms: list[str]) -> str:
    """Highlight search terms in text with HTML.

    Args:
        text: Text to highlight
        terms: List of terms to highlight

    Returns:
        HTML string with highlighted terms
    """
    if not text:
        return text

    # Handle terms being None, empty, or array-like
    if terms is None:
        return text

    try:
        if len(terms) == 0:
            return text
    except (TypeError, ValueError):
        return text

    highlighted = text
    for term in terms:
        if term:
            # Case-insensitive search and replace
            pattern = re.compile(re.escape(term), re.IGNORECASE)
            highlighted = pattern.sub(
                f'<mark style="background-color: yellow;">{term}</mark>',
                highlighted,
            )

    return highlighted


def get_dataset_info() -> dict:
    """Get information about the current dataset."""
    try:
        trials_file = config.CLEAN_DATA_DIR / "trials.parquet"
        if trials_file.exists():
            df = pd.read_parquet(trials_file)
            return {
                "exists": True,
                "count": len(df),
                "phase_top": df["phase"].value_counts().index[0] if len(df) > 0 else "N/A",
                "status_top": df["status"].value_counts().index[0] if len(df) > 0 else "N/A",
            }
        else:
            return {"exists": False}
    except Exception:
        return {"exists": False}


def get_file_info() -> pd.DataFrame:
    """Get information about all data files."""
    files_info = []
    data_files = [
        config.CLEAN_DATA_DIR / "trials.parquet",
        config.CLEAN_DATA_DIR / "eligibility.parquet",
        config.CLEAN_DATA_DIR / "features.parquet",
        config.CLEAN_DATA_DIR / "clusters.parquet",
        config.CLEAN_DATA_DIR / "risks.parquet",
    ]

    for file_path in data_files:
        if file_path.exists():
            stat = file_path.stat()
            files_info.append({
                "File": file_path.name,
                "Size (KB)": f"{stat.st_size / 1024:.1f}",
                "Last Modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
            })

    return pd.DataFrame(files_info) if files_info else pd.DataFrame()


def clear_all_data():
    """Clear all data files and cache."""
    import shutil

    # Clear parquet files
    for file_path in config.CLEAN_DATA_DIR.glob("*.parquet"):
        file_path.unlink()

    # Clear raw data
    for file_path in config.RAW_DATA_DIR.glob("*.jsonl"):
        file_path.unlink()

    # Clear cache
    cache_dir = config.RAW_DATA_DIR / ".cache"
    if cache_dir.exists():
        shutil.rmtree(cache_dir)

    # Clear streamlit cache
    st.cache_data.clear()


def main() -> None:
    """Main Streamlit app."""
    # Inject mobile-responsive CSS
    st.markdown(get_mobile_css(), unsafe_allow_html=True)

    # Initialize session state for tracking systems
    if "referral_tracker" not in st.session_state:
        st.session_state.referral_tracker = ReferralTracker()
    if "email_alerts" not in st.session_state:
        st.session_state.email_alerts = EmailAlertSystem()
    if "similar_patients" not in st.session_state:
        st.session_state.similar_patients = SimilarPatientsAnalyzer()

    st.title("🔬 Clinical Trials Insights")
    st.markdown(
        """
        **Research tool for analyzing clinical trial design and eligibility criteria.**

        ⚠️ **Disclaimer**: This is a research tool only and not medical advice.
        """
    )

    # Sidebar with dataset info and controls
    with st.sidebar:
        st.header("📊 Current Dataset")
        dataset_info = get_dataset_info()

        if dataset_info["exists"]:
            st.metric("Total Trials", dataset_info["count"])
            st.metric("Top Phase", dataset_info["phase_top"])
            st.metric("Top Status", dataset_info["status_top"])

            st.divider()

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Refresh", use_container_width=True, key="refresh_btn"):
                    st.cache_data.clear()
                    st.rerun()

            with col2:
                if st.button("🗑️ Clear", use_container_width=True):
                    if st.session_state.get("confirm_clear", False):
                        clear_all_data()
                        st.session_state["confirm_clear"] = False
                        st.success("Data cleared!")
                        st.rerun()
                    else:
                        st.session_state["confirm_clear"] = True
                        st.warning("Click again to confirm")
        else:
            st.info("No data loaded yet. Use the Fetch Data tab to download trials.")

    # Load data if available
    try:
        trials_df, eligibility_df, features_df, risks_df, clinical_details_df, locations_df = load_data()
        data_available = True
    except FileNotFoundError:
        data_available = False
        trials_df = None

    # Load clinical data if available (prefer enhanced version if exists)
    try:
        interventions_df = pd.read_parquet(config.CLEAN_DATA_DIR / "interventions.parquet")
        locations_df = pd.read_parquet(config.CLEAN_DATA_DIR / "locations.parquet")

        # Try to load enhanced clinical data first
        enhanced_path = config.CLEAN_DATA_DIR / "clinical_details_enhanced.parquet"
        regular_path = config.CLEAN_DATA_DIR / "clinical_details.parquet"

        if enhanced_path.exists():
            clinical_df = pd.read_parquet(enhanced_path)
            st.sidebar.success("✅ Using enhanced clinical data with dose/randomization info")
        else:
            clinical_df = pd.read_parquet(regular_path)

        clinical_data_available = True
    except FileNotFoundError:
        clinical_data_available = False
        interventions_df = None
        locations_df = None
        clinical_df = None

    # Create tabs
    if data_available:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🎯 Patient Matching", "📊 Explore", "🔍 Eligibility Explorer", "⚠️ Risk Analysis", "🔀 Compare Trials", "📋 My Referrals", "⚙️ Settings", "📥 Fetch Data"])
    else:
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["🎯 Patient Matching", "📊 Explore", "🔍 Eligibility Explorer", "⚠️ Risk Analysis", "🔀 Compare Trials", "📋 My Referrals", "⚙️ Settings", "📥 Fetch Data"])

    # Tab 1: Patient Matching
    with tab1:
        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            st.header("🎯 Patient Matching")

            st.markdown("""
            **Match your patient to eligible clinical trials based on their specific characteristics.**

            Enter patient information below to find matching trials.
            """)

            # Quick NCT ID lookup
            st.markdown("---")
            col_nct1, col_nct2 = st.columns([3, 1])
            with col_nct1:
                nct_lookup = st.text_input("🔍 Quick NCT ID Lookup", placeholder="e.g., NCT12345678", key="nct_lookup")
            with col_nct2:
                st.write("")  # Spacing
                st.write("")  # Spacing
                if st.button("Look Up", key="nct_lookup_btn"):
                    if nct_lookup:
                        nct_upper = nct_lookup.strip().upper()
                        trial_match = trials_df[trials_df["trial_id"] == nct_upper]
                        if not trial_match.empty:
                            trial = trial_match.iloc[0]
                            st.success(f"✅ Found: {trial['title']}")
                            with st.expander(f"View {nct_upper} Details", expanded=True):
                                st.markdown(f"**Phase**: {trial['phase']} | **Status**: {trial['status']}")
                                st.markdown(f"**Brief Summary**: {trial.get('brief_summary', '')[:500]}...")

                                # Get clinical details
                                if clinical_data_available and clinical_df is not None:
                                    clinical_info_df = clinical_df[clinical_df["trial_id"] == nct_upper]
                                    if not clinical_info_df.empty:
                                        clinical_info = clinical_info_df.iloc[0]
                                        st.markdown(f"**Sponsor**: {clinical_info.get('sponsor_name', '')}")
                                        primary_outcomes = clinical_info.get("primary_outcomes", [])
                                        if isinstance(primary_outcomes, (list, tuple)) and len(primary_outcomes) > 0:
                                            st.markdown(f"**Primary Endpoint**: {primary_outcomes[0]}")
                                        elif hasattr(primary_outcomes, '__len__') and len(primary_outcomes) > 0:
                                            st.markdown(f"**Primary Endpoint**: {primary_outcomes[0]}")

                                # Show recruiting sites
                                if clinical_data_available and locations_df is not None:
                                    trial_locs = locations_df[locations_df["trial_id"] == nct_upper]
                                    recruiting = trial_locs[trial_locs["status"] == "RECRUITING"]
                                    if not recruiting.empty:
                                        st.markdown(f"**🟢 Recruiting Sites** ({len(recruiting)}):")
                                        for _, loc in recruiting.head(5).iterrows():
                                            st.markdown(f"- {loc['facility']}, {loc['city']}, {loc['state']}")
                        else:
                            st.error(f"❌ NCT ID '{nct_lookup}' not found in current dataset")
            st.markdown("---")

            st.divider()

            # Patient input form - wrapped in form to prevent page reloads
            with st.form("patient_matching_form"):
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("Patient Demographics")
                    patient_age = st.number_input("Age", min_value=0, max_value=120, value=65)
                    patient_sex = st.selectbox("Sex", ["Male", "Female", "All"])

                    st.subheader("Cancer Information")
                    cancer_type = st.text_input("Cancer Type", placeholder="e.g., lung cancer, breast cancer, glioblastoma")
                    cancer_stage = st.selectbox("Stage", ["", "I", "II", "III", "IV", "Recurrent", "Metastatic"])

                with col2:
                    st.subheader("Performance Status")
                    ecog_status = st.selectbox("ECOG Performance Status", ["", "0", "1", "2", "3", "4"])

                    st.subheader("Treatment History")
                    num_prior_therapies = st.number_input("Number of prior therapies", min_value=0, max_value=10, value=0,
                                                          help="How many lines of prior therapy has this patient received?")

                    st.subheader("Biomarkers (select all that apply)")
                    bio_col1, bio_col2 = st.columns(2)
                    with bio_col1:
                        has_egfr = st.checkbox("EGFR mutation")
                        has_alk = st.checkbox("ALK fusion")
                        has_ros1 = st.checkbox("ROS1 fusion")
                        has_her2 = st.checkbox("HER2 positive")
                        has_brca = st.checkbox("BRCA mutation")
                    with bio_col2:
                        has_pdl1 = st.checkbox("PD-L1 positive")
                        has_msi_h = st.checkbox("MSI-High")
                        has_mmr_def = st.checkbox("MMR deficient")
                        has_idh = st.checkbox("IDH mutation")
                        has_mgmt = st.checkbox("MGMT methylated")

                    st.subheader("Location")
                    patient_state = st.text_input("State (for geographic matching)", placeholder="e.g., California, MA")

                # Patient conditions (for auto-exclusion)
                st.subheader("Patient Conditions (auto-exclude incompatible trials)")
                st.caption("⚠️ Excludes trials that forbid ANY checked condition")
                cond_col1, cond_col2 = st.columns(2)
                with cond_col1:
                    has_brain_mets = st.checkbox("Brain metastases")
                    has_autoimmune = st.checkbox("Autoimmune disease")
                    has_prior_immunotherapy = st.checkbox("Prior immunotherapy (PD-1/PD-L1)")
                with cond_col2:
                    has_hiv = st.checkbox("HIV positive")
                    has_hepatitis = st.checkbox("Hepatitis B or C")

                # Filter options
                st.subheader("Filters")
                col_f1, col_f2, col_f3 = st.columns(3)
                with col_f1:
                    show_recruiting_only = st.checkbox("Show only actively recruiting trials", value=True)
                    sort_by_distance = st.checkbox("Sort by distance (closest first)", value=False)
                    hide_stale_trials = st.checkbox("Hide trials not updated in >1 year", value=False)
                with col_f2:
                    st.write("**Filter by Phase:**")
                    phase_col1, phase_col2 = st.columns(2)
                    with phase_col1:
                        include_phase_1 = st.checkbox("Phase 1", value=True)
                        include_phase_2 = st.checkbox("Phase 2", value=True)
                    with phase_col2:
                        include_phase_3 = st.checkbox("Phase 3", value=True)
                        include_phase_4 = st.checkbox("Phase 4", value=True)
                with col_f3:
                    st.write("**Distance Filter:**")
                    max_distance = st.slider("Max distance (miles)", 0, 500, 500, step=50,
                                           help="Many patients can't travel >100 miles weekly")

                # Form submit button
                submitted = st.form_submit_button("🔍 Find Matching Trials", type="primary")

            if submitted:
                # Save search parameters to URL for sharing
                query_params = {
                    "age": patient_age,
                    "sex": patient_sex,
                    "cancer": cancer_type,
                    "stage": cancer_stage,
                    "ecog": ecog_status,
                    "state": patient_state,
                    "prior_therapies": num_prior_therapies
                }

                # Add biomarkers if selected
                if has_egfr:
                    query_params["egfr"] = "1"
                if has_her2:
                    query_params["her2"] = "1"
                if has_alk:
                    query_params["alk"] = "1"

                # Update URL with search parameters
                st.query_params.update(query_params)

                # Generate shareable link
                # Build URL parameters string
                param_string = '&'.join([f'{k}={v}' for k,v in query_params.items() if v])
                st.info(f"📎 **Search saved to URL** - Bookmark or share this page")
                st.code(f"?{param_string}", language=None)
                st.caption("The URL now contains your search parameters - copy the entire URL from your browser to share")

                # Search logic
                st.subheader(f"Matching Trials for {patient_age}yo {patient_sex} with {cancer_type}")

                matching_trials = trials_df.copy()

                # Filter by recruiting status if requested
                if show_recruiting_only:
                    matching_trials = matching_trials[matching_trials["status"] == "RECRUITING"]
                    st.info(f"Filtering to {len(matching_trials)} actively recruiting trials")

                # Filter by phase if requested
                allowed_phases = []
                if include_phase_1:
                    allowed_phases.extend(["Phase 1", "Phase 1/Phase 2"])
                if include_phase_2:
                    allowed_phases.extend(["Phase 2", "Phase 1/Phase 2", "Phase 2/Phase 3"])
                if include_phase_3:
                    allowed_phases.extend(["Phase 3", "Phase 2/Phase 3", "Phase 3/Phase 4"])
                if include_phase_4:
                    allowed_phases.extend(["Phase 4", "Phase 3/Phase 4"])

                if allowed_phases:
                    # Get phase from clinical_df if available, otherwise use trials_df phase
                    if clinical_data_available and clinical_df is not None:
                        matching_trials = matching_trials.merge(
                            clinical_df[["trial_id", "phase"]],
                            on="trial_id",
                            how="left",
                            suffixes=("", "_clinical")
                        )
                        # Use clinical phase if available
                        matching_trials["phase_filter"] = matching_trials["phase_clinical"].fillna(matching_trials["phase"])
                    else:
                        matching_trials["phase_filter"] = matching_trials["phase"]

                    matching_trials = matching_trials[matching_trials["phase_filter"].isin(allowed_phases)]
                    st.info(f"Phase filter: {len(matching_trials)} trials match selected phases")

                # Filter out stale trials if requested
                if hide_stale_trials:
                    from datetime import datetime, timedelta
                    one_year_ago = datetime.now() - timedelta(days=365)

                    # Filter using last_updated field
                    before_filter = len(matching_trials)
                    matching_trials = matching_trials[matching_trials["last_updated"].apply(
                        lambda x: datetime.strptime(x, "%Y-%m-%d") >= one_year_ago if pd.notna(x) else True
                    )]
                    filtered_count = before_filter - len(matching_trials)
                    if filtered_count > 0:
                        st.info(f"🕒 Excluded {filtered_count} stale trials (not updated in >1 year)")

                # Build patient biomarker profile for auto-exclusion
                patient_biomarkers = []
                if has_egfr:
                    patient_biomarkers.append("egfr")
                if has_alk:
                    patient_biomarkers.append("alk")
                if has_ros1:
                    patient_biomarkers.append("ros1")
                if has_her2:
                    patient_biomarkers.append("her2")
                if has_brca:
                    patient_biomarkers.append("brca")
                if has_pdl1:
                    patient_biomarkers.append("pdl1")
                if has_msi_h:
                    patient_biomarkers.append("msi")
                if has_mmr_def:
                    patient_biomarkers.append("mmr")
                if has_idh:
                    patient_biomarkers.append("idh")
                if has_mgmt:
                    patient_biomarkers.append("mgmt")

                # Auto-exclude trials based on patient conditions, ECOG, biomarkers, and prior lines
                excluded_count = 0
                trials_to_exclude = []
                exclusion_reasons = {}  # Track why each trial was excluded

                # Check condition-based exclusions
                if has_brain_mets or has_autoimmune or has_prior_immunotherapy or has_hiv or has_hepatitis or ecog_status or num_prior_therapies > 0 or patient_biomarkers:
                    # Get enhanced eligibility data
                    if "exclusion_text" in eligibility_df.columns:
                        for trial_id in matching_trials["trial_id"]:
                            elig_data = eligibility_df[eligibility_df["trial_id"] == trial_id]
                            if not elig_data.empty:
                                elig_row = elig_data.iloc[0]

                                # Check brain mets exclusion
                                if has_brain_mets and elig_row.get("brain_mets_excluded") == True:
                                    trials_to_exclude.append(trial_id)
                                    exclusion_reasons[trial_id] = "Brain metastases not allowed"
                                    continue

                                # Check autoimmune exclusion
                                if has_autoimmune and elig_row.get("autoimmune_excluded") == True:
                                    trials_to_exclude.append(trial_id)
                                    exclusion_reasons[trial_id] = "Autoimmune disease not allowed"
                                    continue

                                # Check prior immunotherapy exclusion
                                if has_prior_immunotherapy and elig_row.get("prior_immunotherapy_excluded") == True:
                                    trials_to_exclude.append(trial_id)
                                    exclusion_reasons[trial_id] = "Prior immunotherapy not allowed"
                                    continue

                                # Check HIV exclusion
                                if has_hiv and elig_row.get("hiv_excluded") == True:
                                    trials_to_exclude.append(trial_id)
                                    exclusion_reasons[trial_id] = "HIV not allowed"
                                    continue

                                # Check hepatitis exclusion
                                if has_hepatitis and elig_row.get("hepatitis_excluded") == True:
                                    trials_to_exclude.append(trial_id)
                                    exclusion_reasons[trial_id] = "Hepatitis not allowed"
                                    continue

                                # Check ECOG exclusion
                                if ecog_status and ecog_status != "":
                                    patient_ecog = int(ecog_status)
                                    trial_max_ecog = elig_row.get("max_ecog")
                                    if pd.notna(trial_max_ecog) and patient_ecog > trial_max_ecog:
                                        trials_to_exclude.append(trial_id)
                                        exclusion_reasons[trial_id] = f"ECOG {patient_ecog} exceeds trial max of {int(trial_max_ecog)}"
                                        continue

                                # Check prior lines exclusion
                                if num_prior_therapies > 0:
                                    trial_prior_limit = elig_row.get("prior_lines_limit")
                                    if pd.notna(trial_prior_limit) and num_prior_therapies > trial_prior_limit:
                                        trials_to_exclude.append(trial_id)
                                        exclusion_reasons[trial_id] = f"{num_prior_therapies} prior therapies exceeds trial max of {int(trial_prior_limit)}"
                                        continue

                                # Check biomarker mismatch - exclude trials requiring different biomarkers
                                if patient_biomarkers:
                                    trial_biomarkers = elig_row.get("biomarker_requirements")
                                    if trial_biomarkers and isinstance(trial_biomarkers, dict):
                                        # Check if trial requires a biomarker the patient doesn't have
                                        biomarker_mismatch = False

                                        # EGFR check
                                        if trial_biomarkers.get('egfr_mutation') and not has_egfr:
                                            biomarker_mismatch = True
                                        # ALK check
                                        if trial_biomarkers.get('alk_rearrangement') and not has_alk:
                                            biomarker_mismatch = True
                                        # ROS1 check
                                        if trial_biomarkers.get('ros1_rearrangement') and not has_ros1:
                                            biomarker_mismatch = True
                                        # HER2 check
                                        if trial_biomarkers.get('her2_status') == 'Positive' and not has_her2:
                                            biomarker_mismatch = True
                                        # BRCA check
                                        if trial_biomarkers.get('brca_mutation') and not has_brca:
                                            biomarker_mismatch = True
                                        # MSI check
                                        if trial_biomarkers.get('msi_status') and not has_msi_h:
                                            biomarker_mismatch = True
                                        # MMR check
                                        if trial_biomarkers.get('mmr_status') and not has_mmr_def:
                                            biomarker_mismatch = True
                                        # IDH check
                                        if trial_biomarkers.get('idh_mutation') and not has_idh:
                                            biomarker_mismatch = True
                                        # MGMT check
                                        if trial_biomarkers.get('mgmt_methylated') and not has_mgmt:
                                            biomarker_mismatch = True
                                        # PD-L1 check
                                        if (trial_biomarkers.get('pdl1_required') or trial_biomarkers.get('pdl1_cutoff')) and not has_pdl1:
                                            biomarker_mismatch = True

                                        if biomarker_mismatch:
                                            trials_to_exclude.append(trial_id)
                                            # Track which biomarker caused mismatch
                                            mismatched = []
                                            if trial_biomarkers.get('egfr_mutation') and not has_egfr:
                                                mismatched.append("EGFR")
                                            if trial_biomarkers.get('her2_status') == 'Positive' and not has_her2:
                                                mismatched.append("HER2+")
                                            if trial_biomarkers.get('alk_rearrangement') and not has_alk:
                                                mismatched.append("ALK")
                                            exclusion_reasons[trial_id] = f"Requires {', '.join(mismatched)} biomarker(s)"
                                            continue

                # Exclude trials
                if trials_to_exclude:
                    matching_trials = matching_trials[~matching_trials["trial_id"].isin(trials_to_exclude)]
                    excluded_count = len(trials_to_exclude)

                if excluded_count > 0:
                    st.warning(f"⚠️ Auto-excluded {excluded_count} trials based on patient conditions, ECOG, biomarkers, or prior therapies")

                    # Show details of what was excluded
                    with st.expander(f"View excluded trials ({excluded_count})", expanded=False):
                        for trial_id, reason in exclusion_reasons.items():
                            trial_title = trials_df[trials_df["trial_id"] == trial_id]["title"].iloc[0] if not trials_df[trials_df["trial_id"] == trial_id].empty else "Unknown"
                            st.markdown(f"**{trial_id}**: {trial_title[:80]}...")
                            st.caption(f"❌ Reason: {reason}")
                            st.markdown("---")

                match_scores = []

                # Age matching
                eligibility_with_age = eligibility_df.merge(matching_trials[["trial_id"]], on="trial_id")
                for _, trial_row in matching_trials.iterrows():
                    score = 0
                    reasons = []

                    # Check age eligibility
                    elig_row = eligibility_with_age[eligibility_with_age["trial_id"] == trial_row["trial_id"]]
                    if not elig_row.empty:
                        min_age = elig_row.iloc[0].get("min_age")
                        max_age = elig_row.iloc[0].get("max_age")

                        if pd.notna(min_age) and patient_age >= min_age:
                            score += 20
                            reasons.append(f"✅ Age {patient_age} >= minimum {min_age}")
                        elif pd.notna(min_age) and patient_age < min_age:
                            score -= 50
                            reasons.append(f"❌ Age {patient_age} < minimum {min_age}")

                        if pd.notna(max_age) and patient_age <= max_age:
                            score += 20
                        elif pd.notna(max_age) and patient_age > max_age:
                            score -= 50
                            reasons.append(f"❌ Age {patient_age} > maximum {max_age}")

                    # Check cancer type in eligibility text and conditions
                    if cancer_type:
                        elig_text = str(trial_row.get("eligibility_text", "")).lower()
                        if cancer_type.lower() in elig_text:
                            score += 30
                            reasons.append(f"✅ Cancer type '{cancer_type}' found in eligibility")

                        # Check in conditions if available
                        if clinical_data_available:
                            clinical_row = clinical_df[clinical_df["trial_id"] == trial_row["trial_id"]]
                            if not clinical_row.empty:
                                conditions = clinical_row.iloc[0].get("conditions", [])
                                if any(cancer_type.lower() in str(c).lower() for c in conditions):
                                    score += 40
                                    reasons.append(f"✅ Cancer type matches trial condition")

                    # Check biomarkers (patient_biomarkers already built earlier)
                    if patient_biomarkers:
                        elig_text = str(trial_row.get("eligibility_text", "")).lower()
                        for biomarker in patient_biomarkers:
                            if biomarker in elig_text:
                                score += 25
                                reasons.append(f"✅ {biomarker.upper()} biomarker matches")

                    # Check stage
                    if cancer_stage:
                        elig_text = str(trial_row.get("eligibility_text", "")).lower()
                        if cancer_stage.lower() in elig_text or (cancer_stage == "IV" and "metastatic" in elig_text):
                            score += 20
                            reasons.append(f"✅ Stage '{cancer_stage}' mentioned")

                    # Check location
                    if patient_state and clinical_data_available and locations_df is not None:
                        trial_locations = locations_df[locations_df["trial_id"] == trial_row["trial_id"]]
                        if not trial_locations.empty:
                            if any(patient_state.lower() in str(loc).lower() for loc in trial_locations["state"]):
                                score += 15
                                reasons.append(f"✅ Trial sites in {patient_state}")

                    # Check recruiting status
                    if trial_row.get("status") == "RECRUITING":
                        score += 10
                        reasons.append("✅ Currently recruiting")

                    match_scores.append({
                        "trial_id": trial_row["trial_id"],
                        "title": trial_row["title"],
                        "phase": trial_row["phase"],
                        "status": trial_row["status"],
                        "match_score": score,
                        "reasons": reasons,
                    })

                # Sort by recruiting status first, then match score
                match_df = pd.DataFrame(match_scores)

                # Calculate distances for each trial if patient location provided
                if patient_state and clinical_data_available and locations_df is not None:
                    patient_lat, patient_lon = geocode_location(state=patient_state)
                    if patient_lat and patient_lon:
                        match_df["min_distance"] = 9999  # default
                        for idx, row in match_df.iterrows():
                            trial_locs = locations_df[locations_df["trial_id"] == row["trial_id"]]
                            recruiting = trial_locs[trial_locs["status"] == "RECRUITING"]
                            if not recruiting.empty:
                                min_dist = 9999
                                for _, loc in recruiting.iterrows():
                                    if pd.notna(loc.get('latitude')) and pd.notna(loc.get('longitude')):
                                        dist = haversine_distance(patient_lat, patient_lon, loc['latitude'], loc['longitude'])
                                        min_dist = min(min_dist, dist)
                                match_df.at[idx, "min_distance"] = min_dist

                        # Apply distance filter
                        if max_distance < 500:
                            before_filter = len(match_df)
                            match_df = match_df[match_df["min_distance"] <= max_distance]
                            filtered_count = before_filter - len(match_df)
                            if filtered_count > 0:
                                st.info(f"📍 Distance filter: Excluded {filtered_count} trials beyond {max_distance} miles")

                # Add recruiting priority (1 for recruiting, 0 for others)
                match_df["is_recruiting"] = (match_df["status"] == "RECRUITING").astype(int)

                # Sort based on user preference
                if sort_by_distance and "min_distance" in match_df.columns:
                    # Sort by distance first, then recruiting, then score
                    match_df = match_df.sort_values(["min_distance", "is_recruiting", "match_score"],
                                                     ascending=[True, False, False])
                else:
                    # Original sorting: recruiting first, then score
                    match_df = match_df.sort_values(["is_recruiting", "match_score"],
                                                     ascending=[False, False])

                # Filter to positive matches
                positive_matches = match_df[match_df["match_score"] > 0]

                # Show results summary at top
                initial_count = len(trials_df)
                st.info(f"📊 **Results Summary**: Showing {len(positive_matches)} trials (auto-excluded {excluded_count} incompatible trials from {initial_count} total)")

                if len(positive_matches) == 0:
                    st.warning("⚠️ No matching trials found.")

                    # Provide relaxed criteria suggestions
                    st.info("💡 **Suggestions to find more trials:**")
                    suggestions = []

                    # Check what filters are currently applied
                    if show_recruiting_only:
                        # Count trials without recruiting filter
                        all_status_trials = trials_df[
                            (trials_df["status"].isin(["RECRUITING", "NOT_YET_RECRUITING", "ENROLLING_BY_INVITATION"]))
                        ]
                        if len(all_status_trials) > len(matching_trials):
                            suggestions.append(f"- **{len(all_status_trials) - len(matching_trials)} trials** if you include 'Not Yet Recruiting' and 'Enrolling by Invitation' statuses")

                    # Check phase filters
                    excluded_phases = []
                    if not include_phase_1:
                        excluded_phases.append("Phase 1")
                    if not include_phase_2:
                        excluded_phases.append("Phase 2")
                    if not include_phase_3:
                        excluded_phases.append("Phase 3")
                    if not include_phase_4:
                        excluded_phases.append("Phase 4")

                    if excluded_phases:
                        for phase_name in excluded_phases:
                            phase_trials = trials_df[trials_df["phase"].str.contains(phase_name, case=False, na=False)]
                            if len(phase_trials) > 0:
                                suggestions.append(f"- **{len(phase_trials)} trials** if you include {phase_name}")

                    # Check if distance filter is limiting results
                    if max_distance < 500 and patient_state:
                        suggestions.append(f"- Try increasing max distance beyond {max_distance} miles")

                    # Check if auto-exclusions are limiting results
                    if excluded_count > 0:
                        suggestions.append(f"- **{excluded_count} trials were auto-excluded** due to patient conditions, ECOG, biomarkers, or prior therapies - review if any exclusions can be relaxed")

                    if suggestions:
                        for suggestion in suggestions:
                            st.markdown(suggestion)
                    else:
                        st.markdown("- Try broadening your cancer type search or reducing specific criteria")
                else:
                    st.success(f"Found {len(positive_matches)} matching trials")

                    # Initialize session state for trial comparison
                    if "selected_trials" not in st.session_state:
                        st.session_state.selected_trials = []

                    # Show comparison and print buttons if trials selected
                    if len(st.session_state.selected_trials) > 0:
                        col_btn1, col_btn2, col_btn3 = st.columns(3)
                        with col_btn1:
                            st.info(f"📋 {len(st.session_state.selected_trials)} trials selected")
                        with col_btn2:
                            if st.button("🔀 Compare Selected"):
                                st.session_state.show_comparison = True
                        with col_btn3:
                            if st.button("🖨️ Generate Patient Handout"):
                                # Generate print-friendly summary
                                st.markdown("---")
                                st.markdown("## 📄 Patient Handout")
                                st.caption(f"Generated: {datetime.now().strftime('%B %d, %Y')}")
                                st.markdown(f"**Patient**: {patient_age}yo {patient_sex} with {cancer_type}")
                                st.markdown(f"**Location**: {patient_state if patient_state else 'Not specified'}")

                                for trial_id in st.session_state.selected_trials[:3]:  # Limit to top 3
                                    trial_info = positive_matches[positive_matches["trial_id"] == trial_id]
                                    if not trial_info.empty:
                                        st.markdown(f"### {trial_id}")
                                        st.markdown(f"**{trial_info.iloc[0]['title'][:150]}...**")

                                        # Get contact info
                                        if locations_df is not None:
                                            locs = locations_df[(locations_df["trial_id"] == trial_id) &
                                                              (locations_df["status"] == "RECRUITING")]
                                            if not locs.empty:
                                                closest = locs.iloc[0]
                                                st.markdown(f"**Nearest Site**: {closest['facility']}, {closest['city']}, {closest['state']}")
                                                if pd.notna(closest.get('contact_phone')):
                                                    st.markdown(f"**Phone**: {closest['contact_phone']}")

                                        st.markdown(f"🔗 https://clinicaltrials.gov/study/{trial_id}")
                                        st.markdown("")

                                st.info("💡 Print this page using Ctrl+P (or Cmd+P on Mac)")

                    # Add pagination for better performance
                    items_per_page = 10
                    if "page_num" not in st.session_state:
                        st.session_state.page_num = 0

                    total_pages = (len(positive_matches) - 1) // items_per_page + 1

                    # Pagination controls
                    col_prev, col_info, col_next = st.columns([1, 3, 1])
                    with col_prev:
                        if st.button("← Previous", disabled=st.session_state.page_num == 0):
                            st.session_state.page_num -= 1
                            st.rerun()
                    with col_info:
                        st.write(f"Page {st.session_state.page_num + 1} of {total_pages} ({len(positive_matches)} trials)")
                    with col_next:
                        if st.button("Next →", disabled=st.session_state.page_num >= total_pages - 1):
                            st.session_state.page_num += 1
                            st.rerun()

                    # Show paginated results
                    start_idx = st.session_state.page_num * items_per_page
                    end_idx = min(start_idx + items_per_page, len(positive_matches))

                    for idx, match in positive_matches.iloc[start_idx:end_idx].iterrows():
                        # Get enhanced eligibility data
                        elig_data = eligibility_df[eligibility_df["trial_id"] == match["trial_id"]]
                        has_enhanced = not elig_data.empty and "treatment_line" in elig_data.columns

                        # Build title with badges including distance
                        title_badges = []
                        if match['status'] == 'RECRUITING':
                            title_badges.append("🟢 RECRUITING")
                        if has_enhanced:
                            treatment_line = elig_data.iloc[0].get("treatment_line", "")
                            if treatment_line and treatment_line != "Any line":
                                title_badges.append(f"📋 {treatment_line}")

                        # Add closest site distance to title if available
                        if clinical_data_available and locations_df is not None and patient_state:
                            trial_locs = locations_df[locations_df["trial_id"] == match["trial_id"]]
                            recruiting = trial_locs[trial_locs["status"] == "RECRUITING"]
                            if not recruiting.empty:
                                patient_lat, patient_lon = geocode_location(state=patient_state)
                                if patient_lat and patient_lon:
                                    min_distance = 9999
                                    for _, loc in recruiting.iterrows():
                                        if pd.notna(loc.get('latitude')) and pd.notna(loc.get('longitude')):
                                            dist = haversine_distance(patient_lat, patient_lon, loc['latitude'], loc['longitude'])
                                            min_distance = min(min_distance, dist)
                                    if min_distance < 9000:
                                        title_badges.append(f"📍 {int(min_distance)} mi")

                        badge_str = " | ".join(title_badges) if title_badges else ""
                        expander_title = f"{'🟢' if match['match_score'] >= 50 else '🟡'} {match['trial_id']}: {match['title'][:80]}... {badge_str} (Score: {match['match_score']})"

                        # Add checkbox for comparison
                        col_check, col_title = st.columns([1, 11])
                        with col_check:
                            is_selected = st.checkbox("", key=f"select_{match['trial_id']}",
                                                     value=match['trial_id'] in st.session_state.selected_trials,
                                                     help="Select for comparison")
                            if is_selected and match['trial_id'] not in st.session_state.selected_trials:
                                st.session_state.selected_trials.append(match['trial_id'])
                            elif not is_selected and match['trial_id'] in st.session_state.selected_trials:
                                st.session_state.selected_trials.remove(match['trial_id'])

                        with col_title:
                            with st.expander(expander_title):
                                # Generate plain English fit assessment
                                good_fit_reasons = []
                                caution_reasons = []
                                poor_fit_reasons = []

                                # Analyze fit based on score and conditions
                                if match['match_score'] >= 70:
                                    good_fit_reasons.append("High match score")
                                if match['status'] == 'RECRUITING':
                                    good_fit_reasons.append("Actively recruiting")

                                # Check distance if available
                                if "📍" in badge_str:
                                    dist_match = re.search(r"📍 (\d+) mi", badge_str)
                                    if dist_match:
                                        distance = int(dist_match.group(1))
                                        if distance <= 50:
                                            good_fit_reasons.append(f"Close to home ({distance} miles)")
                                        elif distance <= 200:
                                            caution_reasons.append(f"Moderate distance ({distance} miles)")
                                        else:
                                            poor_fit_reasons.append(f"Far from home ({distance} miles)")

                                # Check for Phase 1 dose escalation risk
                                if "Phase 1" in match.get('phase', ''):
                                    caution_reasons.append("Phase 1 trial (higher risk, more visits)")

                                # Check exclusion reasons
                                for reason in match.get('reasons', []):
                                    if "❌" in reason:
                                        poor_fit_reasons.append(reason.replace("❌", "").strip())

                                # Display fit assessment prominently
                                if good_fit_reasons and not poor_fit_reasons:
                                    st.success(f"✅ **Good fit**: {', '.join(good_fit_reasons)}")
                                elif caution_reasons and not poor_fit_reasons:
                                    st.warning(f"⚠️ **Caution**: {', '.join(caution_reasons)}")
                                elif poor_fit_reasons:
                                    st.error(f"❌ **Poor fit**: {', '.join(poor_fit_reasons[:2])}")

                                # Add better copy functionality and ClinicalTrials.gov link
                                col_nct1, col_nct2, col_nct3 = st.columns([2, 2, 3])
                                with col_nct1:
                                    # Simple text display for easy copying
                                    st.code(match['trial_id'], language=None)
                                with col_nct2:
                                    st.caption("↑ Click to select & copy")
                                with col_nct3:
                                    st.markdown(f"🔗 [View on ClinicalTrials.gov](https://clinicaltrials.gov/study/{match['trial_id']})")
                                st.markdown("---")
                            # Get clinical details
                            clinical_info = None
                            if clinical_data_available and clinical_df is not None:
                                clinical_info_df = clinical_df[clinical_df["trial_id"] == match["trial_id"]]
                                if not clinical_info_df.empty:
                                    clinical_info = clinical_info_df.iloc[0]

                            # Show phase, study design, and comparator
                            if clinical_info is not None:
                                phase = clinical_info.get("phase", match['phase'])
                                study_design = clinical_info.get("study_design", "")
                                is_combination = clinical_info.get("is_combination", False)
                                therapy_type = "Combination therapy" if is_combination else "Monotherapy"

                                st.markdown(f"**Phase**: {phase} | **Study Design**: {study_design} | **Type**: {therapy_type}")

                                # Add critical clinical information for Phase 1 trials
                                if "Phase 1" in phase or "PHASE1" in phase.upper():
                                    # Show dose escalation vs expansion status
                                    cohort_info = clinical_info.get("cohort_type", "")
                                    if cohort_info:
                                        if "Escalation" in cohort_info:
                                            st.warning(f"⚠️ **{cohort_info}** - Higher risk, frequent visits, dose finding")
                                        elif "Expansion" in cohort_info:
                                            st.info(f"ℹ️ **{cohort_info}** - Established dose, safety known")

                                # Show randomization ratio if available
                                randomization_ratio = clinical_info.get("randomization_ratio")
                                if randomization_ratio:
                                    st.markdown(f"**Randomization**: {randomization_ratio} (drug:placebo)")

                                # Show crossover information if available
                                crossover_allowed = clinical_info.get("crossover_allowed")
                                if crossover_allowed is not None:
                                    if crossover_allowed:
                                        st.success("✅ **Crossover allowed** - Placebo patients can receive drug if they progress")
                                    else:
                                        st.warning("❌ **No crossover** - Placebo patients cannot switch to drug")

                                st.markdown(f"**Status**: {match['status']}")

                                # Show age range prominently
                                if has_enhanced and elig_data is not None:
                                    min_age = elig_data.iloc[0].get("min_age")
                                    max_age = elig_data.iloc[0].get("max_age")
                                    age_range_parts = []
                                    if pd.notna(min_age):
                                        age_range_parts.append(f"Min: {int(min_age)}")
                                    if pd.notna(max_age):
                                        age_range_parts.append(f"Max: {int(max_age)}")
                                    if age_range_parts:
                                        st.markdown(f"**Age Range**: {' | '.join(age_range_parts)} years")

                                # Show enrollment, completion date and last updated
                                enrollment = match.get('enrollment')
                                enrollment_type = match.get('enrollment_type', '')
                                last_updated = match.get('last_updated', '')
                                completion_date = match.get('completion_date', '')

                                info_parts = []
                                if pd.notna(enrollment):
                                    enroll_str = f"Target Enrollment: {int(enrollment)}"
                                    if enrollment_type == "ACTUAL":
                                        enroll_str = f"Current Enrollment: {int(enrollment)} (Actual)"
                                        # Add warning if nearly full
                                        target_enrollment = clinical_info.get("enrollment", enrollment) if clinical_info is not None else enrollment
                                        if pd.notna(target_enrollment) and enrollment >= target_enrollment * 0.95:
                                            remaining = int(target_enrollment - enrollment)
                                            if remaining <= 20:
                                                enroll_str += f" ⚠️ NEARLY FULL - {remaining} slots remaining"
                                    info_parts.append(enroll_str)

                                if pd.notna(completion_date) and completion_date:
                                    try:
                                        comp_date = datetime.strptime(completion_date, "%Y-%m-%d")
                                        info_parts.append(f"Est. Completion: {comp_date.strftime('%b %Y')}")
                                    except:
                                        info_parts.append(f"Est. Completion: {completion_date}")

                                if pd.notna(last_updated) and last_updated:
                                    # Calculate staleness
                                    from datetime import datetime
                                    try:
                                        update_date = datetime.strptime(last_updated, "%Y-%m-%d")
                                        days_since = (datetime.now() - update_date).days
                                        if days_since > 365:
                                            info_parts.append(f"⚠️ Last updated: {last_updated} ({days_since} days ago - may be stale)")
                                        else:
                                            info_parts.append(f"Last updated: {last_updated}")
                                    except:
                                        info_parts.append(f"Last updated: {last_updated}")

                                if info_parts:
                                    st.markdown(" | ".join(info_parts))

                                # Show sponsor
                                sponsor_class = clinical_info.get("sponsor_class", "")
                                sponsor_name = clinical_info.get("sponsor_name", "")
                                if sponsor_name:
                                    st.markdown(f"**Sponsor**: {sponsor_name} ({sponsor_class})")

                                # Show primary endpoint
                                primary_outcomes = clinical_info.get("primary_outcomes", [])
                                if isinstance(primary_outcomes, (list, tuple)) and len(primary_outcomes) > 0:
                                    st.markdown(f"**Primary Endpoint**: {primary_outcomes[0]}")
                                elif hasattr(primary_outcomes, '__len__') and len(primary_outcomes) > 0:
                                    st.markdown(f"**Primary Endpoint**: {primary_outcomes[0]}")

                                # Show comparator/control arms
                                arms = clinical_info.get("arms", [])
                                if isinstance(arms, (list, tuple)) and len(arms) > 0:
                                    st.markdown("**Treatment Arms:**")
                                    for arm in arms:
                                        arm_label = arm.get('label', '')
                                        arm_type = arm.get('type', '').replace('_', ' ').title()
                                        st.markdown(f"- {arm_label} ({arm_type})")
                            else:
                                st.markdown(f"**Phase**: {match['phase']} | **Status**: {match['status']}")

                            # Separate match reasons into exclusions vs inclusions
                            match_reasons = []
                            exclusion_reasons = []
                            for reason in match['reasons']:
                                if "❌" in reason or "excluded" in reason.lower():
                                    exclusion_reasons.append(reason)
                                else:
                                    match_reasons.append(reason)

                            # Show exclusions prominently at top if any
                            if exclusion_reasons:
                                st.error("**⚠️ EXCLUSION CRITERIA:**")
                                for reason in exclusion_reasons:
                                    st.markdown(f"- {reason}")
                                st.markdown("---")

                            # Show match reasons
                            if match_reasons:
                                st.markdown("**✅ Match Reasons:**")
                                for reason in match_reasons:
                                    st.markdown(f"- {reason}")

                            # Show treatment line requirements and limits
                            if has_enhanced:
                                treatment_line = elig_data.iloc[0].get("treatment_line", "")
                                prior_required = elig_data.iloc[0].get("prior_therapy_required", False)
                                naive_allowed = elig_data.iloc[0].get("treatment_naive_allowed", True)
                                prior_lines_limit = elig_data.iloc[0].get("prior_lines_limit")
                                washout_period = elig_data.iloc[0].get("washout_period")

                                if treatment_line != "Any line":
                                    st.markdown(f"**Treatment Line**: {treatment_line}")
                                    if prior_required:
                                        st.markdown("⚠️ Prior therapy required")
                                    if naive_allowed:
                                        st.markdown("✅ Treatment-naive patients allowed")

                                if pd.notna(prior_lines_limit):
                                    st.markdown(f"**Prior Lines Limit**: ≤{int(prior_lines_limit)} prior therapies allowed")

                                if pd.notna(washout_period) and washout_period:
                                    st.markdown(f"**Washout Period**: {washout_period} required since last therapy")

                            # Show biomarker requirements
                            if has_enhanced:
                                biomarkers = elig_data.iloc[0].get("biomarker_requirements", {})
                                if biomarkers and isinstance(biomarkers, dict) and any(v for v in biomarkers.values() if v):
                                    st.markdown("**Biomarker Requirements:**")
                                    if biomarkers.get('pdl1_cutoff'):
                                        st.markdown(f"- PD-L1 expression {biomarkers['pdl1_cutoff']}")
                                    if biomarkers.get('her2_status'):
                                        st.markdown(f"- HER2 {biomarkers['her2_status']}")
                                    if biomarkers.get('egfr_mutation'):
                                        if biomarkers.get('egfr_specific'):
                                            st.markdown(f"- EGFR {biomarkers['egfr_specific']} mutation")
                                        else:
                                            st.markdown(f"- EGFR mutation required")
                                    if biomarkers.get('alk_rearrangement'):
                                        st.markdown(f"- ALK rearrangement required")
                                    if biomarkers.get('ros1_rearrangement'):
                                        st.markdown(f"- ROS1 rearrangement required")
                                    if biomarkers.get('brca_mutation'):
                                        st.markdown(f"- BRCA mutation required")
                                    if biomarkers.get('msi_status'):
                                        st.markdown(f"- MSI status: {biomarkers['msi_status']}")
                                    if biomarkers.get('mmr_status'):
                                        st.markdown(f"- MMR status: {biomarkers['mmr_status']}")
                                    if biomarkers.get('tmb_cutoff'):
                                        st.markdown(f"- TMB {biomarkers['tmb_cutoff']}")
                                    if biomarkers.get('idh_mutation'):
                                        st.markdown(f"- IDH mutation required")
                                    if biomarkers.get('mgmt_methylated'):
                                        st.markdown(f"- MGMT methylation required")

                            # Show required tests
                            if has_enhanced:
                                required_tests = elig_data.iloc[0].get("required_tests", [])
                                if isinstance(required_tests, (list, tuple)) and len(required_tests) > 0:
                                    st.markdown("**Required Tests/Procedures:**")
                                    for test in required_tests:
                                        st.markdown(f"- {test}")

                            # Show common exclusions
                            if has_enhanced:
                                exclusions = []
                                brain_mets = elig_data.iloc[0].get("brain_mets_excluded")
                                if brain_mets == True:
                                    exclusions.append("❌ Brain metastases excluded")
                                elif brain_mets == False:
                                    exclusions.append("✅ Brain metastases allowed")

                                if elig_data.iloc[0].get("prior_immunotherapy_excluded"):
                                    exclusions.append("❌ Prior immunotherapy excluded")
                                if elig_data.iloc[0].get("autoimmune_excluded"):
                                    exclusions.append("❌ Autoimmune disease excluded")
                                if elig_data.iloc[0].get("hiv_excluded"):
                                    exclusions.append("❌ HIV excluded")

                                if exclusions:
                                    st.markdown("**Common Exclusions:**")
                                    for exclusion in exclusions:
                                        st.markdown(f"- {exclusion}")

                            # Show inclusion/exclusion criteria separately
                            if has_enhanced:
                                inclusion_text = elig_data.iloc[0].get("inclusion_text", "")
                                exclusion_text = elig_data.iloc[0].get("exclusion_text", "")

                                if inclusion_text:
                                    with st.expander("📋 View Inclusion Criteria"):
                                        st.markdown(f'<div style="background-color: rgba(76, 175, 80, 0.1); padding: 10px; border-radius: 5px; border-left: 3px solid #4CAF50;">{inclusion_text[:500]}...</div>', unsafe_allow_html=True)

                                if exclusion_text:
                                    with st.expander("⛔ View Exclusion Criteria"):
                                        st.markdown(f'<div style="background-color: rgba(244, 67, 54, 0.1); padding: 10px; border-radius: 5px; border-left: 3px solid #F44336;">{exclusion_text[:500]}...</div>', unsafe_allow_html=True)

                            # Show interventions if available
                            if clinical_data_available and interventions_df is not None:
                                trial_interventions = interventions_df[interventions_df["trial_id"] == match["trial_id"]]
                                if not trial_interventions.empty:
                                    st.markdown("**Interventions:**")
                                    for _, intervention in trial_interventions.iterrows():
                                        st.markdown(f"- {intervention['type']}: {intervention['name']}")

                            # Show locations with contact info and distance
                            if clinical_data_available and locations_df is not None:
                                trial_locations = locations_df[locations_df["trial_id"] == match["trial_id"]].copy()
                                recruiting_sites = trial_locations[trial_locations["status"] == "RECRUITING"].copy()

                                # Calculate distances if patient location is provided
                                if patient_state and recruiting_sites is not None and not recruiting_sites.empty:
                                    patient_lat, patient_lon = geocode_location(state=patient_state)
                                    if patient_lat and patient_lon:
                                        distances = []
                                        for idx, loc in recruiting_sites.iterrows():
                                            site_lat = loc.get('latitude')
                                            site_lon = loc.get('longitude')
                                            if pd.notna(site_lat) and pd.notna(site_lon):
                                                dist = haversine_distance(patient_lat, patient_lon, site_lat, site_lon)
                                                distances.append(dist)
                                            else:
                                                distances.append(9999)  # Unknown distance
                                        recruiting_sites['distance'] = distances
                                        # Sort by distance
                                        recruiting_sites = recruiting_sites.sort_values('distance')

                                if not recruiting_sites.empty:
                                    # Get state breakdown
                                    state_counts = recruiting_sites['state'].value_counts()
                                    state_breakdown = []
                                    for state, count in state_counts.head(3).items():
                                        state_breakdown.append(f"{count} in {state}")
                                    if len(state_counts) > 3:
                                        other_count = state_counts.iloc[3:].sum()
                                        state_breakdown.append(f"{other_count} other states")
                                    state_summary = f" ({', '.join(state_breakdown)})" if state_breakdown else ""

                                    # Check if any sites have contact info
                                    has_contact = False
                                    for _, loc in recruiting_sites.iterrows():
                                        if pd.notna(loc.get('contact_phone')) or pd.notna(loc.get('contact_email')):
                                            has_contact = True
                                            break

                                    st.markdown(f"**🟢 Recruiting Sites** {len(recruiting_sites)} total{state_summary}{' ⚠️ NO CONTACT INFO' if not has_contact else ''}:")

                                    for _, loc in recruiting_sites.head(3).iterrows():
                                        distance_str = ""
                                        if 'distance' in loc and pd.notna(loc['distance']) and loc['distance'] < 9000:
                                            distance_str = f" - 📍 {int(loc['distance'])} miles"
                                        facility_info = f"**{loc['facility']}** - {loc['city']}, {loc['state']} {loc['zip']}{distance_str}"
                                        st.markdown(facility_info)
                                        if pd.notna(loc.get('contact_name')) or pd.notna(loc.get('contact_phone')):
                                            contact_parts = []
                                            if pd.notna(loc.get('contact_name')):
                                                # Assume contact name is PI unless it looks like a coordinator
                                                contact_name = loc['contact_name']
                                                if 'coordinator' in contact_name.lower() or 'nurse' in contact_name.lower():
                                                    contact_parts.append(f"Coordinator: {contact_name}")
                                                else:
                                                    contact_parts.append(f"PI/Contact: Dr. {contact_name}" if not contact_name.startswith('Dr.') else f"PI/Contact: {contact_name}")
                                            if pd.notna(loc.get('contact_phone')):
                                                # Make phone number clickable
                                                phone = loc['contact_phone'].strip()
                                                contact_parts.append(f"📞 <a href='tel:{phone}'>{phone}</a>")
                                            if pd.notna(loc.get('contact_email')):
                                                email = loc['contact_email'].strip()
                                                contact_parts.append(f"✉️ <a href='mailto:{email}'>{email}</a>")
                                            st.markdown("  " + " | ".join(contact_parts), unsafe_allow_html=True)
                                        else:
                                            st.markdown("  ⚠️ *No contact information available*")

                                    if len(recruiting_sites) > 3:
                                        st.markdown(f"  *...and {len(recruiting_sites) - 3} more recruiting sites*")

                                # Show non-recruiting sites separately if any
                                other_sites = trial_locations[trial_locations["status"] != "RECRUITING"]
                                if not other_sites.empty and len(recruiting_sites) < 3:
                                    remaining = 3 - len(recruiting_sites)
                                    st.markdown(f"**Other Sites** ({len(other_sites)}):")
                                    for _, loc in other_sites.head(remaining).iterrows():
                                        st.markdown(f"- {loc['facility']}, {loc['city']}, {loc['state']}")

                            # Add match quality visual indicator
                            st.markdown(add_match_quality_visual(match['match_score'], match.get('reasons', [])), unsafe_allow_html=True)

                            # Add all enhanced trial sections (safety, enrollment, financial, protocol, similar patients)
                            patient_profile_for_matching = {
                                "age": patient_age,
                                "cancer_type": cancer_type,
                                "stage": cancer_stage,
                                "ecog": ecog_status,
                                "state": patient_state
                            }
                            add_enhanced_trial_sections(match['trial_id'], match.to_dict(), patient_profile_for_matching)

                    # Prepare enhanced export data
                    export_data = positive_matches.copy()

                    # Add clinical details if available
                    if clinical_data_available and clinical_df is not None:
                        export_data = export_data.merge(
                            clinical_df[["trial_id", "phase", "study_design", "is_combination",
                                        "sponsor_name", "sponsor_class", "primary_outcomes"]],
                            on="trial_id",
                            how="left",
                            suffixes=("", "_clinical")
                        )
                        # Use clinical phase if available
                        if "phase_clinical" in export_data.columns:
                            export_data["phase"] = export_data["phase_clinical"].fillna(export_data["phase"])
                            export_data = export_data.drop(columns=["phase_clinical"])

                        # Convert primary_outcomes array to string
                        if "primary_outcomes" in export_data.columns:
                            export_data["primary_endpoint"] = export_data["primary_outcomes"].apply(
                                lambda x: x[0] if isinstance(x, (list, tuple)) and len(x) > 0 else ""
                            )
                            export_data = export_data.drop(columns=["primary_outcomes"])

                    # Add treatment line and age ranges if available
                    if "treatment_line" in eligibility_df.columns:
                        export_data = export_data.merge(
                            eligibility_df[["trial_id", "treatment_line", "prior_lines_limit",
                                          "washout_period", "min_age", "max_age"]].drop_duplicates(subset=["trial_id"]),
                            on="trial_id",
                            how="left"
                        )

                    # Add recruiting site contacts if available
                    if clinical_data_available and locations_df is not None:
                        # Get first recruiting site with contact for each trial
                        recruiting_contacts = locations_df[
                            (locations_df["status"] == "RECRUITING") &
                            (locations_df["contact_phone"].notna())
                        ].drop_duplicates(subset=["trial_id"]).copy()

                        recruiting_contacts["site_contact"] = (
                            recruiting_contacts["facility"] + " | " +
                            recruiting_contacts["city"] + ", " + recruiting_contacts["state"] + " | " +
                            recruiting_contacts["contact_name"].fillna("") + " | " +
                            recruiting_contacts["contact_phone"].fillna("")
                        )

                        export_data = export_data.merge(
                            recruiting_contacts[["trial_id", "site_contact"]],
                            on="trial_id",
                            how="left"
                        )

                    # Select relevant columns for export
                    export_cols = ["trial_id", "title", "phase", "status", "match_score"]
                    if "study_design" in export_data.columns:
                        export_cols.append("study_design")
                    if "sponsor_name" in export_data.columns:
                        export_cols.extend(["sponsor_name", "sponsor_class"])
                    if "primary_endpoint" in export_data.columns:
                        export_cols.append("primary_endpoint")
                    if "treatment_line" in export_data.columns:
                        export_cols.extend(["treatment_line", "prior_lines_limit", "washout_period"])
                    if "site_contact" in export_data.columns:
                        export_cols.append("site_contact")

                    # Filter to available columns
                    export_cols = [col for col in export_cols if col in export_data.columns]

                    csv = export_data[export_cols].to_csv(index=False).encode("utf-8")
                    st.download_button(
                        "📥 Download Matching Trials CSV (with clinical details & contacts)",
                        csv,
                        f"patient_matching_{cancer_type.replace(' ', '_')}_{patient_age}yo.csv",
                        "text/csv",
                        key="download_matches"
                    )

    # Tab 2: Explore
    with tab2:
        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            st.header("📊 Trial Explorer")

            # Filters in columns
            col1, col2, col3 = st.columns(3)

            with col1:
                phases = ["All"] + sorted(trials_df["phase"].dropna().unique().tolist())
                selected_phase = st.selectbox("Phase", phases)

            with col2:
                statuses = ["All"] + sorted(trials_df["status"].dropna().unique().tolist())
                selected_status = st.selectbox("Status", statuses)

            with col3:
                # Cluster filter if available
                if "cluster" in trials_df.columns:
                    clusters = ["All"] + sorted(trials_df["cluster"].dropna().unique().tolist())
                    selected_cluster = st.selectbox("Cluster", clusters)
                else:
                    selected_cluster = "All"

            # Apply filters
            filtered_df = trials_df.copy()
            if selected_phase != "All":
                filtered_df = filtered_df[filtered_df["phase"] == selected_phase]
            if selected_status != "All":
                filtered_df = filtered_df[filtered_df["status"] == selected_status]
            if selected_cluster != "All" and "cluster" in filtered_df.columns:
                filtered_df = filtered_df[filtered_df["cluster"] == selected_cluster]

            # Show results
            st.subheader(f"Results ({len(filtered_df)} trials)")

            # Display columns
            display_cols = [
                "trial_id",
                "title",
                "phase",
                "status",
                "enrollment",
                "start_date",
            ]
            if "cluster" in filtered_df.columns:
                display_cols.append("cluster")

            st.dataframe(
                filtered_df[display_cols],
                use_container_width=True,
                height=400,
            )

            # Export
            csv = filtered_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download CSV",
                csv,
                "filtered_trials.csv",
                "text/csv",
            )

    # Tab 3: Eligibility Explorer
    with tab3:
        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            st.header("🔍 Eligibility Criteria Explorer")

            # Search box
            search_terms = st.text_input(
                "Search eligibility criteria (comma-separated terms)",
                placeholder="e.g., metastatic, ECOG, liver",
            )

            if search_terms:
                terms = [t.strip() for t in search_terms.split(",")]

                # Search in eligibility text from trials table
                def matches_any_term(text):
                    if pd.isna(text):
                        return False
                    text_lower = str(text).lower()
                    return any(term.lower() in text_lower for term in terms)

                # Search in eligibility_text column
                trials_df["matches"] = trials_df["eligibility_text"].apply(matches_any_term)
                matching_df = trials_df[trials_df["matches"]].copy()

                # Merge with eligibility for additional details
                matching_df = matching_df.merge(eligibility_df, on="trial_id", how="left")

                st.subheader(f"Found {len(matching_df)} trials matching your search")

                # Export button
                csv = matching_df.to_csv(index=False).encode("utf-8")
                st.download_button(
                    "📥 Download Search Results CSV",
                    csv,
                    "eligibility_search_results.csv",
                    "text/csv",
                    key="download_eligibility",
                )

                # View mode selection
                view_mode = st.radio(
                    "View mode:",
                    ["Table View", "Detailed View (with highlighting)"],
                    horizontal=True,
                )

                if view_mode == "Table View":
                    # Show as dataframe
                    display_cols = ["trial_id", "title", "phase", "status", "enrollment"]
                    st.dataframe(
                        matching_df[display_cols],
                        use_container_width=True,
                        height=600,
                    )
                else:
                    # Detailed view with expanders
                    # Pagination
                    results_per_page = st.selectbox(
                        "Results per page:",
                        [10, 25, 50, 100, 200],
                        index=2,  # Default to 50
                    )

                    total_pages = (len(matching_df) - 1) // results_per_page + 1
                    page = st.number_input(
                        f"Page (1-{total_pages}):",
                        min_value=1,
                        max_value=total_pages,
                        value=1,
                    )

                    start_idx = (page - 1) * results_per_page
                    end_idx = start_idx + results_per_page

                    st.write(f"Showing results {start_idx + 1}-{min(end_idx, len(matching_df))} of {len(matching_df)}")

                    # Show paginated results
                    for _, row in matching_df.iloc[start_idx:end_idx].iterrows():
                        with st.expander(f"📄 {row['trial_id']}: {row['title'][:100]}..."):
                            st.markdown(f"**Phase**: {row['phase']} | **Status**: {row['status']}")

                            # Show eligibility text with highlighting
                            st.markdown("**Eligibility Criteria:**")
                            eligibility_text = str(row["eligibility_text"]) if pd.notna(row["eligibility_text"]) else "Not available"
                            highlighted_text = highlight_terms(eligibility_text, terms)
                            st.markdown(
                                f'<div style="background-color: rgba(128, 128, 128, 0.1); padding: 10px; '
                                f'border-radius: 5px; border: 1px solid rgba(128, 128, 128, 0.3);">{highlighted_text}</div>',
                                unsafe_allow_html=True,
                            )

                            # Show extracted key terms if available
                            if "key_inclusion_terms" in row.index:
                                try:
                                    key_terms = row["key_inclusion_terms"]
                                    if key_terms is not None and len(key_terms) > 0:
                                        st.markdown("**Key Inclusion Terms:**")
                                        st.write(", ".join(key_terms) if isinstance(key_terms, list) else str(key_terms))
                                except (TypeError, ValueError):
                                    pass

                            if "key_exclusion_terms" in row.index:
                                try:
                                    key_terms = row["key_exclusion_terms"]
                                    if key_terms is not None and len(key_terms) > 0:
                                        st.markdown("**Key Exclusion Terms:**")
                                        st.write(", ".join(key_terms) if isinstance(key_terms, list) else str(key_terms))
                                except (TypeError, ValueError):
                                    pass

            else:
                st.info("Enter search terms above to find trials with specific eligibility criteria.")

    # Tab 4: Risk Analysis
    with tab4:
        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            st.header("⚠️ Risk Analysis")

            # Merge trials with risks
            merged_risks = trials_df.merge(risks_df, on="trial_id", how="inner")

            # Summary statistics at the top
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Trials", len(merged_risks))
            with col2:
                st.metric("Mean Risk Score", f"{merged_risks['total_risk_score'].mean():.1f}")
            with col3:
                high_risk_count = len(merged_risks[merged_risks['total_risk_score'] >= 70])
                st.metric("High Risk (≥70)", high_risk_count)
            with col4:
                st.metric("Max Risk Score", f"{merged_risks['total_risk_score'].max():.1f}")

            st.divider()

            # Filters in sidebar-like columns
            st.subheader("🔍 Filters")
            col1, col2, col3 = st.columns(3)

            with col1:
                risk_threshold = st.slider(
                    "Minimum Risk Score",
                    min_value=0.0,
                    max_value=130.0,
                    value=0.0,
                    step=5.0,
                )

            with col2:
                phase_filter = st.multiselect(
                    "Phase",
                    options=sorted(merged_risks["phase"].dropna().unique().tolist()),
                    default=None,
                )

            with col3:
                status_filter = st.multiselect(
                    "Status",
                    options=sorted(merged_risks["status"].dropna().unique().tolist()),
                    default=None,
                )

            # Apply filters
            filtered_risks = merged_risks[merged_risks["total_risk_score"] >= risk_threshold].copy()
            if phase_filter:
                filtered_risks = filtered_risks[filtered_risks["phase"].isin(phase_filter)]
            if status_filter:
                filtered_risks = filtered_risks[filtered_risks["status"].isin(status_filter)]

            st.info(f"📊 Showing {len(filtered_risks)} trials (filtered from {len(merged_risks)} total)")

            # Risk score distribution
            st.subheader("📈 Risk Score Distribution")

            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 4))

            # Histogram
            ax1.hist(filtered_risks["total_risk_score"].dropna(), bins=20, edgecolor='black', color='coral', alpha=0.7)
            ax1.axvline(30, color='green', linestyle='--', label='Low/Med threshold (30)')
            ax1.axvline(70, color='red', linestyle='--', label='Med/High threshold (70)')
            ax1.set_xlabel("Total Risk Score")
            ax1.set_ylabel("Number of Trials")
            ax1.set_title("Distribution of Risk Scores")
            ax1.legend()

            # Risk component breakdown
            components = ['small_enrollment_penalty', 'no_randomization_penalty',
                         'single_site_penalty', 'long_duration_penalty']
            component_means = [filtered_risks[comp].mean() for comp in components]
            component_labels = ['Small\nEnrollment', 'No\nRandomization',
                              'Single\nSite', 'Long\nDuration']

            ax2.bar(component_labels, component_means, color=['#ff6b6b', '#ee5a6f', '#cc8899', '#aa7799'])
            ax2.set_ylabel("Average Penalty")
            ax2.set_title("Average Risk Components")
            ax2.set_ylim(0, 50)

            st.pyplot(fig)

            # Risk categories breakdown
            st.subheader("🎯 Risk Categories")
            col1, col2, col3 = st.columns(3)

            low = len(filtered_risks[filtered_risks['total_risk_score'] < 30])
            medium = len(filtered_risks[(filtered_risks['total_risk_score'] >= 30) & (filtered_risks['total_risk_score'] < 70)])
            high = len(filtered_risks[filtered_risks['total_risk_score'] >= 70])

            with col1:
                st.metric("🟢 Low Risk (<30)", low, f"{low/len(filtered_risks)*100:.1f}%" if len(filtered_risks) > 0 else "0%")
            with col2:
                st.metric("🟡 Medium Risk (30-70)", medium, f"{medium/len(filtered_risks)*100:.1f}%" if len(filtered_risks) > 0 else "0%")
            with col3:
                st.metric("🔴 High Risk (≥70)", high, f"{high/len(filtered_risks)*100:.1f}%" if len(filtered_risks) > 0 else "0%")

            st.divider()

            # Results table
            st.subheader("📋 Risk Analysis Results")

            # Sort options
            sort_by = st.selectbox(
                "Sort by:",
                ["Total Risk (High to Low)", "Total Risk (Low to High)",
                 "Enrollment Penalty", "Randomization Penalty", "Site Penalty", "Duration Penalty"],
            )

            if sort_by == "Total Risk (High to Low)":
                filtered_risks = filtered_risks.sort_values("total_risk_score", ascending=False)
            elif sort_by == "Total Risk (Low to High)":
                filtered_risks = filtered_risks.sort_values("total_risk_score", ascending=True)
            elif sort_by == "Enrollment Penalty":
                filtered_risks = filtered_risks.sort_values("small_enrollment_penalty", ascending=False)
            elif sort_by == "Randomization Penalty":
                filtered_risks = filtered_risks.sort_values("no_randomization_penalty", ascending=False)
            elif sort_by == "Site Penalty":
                filtered_risks = filtered_risks.sort_values("single_site_penalty", ascending=False)
            elif sort_by == "Duration Penalty":
                filtered_risks = filtered_risks.sort_values("long_duration_penalty", ascending=False)

            display_cols = [
                "trial_id",
                "title",
                "phase",
                "status",
                "total_risk_score",
                "small_enrollment_penalty",
                "no_randomization_penalty",
                "single_site_penalty",
                "long_duration_penalty",
            ]

            # Add risk category column
            def get_risk_category(score):
                if score < 30:
                    return "🟢 Low"
                elif score < 70:
                    return "🟡 Medium"
                else:
                    return "🔴 High"

            filtered_risks["Risk Category"] = filtered_risks["total_risk_score"].apply(get_risk_category)

            display_cols_with_category = ["trial_id", "title", "phase", "status", "Risk Category"] + display_cols[4:]

            st.dataframe(
                filtered_risks[display_cols_with_category],
                use_container_width=True,
                height=500,
            )

            # Export
            csv = filtered_risks.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download Filtered Risk Analysis CSV",
                csv,
                "risk_analysis_results.csv",
                "text/csv",
            )

    # Tab 5: Compare Trials
    with tab5:
        st.header("🔀 Compare Trials Side-by-Side")

        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            # Get selected trials from session state
            if "selected_trials" not in st.session_state or len(st.session_state.selected_trials) == 0:
                st.info("📋 No trials selected. Go to Patient Matching tab and select trials using checkboxes.")
            else:
                selected_ids = st.session_state.selected_trials[:5]  # Limit to 5 for readability
                st.success(f"Comparing {len(selected_ids)} trials")

                # Create comparison table
                comparison_data = []
                for trial_id in selected_ids:
                    trial_data = trials_df[trials_df["trial_id"] == trial_id]
                    if not trial_data.empty:
                        trial = trial_data.iloc[0]
                        row_data = {"Trial ID": trial_id}
                        row_data["Title"] = trial["title"][:100] + "..."
                        row_data["Phase"] = trial.get("phase", "N/A")
                        row_data["Status"] = trial.get("status", "N/A")

                        # Get enhanced eligibility data
                        if eligibility_df is not None:
                            elig_data = eligibility_df[eligibility_df["trial_id"] == trial_id]
                            if not elig_data.empty:
                                elig = elig_data.iloc[0]
                                row_data["Age Range"] = f"{elig.get('min_age', 'N/A')}-{elig.get('max_age', 'N/A')}"
                                row_data["ECOG Max"] = elig.get("max_ecog", "N/A")
                                row_data["Prior Lines Max"] = elig.get("prior_lines_limit", "N/A")
                                row_data["Brain Mets"] = "❌" if elig.get("brain_mets_excluded") else "✅"

                        # Get clinical data
                        if clinical_data_available and clinical_df is not None:
                            clin_data = clinical_df[clinical_df["trial_id"] == trial_id]
                            if not clin_data.empty:
                                clin = clin_data.iloc[0]
                                row_data["Enrollment"] = clin.get("enrollment", "N/A")
                                row_data["Completion"] = clin.get("completion_date", "N/A")
                                row_data["Sites"] = len(locations_df[locations_df["trial_id"] == trial_id]) if locations_df is not None else "N/A"

                        comparison_data.append(row_data)

                # Display comparison table
                if comparison_data:
                    comparison_df = pd.DataFrame(comparison_data)
                    st.dataframe(comparison_df.set_index("Trial ID").T, use_container_width=True)

                    # Add clear selection button
                    if st.button("🗑️ Clear Selection"):
                        st.session_state.selected_trials = []
                        st.rerun()

    # Tab 8: Fetch Data
    with tab8:
        st.header("📥 Fetch Data from ClinicalTrials.gov")

        # Show current dataset info
        if data_available:
            st.success(f"✅ Current dataset loaded: {len(trials_df)} trials")

            # Show file information
            file_info_df = get_file_info()
            if not file_info_df.empty:
                st.subheader("Current Data Files")
                st.dataframe(file_info_df, use_container_width=True)

            # Show phase distribution
            if len(trials_df) > 0:
                st.subheader("Phase Distribution")
                phase_counts = trials_df["phase"].value_counts()
                st.bar_chart(phase_counts)
        else:
            st.info("No data currently loaded.")

        st.divider()

        st.subheader("Fetch New Data")

        # Autocomplete dropdown for common oncology conditions
        oncology_conditions = [
            "breast cancer",
            "lung cancer",
            "melanoma",
            "colorectal cancer",
            "prostate cancer",
            "pancreatic cancer",
            "ovarian cancer",
            "leukemia",
            "lymphoma",
            "glioblastoma",
            "brain cancer",
            "liver cancer",
            "stomach cancer",
            "kidney cancer",
            "bladder cancer",
            "thyroid cancer",
            "esophageal cancer",
            "cervical cancer",
            "uterine cancer",
            "testicular cancer",
            "sarcoma",
            "multiple myeloma",
            "head and neck cancer",
            "skin cancer",
            "mesothelioma",
            "neuroblastoma",
            "oral cancer",
            "bile duct cancer",
            "gallbladder cancer",
            "small cell lung cancer",
            "non-small cell lung cancer",
            "metastatic cancer",
            "stage IV cancer",
        ]

        col1, col2 = st.columns([2, 1])

        with col1:
            condition_choice = st.selectbox(
                "Disease/Condition",
                options=[""] + sorted(oncology_conditions) + ["Other (type below)"],
                help="Select a common oncology disease or choose 'Other' to enter your own"
            )

            if condition_choice == "Other (type below)":
                condition = st.text_input("Enter custom disease/condition", placeholder="e.g., rare disease name")
            elif condition_choice:
                condition = condition_choice
            else:
                condition = ""

        with col2:
            max_trials = st.number_input("Max Trials", min_value=10, max_value=5000, value=500, step=50)

        num_clusters = st.slider("Number of Clusters", min_value=3, max_value=15, value=8)

        if st.button("🚀 Fetch and Process Data", type="primary", disabled=not condition):
            with st.spinner(f"Fetching data for '{condition}'... This may take several minutes."):
                # Run the pipeline
                try:
                    result = subprocess.run(
                        ["./run_pipeline.sh", condition, str(max_trials), str(num_clusters)],
                        cwd="/Users/pjb/Git/nlp-insights",
                        capture_output=True,
                        text=True,
                        timeout=600,
                    )

                    if result.returncode == 0:
                        st.success("✅ Pipeline completed successfully!")

                        # Show output in expander
                        with st.expander("View pipeline output"):
                            st.code(result.stdout)

                        # Clear cache and reload
                        st.cache_data.clear()
                        st.rerun()
                    else:
                        st.error(f"❌ Pipeline failed with error code {result.returncode}")
                        with st.expander("View error details"):
                            st.code(result.stderr)

                except subprocess.TimeoutExpired:
                    st.error("❌ Pipeline timed out after 10 minutes")
                except Exception as e:
                    st.error(f"❌ Error running pipeline: {e}")

        if not condition:
            st.warning("⚠️ Please select or enter a disease/condition to fetch data")

    # Tab 6: My Referrals
    with tab6:
        st.header("📋 My Referrals")

        tracker = st.session_state.referral_tracker

        # Show summary stats
        stats = tracker.get_summary_stats()

        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Referrals", stats["total_referrals"])
        with col2:
            st.metric("Unique Patients", stats["total_patients"])
        with col3:
            st.metric("Unique Trials", stats["total_trials"])

        st.divider()

        # Show referrals needing follow-up
        followup = tracker.get_referrals_needing_followup(days=7)
        if followup:
            st.warning(f"⚠️ {len(followup)} referral(s) need follow-up (no update in 7+ days)")

            for ref in followup[:5]:  # Show up to 5
                with st.expander(f"📌 {ref['patient_id']} → {ref['nct_id']} ({ref['status']})"):
                    st.write(f"**Trial:** {ref['trial_title']}")
                    st.write(f"**Site:** {ref['site_name']}")
                    st.write(f"**Last Updated:** {ref['last_updated'][:10]}")
                    st.write(f"**Notes:** {ref.get('notes', 'No notes')}")

                    # Update status
                    new_status = st.selectbox(
                        "Update Status",
                        REFERRAL_STATUSES,
                        index=REFERRAL_STATUSES.index(ref['status']) if ref['status'] in REFERRAL_STATUSES else 0,
                        key=f"status_{ref['referral_id']}"
                    )

                    update_note = st.text_input("Add Note", key=f"note_{ref['referral_id']}")

                    if st.button("Update", key=f"update_{ref['referral_id']}"):
                        tracker.update_referral_status(ref['referral_id'], new_status, update_note)
                        st.success("✅ Referral updated!")
                        st.rerun()

        st.divider()

        # Status breakdown
        if stats["by_status"]:
            st.subheader("📊 Referrals by Status")

            for status, count in stats["by_status"].items():
                st.write(f"**{status}:** {count}")

        st.divider()

        # All referrals table
        all_referrals = tracker.get_all_referrals()
        if all_referrals:
            st.subheader("📋 All Referrals")

            df = tracker.export_to_dataframe()
            st.dataframe(df, use_container_width=True)

            # Export options
            st.download_button(
                "💾 Download as CSV",
                data=df.to_csv(index=False),
                file_name=f"referrals_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
        else:
            st.info("No referrals yet. Create your first referral in the Patient Matching tab!")

    # Tab 7: Settings
    with tab7:
        st.header("⚙️ Settings")

        # Email Alerts Section
        st.subheader("📧 Email Alerts")

        with st.form("email_alerts_form"):
            email = st.text_input("Email Address", placeholder="your.email@example.com")

            st.write("**Select Alert Types:**")
            alert_selections = {}
            for alert_type in ALERT_TYPES:
                alert_label = alert_type.replace("_", " ").title()
                alert_selections[alert_type] = st.checkbox(alert_label)

            selected_alerts = [k for k, v in alert_selections.items() if v]

            # Optional: Patient profile for matching
            with st.expander("🔍 Patient Profile (for matching alerts)", expanded=False):
                alert_cancer_type = st.text_input("Cancer Type")
                alert_age = st.number_input("Age", min_value=0, max_value=120, value=None)
                alert_location = st.text_input("Location (City, State)")

            if st.form_submit_button("Subscribe to Alerts"):
                if email and selected_alerts:
                    patient_profile = {}
                    if alert_cancer_type:
                        patient_profile["cancer_type"] = alert_cancer_type
                    if alert_age:
                        patient_profile["age"] = alert_age
                    if alert_location:
                        patient_profile["location"] = alert_location

                    sub_id = st.session_state.email_alerts.subscribe(
                        email=email,
                        alert_types=selected_alerts,
                        patient_profile=patient_profile if patient_profile else None
                    )
                    st.success(f"✅ Subscribed! Subscription ID: {sub_id}")
                    st.info("ℹ️ Email notifications are currently in demo mode. SMTP configuration required for production.")
                else:
                    st.error("⚠️ Please enter an email address and select at least one alert type")

        st.divider()

        # Financial Resources Section
        with st.expander("💰 Financial Assistance Resources"):
            st.markdown(get_financial_assistance_resources())

        st.divider()

        # EMR Integration Instructions
        with st.expander("🏥 EMR Integration Guide"):
            st.markdown(get_emr_integration_instructions())


if __name__ == "__main__":
    main()
