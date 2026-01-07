"""Video generation utilities extracted from test.py"""

import os
import ast
import re
import sys
import time
import traceback
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError as FutureTimeoutError
from google.cloud import texttospeech
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_audioclips, AudioFileClip, concatenate_videoclips
from PIL import Image as PILImage

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

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
    language_code: str = "cmn-tw"
) -> str:
    """Synthesizes speech from the input text and saves it to an MP3 file.
    
    Google Cloud TTS has a limit of 4000 bytes for input.text + input.prompt combined.
    This function automatically splits long text into multiple chunks if needed.
    
    Args:
        prompt: Styling instructions on how to synthesize the content in the text field.
        text: The text to synthesize.
        output_filepath: The path to save the generated audio file.
        language_code: Language code (default: cmn-tw for Traditional Chinese)
        
    Returns:
        Path to generated audio file
    """
    # Clear invalid GOOGLE_APPLICATION_CREDENTIALS if it's a placeholder
    creds_path = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if creds_path and ("/path/to/your/" in creds_path or creds_path == "your-google-cloud-credentials.json"):
        # Remove invalid placeholder from environment
        if "GOOGLE_APPLICATION_CREDENTIALS" in os.environ:
            del os.environ["GOOGLE_APPLICATION_CREDENTIALS"]
    
    # Create client (will use default credentials automatically)
    client = texttospeech.TextToSpeechClient()
    
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
            synthesize_speech(chunk_prompt, chunk, chunk_path, language_code)
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
    # Create synthesis input with text and prompt
    synthesis_input = texttospeech.SynthesisInput(text=text, prompt=prompt)
    
    # Select the voice - using Gemini TTS model
    voice = texttospeech.VoiceSelectionParams(
        language_code=language_code,
        name="Charon",
        model_name="gemini-2.5-flash-tts"  # Using flash model for faster generation
    )
    
    # Configure audio output
    audio_config = texttospeech.AudioConfig(
        audio_encoding=texttospeech.AudioEncoding.MP3
    )
    
    # Perform the text-to-speech request
    response = client.synthesize_speech(
        input=synthesis_input,
        voice=voice,
        audio_config=audio_config
    )
    
    # Write the response's audio_content to file
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


def _generate_audio_segment_with_order(
    page_num: int,
    global_index: int,
    text: str,
    speaker: str,
    output_dir: str,
    original_index: int,
    total_items: int,
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
        progress_callback: Optional callback for progress updates
        
    Returns:
        Tuple of (page_number, audio_path, duration, global_index)
    """
    audio_filename = f"page_{page_num}_item_{global_index:04d}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    try:
        # Log start
        text_preview = text[:50] + "..." if len(text) > 50 else text
        print(f"[AUDIO GENERATION] Starting item {global_index} (page {page_num}): {text_preview}")
        
        style_prompt = SPEAKER_STYLES.get(speaker, SPEAKER_STYLES["講者"])
        synthesize_speech(style_prompt, text, audio_path, language_code="cmn-tw")
        
        # Verify file was created
        if not os.path.exists(audio_path):
            raise FileNotFoundError(f"Audio file was not created: {audio_path}")
        
        # Check file size
        file_size = os.path.getsize(audio_path)
        if file_size == 0:
            raise ValueError(f"Audio file is empty: {audio_path}")
        
        print(f"[AUDIO GENERATION] Audio file created: {audio_filename} ({file_size} bytes)")
        
        audio_clip = AudioFileClip(audio_path)
        duration = audio_clip.duration
        audio_clip.close()
        
        if progress_callback:
            progress_callback(f"[{original_index + 1}/{total_items}] Generated: {audio_filename} ({duration:.2f}s)")
        
        print(f"[AUDIO GENERATION] Completed item {global_index}: {audio_filename} ({duration:.2f}s)")
        
        return (page_num, audio_path, duration, global_index)
    except Exception as e:
        error_msg = f"Failed to generate audio for item {global_index} (page {page_num}): {str(e)}"
        print(f"[AUDIO GENERATION ERROR] {error_msg}")
        import traceback
        print(f"[AUDIO GENERATION ERROR] Traceback:\n{traceback.format_exc()}")
        raise Exception(error_msg) from e


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
    
    audio_segments = []
    total_tasks = len(tasks)
    
    if progress_callback:
        progress_callback(f"Found {total_tasks} dialogue items to process")
        progress_callback(f"Generating {total_tasks} audio files using {max_workers} threads...")
    
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
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_task = {}
        task_start_times = {}  # Track when each task started
        
        for task in tasks:
            # task structure: (page_num, global_index, text, speaker, output_dir, original_index, total_items)
            future = executor.submit(_generate_audio_segment_with_order, *task, progress_callback)
            future_to_task[future] = task
            task_start_times[future] = time.time()
        
        # Collect results in order with progress reporting and timeout handling
        results = {}
        completed_count = 0
        start_time = time.time()
        TIMEOUT_PER_TASK = 300  # 5 minutes per task (increased for long texts)
        CHECK_INTERVAL = 10  # Check status every 10 seconds
        
        print(f"[AUDIO GENERATION] Starting to process {total_tasks} tasks with timeout {TIMEOUT_PER_TASK}s per task")
        
        # Use a loop with timeout checking instead of just as_completed
        remaining_futures = set(future_to_task.keys())
        last_status_time = time.time()
        
        while remaining_futures:
            # Check for completed futures
            done_futures = [f for f in remaining_futures if f.done()]
            
            for future in done_futures:
                task = future_to_task[future]
                task_start_time = task_start_times.get(future, start_time)
                
                try:
                    result = future.result()  # Get result (should not block since done() is True)
                    task_duration = time.time() - task_start_time
                    
                    # result is (page_num, audio_path, duration, global_index)
                    global_idx = result[3]  # Extract global_index
                    results[global_idx] = result[:3]  # Store (page_num, audio_path, duration)
                    completed_count += 1
                    
                    # Report progress
                    elapsed_time = time.time() - start_time
                    if progress_callback:
                        progress_callback(f"Progress: {completed_count}/{total_tasks} audio files generated (elapsed: {elapsed_time:.1f}s)")
                    print(f"[AUDIO GENERATION] Progress: {completed_count}/{total_tasks} completed (task {global_idx} took {task_duration:.1f}s)")
                    
                except Exception as e:
                    task_duration = time.time() - task_start_time
                    error_msg = f"Error generating audio for item {task[5]} (global_index {task[1]}): {e}"
                    if progress_callback:
                        progress_callback(f"ERROR: {error_msg}")
                    print(f"[AUDIO GENERATION ERROR] {error_msg}")
                    print(f"[AUDIO GENERATION ERROR] Task took {task_duration:.1f}s before failing")
                    print(f"[AUDIO GENERATION ERROR] Traceback:\n{traceback.format_exc()}")
                    raise
                
                remaining_futures.remove(future)
            
            # Check for timeouts
            current_time = time.time()
            for future in list(remaining_futures):
                task = future_to_task[future]
                task_start_time = task_start_times.get(future, start_time)
                task_elapsed = current_time - task_start_time
                
                if task_elapsed > TIMEOUT_PER_TASK:
                    error_msg = f"Task {task[1]} (item {task[5]}, page {task[0]}) timed out after {task_elapsed:.1f}s"
                    if progress_callback:
                        progress_callback(f"ERROR: {error_msg}")
                    print(f"[AUDIO GENERATION ERROR] {error_msg}")
                    print(f"[AUDIO GENERATION ERROR] Text preview: {task[2][:100]}...")
                    # Cancel the future
                    future.cancel()
                    remaining_futures.remove(future)
                    raise Exception(error_msg)
            
            # Periodic status report
            if current_time - last_status_time >= CHECK_INTERVAL:
                pending_indices = [future_to_task[f][1] for f in remaining_futures]
                running_times = {future_to_task[f][1]: time.time() - task_start_times.get(f, start_time) 
                                for f in remaining_futures}
                print(f"[AUDIO GENERATION] Status: {completed_count}/{total_tasks} completed, {len(remaining_futures)} still running")
                if pending_indices:
                    print(f"[AUDIO GENERATION] Pending tasks: {sorted(pending_indices)[:10]}...")
                    print(f"[AUDIO GENERATION] Running times: {dict(list(running_times.items())[:5])}")
                last_status_time = current_time
            
            # Small sleep to avoid busy waiting
            if not done_futures:
                time.sleep(0.5)
        
        # Verify all tasks completed
        if len(results) != total_tasks:
            missing_indices = set(range(total_tasks)) - set(results.keys())
            error_msg = f"Not all audio files were generated. Missing indices: {sorted(missing_indices)}"
            if progress_callback:
                progress_callback(f"ERROR: {error_msg}")
            print(f"[AUDIO GENERATION ERROR] {error_msg}")
            print(f"[AUDIO GENERATION ERROR] Expected {total_tasks} files, got {len(results)}")
            print(f"[AUDIO GENERATION ERROR] Completed indices: {sorted(results.keys())}")
            raise ValueError(error_msg)
        
        # Sort by global_index to maintain order
        audio_segments = [results[idx] for idx in sorted(results.keys())]
        
        total_time = time.time() - start_time
        if progress_callback:
            progress_callback(f"✓ All {total_tasks} audio files generated successfully in {total_time:.1f}s")
        print(f"[AUDIO GENERATION] ✓ All {total_tasks} audio files generated successfully in {total_time:.1f}s")
    
    return audio_segments

