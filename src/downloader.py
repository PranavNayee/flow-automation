"""
Video downloader module
"""
import requests
from pathlib import Path
from typing import Optional
from .utils import setup_logger
from .queue_manager import Job

logger = setup_logger(__name__)


class Downloader:
    """Downloads generated videos from Flow."""
    
    def __init__(self, download_dir: str = "./data/downloads"):
        """
        Initialize downloader.
        
        Args:
            download_dir: Directory to save downloaded videos
        """
        self.download_dir = Path(download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
    
    def download_video(self, job: Job, url: str) -> Optional[str]:
        """
        Download a video from URL.
        
        Args:
            job: Job containing scene info
            url: URL to download from
            
        Returns:
            Path to downloaded file or None if failed
        """
        try:
            logger.info(f"Downloading video for {job.scene_id}...")
            
            # Construct filename
            filename = f"{job.scene_id}.mp4"
            output_path = self.download_dir / filename
            
            # Download with streaming
            response = requests.get(url, stream=True, timeout=60)
            response.raise_for_status()
            
            # Get file size if available
            total_size = int(response.headers.get('content-length', 0))
            
            # Write to file
            with open(output_path, 'wb') as f:
                downloaded = 0
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        if total_size > 0:
                            progress = (downloaded / total_size) * 100
                            if downloaded % (1024 * 1024) < 8192:  # Log every MB
                                logger.info(f"Download progress: {progress:.1f}%")
            
            logger.info(f"Video downloaded: {output_path}")
            return str(output_path)
            
        except requests.RequestException as e:
            logger.error(f"Download failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error during download: {e}")
            return None
    
    def download_from_job(self, job: Job, page=None) -> Optional[str]:
        """
        Download video based on job metadata.
        
        Args:
            job: Job with download_info in metadata
            page: Playwright page (for button-based downloads)
            
        Returns:
            Path to downloaded file or None if failed
        """
        if not job.metadata or 'download_info' not in job.metadata:
            logger.error(f"No download info in job {job.scene_id}")
            return None
        
        download_info = job.metadata['download_info']
        download_type = download_info.get('type')
        
        if download_type in ['src', 'link']:
            url = download_info.get('url')
            if url:
                return self.download_video(job, url)
            else:
                logger.error("Download info missing URL")
                return None
        
        elif download_type == 'button' and page:
            # Handle download button click
            return self._download_via_button(job, page)
        
        else:
            logger.error(f"Unknown download type: {download_type}")
            return None
    
    def _download_via_button(self, job: Job, page) -> Optional[str]:
        """
        Download by clicking a button and waiting for the download.
        
        Args:
            job: Job info
            page: Playwright page
            
        Returns:
            Path to downloaded file or None
        """
        try:
            logger.info("Attempting download via button click...")
            
            # Set up download handler
            filename = f"{job.scene_id}.mp4"
            output_path = self.download_dir / filename
            
            # Wait for download to start
            with page.expect_download(timeout=60000) as download_info:
                # Click download button
                download_selector = page.locator('[aria-label*="download" i], a[download]').first
                download_selector.click()
            
            download = download_info.value
            
            # Save to our location
            download.save_as(str(output_path))
            
            logger.info(f"Video downloaded via button: {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Button download failed: {e}")
            return None
