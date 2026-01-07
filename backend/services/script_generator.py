"""Script generation service."""

from pathlib import Path
from typing import Tuple, List, Optional

from backend.services.gemini_service import GeminiService
from backend.services.file_service import FileService


class ScriptGenerator:
    """Service for generating presentation scripts."""
    
    def __init__(self):
        """Initialize script generator."""
        self.gemini_service = GeminiService()
    
    def generate_script_from_files(
        self,
        task_id: str,
        abstract_file_path: Path,
        pdf_file_path: Optional[Path] = None,
        length_mode: str = "MEDIUM"
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Generate script from uploaded files.
        
        Args:
            task_id: Task identifier
            abstract_file_path: Path to abstract markdown file
            pdf_file_path: Optional path to PDF file
            length_mode: Script length mode (SHORT, MEDIUM, LONG)
            
        Returns:
            Tuple of (script_content, transcription_data)
        """
        # Read abstract content
        with open(abstract_file_path, 'r', encoding='utf-8') as f:
            abstract_content = f.read()
        
        # Generate script using Gemini
        script_content, transcription_data = self.gemini_service.generate_complete_transcript(
            abstract_content=abstract_content,
            pdf_path=pdf_file_path,
            length_mode=length_mode
        )
        
        # Save script to task directory
        script_path = FileService.get_task_file_path(task_id, "script.md")
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        # Save transcription to task directory
        transcription_path = FileService.get_task_file_path(task_id, "transcription.py")
        with open(transcription_path, 'w', encoding='utf-8') as f:
            f.write(str(transcription_data))
        
        return script_content, transcription_data

