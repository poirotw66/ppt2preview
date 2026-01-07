"""File management service."""

import os
import uuid
import shutil
from pathlib import Path
from typing import Tuple, Optional
from fastapi import UploadFile

from backend.core.config import UPLOAD_DIR, TEMP_DIR, OUTPUT_DIR


class FileService:
    """Service for managing uploaded files and task directories."""
    
    @staticmethod
    def create_task_directory(task_id: str) -> Path:
        """Create a directory for a task.
        
        Args:
            task_id: Unique task identifier
            
        Returns:
            Path to task directory
        """
        task_dir = TEMP_DIR / task_id
        task_dir.mkdir(exist_ok=True)
        return task_dir
    
    @staticmethod
    def save_uploaded_file(file: UploadFile, task_id: str, filename: Optional[str] = None) -> Path:
        """Save an uploaded file to task directory.
        
        Args:
            file: Uploaded file
            task_id: Task identifier
            filename: Optional custom filename
            
        Returns:
            Path to saved file
        """
        task_dir = FileService.create_task_directory(task_id)
        if filename is None:
            filename = file.filename
        file_path = task_dir / filename
        
        with open(file_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
        
        return file_path
    
    @staticmethod
    def get_task_file_path(task_id: str, filename: str) -> Path:
        """Get path to a file in task directory.
        
        Args:
            task_id: Task identifier
            filename: Filename
            
        Returns:
            Path to file
        """
        task_dir = TEMP_DIR / task_id
        return task_dir / filename
    
    @staticmethod
    def get_output_file_path(task_id: str, filename: str) -> Path:
        """Get path to an output file.
        
        Args:
            task_id: Task identifier
            filename: Filename
            
        Returns:
            Path to output file
        """
        output_task_dir = OUTPUT_DIR / task_id
        output_task_dir.mkdir(exist_ok=True, parents=True)
        return output_task_dir / filename
    
    @staticmethod
    def get_output_task_directory(task_id: str) -> Path:
        """Get output directory for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Path to output task directory
        """
        output_task_dir = OUTPUT_DIR / task_id
        output_task_dir.mkdir(exist_ok=True, parents=True)
        return output_task_dir
    
    @staticmethod
    def save_output_file(task_id: str, filename: str, content: str, encoding: str = 'utf-8') -> Path:
        """Save content to output file.
        
        Args:
            task_id: Task identifier
            filename: Filename
            content: File content
            encoding: File encoding (default: utf-8)
            
        Returns:
            Path to saved file
        """
        output_path = FileService.get_output_file_path(task_id, filename)
        with open(output_path, 'w', encoding=encoding) as f:
            f.write(content)
        return output_path
    
    @staticmethod
    def get_output_file_content(task_id: str, filename: str, encoding: str = 'utf-8') -> str:
        """Read content from output file.
        
        Args:
            task_id: Task identifier
            filename: Filename
            encoding: File encoding (default: utf-8)
            
        Returns:
            File content
        """
        output_path = FileService.get_output_file_path(task_id, filename)
        if not output_path.exists():
            raise FileNotFoundError(f"Output file not found: {output_path}")
        with open(output_path, 'r', encoding=encoding) as f:
            return f.read()
    
    @staticmethod
    def list_output_files(task_id: str) -> list[str]:
        """List all files in output directory for a task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            List of filenames
        """
        output_task_dir = FileService.get_output_task_directory(task_id)
        if not output_task_dir.exists():
            return []
        return [f.name for f in output_task_dir.iterdir() if f.is_file()]
    
    @staticmethod
    def cleanup_task(task_id: str, keep_output: bool = False):
        """Clean up task directory.
        
        Args:
            task_id: Task identifier
            keep_output: Whether to keep output files
        """
        task_dir = TEMP_DIR / task_id
        if task_dir.exists():
            if keep_output:
                # Move output files before cleanup
                output_task_dir = OUTPUT_DIR / task_id
                output_task_dir.mkdir(exist_ok=True)
                for file in task_dir.glob("*.mp4"):
                    shutil.move(str(file), str(output_task_dir / file.name))
            shutil.rmtree(task_dir, ignore_errors=True)

