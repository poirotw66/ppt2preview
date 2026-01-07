"""API routes for PPT2Preview."""

import uuid
import json
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict
from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse, Response

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
    
    # Try to read from output directory first
    try:
        script_content = FileService.get_output_file_content(task_id, "script.md")
        # Try to read transcription from output directory
        try:
            transcription_content = FileService.get_output_file_content(task_id, "transcription.py")
            # Parse transcription data
            import ast
            transcription_data = ast.literal_eval(transcription_content)
        except FileNotFoundError:
            # Fall back to task info
            task_info = task_manager.get_task_info(task_id)
            transcription_data = task_info.get("transcription_data", [])
        
        return ScriptResponse(
            task_id=task_id,
            script_content=script_content,
            transcription_data=transcription_data
        )
    except FileNotFoundError:
        # Fall back to task info (for backward compatibility)
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
    
    # Save to output directory only
    FileService.save_output_file(task_id, "script.md", request.script_content)
    
    # Update task info
    task_manager.update_task_info(task_id, {
        "script_content": request.script_content
    })
    
    # Get transcription data
    try:
        transcription_content = FileService.get_output_file_content(task_id, "transcription.py")
        import ast
        transcription_data = ast.literal_eval(transcription_content)
    except FileNotFoundError:
        task_info = task_manager.get_task_info(task_id)
        transcription_data = task_info.get("transcription_data", [])
    
    return ScriptResponse(
        task_id=task_id,
        script_content=request.script_content,
        transcription_data=transcription_data
    )


@router.post("/optimize-script/{task_id}", response_model=ScriptResponse)
async def optimize_script(task_id: str, background_tasks: BackgroundTasks):
    """Optimize script using TRANSCRIPT_REWRITER_PROMPT.
    
    This endpoint reads the current script and optimizes it using
    Gemini's transcript rewriter prompt, which adds TTS markers and
    improves the script for better speech synthesis.
    
    Args:
        task_id: Task identifier
        background_tasks: FastAPI background tasks
        
    Returns:
        Optimized script response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get current script
    try:
        script_content = FileService.get_output_file_content(task_id, "script.md")
    except FileNotFoundError:
        task_info = task_manager.get_task_info(task_id)
        script_content = task_info.get("script_content")
        if not script_content:
            raise HTTPException(status_code=404, detail="Script not found")
    
    # Update status
    await update_status_and_notify(
        task_id,
        TaskStatus.GENERATING_SCRIPT,
        40.0,
        "Optimizing script..."
    )
    
    # Optimize script in background
    async def optimize_script_task():
        try:
            from backend.services.gemini_service import GeminiService
            gemini_service = GeminiService()
            
            optimized_script, transcription_data = gemini_service.optimize_script(script_content)
            
            # Save optimized script and transcription
            FileService.save_output_file(task_id, "script.md", optimized_script)
            transcription_content = str(transcription_data)
            FileService.save_output_file(task_id, "transcription.py", transcription_content)
            
            # Update task info
            task_manager.update_task_info(task_id, {
                "script_content": optimized_script,
                "transcription_data": transcription_data
            })
            
            await update_status_and_notify(
                task_id,
                TaskStatus.SCRIPT_READY,
                50.0,
                "Script optimized successfully"
            )
        except Exception as e:
            await update_status_and_notify(
                task_id,
                TaskStatus.FAILED,
                0.0,
                f"Script optimization failed: {str(e)}",
                error=str(e)
            )
    
    background_tasks.add_task(optimize_script_task)
    
    # Return immediate response
    return ScriptResponse(
        task_id=task_id,
        script_content=script_content,  # Will be updated after optimization
        transcription_data=[]
    )


@router.post("/optimize-script/{task_id}", response_model=ScriptResponse)
async def optimize_script(task_id: str, background_tasks: BackgroundTasks):
    """Optimize script using TRANSCRIPT_REWRITER_PROMPT.
    
    This endpoint reads the current script and optimizes it using
    Gemini's transcript rewriter prompt, which adds TTS markers and
    improves the script for better speech synthesis.
    
    Args:
        task_id: Task identifier
        background_tasks: FastAPI background tasks
        
    Returns:
        Optimized script response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Get current script
    try:
        script_content = FileService.get_output_file_content(task_id, "script.md")
    except FileNotFoundError:
        task_info = task_manager.get_task_info(task_id)
        script_content = task_info.get("script_content")
        if not script_content:
            raise HTTPException(status_code=404, detail="Script not found")
    
    # Update status
    await update_status_and_notify(
        task_id,
        TaskStatus.GENERATING_SCRIPT,
        40.0,
        "Optimizing script..."
    )
    
    # Optimize script in background
    async def optimize_script_task():
        try:
            from backend.services.gemini_service import GeminiService
            gemini_service = GeminiService()
            
            optimized_script, transcription_data = gemini_service.optimize_script(script_content)
            
            # Save optimized script and transcription
            FileService.save_output_file(task_id, "script.md", optimized_script)
            transcription_content = str(transcription_data)
            FileService.save_output_file(task_id, "transcription.py", transcription_content)
            
            # Update task info
            task_manager.update_task_info(task_id, {
                "script_content": optimized_script,
                "transcription_data": transcription_data
            })
            
            await update_status_and_notify(
                task_id,
                TaskStatus.SCRIPT_READY,
                50.0,
                "Script optimized successfully"
            )
        except Exception as e:
            await update_status_and_notify(
                task_id,
                TaskStatus.FAILED,
                0.0,
                f"Script optimization failed: {str(e)}",
                error=str(e)
            )
    
    background_tasks.add_task(optimize_script_task)
    
    # Return immediate response
    return ScriptResponse(
        task_id=task_id,
        script_content=script_content,  # Will be updated after optimization
        transcription_data=[]
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
        import traceback
        error_details = None
        
        try:
            print(f"[VIDEO GENERATION] Starting video generation for task {task_id}")
            print(f"[VIDEO GENERATION] PDF path: {pdf_path}")
            
            output_video_path = FileService.get_output_file_path(task_id, "presentation.mp4")
            
            print(f"[VIDEO GENERATION] Output video path: {output_video_path}")
            
            # Progress callback that sends WebSocket updates
            # Use a queue to send updates asynchronously
            progress_queue = asyncio.Queue()
            loop = asyncio.get_event_loop()
            
            def progress_callback(message: str):
                # Print to console for debugging
                print(f"[VIDEO PROGRESS] {message}")
                # Update status (sync call)
                task_manager.update_status(
                    task_id,
                    TaskStatus.GENERATING_VIDEO,
                    None,  # Progress will be updated by task manager
                    message
                )
                # Queue the WebSocket notification (non-blocking)
                try:
                    progress_queue.put_nowait(message)
                except Exception as e:
                    print(f"[VIDEO PROGRESS] Failed to queue message: {e}")
            
            # Start video generation in a thread pool to avoid blocking
            def run_video_generation():
                try:
                    print(f"[VIDEO GENERATION] Starting video generation in thread")
                    print(f"[VIDEO GENERATION] Transcription data length: {len(task_info.get('transcription_data', []))}")
                    
                    video_generator = VideoGenerator(progress_callback=progress_callback)
                    video_generator.create_video(
                        pdf_path=pdf_path,
                        transcription_data=task_info["transcription_data"],
                        output_video_path=str(output_video_path),
                        task_id=task_id,
                        fps=fps,
                        resolution=resolution,
                        bitrate=bitrate,
                        preset=preset
                    )
                    print(f"[VIDEO GENERATION] Video generation completed successfully")
                except Exception as e:
                    error_msg = f"Video generation error in thread: {str(e)}"
                    error_traceback = traceback.format_exc()
                    print(f"[VIDEO GENERATION ERROR] {error_msg}")
                    print(f"[VIDEO GENERATION ERROR] Traceback:\n{error_traceback}")
                    # Store error for later retrieval
                    nonlocal error_details
                    error_details = {
                        "error": str(e),
                        "traceback": error_traceback
                    }
                    raise
            
            # Run video generation in executor
            executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
            video_future = loop.run_in_executor(executor, run_video_generation)
            
            # Process progress updates while video is generating
            while not video_future.done():
                try:
                    # Wait for progress update with timeout
                    try:
                        message = await asyncio.wait_for(progress_queue.get(), timeout=1.0)
                        # Send WebSocket notification
                        progress_obj = task_manager.get_task_progress(task_id)
                        await connection_manager.send_progress(task_id, progress_obj)
                    except asyncio.TimeoutError:
                        # Send periodic status update even if no new message
                        progress_obj = task_manager.get_task_progress(task_id)
                        await connection_manager.send_progress(task_id, progress_obj)
                        # Check if video generation is still running
                        if video_future.done():
                            break
                except Exception as e:
                    error_msg = f"Error processing progress update: {str(e)}"
                    error_traceback = traceback.format_exc()
                    print(f"[VIDEO PROGRESS ERROR] {error_msg}")
                    print(f"[VIDEO PROGRESS ERROR] Traceback:\n{error_traceback}")
                    break
            
            # Wait for video generation to complete
            print(f"[VIDEO GENERATION] Waiting for video generation to complete...")
            try:
                await video_future
                print(f"[VIDEO GENERATION] Video generation task completed")
            except Exception as e:
                error_msg = f"Video generation task failed: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATION ERROR] {error_msg}")
                print(f"[VIDEO GENERATION ERROR] Traceback:\n{error_traceback}")
                raise
            
            # Check if there was an error in the thread
            if error_details:
                raise Exception(error_details["error"])
            
            await update_status_and_notify(
                task_id,
                TaskStatus.COMPLETED,
                100.0,
                "Video generated successfully"
            )
            print(f"[VIDEO GENERATION] Successfully completed video generation for task {task_id}")
            
        except Exception as e:
            error_msg = f"Video generation failed: {str(e)}"
            error_traceback = traceback.format_exc()
            
            # Print detailed error information
            print("=" * 80)
            print(f"[VIDEO GENERATION FAILED] Task ID: {task_id}")
            print(f"[VIDEO GENERATION FAILED] Error: {error_msg}")
            print(f"[VIDEO GENERATION FAILED] Full traceback:")
            print(error_traceback)
            print("=" * 80)
            
            # Include error details if available
            full_error = error_msg
            if error_details:
                full_error = f"{error_msg}\n\nThread error details:\n{error_details.get('traceback', 'N/A')}"
            
            await update_status_and_notify(
                task_id,
                TaskStatus.FAILED,
                0.0,
                f"Video generation failed: {str(e)}",
                error=full_error
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
    try:
        # Try to get progress (will auto-restore from disk if needed)
        progress = task_manager.get_task_progress(task_id)
        
        return TaskStatusResponse(
            task_id=task_id,
            status=progress.status,
            progress=progress.progress,
            current_step=progress.current_step,
            message=progress.message,
            error=progress.error
        )
    except ValueError:
        # Task not found, check if task directory exists
        task_dir = FileService.create_task_directory(task_id)
        if task_dir.exists() and any(task_dir.iterdir()):
            # Task directory exists but not in manager, try to restore
            # Check for script or transcription files to determine status
            script_path = task_dir / "script.md"
            transcription_path = task_dir / "transcription.py"
            
            if transcription_path.exists():
                # Script is ready
                status = TaskStatus.SCRIPT_READY
                progress_val = 50.0
            elif script_path.exists():
                # Script generating
                status = TaskStatus.GENERATING_SCRIPT
                progress_val = 30.0
            else:
                # Just uploaded
                status = TaskStatus.UPLOADING
                progress_val = 10.0
            
            # Restore task in manager
            task_info = {
                "abstract_path": str(task_dir / "abstract.md"),
                "pdf_path": str(task_dir / "presentation.pdf") if (task_dir / "presentation.pdf").exists() else None,
            }
            task_manager.create_task(task_id, task_info)
            task_manager.update_status(task_id, status, progress_val, f"Task restored (status: {status.value})")
            
            progress = task_manager.get_task_progress(task_id)
            return TaskStatusResponse(
                task_id=task_id,
                status=progress.status,
                progress=progress.progress,
                current_step=progress.current_step,
                message=progress.message,
                error=progress.error
            )
        
        raise HTTPException(status_code=404, detail="Task not found")


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


@router.get("/files/{task_id}/{filename}")
async def get_task_file(task_id: str, filename: str):
    """Get a file from task output directory.
    
    Args:
        task_id: Task identifier
        filename: Filename to retrieve
        
    Returns:
        File content or file response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        file_path = FileService.get_output_file_path(task_id, filename)
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"File not found: {filename}")
        
        # Determine content type based on file extension
        content_type_map = {
            '.md': 'text/markdown',
            '.py': 'text/python',
            '.txt': 'text/plain',
            '.json': 'application/json',
            '.mp4': 'video/mp4',
            '.mp3': 'audio/mpeg',
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        
        ext = file_path.suffix.lower()
        content_type = content_type_map.get(ext, 'application/octet-stream')
        
        # For text files, return as text
        if ext in ['.md', '.py', '.txt', '.json']:
            content = FileService.get_output_file_content(task_id, filename)
            return Response(content=content, media_type=content_type)
        else:
            # For binary files, return as file
            return FileResponse(
                path=str(file_path),
                media_type=content_type,
                filename=filename
            )
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"File not found: {filename}")


@router.get("/files/{task_id}")
async def list_task_files(task_id: str):
    """List all files in task output directory.
    
    Args:
        task_id: Task identifier
        
    Returns:
        List of filenames
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    files = FileService.list_output_files(task_id)
    return {
        "task_id": task_id,
        "files": files,
        "count": len(files)
    }


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
        # Use receive() instead of receive_text() to handle both text and disconnect events
        while True:
            try:
                # Wait for any message (text, bytes, or disconnect)
                message = await websocket.receive()
                
                # Handle text messages
                if "text" in message:
                    data = message["text"]
                    # Echo back or handle client messages if needed
                    await websocket.send_json({"type": "pong", "data": data})
                
                # Handle disconnect
                if message.get("type") == "websocket.disconnect":
                    break
                    
            except WebSocketDisconnect:
                break
            except Exception as e:
                # Log error but keep connection alive
                print(f"WebSocket error for task {task_id}: {e}")
                break
    except WebSocketDisconnect:
        pass
    except Exception as e:
        print(f"WebSocket connection error for task {task_id}: {e}")
    finally:
        connection_manager.disconnect(websocket, task_id)

