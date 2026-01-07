# google-cloud-texttospeech minimum version 2.29.0 is required.

import os
import sys
import ast
import re
from pathlib import Path
from typing import List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from google.cloud import texttospeech
from pdf2image import convert_from_path
from moviepy.editor import ImageClip, concatenate_audioclips, AudioFileClip, concatenate_videoclips

PROJECT_ID = os.getenv("GOOGLE_CLOUD_PROJECT")

# Style prompts for different speakers
SPEAKER_STYLES = {
    "講者": "Speak in a warm, engaging, and authoritative tone like a knowledgeable teacher sharing fascinating insights with genuine enthusiasm. Guide the audience through the presentation slides with clear visual references and storytelling.",
}

def parse_transcription_file(filepath: str) -> List[Tuple[str, str]]:
    """Parse the transcription.py file to extract dialogue content.
    
    Args:
        filepath: Path to transcription.py file
        
    Returns:
        List of tuples (speaker, text)
    """
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use ast.literal_eval to safely parse the Python list
    try:
        dialogue_list = ast.literal_eval(content)
        return dialogue_list
    except Exception as e:
        print(f"Error parsing transcription file: {e}")
        raise

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
        print(f"Audio saved: {output_filepath}")
    
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
        img.verify()  # Verify the image
        img.close()
        # Check file size (should be > 0)
        if os.path.getsize(image_path) == 0:
            return False
        return True
    except Exception as e:
        print(f"  圖片驗證失敗: {e}")
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
    
    # Convert PDF to images with optimized DPI for video
    # Lower DPI = faster processing and smaller files
    # 72 DPI is sufficient for video (standard screen DPI, much faster)
    images = convert_from_path(pdf_path, dpi=72)
    
    image_paths = []
    for i, image in enumerate(images, start=1):
        image_path = os.path.join(output_dir, f"page_{i}.png")
        image.save(image_path, "PNG")
        # Verify the saved image
        if is_valid_image(image_path):
            image_paths.append(image_path)
            print(f"Saved page {i}: {image_path}")
        else:
            print(f"⚠️  警告: 第 {i} 頁圖片可能損壞，嘗試重新生成...")
            # Try saving again
            image.save(image_path, "PNG", optimize=True)
            if is_valid_image(image_path):
                image_paths.append(image_path)
                print(f"✓ 重新生成成功: {image_path}")
            else:
                print(f"❌ 錯誤: 無法修復第 {i} 頁圖片")
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
    total_tasks: int
) -> Tuple[int, str, float]:
    """Generate a single audio segment.
    
    Args:
        page_num: Page number
        segment_index: Segment index for this page
        combined_text: Text to synthesize
        speaker: Speaker name
        output_dir: Directory to save audio files
        task_index: Index of this task (for progress display)
        total_tasks: Total number of tasks
        
    Returns:
        Tuple of (page_number, audio_path, duration)
    """
    # Show progress: which sentence is being generated
    preview_text = combined_text[:50] + "..." if len(combined_text) > 50 else combined_text
    print(f"[{task_index + 1}/{total_tasks}] 正在產生第 {page_num} 頁，片段 {segment_index}: {preview_text}")
    
    audio_filename = f"page_{page_num}_segment_{segment_index}.mp3"
    audio_path = os.path.join(output_dir, audio_filename)
    
    style_prompt = SPEAKER_STYLES.get(speaker, SPEAKER_STYLES["講者"])
    synthesize_speech(style_prompt, combined_text, audio_path, language_code="cmn-tw")
    
    # Get audio duration
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration
    audio_clip.close()
    
    print(f"[{task_index + 1}/{total_tasks}] ✓ 完成: {audio_filename} (時長: {duration:.2f}秒)")
    return (page_num, audio_path, duration)

def process_transcription_to_audio(
    transcription_data: List[Tuple[str, str]],
    output_dir: str = "audio_segments",
    max_workers: int = 10
) -> List[Tuple[int, str, float]]:
    """Process transcription and generate audio files using multi-threading.
    
    Args:
        transcription_data: List of (speaker, text) tuples
        output_dir: Directory to save audio files
        max_workers: Maximum number of worker threads
        
    Returns:
        List of (page_number, audio_path, duration) tuples
    """
    Path(output_dir).mkdir(exist_ok=True)
    
    # First, collect all audio generation tasks
    tasks = []
    current_page = 1
    segment_index = 0
    
    i = 0
    while i < len(transcription_data):
        speaker, text = transcription_data[i]
        
        # Check if this is a page marker
        if speaker == "頁碼":
            current_page = extract_page_number(text)
            i += 1
            continue
        
        # Collect all dialogue for current speaker until next page marker
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
            # Combine dialogue parts
            combined_text = " ".join(dialogue_parts)
            
            # Add task to list
            tasks.append((
                current_page,
                segment_index,
                combined_text,
                current_speaker,
                output_dir
            ))
            segment_index += 1
    
    # Generate audio files in parallel using ThreadPoolExecutor
    audio_segments = []
    total_tasks = len(tasks)
    print(f"開始產生 {total_tasks} 個音訊片段，使用 {max_workers} 個線程...")
    print("-" * 80)
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks with task index
        future_to_task = {}
        for idx, task in enumerate(tasks):
            # Add task_index and total_tasks to task arguments
            task_with_index = task + (idx, total_tasks)
            future = executor.submit(_generate_audio_segment, *task_with_index)
            future_to_task[future] = task
        
        # Collect results as they complete
        completed_count = 0
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                audio_segments.append(result)
                completed_count += 1
            except Exception as e:
                task = future_to_task[future]
                print(f"❌ 錯誤: 產生第 {task[0]} 頁片段 {task[1]} 時發生錯誤: {e}")
                raise
        
        print("-" * 80)
        print(f"✓ 所有音訊片段產生完成！共 {completed_count} 個片段")
    
    # Sort by page number and segment index to maintain order
    audio_segments.sort(key=lambda x: (x[0], x[1]))
    
    return audio_segments

def create_video(
    pdf_path: str,
    transcription_path: str,
    output_video_path: str = "presentation.mp4"
):
    """Main function to create presentation video.
    
    Args:
        pdf_path: Path to PDF file
        transcription_path: Path to transcription.py file
        output_video_path: Output video file path
    """
    print("=" * 80)
    print("開始產生簡報解說影片")
    print("=" * 80)
    
    print("\nStep 1: 解析對話內容檔案...")
    transcription_data = parse_transcription_file(transcription_path)
    print(f"✓ 解析完成，共 {len(transcription_data)} 個對話項目")
    
    print("\nStep 2: 轉換 PDF 為圖片...")
    if os.path.exists("slides") and len([f for f in os.listdir("slides") if f.endswith(".png")]) > 0:
        print("⚠️  投影片圖片已存在，驗證檔案完整性...")
        existing_images = sorted([os.path.join("slides", f) for f in os.listdir("slides") if f.endswith(".png")], 
                                key=lambda x: int(re.search(r'page_(\d+)', x).group(1)))
        
        # Validate all images
        valid_images = []
        invalid_count = 0
        for img_path in existing_images:
            if is_valid_image(img_path):
                valid_images.append(img_path)
            else:
                invalid_count += 1
                page_num = re.search(r'page_(\d+)', img_path).group(1)
                print(f"  ❌ 第 {page_num} 頁圖片損壞: {img_path}")
        
        if invalid_count > 0:
            print(f"⚠️  發現 {invalid_count} 個損壞的圖片檔案，重新生成...")
            slide_images = pdf_to_images(pdf_path)
        else:
            slide_images = valid_images
            print(f"✓ 所有圖片檔案驗證通過，使用現有檔案")
    else:
        slide_images = pdf_to_images(pdf_path)
    print(f"✓ 投影片圖片準備完成，共 {len(slide_images)} 頁")
    
    print("\nStep 3: 產生音訊片段...")
    if os.path.exists("audio_segments") and len([f for f in os.listdir("audio_segments") if f.endswith(".mp3")]) > 0:
        print("⚠️  跳過：音訊檔案已存在，載入現有檔案...")
        audio_files = sorted([f for f in os.listdir("audio_segments") if f.endswith(".mp3")],
                            key=lambda x: (int(re.search(r'page_(\d+)', x).group(1)), 
                                          int(re.search(r'segment_(\d+)', x).group(1))))
        audio_segments = []
        for audio_file in audio_files:
            match = re.search(r'page_(\d+).*segment_(\d+)', audio_file)
            if match:
                page_num = int(match.group(1))
                audio_path = os.path.join("audio_segments", audio_file)
                print(f"  載入: {audio_file}...", end=" ", flush=True)
                audio_clip = AudioFileClip(audio_path)
                duration = audio_clip.duration
                audio_clip.close()
                audio_segments.append((page_num, audio_path, duration))
                print(f"✓ ({duration:.2f}秒)")
        print(f"✓ 載入 {len(audio_segments)} 個現有音訊片段")
    else:
        audio_segments = process_transcription_to_audio(transcription_data)
    
    print("Step 4: Creating video clips...")
    print("-" * 80)
    video_clips = []
    
    # Group audio segments by page
    page_audio_map = {}
    for page_num, audio_path, duration in audio_segments:
        if page_num not in page_audio_map:
            page_audio_map[page_num] = []
        page_audio_map[page_num].append((audio_path, duration))
    
    total_pages = len(page_audio_map)
    print(f"準備處理 {total_pages} 頁投影片...")
    
    # Create video clips for each page
    for idx, page_num in enumerate(sorted(page_audio_map.keys()), 1):
        if page_num > len(slide_images):
            print(f"⚠️  警告: 第 {page_num} 頁超出可用投影片範圍")
            continue
        
        print(f"[{idx}/{total_pages}] 正在處理第 {page_num} 頁...", end=" ", flush=True)
        sys.stdout.flush()
        image_path = slide_images[page_num - 1]  # Convert to 0-indexed
        
        # Get all audio segments for this page
        page_audios = page_audio_map[page_num]
        total_duration = sum(duration for _, duration in page_audios)
        
        print(f"載入圖片...", end=" ", flush=True)
        sys.stdout.flush()
        # Load and resize image using PIL for faster encoding
        # Large images (3000x1688) significantly slow down encoding
        from PIL import Image as PILImage
        pil_img = PILImage.open(image_path)
        original_size = pil_img.size
        
        # Resize to max 1920x1080 (1080p for better quality)
        max_width, max_height = 1920, 1080
        if original_size[0] > max_width or original_size[1] > max_height:
            # Calculate scale to fit within max_width x max_height
            scale = min(max_width / original_size[0], max_height / original_size[1])
            new_width = int(original_size[0] * scale)
            new_height = int(original_size[1] * scale)
            # Ensure dimensions are even (required by H.264 encoder)
            new_width = new_width if new_width % 2 == 0 else new_width - 1
            new_height = new_height if new_height % 2 == 0 else new_height - 1
            new_size = (new_width, new_height)
            # Use NEAREST resampling for maximum speed (quality is acceptable for video)
            pil_img = pil_img.resize(new_size, PILImage.Resampling.NEAREST)
            # Save resized image temporarily with fast compression
            temp_path = image_path.replace('.png', '_resized.png')
            pil_img.save(temp_path, 'PNG', optimize=True, compress_level=1)  # Fast compression
            image_path = temp_path
            print(f"縮放: {original_size} -> {new_size}...", end=" ", flush=True)
        
        img_clip = ImageClip(image_path).set_duration(total_duration)
        
        print(f"載入音訊 ({len(page_audios)} 個片段)...", end=" ", flush=True)
        sys.stdout.flush()
        # Load and concatenate audio clips for this page
        audio_clips = [AudioFileClip(audio_path) for audio_path, _ in page_audios]
        if len(audio_clips) > 1:
            combined_audio = concatenate_audioclips(audio_clips)
        else:
            combined_audio = audio_clips[0]
        
        print(f"合成影片片段...", end=" ", flush=True)
        sys.stdout.flush()
        # Set audio to image clip
        video_clip = img_clip.set_audio(combined_audio)
        video_clips.append(video_clip)
        
        print(f"✓ 完成 (時長: {total_duration:.2f}秒)", flush=True)
        sys.stdout.flush()
    
    print("-" * 80)
    print(f"✓ 所有影片片段創建完成！共 {len(video_clips)} 個片段")
    
    print("\nStep 5: 合併所有影片片段...")
    print("這可能需要一些時間，請稍候...", flush=True)
    sys.stdout.flush()
    final_video = concatenate_videoclips(video_clips, method="compose")
    print("✓ 影片片段合併完成", flush=True)
    
    print("\nStep 6: 輸出影片檔案...")
    print(f"正在將影片寫入: {output_video_path}")
    print("這是最耗時的步驟，請耐心等待...")
    print("進度條會顯示在下方：")
    print("-" * 80)
    sys.stdout.flush()
    
    # Use proglog's default bar logger for progress display
    # The default 'bar' logger already shows progress bars
    logger = 'bar'
    
    # Write video file with maximum speed optimizations
    final_video.write_videofile(
        output_video_path,
        fps=5,  # Very low FPS = much faster encoding (5 fps for presentations)
        codec='libx264',
        audio_codec='aac',
        verbose=True,
        logger=logger,
        preset='ultrafast',  # Fastest encoding preset
        bitrate='2000k',  # Lower bitrate = faster encoding
        threads=8,  # Use all available CPU cores
        ffmpeg_params=[
            '-crf', '30',  # Higher CRF = faster encoding (30 is acceptable for presentations)
            '-movflags', '+faststart',  # Enable fast start for web playback
            '-pix_fmt', 'yuv420p',  # Ensure compatibility
            '-tune', 'fastdecode',  # Optimize for fast decoding
            '-x264-params', 'keyint=60:min-keyint=60:scenecut=0:no-mbtree=1:no-cabac=1'  # Maximum speed settings
        ]
    )
    print()  # New line after progress bar
    
    print("-" * 80)
    print(f"✓ 影片產生成功: {output_video_path}", flush=True)
    
    # Cleanup
    final_video.close()
    for clip in video_clips:
        clip.close()

if __name__ == "__main__":
    # File paths
    PDF_PATH = "three_pig_pdf.pdf"
    TRANSCRIPTION_PATH = "transcription.py"
    OUTPUT_VIDEO = "three_pig_presentation.mp4"
    
    # The function will automatically skip audio/slides generation if files already exist
    create_video(PDF_PATH, TRANSCRIPTION_PATH, OUTPUT_VIDEO)
