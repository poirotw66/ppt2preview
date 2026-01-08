"""Pydantic models for API requests and responses."""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class LengthMode(str, Enum):
    """Script length modes."""
    SHORT = "SHORT"
    MEDIUM = "MEDIUM"
    LONG = "LONG"


class TaskStatus(str, Enum):
    """Task status enumeration."""
    PENDING = "pending"
    UPLOADING = "uploading"
    GENERATING_SCRIPT = "generating_script"
    SCRIPT_READY = "script_ready"
    GENERATING_VIDEO = "generating_video"
    COMPLETED = "completed"
    FAILED = "failed"


class UploadResponse(BaseModel):
    """Response for file upload."""
    task_id: str
    status: str
    message: str


class GenerateScriptRequest(BaseModel):
    """Request for script generation."""
    task_id: str
    length_mode: LengthMode = LengthMode.MEDIUM


class ScriptResponse(BaseModel):
    """Response for script generation."""
    task_id: str
    script_content: str
    transcription_data: List[List[str]]  # List of [speaker, text] tuples


class UpdateScriptRequest(BaseModel):
    """Request for script update."""
    script_content: str


class VideoParams(BaseModel):
    """Video generation parameters."""
    fps: int = Field(default=5, ge=1, le=30)
    resolution_width: int = Field(default=1920, ge=640, le=3840)
    resolution_height: int = Field(default=1080, ge=360, le=2160)
    bitrate: str = Field(default="2000k")
    preset: str = Field(default="ultrafast")


class GenerateVideoRequest(BaseModel):
    """Request for video generation."""
    task_id: str
    video_params: Optional[VideoParams] = None
    voice_name: Optional[str] = Field(default="Aoede", description="TTS voice name for Gemini Flash TTS")


class TaskStatusResponse(BaseModel):
    """Response for task status."""
    task_id: str
    status: TaskStatus
    progress: float = Field(default=0.0, ge=0.0, le=100.0)
    current_step: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class ProgressUpdate(BaseModel):
    """WebSocket progress update."""
    task_id: str
    status: TaskStatus
    progress: float
    current_step: Optional[str] = None
    message: Optional[str] = None

