# Documentation Index

Welcome to the Clinical Trials Insights documentation! This index will help you find what you need.

## 🚀 Getting Started

**New to this project? Start here:**

1. **[GETTING_STARTED.md](../GETTING_STARTED.md)** - Choose your path (1, 5, or 10 minutes)
2. **[QUICKSTART.md](../QUICKSTART.md)** - Fastest way to see results
3. **[README.md](../README.md)** - Complete documentation

## 📚 Documentation by Purpose

### I Want To...

#### ...Get the App Running Now
→ [GETTING_STARTED.md](../GETTING_STARTED.md) - Path 1 (1 minute with sample data)

#### ...Understand What This Does
→ [README.md](../README.md) - Problem statement and features

#### ...Fetch My Own Data
→ [GETTING_STARTED.md](../GETTING_STARTED.md) - Path 2 or 3
→ [README.md](../README.md#example-usage) - Command examples

#### ...Understand the Risk Scores
→ [README.md](../README.md#risk-scoring-methodology) - Detailed methodology
→ [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md#notable-features) - Formula details

#### ...Know What Files Contain
→ [README.md](../README.md#data-dictionary) - Complete data dictionary

#### ...Understand the Architecture
→ [ARCHITECTURE.md](ARCHITECTURE.md) - System design and flow

#### ...Verify Everything Works
→ [VERIFICATION.md](../VERIFICATION.md) - Complete testing checklist

#### ...See What Was Delivered
→ [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) - Deliverables overview
→ [DELIVERY_NOTES.md](../DELIVERY_NOTES.md) - Final delivery package

#### ...Fix an Error
→ [README.md](../README.md#troubleshooting) - Common issues
→ [QUICKSTART.md](../QUICKSTART.md#troubleshooting) - Quick fixes

#### ...Do Custom Analysis
→ [GETTING_STARTED.md](../GETTING_STARTED.md#workflow-3-custom-analysis-in-python) - Python examples
→ [notebooks/example_analysis.py](../notebooks/example_analysis.py) - EDA notebook

#### ...Understand the Code
→ [ARCHITECTURE.md](ARCHITECTURE.md) - Module breakdown
→ Source code in `trials/` with inline docs

#### ...Run Tests
→ [VERIFICATION.md](../VERIFICATION.md#test-suite-verification) - Test instructions
→ [README.md](../README.md#running-tests) - Basic test commands

#### ...Deploy This
→ [README.md](../README.md#quick-start) - Installation guide
→ [ARCHITECTURE.md](ARCHITECTURE.md#future-enhancements) - Deployment considerations

## 📖 Documentation Files

### Core Documentation

| File | Purpose | Read If... |
|------|---------|-----------|
| [README.md](../README.md) | Complete project documentation | You want the full story |
| [GETTING_STARTED.md](../GETTING_STARTED.md) | Quick paths to value | You want to start now |
| [QUICKSTART.md](../QUICKSTART.md) | 5-minute setup | You want the fastest path |

### Reference Documentation

| File | Purpose | Read If... |
|------|---------|-----------|
| [PROJECT_SUMMARY.md](../PROJECT_SUMMARY.md) | Deliverables summary | You want to know what was built |
| [DELIVERY_NOTES.md](../DELIVERY_NOTES.md) | Final delivery package | You're reviewing the project |
| [VERIFICATION.md](../VERIFICATION.md) | Testing checklist | You want to verify it works |
| [ARCHITECTURE.md](ARCHITECTURE.md) | System design | You want to understand how it works |

### Helper Scripts

| File | Purpose | Use When... |
|------|---------|-------------|
| [start_app.sh](../start_app.sh) | Launch Streamlit UI | You want to run the app |
| [run_pipeline.sh](../run_pipeline.sh) | Run full pipeline | You want to fetch and process data |

## 🗂️ Repository Structure

```
nlp-insights/
├── README.md                    ← Start here
├── GETTING_STARTED.md           ← Or here for quick paths
├── QUICKSTART.md                ← Or here for 5-min setup
├── PROJECT_SUMMARY.md           ← What was delivered
├── DELIVERY_NOTES.md            ← Final package overview
├── VERIFICATION.md              ← Testing checklist
├── LICENSE                      ← MIT license
├── requirements.txt             ← Dependencies
├── pyproject.toml               ← Project config
├── .env.example                 ← Config template
├── start_app.sh                 ← Launch app
├── run_pipeline.sh              ← Run pipeline
├── trials/                      ← Source code (13 modules)
│   ├── __init__.py
│   ├── __main__.py
│   ├── config.py
│   ├── models.py
│   ├── client.py
│   ├── fetch.py
│   ├── normalize.py
│   ├── eligibility.py
│   ├── features.py
│   ├── cluster.py
│   ├── risk.py
│   └── app.py               ← Streamlit UI
├── tests/                       ← Test suite
│   ├── test_models.py
│   ├── test_eligibility.py
│   ├── test_features.py
│   ├── test_risk.py
│   └── test_integration.py
├── data/
│   ├── raw/                     ← Raw JSONL files
│   └── clean/                   ← Processed Parquet files
│       ├── sample_*.parquet     ← Sample data (included)
│       ├── trials.parquet
│       ├── eligibility.parquet
│       ├── features.parquet
│       ├── clusters.parquet
│       └── risks.parquet
├── docs/
│   ├── INDEX.md                 ← This file
│   ├── ARCHITECTURE.md          ← System design
│   └── screenshots/             ← UI screenshots
└── notebooks/
    └── example_analysis.py      ← EDA notebook
```

## 🎯 Quick Command Reference

```bash
# Get started with sample data (1 minute)
cd data/clean && for f in sample_*.parquet; do cp "$f" "${f#sample_}"; done && cd ../..
./start_app.sh

# Run full pipeline (5-10 minutes)
./run_pipeline.sh "breast cancer" 500 8
./start_app.sh

# Run tests
python3 -m pytest tests/ -v

# Individual pipeline steps
python3 -m trials.fetch --condition "lung cancer" --max 500
python3 -m trials.normalize
python3 -m trials.eligibility
python3 -m trials.features
python3 -m trials.cluster --k 8
python3 -m trials.risk
```

## 📊 Sample Data

The repository includes 300 breast cancer trials:

- **trials.parquet** - 363 KB - Trial metadata
- **eligibility.parquet** - 285 KB - Parsed criteria
- **features.parquet** - 11 KB - Engineered features
- **clusters.parquet** - 4.4 KB - Cluster labels
- **risks.parquet** - 9.4 KB - Risk scores

Total: **673 KB** of sample data ready to explore.

## 🎓 Learning Path

**Beginner:**
1. Read [GETTING_STARTED.md](../GETTING_STARTED.md)
2. Launch app with sample data
3. Explore the 3 tabs

**Intermediate:**
1. Read [README.md](../README.md) problem statement
2. Run pipeline for a disease area
3. Understand risk methodology
4. Export and analyze CSV

**Advanced:**
1. Read [ARCHITECTURE.md](ARCHITECTURE.md)
2. Review source code
3. Write custom analysis scripts
4. Extend with new features

## 🔧 Troubleshooting Docs

**Common Issues:**
- App won't start → [README.md Troubleshooting](../README.md#troubleshooting)
- Module not found → [README.md Troubleshooting](../README.md#troubleshooting)
- Pipeline errors → [VERIFICATION.md](../VERIFICATION.md)
- Understanding output → [README.md Data Dictionary](../README.md#data-dictionary)

## 📞 Need Help?

1. **Check troubleshooting** in [README.md](../README.md#troubleshooting)
2. **Review verification** in [VERIFICATION.md](../VERIFICATION.md)
3. **Read getting started** in [GETTING_STARTED.md](../GETTING_STARTED.md)
4. **Open GitHub issue** with error details

## ✅ Quick Verification

```bash
# Verify installation
python3 -c "import pandas, sklearn, streamlit, pydantic; print('✓ All dependencies installed')"

# Verify sample data
ls -lh data/clean/sample_*.parquet

# Verify tests pass
python3 -m pytest tests/ -q

# Verify app starts
./start_app.sh
```

---

**Ready to Start?** → [GETTING_STARTED.md](../GETTING_STARTED.md)

**Want Full Details?** → [README.md](../README.md)

**Just Want to See It?** → `./start_app.sh`
