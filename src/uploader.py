"""
YouTube uploader with required disclosures for AI-generated content
"""
import os
import pickle
from pathlib import Path
from typing import Optional, Dict
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from .utils import setup_logger, Config

logger = setup_logger(__name__)

# YouTube API scopes
SCOPES = ['https://www.googleapis.com/auth/youtube.upload']


class YouTubeUploader:
    """Uploads videos to YouTube with proper AI content disclosures."""
    
    def __init__(self, config: Config):
        """
        Initialize YouTube uploader.
        
        Args:
            config: Configuration instance
        """
        self.config = config
        self.credentials = None
        self.youtube = None
        
        self.client_secret_file = config.get_env(
            'YOUTUBE_CLIENT_SECRET_FILE',
            'client_secret.json'
        )
        self.token_file = config.get_env(
            'YOUTUBE_TOKEN_FILE',
            'token.pickle'
        )
        
        self._authenticate()
    
    def _authenticate(self):
        """Authenticate with YouTube API."""
        # Load existing credentials
        if Path(self.token_file).exists():
            with open(self.token_file, 'rb') as token:
                self.credentials = pickle.load(token)
        
        # Refresh or get new credentials
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                logger.info("Refreshing YouTube credentials...")
                self.credentials.refresh(Request())
            else:
                if not Path(self.client_secret_file).exists():
                    raise FileNotFoundError(
                        f"Client secret file not found: {self.client_secret_file}\n"
                        "Please download it from Google Cloud Console and save it as client_secret.json"
                    )
                
                logger.info("Starting OAuth flow...")
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secret_file,
                    SCOPES
                )
                self.credentials = flow.run_local_server(port=0)
            
            # Save credentials
            with open(self.token_file, 'wb') as token:
                pickle.dump(self.credentials, token)
            logger.info("YouTube credentials saved")
        
        # Build YouTube service
        self.youtube = build('youtube', 'v3', credentials=self.credentials)
        logger.info("YouTube API client initialized")
    
    def upload_video(
        self,
        video_path: str,
        title: str,
        description: str = "",
        tags: Optional[list] = None,
        category_id: str = "22",
        privacy_status: str = "private",
        made_for_kids: bool = False,
        notify_subscribers: bool = False
    ) -> Optional[str]:
        """
        Upload a video to YouTube with AI content disclosure.
        
        IMPORTANT: This automatically sets the "altered or synthetic content" flag
        as required by YouTube for AI-generated videos.
        
        Args:
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            category_id: YouTube category ID
            privacy_status: 'private', 'unlisted', or 'public'
            made_for_kids: Whether video is made for kids
            notify_subscribers: Whether to notify subscribers
            
        Returns:
            Video ID if successful, None otherwise
        """
        try:
            logger.info(f"Uploading video: {title}")
            
            # Prepare video metadata
            body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'tags': tags or [],
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'selfDeclaredMadeForKids': made_for_kids,
                    'madeForKids': made_for_kids
                },
                # CRITICAL: AI content disclosure
                'contentDetails': {
                    'hasAlteredOrSyntheticContent': True
                }
            }
            
            # Prepare upload
            media = MediaFileUpload(
                video_path,
                chunksize=-1,  # Upload in a single request
                resumable=True,
                mimetype='video/*'
            )
            
            # Execute upload
            request = self.youtube.videos().insert(
                part='snippet,status,contentDetails',
                body=body,
                media_body=media,
                notifySubscribers=notify_subscribers
            )
            
            response = None
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    logger.info(f"Upload progress: {progress}%")
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Upload complete! Video ID: {video_id}")
            logger.info(f"Video URL: {video_url}")
            logger.info("✓ AI content disclosure flag set")
            
            return video_id
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
        except Exception as e:
            logger.error(f"Upload failed: {e}")
            return None
    
    def update_video_metadata(
        self,
        video_id: str,
        title: Optional[str] = None,
        description: Optional[str] = None,
        tags: Optional[list] = None
    ) -> bool:
        """
        Update metadata for an existing video.
        
        Args:
            video_id: YouTube video ID
            title: New title (optional)
            description: New description (optional)
            tags: New tags (optional)
            
        Returns:
            True if successful
        """
        try:
            # Get current video details
            video = self.youtube.videos().list(
                part='snippet',
                id=video_id
            ).execute()
            
            if not video['items']:
                logger.error(f"Video not found: {video_id}")
                return False
            
            snippet = video['items'][0]['snippet']
            
            # Update fields if provided
            if title:
                snippet['title'] = title
            if description:
                snippet['description'] = description
            if tags:
                snippet['tags'] = tags
            
            # Update video
            self.youtube.videos().update(
                part='snippet',
                body={
                    'id': video_id,
                    'snippet': snippet
                }
            ).execute()
            
            logger.info(f"Video metadata updated: {video_id}")
            return True
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return False
        except Exception as e:
            logger.error(f"Update failed: {e}")
            return False
    
    def get_upload_quota_usage(self) -> Optional[Dict]:
        """
        Get information about API quota usage.
        Note: This is approximate - YouTube doesn't provide exact quota info.
        
        Returns:
            Dictionary with quota info or None
        """
        try:
            # Each upload costs approximately 1600 quota units
            # Daily limit is 10,000 units = ~6 uploads per day
            
            response = self.youtube.channels().list(
                part='statistics',
                mine=True
            ).execute()
            
            if response['items']:
                channel = response['items'][0]
                return {
                    'channel_id': channel['id'],
                    'estimated_daily_limit': 6,
                    'note': 'YouTube API quota is 10,000 units/day, ~1,600 per upload'
                }
            
            return None
            
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            return None
