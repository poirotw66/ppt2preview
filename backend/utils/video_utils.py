"""Video generation utilities extracted from test.py"""

import os
import ast
import re
import sys
import time
import traceback
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from google.cloud import texttospeech
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_audioclips, AudioFileClip, concatenate_videoclips
from PIL import Image as PILImage

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Shared TTS client instance for all threads to reuse
_tts_client = None
_tts_client_lock = __import__('threading').Lock()

def _get_tts_client():
    """Get or create a shared TTS client instance.
    
    Returns:
        TextToSpeechClient instance
    """
    global _tts_client
    if _tts_client is None:
        with _tts_client_lock:
            if _tts_client is None:  # Double-check pattern
                # Clear invalid GOOGLE_APPLICATION_CREDENTIALS if it's a placeholder
                creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
                if creds_path and ("/path/to/your/" in creds_path or creds_path == "your-google-cloud-credentials.json"):
                    if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
                        del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
                _tts_client = texttospeech.TextToSpeechClient()
    return _tts_client

# Style prompts for different speakers
SPEAKER_STYLES = {
    "講者": "Speak in a warm, engaging, and authoritative tone like a knowledgeable teacher sharing fascinating insights with genuine enthusiasm. Guide the audience through the presentation slides with clear visual references and storytelling.",
}

def is_valid_speaker(speaker: str) -> bool:
    """Check if speaker should be processed.
    
    Args:
        speaker: Speaker name
        
    Returns:
        True if speaker should be processed
    """
    # Accept any speaker that is not "頁碼"
    return speaker != "頁碼" and len(speaker.strip()) > 0


def parse_transcription_data(transcription_data: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
    """Parse transcription data (already in list format).
    
    Args:
        transcription_data: List of (speaker, text) tuples
        
    Returns:
        List of tuples (speaker, text)
    """
    return transcription_data


def _split_text_by_bytes(text: str, max_bytes: int = 3500) -> List[str]:
    """Split text into chunks that don't exceed max_bytes.
    
    Args:
        text: Text to split
        max_bytes: Maximum bytes per chunk (default 3500 to leave room for prompt)
        
    Returns:
        List of text chunks
    """
    if len(text.encode('utf-8')) <= max_bytes:
        return [text]
    
    chunks = []
    current_chunk = ""
    
    # Split by sentences first (using common sentence endings)
    sentences = re.split(r'([。！？\n]+)', text)
    
    for i in range(0, len(sentences), 2):
        sentence = sentences[i]
        if i + 1 < len(sentences):
            sentence += sentences[i + 1]  # Include punctuation
        
        # Check if adding this sentence would exceed limit
        test_chunk = current_chunk + sentence if current_chunk else sentence
        if len(test_chunk.encode('utf-8')) <= max_bytes:
            current_chunk = test_chunk
        else:
            # Save current chunk if it has content
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = sentence
            else:
                # Even single sentence is too long, split by characters
                sentence_bytes = sentence.encode('utf-8')
                if len(sentence_bytes) > max_bytes:
                    # Split by character boundaries
                    char_list = list(sentence)
                    temp_chunk = ""
                    for char in char_list:
                        test = temp_chunk + char
                        if len(test.encode('utf-8')) <= max_bytes:
                            temp_chunk = test
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk)
                            temp_chunk = char
                    current_chunk = temp_chunk
                else:
                    current_chunk = sentence
    
    # Add remaining chunk
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


def synthesize_speech(
    prompt: str, 
    text: str, 
    output_filepath: str,
    language_code: str = "cmn-tw",
    voice_name: str = "Aoede",
    max_retries: int = 3
) -> str:
    """Synthesizes speech from the input text and saves it to an MP3 file.
    
    Google Cloud TTS has a limit of 4000 bytes for input.text + input.prompt combined.
    This function automatically splits long text into multiple chunks if needed.
    Includes automatic retry with exponential backoff for network errors.
    
    Args:
        prompt: Styling instructions on how to synthesize the content in the text field.
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
        language_code: Language code (default: cmn-tw for Traditional Chinese)
        voice_name: Voice name for TTS (default: Aoede)
        max_retries: Maximum number of retry attempts (default: 3)
        
    Returns:
        Path to generated audio file
    """
    from google.api_core import exceptions as google_exceptions
    
    # Check total size (prompt + text)
    prompt_bytes = len(prompt.encode('utf-8'))
    text_bytes = len(text.encode('utf-8'))
    total_bytes = prompt_bytes + text_bytes
    MAX_BYTES = 4000
    
    # If total exceeds limit, split text into chunks
    if total_bytes > MAX_BYTES:
        # Reserve space for prompt (with some buffer)
        max_text_bytes = MAX_BYTES - prompt_bytes - 100  # 100 bytes buffer
        text_chunks = _split_text_by_bytes(text, max_text_bytes)
        
        # Generate audio for each chunk and concatenate
        audio_files = []
        base_path = output_filepath.rsplit('.', 1)[0]  # Remove extension
        extension = output_filepath.rsplit('.', 1)[1] if '.' in output_filepath else 'mp3'
        
        for idx, chunk in enumerate(text_chunks):
            chunk_path = f"{base_path}_chunk_{idx}.{extension}"
            # Recursively call synthesize_speech for each chunk (without prompt after first chunk)
            chunk_prompt = prompt if idx == 0 else ""  # Only use prompt for first chunk
            synthesize_speech(chunk_prompt, chunk, chunk_path, language_code, voice_name, max_retries)
            audio_files.append(chunk_path)
        
        # Concatenate audio files
        from moviepy.editor import concatenate_audioclips, AudioFileClip
        audio_clips = [AudioFileClip(f) for f in audio_files]
        if len(audio_clips) > 1:
            final_audio = concatenate_audioclips(audio_clips)
            final_audio.write_audiofile(output_filepath, logger=None)
            final_audio.close()
        else:
            # Only one chunk, just rename
            import shutil
            shutil.move(audio_files[0], output_filepath)
        
        # Clean up chunk files
        for f in audio_files:
            if os.path.exists(f) and f != output_filepath:
                try:
                    os.remove(f)
                except:
                    pass
        
        # Close audio clips
        for clip in audio_clips:
            clip.close()
        
        return output_filepath
    
    # Normal case: text fits within limit
    # Retry loop with exponential backoff
    last_exception = None
    for attempt in range(max_retries):
        try:
            # Get shared TTS client (reuses connection across threads)
            client = _get_tts_client()
            
            # Create synthesis input with text and prompt
            synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)
            
            # Select the voice - using Gemini TTS model
            voice = texttospeech.VoiceSelectionParams(
                language_code=language_code,
                name=voice_name,
                model_name="gemini-2.5-flash-tts"  # Using flash model for faster generation
            )
            
            # Configure audio output
            audio_config = texttospeech.AudioConfig(
                audio_encoding=texttospeech.AudioEncoding.MP3
            )
            
            # Perform the text-to-speech request with timeout
            response = client.synthesize_speech(
                input=synthesis_input,
                voice=voice,
                audio_config=audio_config,
                timeout=120.0  # 2 minutes timeout
            )
            
            # Write the response's audio_content to file
            with open(output_filepath, "wb") as out:
                out.write(response.audio_content)
            
            # Success - return immediately
            return output_filepath
            
        except (google_exceptions.Unknown, 
                google_exceptions.DeadlineExceeded, 
                google_exceptions.ServiceUnavailable,
                google_exceptions.InternalServerError) as e:
            last_exception = e
            if attempt < max_retries - 1:
                # Exponential backoff: 2s, 4s, 6s
                wait_time = (attempt + 1) * 2
                print(f"[TTS RETRY] Attempt {attempt + 1}/{max_retries} failed: {str(e)[:100]}")
                print(f"[TTS RETRY] Retrying in {wait_time}s...")
                time.sleep(wait_time)
                
                # Reset client on connection errors to get fresh connection
                global _tts_client
                _tts_client = None
            else:
                print(f"[TTS ERROR] All {max_retries} attempts failed for: {output_filepath}")
                raise
        except google_exceptions.InvalidArgument as e:
            # Handle sensitive content errors specially
            error_str = str(e)
            if "sensitive or harmful content" in error_str or "Unable to generate audio" in error_str:
                print(f"[TTS ERROR] Sensitive content detected: {error_str[:200]}")
                print(f"[TTS ERROR] Attempting to clean text and retry...")
                
                # Clean the text by removing special characters
                import re
                cleaned_text = re.sub(r'[^\w\s\u4e00-\u9fff\u3000-\u303f]', '', text)
                cleaned_text = ' '.join(cleaned_text.split())  # Normalize whitespace
                
                if cleaned_text and cleaned_text != text:
                    try:
                        print(f"[TTS RETRY] Trying with cleaned text: {cleaned_text[:100]}...")
                        client = _get_tts_client()
                        synthesis_input = texttospeech.SynthesisInput(text=cleaned_text, prompt=prompt)
                        voice = texttospeech.VoiceSelectionParams(
                            language_code=language_code,
                            name=voice_name,
                            model_name="gemini-2.5-flash-tts"
                        )
                        audio_config = texttospeech.AudioConfig(
                            audio_encoding=texttospeech.AudioEncoding.MP3
                        )
                        response = client.synthesize_speech(
                            input=synthesis_input,
                            voice=voice,
                            audio_config=audio_config,
                            timeout=120.0
                        )
                        with open(output_filepath, "wb") as out:
                            out.write(response.audio_content)
                        print(f"[TTS RETRY] ✓ Success with cleaned text")
                        return output_filepath
                    except Exception as retry_error:
                        print(f"[TTS RETRY] Cleaned text also failed: {str(retry_error)[:100]}")
                        # Will create silent audio in the calling function
                        raise google_exceptions.InvalidArgument(f"Sensitive content error: {error_str}") from e
                else:
                    # Text is already clean or empty, raise original error
                    raise
            else:
                # Other InvalidArgument errors, raise as-is
                raise
        except Exception as e:
            # For other exceptions, don't retry
            print(f"[TTS ERROR] Unexpected error (no retry): {e}")
            raise
    
    # If we get here, all retries failed
    if last_exception:
        raise last_exception
    
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


def pdf_to_images(
    pdf_path: str, 
    output_dir: str = "slides", 
    dpi: int = 200,
    max_width: Optional[int] = None,
    max_height: Optional[int] = None,
    progress_callback=None
) -> List[str]:
    """Convert PDF pages to images.
    
    Args:
        pdf_path: Path to PDF file
        output_dir: Directory to save images
        dpi: DPI for image conversion (default: 200 for high quality)
        max_width: Maximum width for resizing (optional)
        max_height: Maximum height for resizing (optional)
        progress_callback: Optional callback function(current, total) for progress updates
        
    Returns:
        List of image file paths in page order
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    if progress_callback:
        progress_callback(0, "開始轉換 PDF...")
    
    # Convert PDF to images
    images = convert_from_path(pdf_path, dpi=dpi)
    total_pages = len(images)
    
    if progress_callback:
        progress_callback(0, f"正在處理 {total_pages} 頁...")
    
    image_paths = []
    for i, image in enumerate(images, start=1):
        # Resize if needed
        if max_width or max_height:
            original_width, original_height = image.size
            new_width, new_height = original_width, original_height
            
            if max_width and original_width > max_width:
                ratio = max_width / original_width
                new_width = max_width
                new_height = int(original_height * ratio)
            
            if max_height and new_height > max_height:
                ratio = max_height / new_height
                new_height = max_height
                new_width = int(new_width * ratio)
            
            # Ensure dimensions are even (required for video encoding)
            new_width = new_width if new_width % 2 == 0 else new_width + 1
            new_height = new_height if new_height % 2 == 0 else new_height + 1
            
            if new_width != original_width or new_height != original_height:
                image = image.resize((new_width, new_height), PILImage.Resampling.LANCZOS)
        
        image_path = os.path.join(output_dir, f"page_{i}.png")
        
        # Save with optimization for smaller file size
        image.save(image_path, "PNG", optimize=True, compress_level=6)
        
        if is_valid_image(image_path):
            image_paths.append(image_path)
        else:
            # Retry with different settings
            image.save(image_path, "PNG", optimize=True)
            if is_valid_image(image_path):
                image_paths.append(image_path)
            else:
                raise ValueError(f"無法生成有效的圖片檔案: {image_path}")
    
    if progress_callback:
        progress_callback(100, f"完成！已轉換 {total_pages} 頁")
    
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


def _generate_audio_segment_with_order(
    page_num: int,
    global_index: int,
    text: str,
    speaker: str,
    output_dir: str,
    original_index: int,
    total_items: int,
    voice_name: str = "Aoede",
    progress_callback=None
) -> Tuple[int, str, float, int]:
    """Generate a single audio segment for one dialogue item.
    
    Args:
        page_num: Page number
        global_index: Global index to maintain order
        text: Single text to synthesize (not combined)
        speaker: Speaker name
        output_dir: Directory to save audio files
        original_index: Original index in transcription_data
        total_items: Total number of items
        voice_name: Voice name for TTS (default: Aoede)
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (page_number, audio_path, duration, global_index)
    """
    audio_filename = f"page_{page_num}_item_{global_index:04d}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Log start (simplified for less I/O overhead)
        if global_index % 5 == 0 or total_items <= 10:  # Only log every 5th item or if total is small
            text_preview = text[:50] + "..." if len(text) > 50 else text
            print(f"[AUDIO GENERATION] Starting item {global_index} (page {page_num}): {text_preview}")
        
        style_prompt = SPEAKER_STYLES.get(speaker, SPEAKER_STYLES["講者"])
        
        try:
            synthesize_speech(style_prompt, text, audio_path, language_code="cmn-tw", voice_name=voice_name)
        except Exception as tts_error:
            # Check if it's a sensitive content error from Google TTS
            error_str = str(tts_error)
            if "sensitive or harmful content" in error_str or "Unable to generate audio" in error_str:
                print(f"[AUDIO GENERATION] ⚠️  Sensitive content detected for item {global_index}, attempting cleanup...")
                
                # Try 1: Clean the text by removing special characters and punctuation
                import re
                cleaned_text = re.sub(r'[^\w\s一-鿿　-〿]', '', text)
                cleaned_text = ' '.join(cleaned_text.split())  # Normalize whitespace
                
                if cleaned_text:
                    try:
                        print(f"[AUDIO GENERATION] Retry with cleaned text: {cleaned_text[:50]}...")
                        synthesize_speech(style_prompt, cleaned_text, audio_path, language_code="cmn-tw", voice_name=voice_name)
                        print(f"[AUDIO GENERATION] ✓ Success with cleaned text")
                    except Exception as retry_error:
                        # Try 2: Create silent audio as fallback
                        print(f"[AUDIO GENERATION] Cleaned text also failed, creating silent audio...")
                        # Don't raise, will be handled by outer exception handler
                        raise tts_error
                else:
                    # Empty text after cleaning, create silent audio
                    print(f"[AUDIO GENERATION] Text became empty after cleaning, creating silent audio...")
                    raise tts_error
            else:
                # Re-raise non-sensitive-content errors
                raise
        
        # Verify file was created and get size
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file was not created: {audio_path}")
        
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise ValueError(f"Audio file is empty: {audio_path}")
        
        # Get duration
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        
        # Simplified logging - one line per file
        print(f"[AUDIO GENERATION] ✓ {audio_filename} ({duration:.1f}s, {file_size//1024}KB)")
        
        if progress_callback:
            progress_callback(f"[{original_index + 1}/{total_items}] Generated: {audio_filename} ({duration:.2f}s)")
        
        return (page_num, audio_path, duration, global_index)
    except Exception as e:
        error_msg = f"Failed to generate audio for item {global_index} (page {page_num}): {str(e)}"
        print(f"[AUDIO GENERATION ERROR] {error_msg}")
        
        # Check if it's a sensitive content error
        if "sensitive or harmful content" in str(e) or "Unable to generate audio" in str(e):
            print(f"[AUDIO GENERATION] ⚠️  Creating silent audio as fallback for item {global_index}...")
            try:
                # Create a silent audio file as fallback (2 seconds)
                from pydub import AudioSegment
                silent_duration_ms = 2000  # 2 seconds
                silent_audio = AudioSegment.silent(duration=silent_duration_ms)
                silent_audio.export(audio_path, format="mp3")
                
                duration = silent_duration_ms / 1000.0
                file_size = os.path.getsize(audio_path)
                print(f"[AUDIO GENERATION] ✓ Created silent audio: {audio_filename} ({duration:.1f}s, {file_size//1024}KB)")
                
                if progress_callback:
                    progress_callback(f"[{original_index + 1}/{total_items}] Skipped (sensitive content): {audio_filename}")
                
                return (page_num, audio_path, duration, global_index)
            except Exception as fallback_error:
                print(f"[AUDIO GENERATION ERROR] Failed to create silent audio: {fallback_error}")
                # Re-raise original error if fallback also fails
                raise Exception(error_msg) from e
        else:
            # For other errors, print traceback and raise
            import traceback
            print(f"[AUDIO GENERATION ERROR] Traceback:\n{traceback.format_exc()}")
            raise Exception(error_msg) from e


def process_transcription_to_audio(
    transcription_data: List[Tuple[str, str]],
    output_dir: str = "audio_segments",
    max_workers: int = 10,
    voice_name: str = "Aoede",
    progress_callback=None
) -> List[Tuple[int, str, float]]:
    """Process transcription and generate audio files using multi-threading.
    
    Args:
        transcription_data: List of (speaker, text) tuples
        output_dir: Directory to save audio files
        max_workers: Maximum number of worker threads
        voice_name: Voice name for TTS (default: Aoede)
        progress_callback: Optional callback for progress updates
        
    Returns:
        List of (page_number, audio_path, duration) tuples
    """
    from concurrent.futures import as_completed
    
    Path(output_dir).mkdir(exist_ok=True)
    
    tasks = []
    current_page = 1
    global_index = 0  # Global index to maintain order across all pages
    
    # Process each item in transcription_data sequentially
    for i, (speaker, text) in enumerate(transcription_data):
        # Handle page markers
        if speaker == "頁碼":
            current_page = extract_page_number(text)
            continue
        
        # Process valid dialogue items one by one (each sentence separately)
        if is_valid_speaker(speaker):
            # Use default style prompt if speaker not in SPEAKER_STYLES
            if speaker not in SPEAKER_STYLES:
                speaker = "講者"
            
            # Create a task for this single dialogue item
            # Use global_index to maintain order
            tasks.append((
                current_page,
                global_index,  # Use global_index to maintain order
                text,  # Single text, not combined
                speaker,
                output_dir,
                i,  # Original index in transcription_data
                len(transcription_data)  # Total items
            ))
            global_index += 1
    
    total_tasks = len(tasks)
    
    if progress_callback:
        progress_callback(f"Found {total_tasks} dialogue items to process")
    
    print(f"[AUDIO GENERATION] Found {total_tasks} dialogue items to process")
    
    if total_tasks == 0:
        error_msg = "No dialogue items found in transcription data. Please check the transcription format."
        if progress_callback:
            progress_callback(f"ERROR: {error_msg}")
        print(f"[AUDIO GENERATION ERROR] {error_msg}")
        print(f"[AUDIO GENERATION ERROR] Transcription data length: {len(transcription_data)}")
        print(f"[AUDIO GENERATION ERROR] Transcription data sample (first 10 items):")
        for idx, item in enumerate(transcription_data[:10]):
            print(f"[AUDIO GENERATION ERROR]   [{idx}] speaker='{item[0]}', text='{item[1][:50]}...'")
        raise ValueError(error_msg)
    
    # Check if audio files already exist
    if os.path.exists(output_dir):
        existing_files = [f for f in os.listdir(output_dir) if f.endswith(".mp3")]
        if len(existing_files) > 0:
            print(f"[AUDIO GENERATION] Found {len(existing_files)} existing audio files")
            if progress_callback:
                progress_callback(f"Found {len(existing_files)} existing audio files")
            
            # Check if we have all required files
            expected_files = set()
            for task in tasks:
                page_num = task[0]
                global_idx = task[1]
                expected_filename = f"page_{page_num}_item_{global_idx:04d}.mp3"
                expected_files.add(expected_filename)
            
            existing_file_set = set(existing_files)
            
            if expected_files.issubset(existing_file_set):
                # All required files exist, load them
                print(f"[AUDIO GENERATION] All {total_tasks} audio files already exist, skipping generation")
                if progress_callback:
                    progress_callback(f"All {total_tasks} audio files already exist, skipping generation")
                
                # Use multi-threading to quickly load audio file metadata
                audio_segments = []
                
                def load_audio_metadata(task):
                    """Load audio file metadata (duration) for a single file."""
                    page_num = task[0]
                    global_idx = task[1]
                    audio_filename = f"page_{page_num}_item_{global_idx:04d}.mp3"
                    audio_path = os.path.join(output_dir, audio_filename)
                    
                    if os.path.exists(audio_path):
                        try:
                            # Get duration using AudioFileClip
                            audio_clip = AudioFileClip(audio_path)
                            duration = audio_clip.duration
                            audio_clip.close()
                            return (page_num, audio_path, duration, global_idx)
                        except Exception as e:
                            print(f"[AUDIO GENERATION WARNING] Failed to load {audio_filename}: {e}")
                            return None
                    return None
                
                # Load metadata in parallel for speed
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = [executor.submit(load_audio_metadata, task) for task in tasks]
                    
                    load_results = {}
                    for future in as_completed(futures):
                        result = future.result()
                        if result is not None:
                            global_idx = result[3]
                            load_results[global_idx] = result[:3]
                
                # Check if all files loaded successfully
                if len(load_results) == total_tasks:
                    # Sort by global_index to maintain order
                    audio_segments = [load_results[idx] for idx in sorted(load_results.keys())]
                    print(f"[AUDIO GENERATION] ✓ All {total_tasks} audio files loaded successfully")
                    if progress_callback:
                        progress_callback(f"✓ All {total_tasks} audio files loaded successfully")
                    return audio_segments
                else:
                    print(f"[AUDIO GENERATION] Some files failed to load ({len(load_results)}/{total_tasks}), will regenerate all")
                    if progress_callback:
                        progress_callback(f"Some files failed to load, will regenerate all")
            else:
                missing_files = expected_files - existing_file_set
                print(f"[AUDIO GENERATION] Missing {len(missing_files)} files, will generate them")
                if progress_callback:
                    progress_callback(f"Missing {len(missing_files)} files, will generate them")
    
    # Generate audio files
    if progress_callback:
        progress_callback(f"Generating {total_tasks} audio files using {max_workers} threads...")
    print(f"[AUDIO GENERATION] Generating {total_tasks} audio files using {max_workers} threads...")
    
    # Use ThreadPoolExecutor with as_completed (like test.py)
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_task = {}
        for task in tasks:
            # task structure: (page_num, global_index, text, speaker, output_dir, original_index, total_items)
            future = executor.submit(_generate_audio_segment_with_order, *task, voice_name, progress_callback)
            future_to_task[future] = task
        
        # Collect results as they complete (like test.py)
        results = {}
        completed_count = 0
        start_time = time.time()
        
        print(f"[AUDIO GENERATION] Starting to process {total_tasks} tasks")
        
        failed_tasks = []  # Track failed tasks for retry or fallback
        
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                # result is (page_num, audio_path, duration, global_index)
                global_idx = result[3]  # Extract global_index
                results[global_idx] = result[:3]  # Store (page_num, audio_path, duration)
                completed_count += 1
                
                elapsed_time = time.time() - start_time
                print(f"[AUDIO GENERATION] Progress: {completed_count}/{total_tasks} completed (elapsed: {elapsed_time:.1f}s)")
                
                if progress_callback:
                    progress_callback(f"Progress: {completed_count}/{total_tasks} audio files generated (elapsed: {elapsed_time:.1f}s)")
                    
            except Exception as e:
                task = future_to_task[future]
                error_msg = f"Error generating audio for item {task[5]} (global_index {task[1]}): {e}"
                print(f"[AUDIO GENERATION ERROR] {error_msg}")
                
                # Check if it's a sensitive content error
                error_str = str(e)
                if "sensitive or harmful content" in error_str or "Unable to generate audio" in error_str:
                    print(f"[AUDIO GENERATION] ⚠️  Sensitive content detected, will create silent audio as fallback")
                    # Try to create silent audio as fallback
                    try:
                        page_num = task[0]
                        global_idx = task[1]
                        output_dir = task[4]
                        audio_filename = f"page_{page_num}_item_{global_idx:04d}.mp3"
                        audio_path = os.path.join(output_dir, audio_filename)
                        
                        from pydub import AudioSegment
                        silent_duration_ms = 2000  # 2 seconds
                        silent_audio = AudioSegment.silent(duration=silent_duration_ms)
                        silent_audio.export(audio_path, format="mp3")
                        
                        duration = silent_duration_ms / 1000.0
                        results[global_idx] = (page_num, audio_path, duration)
                        completed_count += 1
                        
                        print(f"[AUDIO GENERATION] ✓ Created silent audio fallback: {audio_filename}")
                        if progress_callback:
                            progress_callback(f"Skipped (sensitive content): {audio_filename} - using silent audio")
                    except Exception as fallback_error:
                        print(f"[AUDIO GENERATION ERROR] Failed to create silent audio fallback: {fallback_error}")
                        failed_tasks.append((task, error_msg))
                else:
                    # For other errors, log but don't fail immediately
                    print(f"[AUDIO GENERATION ERROR] Traceback:\n{traceback.format_exc()}")
                    failed_tasks.append((task, error_msg))
                    if progress_callback:
                        progress_callback(f"ERROR: {error_msg}")
        
        # After all tasks complete, check if we have failures
        if failed_tasks:
            print(f"[AUDIO GENERATION WARNING] {len(failed_tasks)} tasks failed out of {total_tasks}")
            for task, error_msg in failed_tasks:
                print(f"[AUDIO GENERATION WARNING] Failed task: {error_msg}")
            
            # If we have some results, continue with what we have
            if len(results) > 0:
                print(f"[AUDIO GENERATION] Continuing with {len(results)}/{total_tasks} successful audio files")
                if progress_callback:
                    progress_callback(f"Warning: {len(failed_tasks)} audio files failed, continuing with {len(results)} successful files")
            else:
                # All tasks failed, raise error
                error_msg = f"All {total_tasks} audio generation tasks failed"
                print(f"[AUDIO GENERATION ERROR] {error_msg}")
                if progress_callback:
                    progress_callback(f"ERROR: {error_msg}")
                raise ValueError(error_msg)
        
        # Verify all tasks completed (or have fallbacks)
        if len(results) != total_tasks:
            missing_indices = set(range(total_tasks)) - set(results.keys())
            print(f"[AUDIO GENERATION WARNING] Not all audio files were generated. Missing indices: {sorted(missing_indices)}")
            print(f"[AUDIO GENERATION WARNING] Expected {total_tasks} files, got {len(results)}")
            print(f"[AUDIO GENERATION WARNING] Completed indices: {sorted(results.keys())}")
            
            # Try to create silent audio for missing indices
            for missing_idx in missing_indices:
                try:
                    # Find the task for this index
                    task = None
                    for t in tasks:
                        if t[1] == missing_idx:  # global_index matches
                            task = t
                            break
                    
                    if task:
                        page_num = task[0]
                        output_dir = task[4]
                        audio_filename = f"page_{page_num}_item_{missing_idx:04d}.mp3"
                        audio_path = os.path.join(output_dir, audio_filename)
                        
                        from pydub import AudioSegment
                        silent_duration_ms = 2000  # 2 seconds
                        silent_audio = AudioSegment.silent(duration=silent_duration_ms)
                        silent_audio.export(audio_path, format="mp3")
                        
                        duration = silent_duration_ms / 1000.0
                        results[missing_idx] = (page_num, audio_path, duration)
                        print(f"[AUDIO GENERATION] ✓ Created silent audio fallback for missing index {missing_idx}")
                except Exception as fallback_error:
                    print(f"[AUDIO GENERATION ERROR] Failed to create fallback for index {missing_idx}: {fallback_error}")
            
            # Check again after creating fallbacks
            if len(results) != total_tasks:
                missing_indices = set(range(total_tasks)) - set(results.keys())
                error_msg = f"Failed to generate {len(missing_indices)} audio files even with fallbacks. Missing indices: {sorted(missing_indices)}"
                print(f"[AUDIO GENERATION ERROR] {error_msg}")
                if progress_callback:
                    progress_callback(f"ERROR: {error_msg}")
                raise ValueError(error_msg)
            else:
                print(f"[AUDIO GENERATION] ✓ All {total_tasks} audio files ready (some are silent fallbacks)")
                if progress_callback:
                    progress_callback(f"✓ All {total_tasks} audio files ready (some are silent fallbacks)")
        
        # Sort by global_index to maintain order
        audio_segments = [results[idx] for idx in sorted(results.keys())]
        
        total_time = time.time() - start_time
        print(f"[AUDIO GENERATION] ✓ All {total_tasks} audio files generated successfully in {total_time:.1f}s")
        if progress_callback:
            progress_callback(f"✓ All {total_tasks} audio files generated successfully in {total_time:.1f}s")
    
    return audio_segments

