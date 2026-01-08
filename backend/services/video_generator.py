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
        task_id: str,
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
            task_id: Task identifier for output directory
            fps: Frames per second
            resolution: Video resolution (width, height)
            bitrate: Video bitrate
            preset: Encoding preset
        """
        import traceback
        
        import traceback
        
        try:
            self._log("=" * 80)
            self._log("開始產生簡報解說影片")
            self._log("=" * 80)
            self._log(f"PDF 路徑: {pdf_path}")
            self._log(f"輸出路徑: {output_video_path}")
            self._log(f"任務 ID: {task_id}")
            self._log(f"FPS: {fps}, 解析度: {resolution}, 位元率: {bitrate}, 預設: {preset}")
            self._log(f"對話項目數量: {len(transcription_data)}")
            
            # Step 1: Parse transcription
            self._log("\nStep 1: 解析對話內容...")
            try:
                parsed_data = parse_transcription_data(transcription_data)
                self._log(f"✓ 解析完成，共 {len(parsed_data)} 個對話項目")
            except Exception as e:
                error_msg = f"解析對話內容失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            
            # Step 2: Convert PDF to images - Save directly to output directory
            from backend.services.file_service import FileService
            output_task_dir = FileService.get_output_task_directory(task_id)
            output_slides_dir = output_task_dir / "slides"
            output_slides_dir.mkdir(exist_ok=True, parents=True)
            
            self._log("\nStep 2: 轉換 PDF 為圖片...")
            try:
                if not os.path.exists(pdf_path):
                    raise FileNotFoundError(f"PDF 檔案不存在: {pdf_path}")
                # Generate images directly in output directory
                slide_images = pdf_to_images(pdf_path, str(output_slides_dir))
                self._log(f"✓ 投影片圖片準備完成，共 {len(slide_images)} 頁")
            except Exception as e:
                error_msg = f"轉換 PDF 為圖片失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            
            # Step 3: Generate audio segments - Save directly to output directory
            audio_dir = output_task_dir / "audio_segments"
            audio_dir.mkdir(exist_ok=True, parents=True)
            
            self._log("\nStep 3: 產生音訊片段...")
            try:
                # Generate directly in output directory
                audio_segments = process_transcription_to_audio(
                    parsed_data,
                    str(audio_dir),
                    max_workers=MAX_WORKERS,
                    progress_callback=self._log
                )
                self._log(f"✓ 所有音訊片段產生完成！共 {len(audio_segments)} 個片段")
            except Exception as e:
                error_msg = f"產生音訊片段失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            
            # Step 4: Create video clips
            self._log("\nStep 4: 創建影片片段...")
            video_clips = []
            
            try:
                page_audio_map = {}
                for page_num, audio_path, duration in audio_segments:
                    if page_num not in page_audio_map:
                        page_audio_map[page_num] = []
                    page_audio_map[page_num].append((audio_path, duration))
                
                total_pages = len(page_audio_map)
                self._log(f"準備處理 {total_pages} 頁投影片...")
                
                for idx, page_num in enumerate(sorted(page_audio_map.keys()), 1):
                    try:
                        if page_num > len(slide_images):
                            error_msg = f"第 {page_num} 頁超出可用投影片範圍 (共 {len(slide_images)} 頁)"
                            print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                            self._log(f"⚠️  警告: {error_msg}")
                            continue
                        
                        self._log(f"[{idx}/{total_pages}] 正在處理第 {page_num} 頁...")
                        # Use output directory images
                        image_path = slide_images[page_num - 1]
                        
                        if not os.path.exists(image_path):
                            raise FileNotFoundError(f"圖片檔案不存在: {image_path}")
                        
                        page_audios = page_audio_map[page_num]
                        total_duration = sum(duration for _, duration in page_audios)
                        
                        # Load and resize image to match target resolution
                        pil_img = PILImage.open(image_path)
                        original_size = pil_img.size
                        
                        max_width, max_height = resolution
                        
                        # Calculate scale to fit the target resolution while maintaining aspect ratio
                        scale_width = max_width / original_size[0]
                        scale_height = max_height / original_size[1]
                        
                        # Use the smaller scale to ensure image fits within target resolution
                        scale = min(scale_width, scale_height)
                        
                        # Calculate new dimensions
                        new_width = int(original_size[0] * scale)
                        new_height = int(original_size[1] * scale)
                        
                        # Ensure dimensions are even (required by H.264 encoder)
                        new_width = new_width if new_width % 2 == 0 else new_width - 1
                        new_height = new_height if new_height % 2 == 0 else new_height - 1
                        
                        # Resize image
                        new_size = (new_width, new_height)
                        # Use LANCZOS for better quality when scaling
                        pil_img = pil_img.resize(new_size, PILImage.Resampling.LANCZOS)
                        
                        # If image doesn't match target resolution, create a canvas and center the image
                        if (new_width, new_height) != (max_width, max_height):
                            # Create a black canvas with target resolution
                            canvas = PILImage.new('RGB', (max_width, max_height), (0, 0, 0))
                            # Calculate position to center the image
                            x_offset = (max_width - new_width) // 2
                            y_offset = (max_height - new_height) // 2
                            # Paste the resized image onto the canvas
                            canvas.paste(pil_img, (x_offset, y_offset))
                            pil_img = canvas
                            self._log(f"  圖片調整: {original_size} -> {new_size} -> {(max_width, max_height)} (居中)")
                        else:
                            self._log(f"  圖片調整: {original_size} -> {new_size}")
                        
                        # Save the final image
                        resized_name = f"page_{page_num}_resized.png"
                        resized_path = output_slides_dir / resized_name
                        pil_img.save(str(resized_path), 'PNG', optimize=True, compress_level=1)
                        image_path = str(resized_path)
                        
                        img_clip = ImageClip(image_path).set_duration(total_duration)
                        
                        # Load and concatenate audio
                        audio_clips = []
                        for audio_path, _ in page_audios:
                            if not os.path.exists(audio_path):
                                raise FileNotFoundError(f"音訊檔案不存在: {audio_path}")
                            audio_clips.append(AudioFileClip(audio_path))
                        
                        if len(audio_clips) > 1:
                            combined_audio = concatenate_audioclips(audio_clips)
                        else:
                            combined_audio = audio_clips[0]
                        
                        video_clip = img_clip.set_audio(combined_audio)
                        video_clips.append(video_clip)
                        
                        self._log(f"✓ 完成 (時長: {total_duration:.2f}秒)")
                    except Exception as e:
                        error_msg = f"處理第 {page_num} 頁時發生錯誤: {str(e)}"
                        error_traceback = traceback.format_exc()
                        print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                        print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                        self._log(f"✗ {error_msg}")
                        raise Exception(error_msg) from e
                
                self._log(f"✓ 所有影片片段創建完成！共 {len(video_clips)} 個片段")
            except Exception as e:
                error_msg = f"創建影片片段失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            
            # Step 5: Concatenate video clips
            self._log("\nStep 5: 合併所有影片片段...")
            try:
                if not video_clips:
                    raise ValueError("沒有可合併的影片片段")
                final_video = concatenate_videoclips(video_clips, method="compose")
                self._log("✓ 影片片段合併完成")
            except Exception as e:
                error_msg = f"合併影片片段失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            
            # Step 6: Write video file
            self._log("\nStep 6: 輸出影片檔案...")
            self._log(f"正在將影片寫入: {output_video_path}")
            
            try:
                # Ensure output directory exists
                output_dir = os.path.dirname(output_video_path)
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
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
            except Exception as e:
                error_msg = f"輸出影片檔案失敗: {str(e)}"
                error_traceback = traceback.format_exc()
                print(f"[VIDEO GENERATOR ERROR] {error_msg}")
                print(f"[VIDEO GENERATOR ERROR] Traceback:\n{error_traceback}")
                self._log(f"✗ {error_msg}")
                raise Exception(error_msg) from e
            finally:
                # Cleanup
                try:
                    final_video.close()
                    for clip in video_clips:
                        clip.close()
                except Exception as e:
                    print(f"[VIDEO GENERATOR WARNING] Cleanup error: {e}")
        
        except Exception as e:
            error_msg = f"影片產生過程發生錯誤: {str(e)}"
            error_traceback = traceback.format_exc()
            print("=" * 80)
            print(f"[VIDEO GENERATOR FAILED] {error_msg}")
            print(f"[VIDEO GENERATOR FAILED] Full traceback:")
            print(error_traceback)
            print("=" * 80)
            raise Exception(error_msg) from e

