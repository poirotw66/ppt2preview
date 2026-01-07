#!/bin/bash
# Start PPT2Preview API server

cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
    
    # Clear invalid GOOGLE_APPLICATION_CREDENTIALS placeholder
    if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        if [[ "$GOOGLE_APPLICATION_CREDENTIALS" == *"/path/to/your/"* ]] || [[ "$GOOGLE_APPLICATION_CREDENTIALS" == "your-google-cloud-credentials.json" ]]; then
            echo "⚠️  Warning: GOOGLE_APPLICATION_CREDENTIALS contains placeholder value, clearing it..."
            unset GOOGLE_APPLICATION_CREDENTIALS
            echo "   Using Application Default Credentials instead."
            echo "   To set up credentials, run: gcloud auth application-default login"
        fi
    fi
    
    echo "✓ Environment variables loaded"
    echo ""
fi

source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

# Set PYTHONPATH to include project root
export PYTHONPATH="${PYTHONPATH}:$(pwd)"

echo "Starting PPT2Preview API server..."
echo "Server will be available at http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

# Run from project root directory
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

