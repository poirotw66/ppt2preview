#!/bin/bash
# Load environment variables from .env file

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/.env"

if [ -f "$ENV_FILE" ]; then
    echo "Loading environment variables from .env file..."
    # Export all variables from .env file
    set -a
    source "$ENV_FILE"
    set +a
    echo "✓ Environment variables loaded"
else
    echo "⚠️  .env file not found at $ENV_FILE"
    echo "   Please create it by copying .env.example:"
    echo "   cp .env.example .env"
    echo "   Then edit .env with your actual values"
    exit 1
fi

