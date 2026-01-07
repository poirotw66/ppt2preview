"""Video generation service."""

import os
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Callable
from moviepy.editor import ImageClip, concatenate_audioclips, AudioFileClip, concatenate_videoclips
from PIL import Image as PILImage

from backend.utils.video_utils import (
    parse_transcription_data,
    pdf_to_images,
    is_valid_image,
    process_transcription_to_audio
)
from backend.core.config import DEFAULT_FPS, DEFAULT_RESOLUTION, DEFAULT_BITRATE, DEFAULT_PRESET, MAX_WORKERS


class VideoGenerator:
    """Service for generating presentation videos."""
    
    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize video generator.
        
        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback or (lambda x: None)
    
    def _log(self, message: str):
        """Log progress message."""
        self.progress_callback(message)
        sys.stdout.flush()
    
    def create_video(
        self,
        pdf_path: str,
        transcription_data: List[Tuple[str, str]],
        output_video_path: str,
        task_dir: Path,
        fps: int = DEFAULT_FPS,
        resolution: Tuple[int, int] = DEFAULT_RESOLUTION,
        bitrate: str = DEFAULT_BITRATE,
        preset: str = DEFAULT_PRESET
    ):
        """Create presentation video.
        
        Args:
            pdf_path: Path to PDF file
            transcription_data: List of (speaker, text) tuples
            output_video_path: Output video file path
            task_dir: Task directory for intermediate files
            fps: Frames per second
            resolution: Video resolution (width, height)
            bitrate: Video bitrate
            preset: Encoding preset
        """
        self._log("=" * 80)
        self._log("開始產生簡報解說影片")
        self._log("=" * 80)
        
        # Step 1: Parse transcription
        self._log("\nStep 1: 解析對話內容...")
        parsed_data = parse_transcription_data(transcription_data)
        self._log(f"✓ 解析完成，共 {len(parsed_data)} 個對話項目")
        
        # Step 2: Convert PDF to images
        slides_dir = task_dir / "slides"
        self._log("\nStep 2: 轉換 PDF 為圖片...")
        slide_images = pdf_to_images(pdf_path, str(slides_dir))
        self._log(f"✓ 投影片圖片準備完成，共 {len(slide_images)} 頁")
        
        # Step 3: Generate audio segments
        audio_dir = task_dir / "audio_segments"
        self._log("\nStep 3: 產生音訊片段...")
        audio_segments = process_transcription_to_audio(
            parsed_data,
            str(audio_dir),
            max_workers=MAX_WORKERS,
            progress_callback=self._log
        )
        self._log(f"✓ 所有音訊片段產生完成！共 {len(audio_segments)} 個片段")
        
        # Step 4: Create video clips
        self._log("\nStep 4: 創建影片片段...")
        video_clips = []
        
        page_audio_map = {}
        for page_num, audio_path, duration in audio_segments:
            if page_num not in page_audio_map:
                page_audio_map[page_num] = []
            page_audio_map[page_num].append((audio_path, duration))
        
        total_pages = len(page_audio_map)
        self._log(f"準備處理 {total_pages} 頁投影片...")
        
        for idx, page_num in enumerate(sorted(page_audio_map.keys()), 1):
            if page_num > len(slide_images):
                self._log(f"⚠️  警告: 第 {page_num} 頁超出可用投影片範圍")
                continue
            
            self._log(f"[{idx}/{total_pages}] 正在處理第 {page_num} 頁...")
            image_path = slide_images[page_num - 1]
            
            page_audios = page_audio_map[page_num]
            total_duration = sum(duration for _, duration in page_audios)
            
            # Load and resize image
            pil_img = PILImage.open(image_path)
            original_size = pil_img.size
            
            max_width, max_height = resolution
            if original_size[0] > max_width or original_size[1] > max_height:
                scale = min(max_width / original_size[0], max_height / original_size[1])
                new_width = int(original_size[0] * scale)
                new_height = int(original_size[1] * scale)
                new_width = new_width if new_width % 2 == 0 else new_width - 1
                new_height = new_height if new_height % 2 == 0 else new_height - 1
                new_size = (new_width, new_height)
                pil_img = pil_img.resize(new_size, PILImage.Resampling.NEAREST)
                temp_path = image_path.replace('.png', '_resized.png')
                pil_img.save(temp_path, 'PNG', optimize=True, compress_level=1)
                image_path = temp_path
            
            img_clip = ImageClip(image_path).set_duration(total_duration)
            
            # Load and concatenate audio
            audio_clips = [AudioFileClip(audio_path) for audio_path, _ in page_audios]
            if len(audio_clips) > 1:
                combined_audio = concatenate_audioclips(audio_clips)
            else:
                combined_audio = audio_clips[0]
            
            video_clip = img_clip.set_audio(combined_audio)
            video_clips.append(video_clip)
            
            self._log(f"✓ 完成 (時長: {total_duration:.2f}秒)")
        
        self._log(f"✓ 所有影片片段創建完成！共 {len(video_clips)} 個片段")
        
        # Step 5: Concatenate video clips
        self._log("\nStep 5: 合併所有影片片段...")
        final_video = concatenate_videoclips(video_clips, method="compose")
        self._log("✓ 影片片段合併完成")
        
        # Step 6: Write video file
        self._log("\nStep 6: 輸出影片檔案...")
        self._log(f"正在將影片寫入: {output_video_path}")
        
        final_video.write_videofile(
            output_video_path,
            fps=fps,
            codec='libx264',
            audio_codec='aac',
            verbose=True,
            logger='bar',
            preset=preset,
            bitrate=bitrate,
            threads=8,
            ffmpeg_params=[
                '-crf', '30',
                '-movflags', '+faststart',
                '-pix_fmt', 'yuv420p',
                '-tune', 'fastdecode',
                '-x264-params', 'keyint=60:min-keyint=60:scenecut=0:no-mbtree=1:no-cabac=1'
            ]
        )
        
        self._log(f"✓ 影片產生成功: {output_video_path}")
        
        # Cleanup
        final_video.close()
        for clip in video_clips:
            clip.close()

