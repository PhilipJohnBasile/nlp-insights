# Getting Started with Clinical Trials Insights

## Quick Links

- **[Full Documentation](README.md)** - Complete guide
- **[5-Minute Quickstart](QUICKSTART.md)** - Get running fast
- **[Verification Checklist](VERIFICATION.md)** - Testing guide
- **[Project Summary](PROJECT_SUMMARY.md)** - Deliverables overview

## Choose Your Path

### Path 1: Just Want to See the App? (1 minute)

```bash
# Use pre-loaded sample data
cd data/clean
for f in sample_*.parquet; do cp "$f" "${f#sample_}"; done
cd ../..

# Start the app
./start_app.sh
```

Then open http://localhost:8501 in your browser.

### Path 2: Fetch Fresh Data (5-10 minutes)

```bash
# Install dependencies
python3 -m pip install -r requirements.txt

# Run the full pipeline
./run_pipeline.sh "breast cancer" 500 8

# Start the app
./start_app.sh
```

### Path 3: Custom Analysis

```bash
# Fetch specific disease
python3 -m trials.fetch --condition "melanoma" --max 1000

# Process data
python3 -m trials.normalize
python3 -m trials.eligibility
python3 -m trials.features
python3 -m trials.cluster --k 10
python3 -m trials.risk

# View results
./start_app.sh
```

## What You'll Get

### Sample Data Included

The repository includes 300 breast cancer trials ready to explore:

- **trials.parquet** - Trial metadata
- **eligibility.parquet** - Parsed criteria
- **features.parquet** - Engineered features
- **clusters.parquet** - Cluster assignments
- **risks.parquet** - Risk scores

### Streamlit App Features

**Explore Tab:**
- Filter by phase, status, enrollment
- Search titles
- View trial details
- Export to CSV

**Eligibility Explorer:**
- Search for specific criteria (e.g., "metastatic", "stage IV")
- Highlighted matching terms
- Disease stage visualization

**Risk Analysis:**
- Identify high-risk trials
- View risk components
- Sort by risk score
- Export high-risk trials

## Command Reference

### Data Pipeline

```bash
# Fetch trials
python3 -m trials.fetch --condition "lung cancer" --max 500

# Normalize
python3 -m trials.normalize

# Parse eligibility
python3 -m trials.eligibility

# Build features
python3 -m trials.features

# Cluster
python3 -m trials.cluster --k 8

# Risk scoring
python3 -m trials.risk

# All in one
./run_pipeline.sh "lung cancer" 500 8
```

### App & Testing

```bash
# Start app
./start_app.sh

# Run tests
python3 -m pytest tests/ -v

# Quick test
python3 -m pytest tests/ -q
```

## Understanding the Output

### Risk Scores

Trials are scored on 4 components (max 130 points):

1. **Small Enrollment** (0-50 pts) - Penalty for < 50 participants
2. **No Randomization** (0-30 pts) - Penalty for non-randomized design
3. **Single Site** (0-20 pts) - Penalty for few sites
4. **Long Duration** (0-30 pts) - Penalty for > 2 year trials

**Interpretation:**
- 0-30: Low risk
- 31-60: Medium risk
- 61-90: High risk
- 91+: Very high risk

### Clusters

Trials are grouped by design similarity. Example profiles:

- **Cluster 0**: Large randomized trials
- **Cluster 1**: Single-arm observational studies
- **Cluster 2**: Early phase trials
- etc.

Check the cluster profiles in the pipeline output for your data.

## Common Workflows

### Workflow 1: Explore Oncology Trials

```bash
# Fetch various cancer types
python3 -m trials.fetch --condition "breast cancer" --max 500
python3 -m trials.fetch --condition "lung cancer" --max 500
python3 -m trials.fetch --condition "melanoma" --max 300

# Process
python3 -m trials.normalize
python3 -m trials.eligibility
python3 -m trials.features
python3 -m trials.cluster --k 10
python3 -m trials.risk

# Explore in UI
./start_app.sh
```

### Workflow 2: Risk Analysis

```bash
# Process data
./run_pipeline.sh "your condition" 1000 8

# In the app:
# 1. Go to "Risks" tab
# 2. Set threshold to 70+
# 3. Export high-risk trials
# 4. Analyze in Excel/Python
```

### Workflow 3: Custom Analysis in Python

```python
import pandas as pd

# Load all data
trials = pd.read_parquet("data/clean/trials.parquet")
risks = pd.read_parquet("data/clean/risks.parquet")
clusters = pd.read_parquet("data/clean/clusters.parquet")

# Merge
df = trials.merge(risks, on="trial_id").merge(clusters, on="trial_id")

# Custom analysis
high_risk_phase3 = df[
    (df["phase"] == "PHASE3") &
    (df["total_risk_score"] > 80)
]

print(f"Found {len(high_risk_phase3)} high-risk Phase 3 trials")

# Export
high_risk_phase3.to_csv("my_analysis.csv", index=False)
```

## File Locations

```
data/
  raw/              # Raw JSONL from API
  clean/            # Processed Parquet files
    trials.parquet          # Main trial data
    eligibility.parquet     # Parsed criteria
    features.parquet        # Numeric features
    clusters.parquet        # Cluster labels
    risks.parquet           # Risk scores
    sample_*.parquet        # Sample data (committed)
```

## Troubleshooting

### App won't start

**Error**: `ModuleNotFoundError: No module named 'trials'`

**Solution**: Use `./start_app.sh` instead of `streamlit run trials/app.py`

### Pipeline fails

**Error**: `command not found: python`

**Solution**: Use `python3` or `./run_pipeline.sh`

### No data files

**Error**: App shows "Data files not found"

**Solution**: Either run the pipeline or copy sample data:
```bash
cd data/clean && for f in sample_*.parquet; do cp "$f" "${f#sample_}"; done && cd ../..
```

### Tests fail

Make sure dependencies are installed:
```bash
python3 -m pip install -r requirements.txt
```

## Next Steps

1. ✅ **Start Simple**: Use sample data and explore the app
2. ✅ **Fetch Data**: Run pipeline for your disease of interest
3. ✅ **Explore**: Use filters and search in the UI
4. ✅ **Analyze**: Export CSV and do custom analysis
5. ✅ **Learn**: Read the full README for methodology details

## Get Help

- **Documentation Issues**: Check [README.md](README.md)
- **Technical Issues**: Review [VERIFICATION.md](VERIFICATION.md)
- **Understanding Output**: See data dictionary in [README.md](README.md#data-dictionary)
- **Bug Reports**: Open a GitHub issue

---

**Ready to Start?**

```bash
./start_app.sh
```

Then open http://localhost:8501 in your browser! 🚀
