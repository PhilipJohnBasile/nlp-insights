#!/bin/bash
# Start the Streamlit app with correct PYTHONPATH

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set PYTHONPATH to include the project root
export PYTHONPATH="${SCRIPT_DIR}:${PYTHONPATH}"

# Start Streamlit
echo "Starting Streamlit app..."
echo "PYTHONPATH: ${PYTHONPATH}"
echo ""

streamlit run "${SCRIPT_DIR}/trials/app.py"
