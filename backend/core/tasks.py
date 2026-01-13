"""Background task management system."""

import threading
import json
import os
from typing import Dict, Optional, Callable
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path

from backend.api.models import TaskStatus
from backend.core.config import OUTPUT_DIR


@dataclass
class TaskProgress:
    """Task progress information."""
    status: TaskStatus
    progress: float  # 0.0 to 100.0
    current_step: Optional[str] = None
    message: Optional[str] = None
    error: Optional[str] = None


class TaskManager:
    """Manages background tasks and their progress."""
    
    def __init__(self):
        """Initialize task manager."""
        self._tasks: Dict[str, Dict] = {}
        self._progress: Dict[str, TaskProgress] = {}
        self._lock = threading.Lock()
        self._progress_callbacks: Dict[str, list] = {}  # task_id -> list of callbacks
        self._state_file = OUTPUT_DIR / ".task_manager_state.json"
        # Load existing tasks from disk
        self._load_state()
    
    def _load_state(self):
        """Load task state from disk if available."""
        if self._state_file.exists():
            try:
                with open(self._state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                    self._tasks = state.get('tasks', {})
                    # Restore progress
                    for task_id, progress_data in state.get('progress', {}).items():
                        try:
                            self._progress[task_id] = TaskProgress(
                                status=TaskStatus(progress_data['status']),
                                progress=progress_data.get('progress', 0.0),
                                current_step=progress_data.get('current_step'),
                                message=progress_data.get('message'),
                                error=progress_data.get('error')
                            )
                        except (KeyError, ValueError) as e:
                            print(f"Warning: Failed to restore progress for task {task_id}: {e}")
                            # Create default progress for this task
                            self._progress[task_id] = TaskProgress(
                                status=TaskStatus.PENDING,
                                progress=0.0
                            )
            except (json.JSONDecodeError, IOError, Exception) as e:
                print(f"Warning: Failed to load task state: {e}")
                # Reset to empty state on error
                self._tasks = {}
                self._progress = {}
    
    def _save_state(self):
        """Save task state to disk."""
        try:
            state = {
                'tasks': self._tasks,
                'progress': {
                    task_id: {
                        'status': progress.status.value,
                        'progress': progress.progress,
                        'current_step': progress.current_step,
                        'message': progress.message,
                        'error': progress.error
                    }
                    for task_id, progress in self._progress.items()
                }
            }
            with open(self._state_file, 'w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Warning: Failed to save task state: {e}")
    
    def create_task(self, task_id: str, task_info: Dict):
        """Create a new task.
        
        Args:
            task_id: Task identifier
            task_info: Task information dictionary
        """
        with self._lock:
            self._tasks[task_id] = task_info
            self._progress[task_id] = TaskProgress(
                status=TaskStatus.PENDING,
                progress=0.0
            )
            self._save_state()
    
    def task_exists(self, task_id: str) -> bool:
        """Check if task exists.
        
        Args:
            task_id: Task identifier
            
        Returns:
            True if task exists
        """
        with self._lock:
            # Check memory first
            if task_id in self._tasks:
                return True
            # Check disk
            task_dir = OUTPUT_DIR / task_id
            if task_dir.exists():
                # Try to restore
                self._load_state()
                return task_id in self._tasks
            return False
    
    def get_task_info(self, task_id: str) -> Dict:
        """Get task information.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task information dictionary
            
        Raises:
            ValueError: If task not found
        """
        with self._lock:
            # Try to restore from disk if not in memory
            if task_id not in self._tasks:
                # Check if task directory exists
                task_dir = OUTPUT_DIR / task_id
                if task_dir.exists():
                    # Try to restore task
                    self._load_state()
                    if task_id not in self._tasks:
                        raise ValueError(f"Task {task_id} not found")
                else:
                    raise ValueError(f"Task {task_id} not found")
            return self._tasks[task_id].copy()
    
    def update_task_info(self, task_id: str, updates: Dict):
        """Update task information.
        
        Args:
            task_id: Task identifier
            updates: Dictionary of updates
        """
        with self._lock:
            if task_id not in self._tasks:
                raise ValueError(f"Task {task_id} not found")
            self._tasks[task_id].update(updates)
            self._save_state()
    
    def add_progress_callback(self, task_id: str, callback: Callable[[TaskProgress], None]):
        """Add a progress callback for a task.
        
        Args:
            task_id: Task identifier
            callback: Callback function to call on progress updates
        """
        with self._lock:
            if task_id not in self._progress_callbacks:
                self._progress_callbacks[task_id] = []
            self._progress_callbacks[task_id].append(callback)
    
    def update_status(
        self,
        task_id: str,
        status: TaskStatus,
        progress: Optional[float] = None,
        message: Optional[str] = None,
        current_step: Optional[str] = None,
        error: Optional[str] = None
    ):
        """Update task status.
        
        Args:
            task_id: Task identifier
            status: New status
            progress: Progress percentage (0.0-100.0)
            message: Status message
            current_step: Current step description
            error: Error message if failed
        """
        with self._lock:
            if task_id not in self._progress:
                self._progress[task_id] = TaskProgress(
                    status=status,
                    progress=0.0
                )
            
            progress_obj = self._progress[task_id]
            progress_obj.status = status
            
            if progress is not None:
                progress_obj.progress = progress
            
            if message is not None:
                progress_obj.message = message
            
            if current_step is not None:
                progress_obj.current_step = current_step
            
            if error is not None:
                progress_obj.error = error
            
            # Save state after update
            self._save_state()
        
        # Call progress callbacks
        if task_id in self._progress_callbacks:
            for callback in self._progress_callbacks[task_id]:
                try:
                    callback(progress_obj)
                except Exception:
                    pass  # Ignore callback errors
    
    def get_task_progress(self, task_id: str) -> TaskProgress:
        """Get task progress.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task progress object
        """
        with self._lock:
            # Try to restore from disk if not in memory
            if task_id not in self._progress:
                # Check if task directory exists
                task_dir = OUTPUT_DIR / task_id
                if task_dir.exists():
                    # Try to restore task
                    self._load_state()
                    if task_id not in self._progress:
                        raise ValueError(f"Task {task_id} not found")
            return self._progress[task_id]
    
    def delete_task(self, task_id: str):
        """Delete a task.
        
        Args:
            task_id: Task identifier
        """
        with self._lock:
            if task_id in self._tasks:
                del self._tasks[task_id]
            if task_id in self._progress:
                del self._progress[task_id]

