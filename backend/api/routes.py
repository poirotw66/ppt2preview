"""API routes for PPT2Preview."""

import uuid
import json
from pathlib import Path
from typing import Optional, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse

from backend.api.models import (
    UploadResponse,
    GenerateScriptRequest,
    ScriptResponse,
    UpdateScriptRequest,
    GenerateVideoRequest,
    TaskStatusResponse,
    TaskStatus,
    LengthMode
)
from backend.services.file_service import FileService
from backend.services.script_generator import ScriptGenerator
from backend.services.video_generator import VideoGenerator
from backend.core.tasks import TaskManager, TaskProgress


router = APIRouter()
task_manager = TaskManager()

# WebSocket connections manager
class ConnectionManager:
    """Manages WebSocket connections."""
    
    def __init__(self):
        """Initialize connection manager."""
        self.active_connections: Dict[str, list] = {}
    
    async def connect(self, websocket: WebSocket, task_id: str):
        """Connect a WebSocket for a task.
        
        Args:
            websocket: WebSocket connection
            task_id: Task identifier
        """
        await websocket.accept()
        if task_id not in self.active_connections:
            self.active_connections[task_id] = []
        self.active_connections[task_id].append(websocket)
    
    def disconnect(self, websocket: WebSocket, task_id: str):
        """Disconnect a WebSocket.
        
        Args:
            websocket: WebSocket connection
            task_id: Task identifier
        """
        if task_id in self.active_connections:
            if websocket in self.active_connections[task_id]:
                self.active_connections[task_id].remove(websocket)
            if not self.active_connections[task_id]:
                del self.active_connections[task_id]
    
    async def send_progress(self, task_id: str, progress: TaskProgress):
        """Send progress update to all connected clients for a task.
        
        Args:
            task_id: Task identifier
            progress: Task progress object
        """
        if task_id not in self.active_connections:
            return
        
        message = {
            "task_id": task_id,
            "status": progress.status.value,
            "progress": progress.progress,
            "current_step": progress.current_step,
            "message": progress.message,
            "error": progress.error
        }
        
        disconnected = []
        for websocket in self.active_connections[task_id]:
            try:
                await websocket.send_json(message)
            except Exception:
                disconnected.append(websocket)
        
        # Remove disconnected websockets
        for ws in disconnected:
            self.disconnect(ws, task_id)


connection_manager = ConnectionManager()


async def update_status_and_notify(
    task_id: str,
    status: TaskStatus,
    progress: Optional[float] = None,
    message: Optional[str] = None,
    current_step: Optional[str] = None,
    error: Optional[str] = None
):
    """Update task status and notify via WebSocket.
    
    Args:
        task_id: Task identifier
        status: New status
        progress: Progress percentage
        message: Status message
        current_step: Current step description
        error: Error message if failed
    """
    task_manager.update_status(task_id, status, progress, message, current_step, error)
    progress_obj = task_manager.get_task_progress(task_id)
    await connection_manager.send_progress(task_id, progress_obj)


@router.post("/upload", response_model=UploadResponse)
async def upload_files(
    abstract_file: UploadFile = File(..., description="Abstract markdown file"),
    pdf_file: Optional[UploadFile] = File(None, description="PDF presentation file")
):
    """Upload abstract and PDF files for a new task.
    
    Args:
        abstract_file: Abstract markdown file (required)
        pdf_file: PDF presentation file (optional)
        
    Returns:
        Upload response with task_id
    """
    # Generate task ID
    task_id = str(uuid.uuid4())
    
    # Save uploaded files
    abstract_path = FileService.save_uploaded_file(abstract_file, task_id, "abstract.md")
    pdf_path = None
    if pdf_file:
        pdf_path = FileService.save_uploaded_file(pdf_file, task_id, "presentation.pdf")
    
    # Initialize task status
    task_manager.create_task(task_id, {
        "abstract_path": str(abstract_path),
        "pdf_path": str(pdf_path) if pdf_path else None,
        "status": TaskStatus.UPLOADING
    })
    
    await update_status_and_notify(task_id, TaskStatus.UPLOADING, 10.0, "Files uploaded successfully")
    
    return UploadResponse(
        task_id=task_id,
        status=TaskStatus.UPLOADING,
        message="Files uploaded successfully"
    )


@router.post("/generate-script", response_model=ScriptResponse)
async def generate_script(
    request: GenerateScriptRequest,
    background_tasks: BackgroundTasks
):
    """Generate presentation script from uploaded files.
    
    Args:
        request: Script generation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Script response with generated content
    """
    task_id = request.task_id
    
    # Check if task exists
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_manager.get_task_info(task_id)
    abstract_path = Path(task_info["abstract_path"])
    pdf_path = Path(task_info["pdf_path"]) if task_info.get("pdf_path") else None
    
    if not abstract_path.exists():
        raise HTTPException(status_code=404, detail="Abstract file not found")
    
    # Update status
    await update_status_and_notify(
        task_id,
        TaskStatus.GENERATING_SCRIPT,
        20.0,
        "Generating script..."
    )
    
    # Generate script in background (async for WebSocket support)
    async def generate_script_task():
        try:
            script_generator = ScriptGenerator()
            script_content, transcription_data = script_generator.generate_script_from_files(
                task_id=task_id,
                abstract_file_path=abstract_path,
                pdf_file_path=pdf_path,
                length_mode=request.length_mode.value
            )
            
            # Update task info
            task_manager.update_task_info(task_id, {
                "script_content": script_content,
                "transcription_data": transcription_data
            })
            
            await update_status_and_notify(
                task_id,
                TaskStatus.SCRIPT_READY,
                50.0,
                "Script generated successfully"
            )
        except Exception as e:
            await update_status_and_notify(
                task_id,
                TaskStatus.FAILED,
                0.0,
                f"Script generation failed: {str(e)}",
                error=str(e)
            )
    
    background_tasks.add_task(generate_script_task)
    
    # Return immediate response (script will be generated in background)
    return ScriptResponse(
        task_id=task_id,
        script_content="",  # Will be available after generation
        transcription_data=[]
    )


@router.get("/script/{task_id}", response_model=ScriptResponse)
async def get_script(task_id: str):
    """Get generated script for a task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Script response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_manager.get_task_info(task_id)
    
    if "script_content" not in task_info:
        raise HTTPException(status_code=404, detail="Script not generated yet")
    
    return ScriptResponse(
        task_id=task_id,
        script_content=task_info["script_content"],
        transcription_data=task_info.get("transcription_data", [])
    )


@router.put("/script/{task_id}", response_model=ScriptResponse)
async def update_script(task_id: str, request: UpdateScriptRequest):
    """Update script content for a task.
    
    Args:
        task_id: Task identifier
        request: Script update request
        
    Returns:
        Updated script response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Save updated script
    script_path = FileService.get_task_file_path(task_id, "script.md")
    with open(script_path, 'w', encoding='utf-8') as f:
        f.write(request.script_content)
    
    # Update task info
    task_manager.update_task_info(task_id, {
        "script_content": request.script_content
    })
    
    task_info = task_manager.get_task_info(task_id)
    
    return ScriptResponse(
        task_id=task_id,
        script_content=request.script_content,
        transcription_data=task_info.get("transcription_data", [])
    )


@router.post("/generate-video")
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks
):
    """Generate video from script and PDF.
    
    Args:
        request: Video generation request
        background_tasks: FastAPI background tasks
        
    Returns:
        Task status response
    """
    task_id = request.task_id
    
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    task_info = task_manager.get_task_info(task_id)
    
    if "transcription_data" not in task_info:
        raise HTTPException(status_code=400, detail="Script must be generated first")
    
    pdf_path = task_info.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        raise HTTPException(status_code=404, detail="PDF file not found")
    
    # Update status
    await update_status_and_notify(
        task_id,
        TaskStatus.GENERATING_VIDEO,
        60.0,
        "Generating video..."
    )
    
    # Video parameters
    video_params = request.video_params
    fps = video_params.fps if video_params else 5
    resolution = (
        video_params.resolution_width if video_params else 1920,
        video_params.resolution_height if video_params else 1080
    )
    bitrate = video_params.bitrate if video_params else "2000k"
    preset = video_params.preset if video_params else "ultrafast"
    
    # Generate video in background (async for WebSocket support)
    async def generate_video_task():
        try:
            task_dir = FileService.create_task_directory(task_id)
            output_video_path = FileService.get_output_file_path(task_id, "presentation.mp4")
            
            # Progress callback that sends WebSocket updates
            def progress_callback(message: str):
                # Update status (sync call)
                task_manager.update_status(
                    task_id,
                    TaskStatus.GENERATING_VIDEO,
                    None,  # Progress will be updated by task manager
                    message
                )
                # Send WebSocket notification (async, but we'll handle it in the async context)
                # Note: This is called from sync context, so we'll notify after the fact
            
            video_generator = VideoGenerator(progress_callback=progress_callback)
            video_generator.create_video(
                pdf_path=pdf_path,
                transcription_data=task_info["transcription_data"],
                output_video_path=str(output_video_path),
                task_dir=task_dir,
                fps=fps,
                resolution=resolution,
                bitrate=bitrate,
                preset=preset
            )
            
            await update_status_and_notify(
                task_id,
                TaskStatus.COMPLETED,
                100.0,
                "Video generated successfully"
            )
        except Exception as e:
            await update_status_and_notify(
                task_id,
                TaskStatus.FAILED,
                0.0,
                f"Video generation failed: {str(e)}",
                error=str(e)
            )
    
    background_tasks.add_task(generate_video_task)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=TaskStatus.GENERATING_VIDEO,
        progress=60.0,
        current_step="Generating video...",
        message="Video generation started"
    )


@router.get("/status/{task_id}", response_model=TaskStatusResponse)
async def get_task_status(task_id: str):
    """Get task status.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Task status response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    progress = task_manager.get_task_progress(task_id)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=progress.status,
        progress=progress.progress,
        current_step=progress.current_step,
        message=progress.message,
        error=progress.error
    )


@router.get("/download/{task_id}")
async def download_video(task_id: str):
    """Download generated video.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Video file response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    progress = task_manager.get_task_progress(task_id)
    
    if progress.status != TaskStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Video not ready yet")
    
    video_path = FileService.get_output_file_path(task_id, "presentation.mp4")
    
    if not video_path.exists():
        raise HTTPException(status_code=404, detail="Video file not found")
    
    return FileResponse(
        path=str(video_path),
        media_type="video/mp4",
        filename="presentation.mp4"
    )


@router.websocket("/ws/{task_id}")
async def websocket_endpoint(websocket: WebSocket, task_id: str):
    """WebSocket endpoint for real-time progress updates.
    
    Args:
        websocket: WebSocket connection
        task_id: Task identifier
    """
    await connection_manager.connect(websocket, task_id)
    
    try:
        # Send initial status
        if task_manager.task_exists(task_id):
            progress = task_manager.get_task_progress(task_id)
            await connection_manager.send_progress(task_id, progress)
        
        # Keep connection alive and listen for messages
        while True:
            try:
                data = await websocket.receive_text()
                # Echo back or handle client messages if needed
                await websocket.send_json({"type": "pong", "data": data})
            except WebSocketDisconnect:
                break
    except WebSocketDisconnect:
        pass
    finally:
        connection_manager.disconnect(websocket, task_id)

