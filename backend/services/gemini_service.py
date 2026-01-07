"""Gemini 3 Flash API integration service."""

import os
import json
from typing import Optional, List, Tuple
from pathlib import Path

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False

import sys
from pathlib import Path

# Add project root to path for prompt import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import GEMINI_API_KEY, GEMINI_MODEL
from prompt import SOLO_PRESENTATION_PROMPT, TRANSCRIPT_REWRITER_PROMPT


class GeminiService:
    """Service for interacting with Gemini 3 Flash API."""
    
    def __init__(self):
        """Initialize Gemini service."""
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai package is not installed")
        
        if not GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        genai.configure(api_key=GEMINI_API_KEY)
        self.model = genai.GenerativeModel(GEMINI_MODEL)
    
    def generate_script(
        self,
        abstract_content: str,
        pdf_path: Optional[Path] = None,
        length_mode: str = "MEDIUM"
    ) -> str:
        """Generate presentation script using Gemini 3 Flash.
        
        Args:
            abstract_content: Content from abstract markdown file
            pdf_path: Optional path to PDF file (for future PDF analysis)
            length_mode: Script length mode (SHORT, MEDIUM, LONG)
            
        Returns:
            Generated script content
        """
        # Prepare prompt with abstract content
        prompt = SOLO_PRESENTATION_PROMPT.replace("{SHORT | MEDIUM | LONG}", length_mode)
        
        # Add abstract content to prompt
        full_prompt = f"""{prompt}

---

## 簡報大綱內容

{abstract_content}

---

請根據以上簡報大綱，生成逐頁導讀講稿。請直接從 `### [PAGE 1]` 開始你的演說。"""
        
        # Generate script
        response = self.model.generate_content(full_prompt)
        
        if not response.text:
            raise ValueError("Failed to generate script from Gemini")
        
        return response.text
    
    def rewrite_transcript(self, script_content: str) -> List[Tuple[str, str]]:
        """Rewrite script to transcription format using Gemini.
        
        Args:
            script_content: Original script content
            
        Returns:
            List of (speaker, text) tuples in transcription format
        """
        prompt = f"""{TRANSCRIPT_REWRITER_PROMPT}

---

## 原始講稿內容

{script_content}

---

請將以上講稿轉換為適合 Gemini TTS 的格式。"""
        
        response = self.model.generate_content(prompt)
        
        if not response.text:
            raise ValueError("Failed to rewrite transcript from Gemini")
        
        # Parse the response - it should be a Python list
        try:
            # Extract Python list from response
            transcript_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if transcript_text.startswith("```python"):
                transcript_text = transcript_text[9:]
            if transcript_text.startswith("```"):
                transcript_text = transcript_text[3:]
            if transcript_text.endswith("```"):
                transcript_text = transcript_text[:-3]
            
            transcript_text = transcript_text.strip()
            
            # Parse as Python literal
            import ast
            transcript_data = ast.literal_eval(transcript_text)
            
            # Validate format
            if not isinstance(transcript_data, list):
                raise ValueError("Transcript must be a list")
            
            # Convert to list of tuples
            result = []
            for item in transcript_data:
                if isinstance(item, (list, tuple)) and len(item) == 2:
                    result.append((str(item[0]), str(item[1])))
                else:
                    raise ValueError(f"Invalid transcript item format: {item}")
            
            return result
            
        except Exception as e:
            raise ValueError(f"Failed to parse transcript: {e}")
    
    def generate_complete_transcript(
        self,
        abstract_content: str,
        pdf_path: Optional[Path] = None,
        length_mode: str = "MEDIUM"
    ) -> Tuple[str, List[Tuple[str, str]]]:
        """Generate complete transcript in one call.
        
        Args:
            abstract_content: Content from abstract markdown file
            pdf_path: Optional path to PDF file
            length_mode: Script length mode
            
        Returns:
            Tuple of (script_content, transcription_data)
        """
        # Step 1: Generate script
        script_content = self.generate_script(abstract_content, pdf_path, length_mode)
        
        # Step 2: Rewrite to transcription format
        transcription_data = self.rewrite_transcript(script_content)
        
        return script_content, transcription_data

