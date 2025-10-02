"""Streamlit app for exploring clinical trials data."""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from trials.config import config

# Page config
st.set_page_config(
    page_title="Clinical Trials Insights",
    page_icon="🔬",
    layout="wide",
)


@st.cache_data(ttl=60)  # Cache for 60 seconds to allow refresh after data fetch
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all processed data files.

    Returns:
        Tuple of (trials, eligibility, features, risks) DataFrames
    """
    trials = pd.read_parquet(config.CLEAN_DATA_DIR / "trials.parquet")
    eligibility = pd.read_parquet(config.CLEAN_DATA_DIR / "eligibility.parquet")
    features = pd.read_parquet(config.CLEAN_DATA_DIR / "features.parquet")
    risks = pd.read_parquet(config.CLEAN_DATA_DIR / "risks.parquet")

    # Merge cluster data if available
    cluster_file = config.CLEAN_DATA_DIR / "clusters.parquet"
    if cluster_file.exists():
        clusters = pd.read_parquet(cluster_file)
        trials = trials.merge(clusters, on="trial_id", how="left")

    return trials, eligibility, features, risks


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
        trials_df, eligibility_df, features_df, risks_df = load_data()
        data_available = True
    except FileNotFoundError:
        data_available = False
        trials_df = None

    # Create tabs
    if data_available:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Explore", "🔍 Eligibility Explorer", "⚠️ Risk Analysis", "📥 Fetch Data"])
    else:
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Explore", "🔍 Eligibility Explorer", "⚠️ Risk Analysis", "📥 Fetch Data"])

    # Tab 1: Explore
    with tab1:
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

    # Tab 2: Eligibility Explorer
    with tab2:
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

                # Limit display
                num_to_show = st.slider("Number of results to display", min_value=10, max_value=min(100, len(matching_df)), value=min(50, len(matching_df)), step=10)

                # Show results
                for _, row in matching_df.head(num_to_show).iterrows():
                    with st.expander(f"📄 {row['trial_id']}: {row['title'][:100]}..."):
                        st.markdown(f"**Phase**: {row['phase']} | **Status**: {row['status']}")

                        # Show eligibility text with highlighting
                        st.markdown("**Eligibility Criteria:**")
                        eligibility_text = str(row["eligibility_text"]) if pd.notna(row["eligibility_text"]) else "Not available"
                        highlighted_text = highlight_terms(eligibility_text, terms)
                        st.markdown(
                            f'<div style="background-color: #f0f0f0; padding: 10px; '
                            f'border-radius: 5px; color: #000000;">{highlighted_text}</div>',
                            unsafe_allow_html=True,
                        )

                        # Show extracted key terms if available
                        if "key_inclusion_terms" in row.index:
                            try:
                                terms = row["key_inclusion_terms"]
                                if terms is not None and len(terms) > 0:
                                    st.markdown("**Key Inclusion Terms:**")
                                    st.write(", ".join(terms) if isinstance(terms, list) else str(terms))
                            except (TypeError, ValueError):
                                pass

                        if "key_exclusion_terms" in row.index:
                            try:
                                terms = row["key_exclusion_terms"]
                                if terms is not None and len(terms) > 0:
                                    st.markdown("**Key Exclusion Terms:**")
                                    st.write(", ".join(terms) if isinstance(terms, list) else str(terms))
                            except (TypeError, ValueError):
                                pass

            else:
                st.info("Enter search terms above to find trials with specific eligibility criteria.")

    # Tab 3: Risk Analysis
    with tab3:
        if not data_available:
            st.info("👉 No data loaded. Please use the **Fetch Data** tab to download trials first.")
        else:
            st.header("⚠️ Risk Analysis")

            # Merge trials with risks
            merged_risks = trials_df.merge(risks_df, on="trial_id", how="inner")

            # Risk score distribution
            st.subheader("Risk Score Distribution")

            fig, ax = plt.subplots(figsize=(10, 4))
            ax.hist(merged_risks["total_risk_score"].dropna(), bins=20, edgecolor='black', color='coral')
            ax.set_xlabel("Total Risk Score")
            ax.set_ylabel("Number of Trials")
            ax.set_title("Distribution of Risk Scores")
            st.pyplot(fig)

            # Top risky trials
            st.subheader("🚨 Highest Risk Trials")

            top_risks = merged_risks.nlargest(20, "total_risk_score")

            display_cols = [
                "trial_id",
                "title",
                "phase",
                "total_risk_score",
                "small_enrollment_penalty",
                "no_randomization_penalty",
                "single_site_penalty",
                "long_duration_penalty",
            ]

            st.dataframe(
                top_risks[display_cols],
                use_container_width=True,
                height=400,
            )

            # Export
            csv = top_risks.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Download High-Risk Trials CSV",
                csv,
                "high_risk_trials.csv",
                "text/csv",
            )

    # Tab 4: Fetch Data
    with tab4:
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
            with st.spinner(f"Fetching data for '{condition}'..."):
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
                        st.code(result.stderr)

                except subprocess.TimeoutExpired:
                    st.error("❌ Pipeline timed out after 10 minutes")
                except Exception as e:
                    st.error(f"❌ Error running pipeline: {e}")

        if not condition:
            st.warning("⚠️ Please select or enter a disease/condition to fetch data")


if __name__ == "__main__":
    main()
