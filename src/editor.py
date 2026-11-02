"""
Video editor using FFmpeg
"""
import subprocess
import json
from pathlib import Path
from typing import List, Optional, Dict
from .utils import setup_logger, Config

logger = setup_logger(__name__)


class VideoEditor:
    """Video editor using FFmpeg."""
    
    def __init__(self, config: Config):
        """
        Initialize video editor.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.output_dir = Path("./data/projects")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self._check_ffmpeg()
    
    def _check_ffmpeg(self):
        """Check if FFmpeg is installed."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("FFmpeg is available")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.error("FFmpeg not found. Please install FFmpeg.")
            raise RuntimeError("FFmpeg is required but not installed")
    
    def stitch_videos(
        self,
        video_paths: List[str],
        output_name: str,
        transition_duration: float = 0.5
    ) -> Optional[str]:
        """
        Stitch multiple videos together.
        
        Args:
            video_paths: List of video file paths in order
            output_name: Name for output file (without extension)
            transition_duration: Duration of crossfade transition (seconds)
            
        Returns:
            Path to output file or None if failed
        """
        if not video_paths:
            logger.error("No video paths provided")
            return None
        
        try:
            output_path = self.output_dir / f"{output_name}.mp4"
            
            if len(video_paths) == 1:
                # Just copy the single video
                return self._copy_video(video_paths[0], output_path)
            
            # Create concat file
            concat_file = self.output_dir / f"{output_name}_concat.txt"
            with open(concat_file, 'w') as f:
                for path in video_paths:
                    f.write(f"file '{Path(path).absolute()}'\n")
            
            # Build FFmpeg command
            codec = self.config.get('editor.default_codec', 'libx264')
            audio_codec = self.config.get('editor.default_audio_codec', 'aac')
            crf = self.config.get('editor.default_crf', 23)
            
            cmd = [
                'ffmpeg',
                '-f', 'concat',
                '-safe', '0',
                '-i', str(concat_file),
                '-c:v', codec,
                '-crf', str(crf),
                '-c:a', audio_codec,
                '-movflags', '+faststart',  # Optimize for web
                '-y',  # Overwrite output
                str(output_path)
            ]
            
            logger.info(f"Stitching {len(video_paths)} videos...")
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            # Clean up concat file
            concat_file.unlink()
            
            logger.info(f"Video stitched: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Stitching failed: {e}")
            return None
    
    def _copy_video(self, input_path: str, output_path: Path) -> str:
        """Copy a single video (fast, no re-encoding)."""
        cmd = [
            'ffmpeg',
            '-i', input_path,
            '-c', 'copy',
            '-y',
            str(output_path)
        ]
        
        subprocess.run(cmd, capture_output=True, check=True)
        logger.info(f"Video copied: {output_path}")
        return str(output_path)
    
    def add_audio(
        self,
        video_path: str,
        audio_path: str,
        output_name: str,
        audio_volume: float = 0.3
    ) -> Optional[str]:
        """
        Add background music to a video.
        
        Args:
            video_path: Path to video file
            audio_path: Path to audio file
            output_name: Name for output file
            audio_volume: Volume for background audio (0.0-1.0)
            
        Returns:
            Path to output file or None
        """
        try:
            output_path = self.output_dir / f"{output_name}.mp4"
            
            codec = self.config.get('editor.default_codec', 'libx264')
            audio_codec = self.config.get('editor.default_audio_codec', 'aac')
            crf = self.config.get('editor.default_crf', 23)
            
            # Mix original audio with background music
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-i', audio_path,
                '-filter_complex',
                f'[1:a]volume={audio_volume}[bg];[0:a][bg]amix=inputs=2:duration=shortest',
                '-c:v', codec,
                '-crf', str(crf),
                '-c:a', audio_codec,
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
            
            logger.info("Adding audio...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Audio added: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to add audio: {e}")
            return None
    
    def add_subtitles(
        self,
        video_path: str,
        srt_path: str,
        output_name: str,
        font: str = "Arial",
        font_size: int = 24
    ) -> Optional[str]:
        """
        Burn subtitles into video.
        
        Args:
            video_path: Path to video file
            srt_path: Path to SRT subtitle file
            output_name: Name for output file
            font: Font name
            font_size: Font size
            
        Returns:
            Path to output file or None
        """
        try:
            output_path = self.output_dir / f"{output_name}.mp4"
            
            codec = self.config.get('editor.default_codec', 'libx264')
            audio_codec = self.config.get('editor.default_audio_codec', 'aac')
            crf = self.config.get('editor.default_crf', 23)
            
            # Use subtitles filter
            subtitle_style = f"FontName={font},FontSize={font_size}"
            
            cmd = [
                'ffmpeg',
                '-i', video_path,
                '-vf', f"subtitles={srt_path}:force_style='{subtitle_style}'",
                '-c:v', codec,
                '-crf', str(crf),
                '-c:a', audio_codec,
                '-movflags', '+faststart',
                '-y',
                str(output_path)
            ]
            
            logger.info("Adding subtitles...")
            subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info(f"Subtitles added: {output_path}")
            return str(output_path)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to add subtitles: {e}")
            return None
    
    def get_video_info(self, video_path: str) -> Optional[Dict]:
        """
        Get video metadata using ffprobe.
        
        Args:
            video_path: Path to video file
            
        Returns:
            Dictionary with video info or None
        """
        try:
            cmd = [
                'ffprobe',
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                video_path
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            return json.loads(result.stdout)
            
        except subprocess.CalledProcessError as e:
            logger.error(f"FFprobe error: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to get video info: {e}")
            return None
