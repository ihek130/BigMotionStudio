"""
YouTube Upload Engine (SaaS Multi-Tenant Version)
Uploads videos using user's stored OAuth tokens from database.
"""

import os
from datetime import datetime, timezone
from typing import Dict, Optional
import logging

from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

logger = logging.getLogger(__name__)


class YouTubeUploadEngine:
    """
    Multi-tenant YouTube upload engine.
    Uses PlatformConnection tokens from database instead of local pickle file.
    """
    
    def __init__(self):
        self.client_id = os.getenv('YOUTUBE_CLIENT_ID')
        self.client_secret = os.getenv('YOUTUBE_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("YouTube credentials not configured. Set YOUTUBE_CLIENT_ID and YOUTUBE_CLIENT_SECRET in .env")
    
    def upload_video(
        self,
        platform_connection,
        video_path: str,
        title: str,
        description: str,
        tags: list = None,
        thumbnail_path: str = None,
        scheduled_time: datetime = None,
        category_id: str = "26",  # Entertainment
        privacy_status: str = "public",
        made_for_kids: bool = False
    ) -> Dict:
        """
        Upload video to YouTube using user's OAuth tokens.
        
        Args:
            platform_connection: PlatformConnection object with YouTube tokens
            video_path: Path to video file
            title: Video title
            description: Video description
            tags: List of tags
            thumbnail_path: Optional thumbnail path
            scheduled_time: Optional scheduled publish time (UTC or local)
            category_id: YouTube category ID
            privacy_status: public, private, or unlisted
            made_for_kids: Whether video is made for kids
            
        Returns:
            Dict with upload result including video_id and video_url
        """
        try:
            logger.info(f"Starting YouTube upload: {title}")
            
            # Build credentials from database tokens
            credentials = self._build_credentials(platform_connection)
            
            # Check if token needs refresh
            if credentials.expired and credentials.refresh_token:
                logger.info("YouTube token expired, refreshing...")
                credentials.refresh(Request())
                
                # Update database with new token
                from database.connection import get_db
                db = next(get_db())
                platform_connection.access_token = credentials.token
                platform_connection.access_token_expires_at = credentials.expiry
                platform_connection.status = "active"
                db.commit()
                logger.info("YouTube token refreshed successfully")
            
            # Build YouTube service
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Prepare video metadata
            tags = tags or []
            request_body = {
                'snippet': {
                    'title': title[:100],  # YouTube limit is 100 chars
                    'description': description,
                    'tags': tags[:500],  # Max 500 tags
                    'categoryId': category_id
                },
                'status': {
                    'privacyStatus': privacy_status,
                    'madeForKids': made_for_kids,
                    'selfDeclaredMadeForKids': made_for_kids
                }
            }
            
            # Add scheduled publish time if provided
            if scheduled_time:
                # Convert to UTC if needed
                if scheduled_time.tzinfo is None:
                    # Assume local time, convert to UTC
                    scheduled_time = scheduled_time.astimezone()
                
                utc_time = scheduled_time.astimezone(timezone.utc)
                publish_at = utc_time.strftime('%Y-%m-%dT%H:%M:%S.000Z')
                
                request_body['status']['publishAt'] = publish_at
                request_body['status']['privacyStatus'] = 'private'  # Must be private for scheduling
                
                logger.info(f"Video scheduled for: {publish_at}")
            
            # Verify file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            # Upload video
            logger.info(f"Uploading video file: {video_path}")
            media = MediaFileUpload(
                video_path,
                chunksize=1024*1024*10,  # 10MB chunks
                resumable=True
            )
            
            request = youtube.videos().insert(
                part='snippet,status',
                body=request_body,
                media_body=media
            )
            
            response = None
            last_progress = 0
            
            while response is None:
                status, response = request.next_chunk()
                if status:
                    progress = int(status.progress() * 100)
                    if progress != last_progress:
                        logger.info(f"YouTube upload progress: {progress}%")
                        last_progress = progress
            
            video_id = response['id']
            video_url = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"✅ YouTube upload successful: {video_url}")
            
            # Upload thumbnail if provided
            thumbnail_uploaded = False
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    logger.info("Uploading custom thumbnail...")
                    thumb_request = youtube.thumbnails().set(
                        videoId=video_id,
                        media_body=MediaFileUpload(thumbnail_path)
                    )
                    thumb_request.execute()
                    logger.info("✅ Thumbnail uploaded successfully")
                    thumbnail_uploaded = True
                except Exception as thumb_error:
                    logger.warning(f"Thumbnail upload failed: {thumb_error}")
            
            return {
                'success': True,
                'platform': 'youtube',
                'video_id': video_id,
                'video_url': video_url,
                'title': title,
                'thumbnail_uploaded': thumbnail_uploaded,
                'scheduled_for': scheduled_time.isoformat() if scheduled_time else None,
                'uploaded_at': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"❌ YouTube upload failed: {e}", exc_info=True)
            
            # Update connection status if auth error
            if "invalid_grant" in str(e) or "invalid_client" in str(e):
                from database.connection import get_db
                db = next(get_db())
                platform_connection.status = "expired"
                platform_connection.last_error = str(e)
                db.commit()
            
            return {
                'success': False,
                'platform': 'youtube',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def _build_credentials(self, platform_connection) -> Credentials:
        """Build Google OAuth credentials from database connection"""
        return Credentials(
            token=platform_connection.access_token,
            refresh_token=platform_connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=self.client_id,
            client_secret=self.client_secret,
            scopes=[
                "https://www.googleapis.com/auth/youtube.upload",
                "https://www.googleapis.com/auth/youtube"
            ]
        )
    
    def verify_connection(self, platform_connection) -> bool:
        """
        Verify YouTube connection is valid.
        
        Args:
            platform_connection: PlatformConnection to verify
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            credentials = self._build_credentials(platform_connection)
            
            if credentials.expired and credentials.refresh_token:
                credentials.refresh(Request())
            
            youtube = build('youtube', 'v3', credentials=credentials)
            
            # Simple API call to verify connection
            youtube.channels().list(part="id", mine=True).execute()
            
            return True
            
        except Exception as e:
            logger.error(f"YouTube connection verification failed: {e}")
            return False
