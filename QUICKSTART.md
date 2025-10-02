# Quick Start Guide

This guide will get you up and running with the Clinical Trials Insights tool in 5 minutes.

## Prerequisites

- Python 3.11 or higher
- pip or uv package manager

## Installation

```bash
# Clone the repository
git clone <your-repo-url>
cd nlp-insights

# Install dependencies
python3 -m pip install requests pydantic pandas scikit-learn numpy streamlit pyarrow python-dotenv pytest
```

## Option 1: Use Sample Data

Sample data is already included in `data/clean/sample_*.parquet` files.

```bash
# Rename sample files to active files
cd data/clean
for f in sample_*.parquet; do cp "$f" "${f#sample_}"; done
cd ../..

# Launch the Streamlit app
./start_app.sh
```

The app will open in your browser at http://localhost:8501

## Option 2: Fetch Fresh Data

```bash
# Run the full pipeline (takes 5-10 minutes)
./run_pipeline.sh "breast cancer" 500 6

# Or run step-by-step:
python3 -m trials.fetch --condition "breast cancer" --max 500
python3 -m trials.normalize
python3 -m trials.eligibility
python3 -m trials.features
python3 -m trials.cluster --k 6
python3 -m trials.risk

# Launch app
./start_app.sh
```

## Running Tests

```bash
# Quick test
pytest -q

# Verbose output
pytest -v

# With coverage
pytest --cov=trials
```

## Using the App

Once the Streamlit app is running:

### Explore Tab
- Use filters to narrow down trials by phase, status, enrollment
- Search titles with keywords
- Click "Export CSV" to download filtered results

### Eligibility Explorer Tab
- Enter comma-separated search terms (e.g., "metastatic, stage IV")
- View trials with matching eligibility criteria
- Terms are highlighted in yellow

### Risk Analysis Tab
- Adjust the minimum risk score slider
- View high-risk trials with component scores
- Export high-risk trials for further analysis

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Check out the [data dictionary](README.md#data-dictionary) to understand the output files
- Explore [examples](README.md#example-usage) for custom analysis

## Troubleshooting

### No data files found
- Make sure you've run the pipeline or copied sample files
- Check that files exist in `data/clean/`

### Import errors
- Ensure all dependencies are installed: `pip install -r requirements.txt`

### API rate limiting
- The client has built-in rate limiting (1 second delay)
- If you see errors, increase `RATE_LIMIT_DELAY` in `.env`

## Getting Help

- Check the [README](README.md) for detailed documentation
- Review test files in `tests/` for usage examples
- Open an issue on GitHub
