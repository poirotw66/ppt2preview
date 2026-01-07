"""Video generation utilities extracted from test.py"""

import os
import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import texttospeech
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_audioclips, AudioFileClip, concatenate_videoclips
from PIL import Image as PILImage

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Style prompts for different speakers
SPEAKER_STYLES = {
    "講者": "Speak in a warm, engaging, and authoritative tone like a knowledgeable teacher sharing fascinating insights with genuine enthusiasm. Guide the audience through the presentation slides with clear visual references and storytelling.",
}


def parse_transcription_data(transcription_data: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Parse transcription data (already in list format).
    
    Args:
        transcription_data: List of (speaker, text) tuples
        
    Returns:
        List of tuples (speaker, text)
    """
    return transcription_data


def synthesize_speech(
    prompt: str, 
    text: str, 
    output_filepath: str,
    language_code: str = "cmn-tw"
) -> str:
    """Synthesize speech from text using Gemini TTS.
    
    Args:
        prompt: Style prompt for TTS
        text: Text to synthesize
        output_filepath: Output audio file path
        language_code: Language code (default: cmn-tw for Traditional Chinese)
        
    Returns:
        Path to generated audio file
    """
    client = texttospeech.TextToSpeechClient()
    
    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)
    
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name="Charon",
        model_name="gemini-2.5-flash-tts"
    )
    
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    with open(output_filepath, "wb") as out:
        out.write(response.audio_content)
    
    return output_filepath


def is_valid_image(image_path: str) -> bool:
    """Check if an image file is valid and not corrupted.
    
    Args:
        image_path: Path to image file
        
    Returns:
        True if image is valid, False otherwise
    """
    try:
        from PIL import Image
        img = Image.open(image_path)
        img.verify()
        img.close()
        if os.path.getsize(image_path) == 0:
            return False
        return True
    except Exception:
        return False


def pdf_to_images(pdf_path: str, output_dir: str = "slides") -> List[str]:
    """Convert PDF pages to images.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images
        
    Returns:
        List of image file paths in page order
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    images = convert_from_path(pdf_path, dpi=72)
    
    image_paths = []
    for i, image in enumerate(images, start=1):
        image_path = os.path.join(output_dir, f"page_{i}.png")
        image.save(image_path, "PNG")
        if is_valid_image(image_path):
            image_paths.append(image_path)
        else:
            image.save(image_path, "PNG", optimize=True)
            if is_valid_image(image_path):
                image_paths.append(image_path)
            else:
                raise ValueError(f"無法生成有效的圖片檔案: {image_path}")
    
    return image_paths


def extract_page_number(page_marker: str) -> int:
    """Extract page number from page marker like '[PAGE 1]'.
    
    Args:
        page_marker: String like '[PAGE 1]'
        
    Returns:
        Page number (1-indexed)
    """
    match = re.search(r'PAGE\s+(\d+)', page_marker)
    if match:
        return int(match.group(1))
    return 1


def _generate_audio_segment(
    page_num: int,
    segment_index: int,
    combined_text: str,
    speaker: str,
    output_dir: str,
    task_index: int,
    total_tasks: int,
    progress_callback=None
) -> Tuple[int, str, float]:
    """Generate a single audio segment.
    
    Args:
        page_num: Page number
        segment_index: Segment index for this page
        combined_text: Text to synthesize
        speaker: Speaker name
        output_dir: Directory to save audio files
        task_index: Index of this task
        total_tasks: Total number of tasks
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (page_number, audio_path, duration)
    """
    audio_filename = f"page_{page_num}_segment_{segment_index}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    style_prompt = SPEAKER_STYLES.get(speaker, SPEAKER_STYLES["講者"])
    synthesize_speech(style_prompt, combined_text, audio_path, language_code="cmn-tw")
    
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    audio_clip.close()
    
    if progress_callback:
        progress_callback(f"Generated audio: {audio_filename} ({duration:.2f}s)")
    
    return (page_num, audio_path, duration)


def process_transcription_to_audio(
    transcription_data: List[Tuple[str, str]],
    output_dir: str = "audio_segments",
    max_workers: int = 10,
    progress_callback=None
) -> List[Tuple[int, str, float]]:
    """Process transcription and generate audio files using multi-threading.
    
    Args:
        transcription_data: List of (speaker, text) tuples
        output_dir: Directory to save audio files
        max_workers: Maximum number of worker threads
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of (page_number, audio_path, duration) tuples
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    tasks = []
    current_page = 1
    segment_index = 0
    
    i = 0
    while i < len(transcription_data):
        speaker, text = transcription_data[i]
        
        if speaker == "頁碼":
            current_page = extract_page_number(text)
            i += 1
            continue
        
        dialogue_parts = []
        current_speaker = speaker
        while i < len(transcription_data):
            speaker, text = transcription_data[i]
            if speaker == "頁碼":
                break
            if speaker in SPEAKER_STYLES:
                dialogue_parts.append(text)
                current_speaker = speaker
            i += 1
        
        if dialogue_parts:
            combined_text = " ".join(dialogue_parts)
            tasks.append((
                current_page,
                segment_index,
                combined_text,
                current_speaker,
                output_dir
            ))
            segment_index += 1
    
    audio_segments = []
    total_tasks = len(tasks)
    
    if progress_callback:
        progress_callback(f"Generating {total_tasks} audio segments using {max_workers} threads...")
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {}
        for idx, task in enumerate(tasks):
            task_with_index = task + (idx, total_tasks)
            future = executor.submit(_generate_audio_segment, *task_with_index, progress_callback)
            future_to_task[future] = task
        
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                audio_segments.append(result)
            except Exception as e:
                task = future_to_task[future]
                if progress_callback:
                    progress_callback(f"Error generating audio for page {task[0]}, segment {task[1]}: {e}")
                raise
    
    audio_segments.sort(key=lambda x: (x[0], x[1]))
    return audio_segments

