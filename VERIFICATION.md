# Verification Checklist

Use this checklist to verify the complete MVP is working correctly.

## Installation Verification

- [ ] Python 3.11+ installed: `python3 --version`
- [ ] Dependencies installed: `pip install -r requirements.txt`
- [ ] No import errors: `python3 -c "import trials; print('OK')"`

## Data Pipeline Verification

### 1. Fetch Module
```bash
python3 -m trials.fetch --condition "melanoma" --max 50
```
- [ ] Creates JSONL file in `data/raw/`
- [ ] File contains 50 JSON records
- [ ] No errors or exceptions

### 2. Normalize Module
```bash
python3 -m trials.normalize
```
- [ ] Creates `data/clean/trials.parquet`
- [ ] Prints summary statistics
- [ ] Shows phase and status distributions

### 3. Eligibility Module
```bash
python3 -m trials.eligibility
```
- [ ] Creates `data/clean/eligibility.parquet`
- [ ] Prints eligibility summary
- [ ] No parsing errors

### 4. Features Module
```bash
python3 -m trials.features
```
- [ ] Creates `data/clean/features.parquet`
- [ ] Prints feature summary with statistics
- [ ] All features have valid ranges

### 5. Cluster Module
```bash
python3 -m trials.cluster --k 5
```
- [ ] Creates `data/clean/clusters.parquet`
- [ ] Prints cluster sizes
- [ ] Shows cluster profiles

### 6. Risk Module
```bash
python3 -m trials.risk
```
- [ ] Creates `data/clean/risks.parquet`
- [ ] Prints risk score summary
- [ ] Lists highest risk trials

## Test Suite Verification

```bash
pytest -v
```
- [ ] 16/16 tests pass
- [ ] No failures or errors
- [ ] All modules tested

Quick test:
```bash
pytest -q
```
- [ ] Shows passing count
- [ ] No warnings critical to functionality

## UI Verification

```bash
streamlit run trials/app.py
```

### Explore Tab
- [ ] App launches in browser
- [ ] Phase filter works
- [ ] Status filter works
- [ ] Min enrollment filter works
- [ ] Search box filters titles
- [ ] Data table displays correctly
- [ ] Export CSV button works
- [ ] Downloaded CSV opens correctly
- [ ] Summary metrics display

### Eligibility Explorer Tab
- [ ] Search input accepts text
- [ ] Comma-separated terms work
- [ ] Matching trials appear
- [ ] Expanders open/close
- [ ] Terms are highlighted in yellow
- [ ] Disease stage chart displays

### Risk Analysis Tab
- [ ] Risk slider works (0-130)
- [ ] High-risk trials display
- [ ] Risk components show in table
- [ ] Export button works
- [ ] Risk distribution histogram displays

## Data Quality Verification

### Check Parquet Files
```bash
ls -lh data/clean/
```
- [ ] All 5 files present (trials, eligibility, features, clusters, risks)
- [ ] File sizes reasonable (>0 bytes)

### Inspect Data
```python
import pandas as pd

# Load all files
trials = pd.read_parquet("data/clean/trials.parquet")
eligibility = pd.read_parquet("data/clean/eligibility.parquet")
features = pd.read_parquet("data/clean/features.parquet")
clusters = pd.read_parquet("data/clean/clusters.parquet")
risks = pd.read_parquet("data/clean/risks.parquet")

# Basic checks
assert len(trials) > 0, "No trials"
assert len(trials) == len(eligibility), "Length mismatch"
assert len(trials) == len(features), "Length mismatch"
assert len(trials) == len(clusters), "Length mismatch"
assert len(trials) == len(risks), "Length mismatch"

# Check for required columns
assert "trial_id" in trials.columns
assert "phase" in trials.columns
assert "total_risk_score" in risks.columns
assert "cluster" in clusters.columns

print("✓ All data quality checks passed")
```

## Sample Data Verification

```bash
ls -lh data/clean/sample_*.parquet
```
- [ ] 5 sample files present
- [ ] Total size ~1-2 MB
- [ ] Files can be loaded

## Documentation Verification

- [ ] README.md is complete
- [ ] QUICKSTART.md exists
- [ ] PROJECT_SUMMARY.md exists
- [ ] docs/ARCHITECTURE.md exists
- [ ] LICENSE file exists
- [ ] requirements.txt lists all dependencies
- [ ] .env.example has all config options

## Code Quality Verification

### Type Hints
```bash
grep -r "def " trials/*.py | head -5
```
- [ ] Functions have type hints
- [ ] Return types specified

### Error Handling
```bash
grep -r "try:" trials/*.py | wc -l
```
- [ ] Error handling present
- [ ] Graceful failures

### Docstrings
```bash
grep -r '"""' trials/*.py | wc -l
```
- [ ] Modules documented
- [ ] Functions documented

## Integration Test

Run the full pipeline end-to-end:

```bash
# Clean previous data
rm -f data/clean/*.parquet
rm -f data/raw/*.jsonl

# Run pipeline
./run_pipeline.sh "breast cancer" 100 5

# Verify output
ls -lh data/clean/
```

- [ ] All 5 Parquet files created
- [ ] Pipeline completes without errors
- [ ] Sample size = 100 trials
- [ ] 5 clusters created

## Performance Verification

Time the pipeline:

```bash
time ./run_pipeline.sh "lung cancer" 200 6
```

- [ ] Completes in reasonable time (<10 minutes for 200 trials)
- [ ] No memory errors
- [ ] Progress updates display

## Edge Cases

### Empty Results
```bash
python3 -m trials.fetch --condition "zzz_nonexistent_disease" --max 10
```
- [ ] Handles gracefully
- [ ] Informative error message

### Large Dataset
```bash
python3 -m trials.fetch --condition "cancer" --max 2000
```
- [ ] Pagination works
- [ ] Cache prevents duplicate requests
- [ ] Memory usage reasonable

### Invalid Input
```bash
python3 -m trials.cluster --k -1
```
- [ ] Validates input
- [ ] Error message clear

## Security Verification

- [ ] No hardcoded credentials
- [ ] .env not committed
- [ ] API key not required
- [ ] Rate limiting prevents abuse
- [ ] Input validation present

## Reproducibility Verification

Run pipeline twice:

```bash
# First run
python3 -m trials.cluster --k 6
cp data/clean/clusters.parquet /tmp/clusters1.parquet

# Second run (without re-fetching)
python3 -m trials.cluster --k 6
cp data/clean/clusters.parquet /tmp/clusters2.parquet

# Compare
diff /tmp/clusters1.parquet /tmp/clusters2.parquet
```

- [ ] Results are identical
- [ ] Deterministic behavior (RANDOM_SEED works)

## Acceptance Criteria (from requirements)

1. ✓ **CLI for "breast cancer" creates clean Parquet files**
   - [ ] Verified above in "Data Pipeline Verification"

2. ✓ **Streamlit app launches with filters and CSV export**
   - [ ] Verified in "UI Verification"

3. ✓ **At least one risk cluster interpretably different**
   - [ ] Check cluster profiles in risk module output
   - [ ] Document one cluster's distinctive characteristics

4. ✓ **All tests pass with pytest -q**
   - [ ] Verified in "Test Suite Verification"

## Final Checklist

- [ ] All module CLIs work independently
- [ ] Full pipeline completes successfully
- [ ] Tests pass (16/16)
- [ ] Streamlit app functional
- [ ] Sample data included
- [ ] Documentation complete
- [ ] License file present
- [ ] .gitignore configured
- [ ] No sensitive data committed

## Sign-off

Date: _______________

Verifier: _______________

Notes:
________________________________________________________________________________
________________________________________________________________________________
________________________________________________________________________________

## Next Steps After Verification

1. [ ] Take screenshots of Streamlit app
2. [ ] Add screenshots to `docs/screenshots/`
3. [ ] Update README with actual screenshot paths
4. [ ] Create GitHub repository
5. [ ] Push code
6. [ ] Write release notes
7. [ ] Share with stakeholders

---

**Status**: ⬜ Not Started | 🟡 In Progress | ✅ Complete
