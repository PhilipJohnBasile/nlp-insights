# Clinical Trials NLP Insights

A production-grade MVP for mining ClinicalTrials.gov to extract insights about trial design and eligibility criteria.

## Problem Statement

Clinical trial design is complex and understanding patterns across trials can be challenging. This tool:

- Fetches and analyzes clinical trial data from ClinicalTrials.gov
- Extracts structured information from free-text eligibility criteria
- Identifies trial design patterns through clustering
- Flags potential design risks (small enrollment, lack of randomization, etc.)
- Provides an interactive web interface for exploration and export

**⚠️ Disclaimer**: This is a research tool only and not medical advice. All data is sourced from publicly available ClinicalTrials.gov records.

## Features

- **Data Fetching**: Retrieve trials via ClinicalTrials.gov v2 API with caching
- **Data Normalization**: Clean and structure trial metadata
- **Eligibility Parsing**: Extract age, sex, inclusion/exclusion criteria from free text
- **Feature Engineering**: Generate numeric features for analysis
- **Clustering**: Group similar trials using K-means
- **Risk Scoring**: Transparent risk assessment based on design characteristics
- **Interactive UI**: Streamlit app with filtering, search, and CSV export

## Quick Start

### Prerequisites

- Python 3.11+
- pip or uv

### Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd nlp-insights

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .

# Or with uv (faster)
uv pip install -e .
```

### Running the Pipeline

```bash
# 1. Fetch trials (example: breast cancer, max 500 trials)
python -m trials.fetch --condition "breast cancer" --max 500

# 2. Normalize raw data
python -m trials.normalize

# 3. Parse eligibility criteria
python -m trials.eligibility

# 4. Build feature matrix
python -m trials.features

# 5. Cluster trials
python -m trials.cluster --k 8

# 6. Calculate risk scores
python -m trials.risk

# 7. Launch Streamlit app
./start_app.sh

# Or manually with PYTHONPATH:
# PYTHONPATH=. streamlit run trials/app.py
```

### Running Tests

```bash
# Run all tests
pytest -v

# Run with coverage
pytest --cov=trials --cov-report=html

# Quick test
pytest -q
```

## Data Dictionary

### trials.parquet

Normalized trial metadata.

| Column | Type | Description |
|--------|------|-------------|
| trial_id | str | NCT identifier (e.g., NCT12345678) |
| title | str | Trial title |
| phase | str | Study phase (Phase 1, Phase 2, etc.) |
| status | str | Overall status (Recruiting, Completed, etc.) |
| start_date | str | Study start date |
| completion_date | str | Study completion date |
| enrollment | int | Planned enrollment count |
| arms | int | Number of study arms/groups |
| countries | list[str] | List of countries where trial is conducted |
| study_type | str | Study type (Interventional, Observational) |
| masking | str | Masking/blinding approach |
| allocation | str | Allocation type (Randomized, Non-Randomized) |
| primary_outcomes | list[str] | Primary outcome measures |
| eligibility_text | str | Full eligibility criteria text |

### eligibility.parquet

Parsed eligibility criteria.

| Column | Type | Description |
|--------|------|-------------|
| trial_id | str | NCT identifier |
| min_age | float | Minimum age in years |
| max_age | float | Maximum age in years |
| sex | str | Sex eligibility (All, Male, Female) |
| key_inclusion_terms | list[str] | Extracted inclusion criteria (top 20) |
| key_exclusion_terms | list[str] | Extracted exclusion criteria (top 20) |
| disease_stage_terms | list[str] | Disease stage mentions (e.g., "stage IV", "metastatic") |

### features.parquet

Engineered features for clustering and analysis.

| Column | Type | Description |
|--------|------|-------------|
| trial_id | str | NCT identifier |
| planned_enrollment | float | Planned enrollment count |
| num_sites | int | Number of sites/countries |
| phase_code | int | Numeric phase code (0-5) |
| arm_count | int | Number of study arms |
| randomized_flag | int | 1 if randomized, 0 otherwise |
| parallel_flag | int | 1 if parallel design, 0 otherwise |
| masking_level | int | Masking level (0-4) |
| duration_days | float | Planned study duration in days |

### clusters.parquet

Cluster assignments.

| Column | Type | Description |
|--------|------|-------------|
| trial_id | str | NCT identifier |
| cluster | int | Cluster label (0 to k-1) |

### risks.parquet

Risk assessment scores.

| Column | Type | Description |
|--------|------|-------------|
| trial_id | str | NCT identifier |
| small_enrollment_penalty | float | Penalty for small enrollment (0-50) |
| no_randomization_penalty | float | Penalty for non-randomized design (0 or 30) |
| single_site_penalty | float | Penalty for few sites (0-20) |
| long_duration_penalty | float | Penalty for long duration (0-30) |
| total_risk_score | float | Sum of all penalties (max 130) |

## Risk Scoring Methodology

The risk score is a transparent, rule-based composite score with four components:

1. **Small Enrollment Penalty** (0-50 points)
   - Trials with < 50 participants receive increasing penalties
   - Based on evidence that small trials have higher failure rates

2. **No Randomization Penalty** (30 points)
   - Non-randomized trials receive a fixed penalty
   - Randomization is a gold standard for reducing bias

3. **Single Site Penalty** (0-20 points)
   - Trials at 0-3 sites receive penalties
   - Multi-site trials provide more generalizable results

4. **Long Duration Penalty** (0-30 points)
   - Trials longer than 2 years receive increasing penalties
   - Long trials have higher dropout and operational risks

**Total Risk Score**: Sum of all components (maximum 130 points)

Higher scores indicate trials with more design-related risk factors.

## Cluster Interpretation

Example cluster profiles (will vary based on data):

- **Cluster 0**: Large Phase 3 trials (high enrollment, randomized, multi-site)
- **Cluster 1**: Early phase trials (small enrollment, few sites)
- **Cluster 2**: Single-arm studies (no randomization)
- **Cluster 3**: Observational studies

Run clustering to see actual profiles for your dataset.

## Architecture

```
trials/
├── __init__.py         # Package initialization
├── __main__.py         # CLI entry point
├── config.py           # Configuration management
├── models.py           # Pydantic data models
├── client.py           # ClinicalTrials.gov API client
├── fetch.py            # Data fetching module
├── normalize.py        # Data normalization
├── eligibility.py      # Eligibility parsing with NLP
├── features.py         # Feature engineering
├── cluster.py          # K-means clustering
├── risk.py             # Risk scoring
└── app.py              # Streamlit web app

data/
├── raw/                # Raw JSONL files from API
└── clean/              # Processed Parquet files

tests/
├── test_models.py      # Model tests
├── test_eligibility.py # Eligibility parsing tests
├── test_features.py    # Feature engineering tests
├── test_risk.py        # Risk scoring tests
└── test_integration.py # End-to-end integration test
```

## Technologies Used

- **Data**: ClinicalTrials.gov v2 API (free, public)
- **Language**: Python 3.11
- **Data Processing**: Pandas, NumPy
- **ML/NLP**: Scikit-learn, HuggingFace Transformers (sentence embeddings)
- **Validation**: Pydantic
- **Web UI**: Streamlit
- **Testing**: pytest
- **Code Quality**: Ruff (linting)

## Limitations and Ethics

### Limitations

1. **Data Quality**: Relies on self-reported ClinicalTrials.gov data
2. **NLP Accuracy**: Eligibility parsing uses rule-based extraction; may miss complex criteria
3. **Risk Model**: Transparent but simplified; does not replace expert clinical judgment
4. **Scope**: Currently focused on design features; does not analyze efficacy or safety
5. **Clustering**: Unsupervised; cluster interpretations are post-hoc

### Ethical Considerations

- **Research Only**: This tool is for research and education, not clinical decision-making
- **No PHI**: Uses only publicly available, de-identified trial metadata
- **Transparency**: All risk scoring formulas are documented and deterministic
- **Bias Awareness**: Clustering may reflect historical biases in trial design
- **No Medical Advice**: Users should consult qualified professionals for medical decisions

### Responsible Use

- Do not use for patient recruitment or screening
- Do not use as sole basis for trial design decisions
- Validate findings with domain experts
- Be aware of potential biases in historical trial data
- Cite ClinicalTrials.gov as the original data source

## Example Usage

### Fetch Oncology Trials

```bash
# Breast cancer
python -m trials.fetch --condition "breast cancer" --max 1000

# Lung cancer
python -m trials.fetch --condition "lung cancer" --max 500

# Multiple myeloma
python -m trials.fetch --condition "multiple myeloma" --max 300
```

### Custom Analysis

```python
import pandas as pd

# Load processed data
trials = pd.read_parquet("data/clean/trials.parquet")
risks = pd.read_parquet("data/clean/risks.parquet")

# Merge and analyze
df = trials.merge(risks, on="trial_id")

# Find high-risk Phase 3 trials
high_risk_p3 = df[
    (df["phase"] == "Phase 3") &
    (df["total_risk_score"] > 60)
]

print(f"Found {len(high_risk_p3)} high-risk Phase 3 trials")
```

## Screenshots

### Explore Tab
![Explore Tab](docs/screenshots/explore.png)

*Filter trials by phase, status, enrollment; search titles; export to CSV*

### Eligibility Explorer Tab
![Eligibility Tab](docs/screenshots/eligibility.png)

*Search eligibility criteria; highlight matching terms; view disease stages*

### Risk Analysis Tab
![Risk Tab](docs/screenshots/risk.png)

*Identify high-risk trials; view risk score components; export for further analysis*

## Troubleshooting

### "ModuleNotFoundError: No module named 'trials'"

Use the provided startup script instead of calling streamlit directly:

```bash
./start_app.sh
```

Or set PYTHONPATH manually:

```bash
PYTHONPATH=. streamlit run trials/app.py
```

### "command not found: python"

The project uses `python3`. Make sure all scripts use `python3`:
- Use `./run_pipeline.sh` (already updated)
- Use `./start_app.sh` for the app
- Use `python3 -m trials.fetch` for CLI commands

### API Rate Limiting

If you encounter rate limit errors, increase the delay in `.env`:

```
RATE_LIMIT_DELAY=2.0
```

## Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure `pytest` and `ruff` pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Acknowledgments

- Data from [ClinicalTrials.gov](https://clinicaltrials.gov)
- Built with Claude Code

## Citation

If you use this tool in research, please cite:

```
Clinical Trials NLP Insights (2024)
https://github.com/your-username/nlp-insights
Data source: ClinicalTrials.gov
```

---

**Questions or Issues?** Please open a GitHub issue.
