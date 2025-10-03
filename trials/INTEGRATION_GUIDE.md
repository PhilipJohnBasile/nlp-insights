# Clinical Trials App - New Features Integration Guide

This document explains how to integrate the newly created feature modules into the main Streamlit app.

## New Modules Created

1. **safety_parser.py** - Parse and display safety/toxicity data
2. **enrollment_tracker.py** - Track enrollment status and urgency
3. **referral_tracker.py** - Manage patient referrals
4. **mobile_styles.py** - Mobile-responsive CSS
5. **email_alerts.py** - Email notification system
6. **financial_info.py** - Insurance and financial information
7. **protocol_access.py** - Protocol documents and consent forms
8. **similar_patients.py** - Similar patient analysis
9. **emr_integration.py** - EMR export/import utilities

## Integration Steps

### 1. Add Imports to app.py

```python
# Add these imports at the top of trials/app.py
from trials.safety_parser import parse_adverse_events, format_safety_display
from trials.enrollment_tracker import parse_enrollment_data, format_enrollment_display
from trials.referral_tracker import ReferralTracker, REFERRAL_STATUSES
from trials.mobile_styles import get_mobile_css
from trials.email_alerts import EmailAlertSystem, ALERT_TYPES
from trials.financial_info import parse_financial_info, format_financial_display, get_financial_assistance_resources
from trials.protocol_access import get_protocol_links, format_protocol_documents, generate_eligibility_checklist
from trials.similar_patients import SimilarPatientsAnalyzer, format_similar_patients_display
from trials.emr_integration import export_to_emr_format, get_emr_integration_instructions
```

### 2. Add Mobile CSS

Add this at the beginning of main() function:

```python
def main():
    # Inject mobile-responsive CSS
    st.markdown(get_mobile_css(), unsafe_allow_html=True)

    # Rest of the app...
```

### 3. Initialize Systems in Session State

```python
# Add to session state initialization
if "referral_tracker" not in st.session_state:
    st.session_state.referral_tracker = ReferralTracker()

if "email_alerts" not in st.session_state:
    st.session_state.email_alerts = EmailAlertSystem()

if "similar_patients" not in st.session_state:
    st.session_state.similar_patients = SimilarPatientsAnalyzer()
```

### 4. Add New Tab: "Safety & Financial"

Add a new tab after the existing tabs:

```python
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "🏠 Home",
    "👤 Patient Matching",
    "🔬 By Disease",
    "📊 Analytics",
    "🆚 Compare Trials",
    "📋 My Referrals",  # NEW
    "⚙️ Settings"  # NEW
])

# In the new My Referrals tab:
with tab6:
    st.header("📋 My Referrals")

    # Display referral tracking interface
    tracker = st.session_state.referral_tracker

    # Show summary stats
    stats = tracker.get_summary_stats()
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Referrals", stats["total_referrals"])
    col2.metric("Unique Patients", stats["total_patients"])
    col3.metric("Unique Trials", stats["total_trials"])

    # Show referrals needing follow-up
    followup = tracker.get_referrals_needing_followup(days=7)
    if followup:
        st.warning(f"⚠️ {len(followup)} referrals need follow-up")

    # Display all referrals
    all_referrals = tracker.get_all_referrals()
    if all_referrals:
        df = tracker.export_to_dataframe()
        st.dataframe(df)

# In the Settings tab:
with tab7:
    st.header("⚙️ Settings")

    st.subheader("📧 Email Alerts")
    with st.form("email_alerts_form"):
        email = st.text_input("Email Address")
        alert_types = st.multiselect("Alert Types", ALERT_TYPES)

        if st.form_submit_button("Subscribe"):
            sub_id = st.session_state.email_alerts.subscribe(
                email=email,
                alert_types=alert_types
            )
            st.success(f"Subscribed! Subscription ID: {sub_id}")
```

### 5. Enhance Trial Display with New Features

When displaying individual trials, add these sections:

```python
# For each trial in results:
with st.expander(f"{trial_row['nct_id']} - {trial_row['title'][:100]}..."):

    # Existing display code...

    # NEW: Safety/Toxicity Data
    with st.expander("⚠️ Safety & Toxicity", expanded=False):
        safety_data = parse_adverse_events(
            eligibility_text=trial_row.get("eligibility"),
            description=trial_row.get("description")
        )
        st.markdown(format_safety_display(safety_data))

    # NEW: Enrollment Status
    with st.expander("📊 Enrollment Status", expanded=False):
        # Load full trial data from JSON
        trial_json = load_trial_json(trial_row['nct_id'])
        enrollment_data = parse_enrollment_data(trial_json)
        st.markdown(format_enrollment_display(enrollment_data))

    # NEW: Financial Information
    with st.expander("💰 Financial Information", expanded=False):
        financial_info = parse_financial_info(trial_json)
        st.markdown(format_financial_display(financial_info))

    # NEW: Protocol Documents
    with st.expander("📄 Protocol Documents", expanded=False):
        protocol_links = get_protocol_links(trial_json)
        st.markdown(format_protocol_documents(protocol_links))

    # NEW: Similar Patients
    with st.expander("👥 Similar Patients", expanded=False):
        similar_stats = st.session_state.similar_patients.find_similar_patients(
            patient_profile=get_current_patient_profile(),
            nct_id=trial_row['nct_id']
        )
        st.markdown(format_similar_patients_display(similar_stats))

    # NEW: Quick Actions
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button(f"📝 Create Referral", key=f"refer_{trial_row['nct_id']}"):
            # Show referral creation form
            st.session_state.show_referral_form = trial_row['nct_id']

    with col2:
        if st.button(f"📧 Set Alert", key=f"alert_{trial_row['nct_id']}"):
            # Subscribe to updates for this trial
            st.success("Alert set for protocol updates")

    with col3:
        if st.button(f"💾 Export to EMR", key=f"emr_{trial_row['nct_id']}"):
            # Show EMR export options
            st.session_state.show_emr_export = trial_row['nct_id']
```

### 6. Add EMR Export Functionality

Add this function and UI:

```python
# Add after trial results display
if st.session_state.get("show_emr_export"):
    st.subheader("💾 Export to EMR")

    export_format = st.radio("Format", ["text", "csv", "json"])

    if st.button("Generate Export"):
        export_data = export_to_emr_format(
            patient_data=get_current_patient_profile(),
            trials=selected_trials,
            format=export_format
        )

        st.text_area("Export Data (Copy to EMR)", export_data, height=400)
        st.download_button(
            "Download Export",
            data=export_data,
            file_name=f"trial_export_{datetime.now().strftime('%Y%m%d')}.{export_format}",
            mime="text/plain"
        )

    # Show integration instructions
    with st.expander("📖 EMR Integration Instructions"):
        st.markdown(get_emr_integration_instructions())
```

### 7. Add Referral Creation Form

```python
if st.session_state.get("show_referral_form"):
    nct_id = st.session_state.show_referral_form

    st.subheader("📝 Create Patient Referral")

    with st.form("referral_form"):
        patient_id = st.text_input("Patient ID (De-identified)")
        site_name = st.text_input("Referral Site")
        site_contact = st.text_input("Contact Person")
        site_phone = st.text_input("Contact Phone")
        notes = st.text_area("Notes")

        if st.form_submit_button("Create Referral"):
            tracker = st.session_state.referral_tracker
            ref_id = tracker.add_referral(
                patient_id=patient_id,
                nct_id=nct_id,
                trial_title=trial_row['title'],
                site_name=site_name,
                site_contact=site_contact,
                site_phone=site_phone,
                notes=notes
            )
            st.success(f"✅ Referral created: {ref_id}")
            st.session_state.show_referral_form = None
            st.rerun()
```

### 8. Add Financial Resources Sidebar

```python
# In the sidebar, add a section:
with st.sidebar:
    # Existing sidebar code...

    st.markdown("---")
    with st.expander("💰 Financial Resources"):
        st.markdown(get_financial_assistance_resources())
```

## Testing Checklist

After integration, test these features:

- [ ] Mobile responsiveness on phone/tablet
- [ ] Safety data displays correctly
- [ ] Enrollment status shows urgency correctly
- [ ] Can create and track referrals
- [ ] Email subscription works (with mock data)
- [ ] Financial info parses correctly
- [ ] Protocol links are clickable
- [ ] Similar patients analytics work
- [ ] EMR export generates valid output
- [ ] All new tabs render correctly

## Performance Considerations

1. **Lazy Loading**: Only parse safety/enrollment data when expanders are opened
2. **Caching**: Use `@st.cache_data` for parsing functions
3. **Pagination**: Limit number of trials displayed at once
4. **Async Loading**: Consider loading trial details asynchronously

## Database Considerations

For production deployment:

1. Replace JSON file storage with proper database (PostgreSQL, MongoDB)
2. Add user authentication for referral tracking
3. Implement proper email configuration with environment variables
4. Add audit logging for all referral actions
5. Implement backup and recovery procedures

## Next Steps

1. Integrate modules one at a time to test incrementally
2. Add unit tests for each new module
3. Update documentation with screenshots
4. Get user feedback from oncologists
5. Add analytics tracking for feature usage
