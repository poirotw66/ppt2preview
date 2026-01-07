"""Configuration management for the backend."""

import os
from pathlib import Path
from typing import Optional

# Base directory
BASE_DIR = Path(__file__).parent.parent.parent
UPLOAD_DIR = BASE_DIR / "uploads"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Create directories if they don't exist
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# API Configuration
API_V1_PREFIX = "/api/v1"

# Gemini Configuration
GEMINI_API_KEY: Optional[str] = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = "gemini-2.0-flash-exp"  # Using Gemini 3 Flash equivalent

# Google Cloud TTS Configuration
GOOGLE_CLOUD_PROJECT = os.getenv("GOOGLE_CLOUD_PROJECT")
GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

# Video Generation Settings
DEFAULT_FPS = 5
DEFAULT_RESOLUTION = (1920, 1080)
DEFAULT_BITRATE = "2000k"
DEFAULT_PRESET = "ultrafast"

# Task Settings
TASK_TIMEOUT = 3600  # 1 hour in seconds
MAX_WORKERS = 10  # For audio generation

