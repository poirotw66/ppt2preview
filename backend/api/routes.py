"""API routes for PPT2Preview."""

import uuid
import json
import asyncio
import concurrent.futures
from pathlib import Path
from typing import Optional, Dict, List, Tuple
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
    LengthMode,
    UpdateProjectNameRequest,
)
from backend.services.file_service import FileService
from backend.services.script_generator import ScriptGenerator
from backend.services.video_generator import VideoGenerator
from backend.services.gemini_service import GeminiService
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
        
        # Get project name from task info (with error handling)
        project_name = None
        try:
            task_info = task_manager.get_task_info(task_id)
            project_name = task_info.get("project_name") if task_info else None
        except ValueError:
            # Task not found, use None for project_name
            pass
        
        message = {
            "task_id": task_id,
            "status": progress.status.value,
            "progress": progress.progress,
            "current_step": progress.current_step,
            "message": progress.message,
            "error": progress.error,
            "project_name": project_name
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
    background_tasks: BackgroundTasks,
    abstract_file: UploadFile = File(..., description="Abstract markdown file"),
    pdf_file: Optional[UploadFile] = File(None, description="PDF presentation file")
):
    """Upload abstract and PDF files for a new task.
    
    Args:
        background_tasks: FastAPI background tasks
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
        "status": TaskStatus.UPLOADING,
        "project_name": "處理中..."  # Default value, will be updated by background task
    })
    
    await update_status_and_notify(task_id, TaskStatus.UPLOADING, 10.0, "Files uploaded successfully")
    
    # Background tasks for processing
    async def process_upload_background():
        # Task 1: Extract PDF slides (if PDF was uploaded)
        if pdf_path:
            try:
                from backend.utils.video_utils import pdf_to_images
                output_task_dir = FileService.get_output_task_directory(task_id)
                output_slides_dir = output_task_dir / "slides"
                output_slides_dir.mkdir(exist_ok=True, parents=True)
                
                # Convert PDF to images
                slide_images = pdf_to_images(str(pdf_path), str(output_slides_dir))
                print(f"✓ Extracted {len(slide_images)} slides from PDF for preview")
                
                # Notify clients about slide extraction completion
                await update_status_and_notify(
                    task_id,
                    TaskStatus.UPLOADING,
                    12.0,
                    f"已提取 {len(slide_images)} 張投影片"
                )
            except Exception as e:
                error_msg = f"投影片提取失敗：{str(e)}"
                print(f"Error: {error_msg}")
                # Update task with error info for user visibility
                task_manager.update_task_info(task_id, {
                    "slide_extraction_error": error_msg
                })
                # Notify user about the error (but don't fail the entire upload)
                await update_status_and_notify(
                    task_id,
                    TaskStatus.UPLOADING,
                    12.0,
                    f"⚠️ {error_msg}"
                )
        
        # Task 2: Generate project name
        try:
            # Read abstract content
            with open(abstract_path, 'r', encoding='utf-8') as f:
                abstract_content = f.read()
            
            # Generate project name using Gemini
            gemini_service = GeminiService()
            project_name = gemini_service.generate_project_name(abstract_content)
            
            # Update task info with project name
            task_manager.update_task_info(task_id, {
                "project_name": project_name
            })
            
            # Notify clients about the project name
            await update_status_and_notify(
                task_id,
                TaskStatus.UPLOADING,
                15.0,
                f"專案名稱：{project_name}"
            )
        except Exception as e:
            print(f"Failed to generate project name: {e}")
            # Don't fail the upload if naming fails
            task_manager.update_task_info(task_id, {
                "project_name": "未命名專案"
            })
    
    background_tasks.add_task(process_upload_background)
    
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


def parse_script_to_transcription(script_content: str) -> List[Tuple[str, str]]:
    """Parse script.md content to transcription format without AI processing.
    
    Converts script.md format (with ### [PAGE X] markers) to transcription format
    [('頁碼', '[PAGE X]'), ('講者', 'text'), ...] while preserving user's exact content.
    
    Args:
        script_content: Script content in markdown format
        
    Returns:
        List of (speaker, text) tuples in transcription format
    """
    import re
    transcription_data = []
    lines = script_content.split('\n')
    current_page = None
    current_text = []
    
    # Handle case where script starts without page marker
    # Assign to page 1 by default
    if lines and not re.match(r'^###\s+\[PAGE\s+\d+\]', lines[0].strip()):
        current_page = 1
        transcription_data.append(('頁碼', '[PAGE 1]'))
    
    for line in lines:
        # Check for page marker: ### [PAGE X]
        page_match = re.match(r'^###\s+\[PAGE\s+(\d+)\]', line.strip())
        if page_match:
            # Save previous page's text if exists
            if current_page is not None and current_text:
                text = '\n'.join(current_text).strip()
                if text:
                    transcription_data.append(('講者', text))
            
            # Start new page
            page_num = page_match.group(1)
            transcription_data.append(('頁碼', f'[PAGE {page_num}]'))
            current_page = page_num
            current_text = []
        else:
            # Accumulate text for current page
            stripped = line.strip()
            if stripped:  # Skip empty lines
                current_text.append(stripped)
    
    # Save last page's text
    if current_page is not None and current_text:
        text = '\n'.join(current_text).strip()
        if text:
            transcription_data.append(('講者', text))
    
    # If no pages were found but there's content, create a default page 1 entry
    if not transcription_data and script_content.strip():
        transcription_data.append(('頁碼', '[PAGE 1]'))
        text = script_content.strip()
        if text:
            transcription_data.append(('講者', text))
    
    return transcription_data


@router.put("/script/{task_id}", response_model=ScriptResponse)
async def update_script(task_id: str, request: UpdateScriptRequest):
    """Update script content for a task.
    
    This endpoint saves the user-edited script content to script.md and
    converts it to transcription.py format without AI processing, preserving
    the user's exact content.
    
    Args:
        task_id: Task identifier
        request: Script update request
        
    Returns:
        Updated script response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Save user-edited script content to script.md
    FileService.save_output_file(task_id, "script.md", request.script_content)
    
    # Convert script.md to transcription.py format without AI processing
    # This preserves user's exact content while maintaining proper format
    try:
        transcription_data = parse_script_to_transcription(request.script_content)
        
        # Save updated transcription.py
        transcription_content = str(transcription_data)
        FileService.save_output_file(task_id, "transcription.py", transcription_content)
    except Exception as e:
        # If conversion fails, log error but still save script
        print(f"[UPDATE SCRIPT] Failed to convert script to transcription: {e}")
        import traceback
        traceback.print_exc()
        # Try to get existing transcription data as fallback
        try:
            transcription_content = FileService.get_output_file_content(task_id, "transcription.py")
            import ast
            transcription_data = ast.literal_eval(transcription_content)
        except (FileNotFoundError, ValueError, SyntaxError):
            # If no existing transcription, use empty list
            task_info = task_manager.get_task_info(task_id)
            transcription_data = task_info.get("transcription_data", [])
            print("[UPDATE SCRIPT] Using existing transcription_data from task info")
    
    # Update task info with user's exact script content and converted transcription
    task_manager.update_task_info(task_id, {
        "script_content": request.script_content,  # User's edited content
        "transcription_data": transcription_data    # Converted from edited script (no AI)
    })
    
    return ScriptResponse(
        task_id=task_id,
        script_content=request.script_content,  # Return exactly what user sent
        transcription_data=transcription_data     # Return converted transcription
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
    
    # Update status and clear any previous errors
    await update_status_and_notify(
        task_id,
        TaskStatus.GENERATING_VIDEO,
        60.0,
        "Generating video...",
        current_step="Generating video...",
        error=None  # Explicitly clear previous errors
    )
    
    # Video parameters
    video_params = request.video_params
    voice_name = request.voice_name if request.voice_name else "Aoede"
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
                    print("[VIDEO GENERATION] Starting video generation in thread")
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
                        preset=preset,
                        voice_name=voice_name
                    )
                    print("[VIDEO GENERATION] Video generation completed successfully")
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
            print("[VIDEO GENERATION] Waiting for video generation to complete...")
            try:
                await video_future
                print("[VIDEO GENERATION] Video generation task completed")
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
            print("[VIDEO GENERATION FAILED] Full traceback:")
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
        
        # Get task info to retrieve project name
        task_info = task_manager.get_task_info(task_id)
        project_name = task_info.get("project_name")
        
        return TaskStatusResponse(
            task_id=task_id,
            status=progress.status,
            progress=progress.progress,
            current_step=progress.current_step,
            message=progress.message,
            error=progress.error,
            project_name=project_name
        )
    except ValueError:
        # Task not found, check if task directory exists
        from backend.core.config import OUTPUT_DIR
        task_dir = OUTPUT_DIR / task_id
        
        # Check if directory exists with files
        if task_dir.exists() and any(task_dir.iterdir()):
            # Task directory exists but not in manager, try to restore
            # Check for script or transcription files
            script_path = task_dir / "script.md"
            transcription_path = task_dir / "transcription.py"
            video_path = task_dir / "presentation.mp4"
            
            # Determine status based on available files
            if video_path and video_path.exists():
                # Video is completed
                status = TaskStatus.COMPLETED
                progress_val = 100.0
            elif transcription_path.exists():
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
            abstract_path = task_dir / "abstract.md"
            pdf_path = task_dir / "presentation.pdf"
            
            task_info = {
                "abstract_path": str(abstract_path) if abstract_path.exists() else None,
                "pdf_path": str(pdf_path) if pdf_path.exists() else None,
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


@router.get("/files/{task_id}/slides/{filename}")
async def get_slide_image(task_id: str, filename: str):
    """Get a slide image from task slides directory.
    
    Args:
        task_id: Task identifier
        filename: Slide image filename
        
    Returns:
        Image file
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        output_task_dir = FileService.get_output_task_directory(task_id)
        file_path = output_task_dir / "slides" / filename
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"Slide image not found: {filename}")
        
        # Determine content type
        ext = file_path.suffix.lower()
        content_type_map = {
            '.png': 'image/png',
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
        }
        content_type = content_type_map.get(ext, 'image/png')
        
        return FileResponse(
            path=str(file_path),
            media_type=content_type,
            filename=filename
        )
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Slide image not found: {filename}")


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


@router.get("/slides/{task_id}")
async def get_task_slides(task_id: str):
    """Get list of slide images for a task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        List of slide image filenames with page numbers
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    try:
        # Get slides directory
        output_task_dir = FileService.get_output_task_directory(task_id)
        slides_dir = output_task_dir / "slides"
        
        if not slides_dir.exists():
            return {
                "task_id": task_id,
                "slides": [],
                "count": 0
            }
        
        # Get all slide images
        import re
        slides = []
        for file in sorted(slides_dir.iterdir()):
            if file.suffix.lower() in ['.png', '.jpg', '.jpeg']:
                # Extract page number from filename (e.g., page_1.png)
                match = re.search(r'page_(\d+)', file.name)
                if match:
                    page_num = int(match.group(1))
                    slides.append({
                        "page": page_num,
                        "filename": file.name,
                        "url": f"/api/files/{task_id}/slides/{file.name}"
                    })
        
        # Sort by page number
        slides.sort(key=lambda x: x["page"])
        
        return {
            "task_id": task_id,
            "slides": slides,
            "count": len(slides)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing slides: {str(e)}")


@router.put("/project-name/{task_id}", response_model=TaskStatusResponse)
async def update_project_name(task_id: str, request: UpdateProjectNameRequest):
    """Update project name for a task.
    
    Args:
        task_id: Task identifier
        request: Update project name request
        
    Returns:
        Updated task status response
    """
    if not task_manager.task_exists(task_id):
        raise HTTPException(status_code=404, detail="Task not found")
    
    project_name = request.project_name.strip()
    if not project_name:
        raise HTTPException(status_code=400, detail="Project name cannot be empty")
    
    if len(project_name) > 20:
        raise HTTPException(status_code=400, detail="Project name must be 20 characters or less")
    
    # Update task info with new project name
    task_manager.update_task_info(task_id, {
        "project_name": project_name
    })
    
    # Get current progress to return
    progress = task_manager.get_task_progress(task_id)
    
    return TaskStatusResponse(
        task_id=task_id,
        status=progress.status,
        progress=progress.progress,
        current_step=progress.current_step,
        message=progress.message,
        error=progress.error,
        project_name=project_name
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


@router.get("/history")
async def get_history_projects():
    """Get list of all historical projects from output directory.
    
    Returns:
        List of project information including task_id, created_time, status, etc.
    """
    import os
    from datetime import datetime
    
    output_dir = Path("output")
    if not output_dir.exists():
        return {"projects": []}
    
    projects = []
    
    # Iterate through all directories in output/
    for project_dir in output_dir.iterdir():
        if not project_dir.is_dir():
            continue
            
        task_id = project_dir.name
        project_info = {
            "task_id": task_id,
            "created_time": None,
            "modified_time": None,
            "has_script": False,
            "has_video": False,
            "status": "unknown",
            "project_name": None
        }
        
        # Get directory creation/modification time
        try:
            stat = project_dir.stat()
            project_info["created_time"] = datetime.fromtimestamp(stat.st_ctime).isoformat()
            project_info["modified_time"] = datetime.fromtimestamp(stat.st_mtime).isoformat()
        except Exception as e:
            print(f"Error getting stats for {task_id}: {e}")
        
        # Check for script file
        script_file = project_dir / "script.md"
        if script_file.exists():
            project_info["has_script"] = True
        
        # Check for video file
        video_file = project_dir / "output.mp4"
        if video_file.exists():
            project_info["has_video"] = True
            project_info["status"] = "completed"
        elif project_info["has_script"]:
            project_info["status"] = "script_ready"
        
        # Check if task is in task_manager
        if task_manager.task_exists(task_id):
            task_info = task_manager.get_task_info(task_id)
            if "status" in task_info:
                project_info["status"] = task_info["status"]
            if "project_name" in task_info:
                project_info["project_name"] = task_info["project_name"]
        
        projects.append(project_info)
    
    # Sort by modified time (most recent first)
    projects.sort(key=lambda x: x.get("modified_time") or "", reverse=True)
    
    return {"projects": projects}

