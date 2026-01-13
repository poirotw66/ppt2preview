"""Gemini 3 Flash API integration service."""

import os
import json
import warnings
from typing import Optional, List, Tuple
from pathlib import Path

# Suppress FutureWarning for deprecated google.generativeai
# Must be set before importing google.generativeai
# Note: google.generativeai is deprecated but still functional
# TODO: Migrate to google.genai when stable version is available
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', message='.*google.generativeai.*')

try:
    # Try new API first (for future compatibility)
    try:
        import google.genai as genai
        GEMINI_AVAILABLE = True
        USE_NEW_API = True
    except ImportError:
        # Fall back to deprecated but working API
        import google.generativeai as genai
        GEMINI_AVAILABLE = True
        USE_NEW_API = False
except ImportError:
    GEMINI_AVAILABLE = False
    USE_NEW_API = False

import sys

# Add project root to path for prompt import
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.core.config import GEMINI_API_KEY, GEMINI_MODEL
from prompt import SOLO_PRESENTATION_PROMPT, TRANSCRIPT_REWRITER_PROMPT, PROJECT_NAME_GENERATOR_PROMPT


class GeminiService:
    """Service for interacting with Gemini 3 Flash API."""
    
    def __init__(self):
        """Initialize Gemini service."""
        if not GEMINI_AVAILABLE:
            raise ImportError(
                "google-generativeai package is not installed. "
                "Please install it with: pip install google-generativeai"
            )
        
        if not GEMINI_API_KEY:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not set. "
                "Please set it in your .env file or environment variables."
            )
        
        try:
            # Configure API key (works for both old and new API)
            if USE_NEW_API and hasattr(genai, 'Client'):
                # New API: google.genai
                self.client = genai.Client(api_key=GEMINI_API_KEY)
                self.model = self.client.models.get(GEMINI_MODEL)
                self._use_new_api = True
            elif hasattr(genai, 'configure'):
                # Old API: google.generativeai (deprecated but working)
                genai.configure(api_key=GEMINI_API_KEY)
                self.model = genai.GenerativeModel(GEMINI_MODEL)
                self._use_new_api = False
            else:
                raise RuntimeError("Unsupported genai API version")
        except Exception as e:
            raise RuntimeError(f"Failed to initialize Gemini service: {e}") from e
    
    def _get_response_text(self, response) -> str:
        """Extract text from response (compatible with both APIs)."""
        if hasattr(response, 'text') and response.text:
            return response.text
        elif hasattr(response, 'content') and response.content:
            # New API format
            return response.content
        elif hasattr(response, 'candidates') and response.candidates:
            # Alternative response format
            candidate = response.candidates[0]
            if hasattr(candidate, 'content'):
                parts = candidate.content.parts
                if parts:
                    return parts[0].text
        return None
    
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
        
        # Extract text from response
        response_text = self._get_response_text(response)
        if not response_text:
            raise ValueError("Failed to generate script from Gemini: Empty response")
        
        return response_text
    
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
        
        # Extract text from response
        response_text = self._get_response_text(response)
        if not response_text:
            raise ValueError("Failed to rewrite transcript from Gemini: Empty response")
        
        # Parse the response - it should be a Python list
        try:
            # Extract Python list from response
            transcript_text = response_text.strip()
            
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
    
    def optimize_script(self, script_content: str) -> Tuple[str, List[Tuple[str, str]]]:
        """Optimize existing script using TRANSCRIPT_REWRITER_PROMPT.
        
        This method takes an existing script and optimizes it using the
        transcript rewriter prompt, which adds TTS markers and improves
        the script for better speech synthesis.
        
        Args:
            script_content: Original script content to optimize
            
        Returns:
            Tuple of (optimized_script_content, transcription_data)
        """
        # Use rewrite_transcript to optimize the script
        transcription_data = self.rewrite_transcript(script_content)
        
        # Convert transcription back to script format
        # Group by page and convert to script format
        optimized_script_parts = []
        current_page = None
        
        for speaker, text in transcription_data:
            if speaker == "頁碼":
                # Extract page number from text like "[PAGE 1]"
                import re
                page_match = re.search(r'PAGE\s+(\d+)', text)
                if page_match:
                    page_num = int(page_match.group(1))
                    if current_page is not None:
                        optimized_script_parts.append("")  # Add blank line between pages
                    optimized_script_parts.append(f"### [PAGE {page_num}]")
                    current_page = page_num
            else:
                # Add dialogue text
                optimized_script_parts.append(text)
        
        optimized_script_content = "\n\n".join(optimized_script_parts)
        
        return optimized_script_content, transcription_data
    
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
    
    def generate_project_name(self, abstract_content: str) -> str:
        """Generate a concise project name based on abstract content.
        
        Args:
            abstract_content: Content from abstract markdown file
            
        Returns:
            Generated project name (within 10 characters)
        """
        prompt = f"""{PROJECT_NAME_GENERATOR_PROMPT}

---

## 簡報大綱內容

{abstract_content}

---

請根據以上簡報大綱，生成一個簡短精準的專案名稱（10字以內）。"""
        
        # Generate project name
        response = self.model.generate_content(prompt)
        
        # Extract text from response
        response_text = self._get_response_text(response)
        if not response_text:
            raise ValueError("Failed to generate project name from Gemini: Empty response")
        
        # Clean up the response (remove quotes, extra spaces, newlines)
        project_name = response_text.strip().strip('"').strip("'").strip()
        
        # Limit to 10 characters as safety measure
        if len(project_name) > 10:
            project_name = project_name[:10]
        
        return project_name
