#!/bin/bash
# Check backend dependencies

cd "$(dirname "$0")"

source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

echo "Checking backend dependencies..."
echo ""

# Check Python version
echo "Python version:"
python --version
echo ""

# Check critical packages
echo "Checking packages:"
python -c "import fastapi; print('✓ fastapi')" 2>/dev/null || echo "✗ fastapi - MISSING"
python -c "import google.generativeai as genai; print('✓ google-generativeai')" 2>/dev/null || echo "✗ google-generativeai - MISSING (run: pip install google-generativeai)"
python -c "import google.cloud.texttospeech; print('✓ google-cloud-texttospeech')" 2>/dev/null || echo "✗ google-cloud-texttospeech - MISSING"
python -c "import moviepy; print('✓ moviepy')" 2>/dev/null || echo "✗ moviepy - MISSING"
python -c "from pdf2image import convert_from_path; print('✓ pdf2image')" 2>/dev/null || echo "✗ pdf2image - MISSING"
python -c "import uvicorn; print('✓ uvicorn')" 2>/dev/null || echo "✗ uvicorn - MISSING"
python -c "import pydantic; print('✓ pydantic')" 2>/dev/null || echo "✗ pydantic - MISSING"

echo ""
echo "Checking backend module imports:"
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
python -c "from backend.services.gemini_service import GeminiService; print('✓ GeminiService')" 2>/dev/null || echo "✗ GeminiService - Cannot import (check google-generativeai)"
python -c "from backend.main import app; print('✓ FastAPI app')" 2>/dev/null || echo "✗ FastAPI app - Cannot import"

echo ""
echo "Done!"

