#!/bin/bash
# Run the full clinical trials analysis pipeline

set -e  # Exit on error

echo "======================================"
echo "Clinical Trials Analysis Pipeline"
echo "======================================"
echo ""

# Parse arguments
CONDITION=${1:-"breast cancer"}
MAX_TRIALS=${2:-500}
CLUSTERS=${3:-8}

echo "Configuration:"
echo "  Condition: $CONDITION"
echo "  Max trials: $MAX_TRIALS"
echo "  Clusters: $CLUSTERS"
echo ""

# Step 1: Fetch
echo "Step 1/6: Fetching trials..."
python3 -m trials.fetch --condition "$CONDITION" --max "$MAX_TRIALS"
echo ""

# Step 2: Normalize
echo "Step 2/6: Normalizing data..."
python3 -m trials.normalize
echo ""

# Step 3: Parse eligibility
echo "Step 3/6: Parsing eligibility criteria..."
python3 -m trials.eligibility
echo ""

# Step 4: Build features
echo "Step 4/6: Building features..."
python3 -m trials.features
echo ""

# Step 5: Cluster
echo "Step 5/6: Clustering trials..."
python3 -m trials.cluster --k "$CLUSTERS"
echo ""

# Step 6: Risk scoring
echo "Step 6/6: Calculating risk scores..."
python3 -m trials.risk
echo ""

echo "======================================"
echo "✓ Pipeline complete!"
echo "======================================"
echo ""
echo "Next steps:"
echo "  - Run tests: pytest -q"
echo "  - Launch app: ./start_app.sh"
echo "  - View data: ls -lh data/clean/"
echo ""
