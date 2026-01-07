#!/bin/bash
# Start PPT2Preview API server

cd "$(dirname "$0")"

# Load environment variables from .env file if it exists
if [ -f ".env" ]; then
    echo "Loading environment variables from .env file..."
    set -a
    source .env
    set +a
    echo "✓ Environment variables loaded"
    echo ""
fi

source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

echo "Starting PPT2Preview API server..."
echo "Server will be available at http://localhost:8000"
echo "API docs will be available at http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload

