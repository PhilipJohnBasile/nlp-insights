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
echo "Step 1/7: Fetching trials..."
python3 -m trials.fetch --condition "$CONDITION" --max "$MAX_TRIALS"
echo ""

# Step 2: Normalize
echo "Step 2/7: Normalizing data..."
python3 -m trials.normalize
echo ""

# Step 3: Extract clinical data
echo "Step 3/7: Extracting clinical data (interventions, locations, sponsors)..."
python3 -m trials.clinical_data
echo ""

# Step 4: Parse eligibility
echo "Step 4/8: Parsing eligibility criteria..."
python3 -m trials.eligibility
echo ""

# Step 5: Enhance eligibility with clinical features
echo "Step 5/8: Enhancing eligibility (inclusion/exclusion separation, treatment lines)..."
python3 -m trials.enhance_eligibility
echo ""

# Step 6: Build features
echo "Step 6/8: Building features..."
python3 -m trials.features
echo ""

# Step 7: Cluster
echo "Step 7/8: Clustering trials..."
python3 -m trials.cluster --k "$CLUSTERS"
echo ""

# Step 8: Risk scoring
echo "Step 8/8: Calculating risk scores..."
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
