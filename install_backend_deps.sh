#!/bin/bash
# Install backend dependencies

cd "$(dirname "$0")"

source /Users/cfh00896102/miniconda3/etc/profile.d/conda.sh
conda activate p2v

echo "Installing backend dependencies..."
echo ""

pip install -r backend/requirements.txt

echo ""
echo "✓ Backend dependencies installed"
echo ""
echo "Verifying critical packages..."
python -c "import fastapi; print('✓ fastapi')" 2>/dev/null || echo "✗ fastapi"
python -c "import google.generativeai; print('✓ google-generativeai')" 2>/dev/null || echo "✗ google-generativeai"
python -c "import google.cloud.texttospeech; print('✓ google-cloud-texttospeech')" 2>/dev/null || echo "✗ google-cloud-texttospeech"
python -c "import moviepy; print('✓ moviepy')" 2>/dev/null || echo "✗ moviepy"
python -c "from pdf2image import convert_from_path; print('✓ pdf2image')" 2>/dev/null || echo "✗ pdf2image"

echo ""
echo "Done!"

