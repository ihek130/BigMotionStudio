"""
TikTok Upload Engine
Uploads videos to TikTok using TikTok Content Posting API.
"""

import os
from datetime import datetime
from typing import Dict, Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class TikTokUploadEngine:
    """
    TikTok video upload engine using TikTok Content Posting API.
    Requires approved TikTok Developer account and app credentials.
    """
    
    def __init__(self):
        self.api_url = "https://open.tiktokapis.com"
        self.client_key = os.getenv("TIKTOK_CLIENT_KEY")
        self.client_secret = os.getenv("TIKTOK_CLIENT_SECRET")
        
        if not self.client_key or not self.client_secret:
            logger.warning("TikTok credentials not configured. Set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET when ready.")
    
    async def upload_video(
        self,
        platform_connection,
        video_path: str,
        title: str,
        description: str = "",
        privacy_level: str = "SELF_ONLY",  # SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, PUBLIC_TO_EVERYONE
        disable_duet: bool = False,
        disable_stitch: bool = False,
        disable_comment: bool = False
    ) -> Dict:
        """
        Upload video to TikTok.
        
        TikTok Upload Process:
        1. Initialize upload and get upload URL
        2. Upload video file to provided URL
        3. Publish video
        
        Args:
            platform_connection: PlatformConnection with TikTok tokens
            video_path: Path to video file
            title: Video title/caption
            description: Additional description
            privacy_level: SELF_ONLY, MUTUAL_FOLLOW_FRIENDS, or PUBLIC_TO_EVERYONE
            disable_duet: Whether to disable duet feature
            disable_stitch: Whether to disable stitch feature
            disable_comment: Whether to disable comments
            
        Returns:
            Dict with upload result including video_id and share_url
        """
        
        # Check if credentials are configured
        if not self.client_key or not self.client_secret:
            logger.warning("TikTok upload skipped - credentials not configured yet")
            return {
                'success': False,
                'platform': 'tiktok',
                'error': 'TikTok API credentials not configured. Will be available after deployment.',
                'error_type': 'ConfigurationError',
                'note': 'TikTok requires app approval. Configure TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET after deployment.'
            }
        
        try:
            logger.info(f"Starting TikTok upload: {title}")
            
            access_token = platform_connection.access_token
            
            # Check token expiry
            if platform_connection.needs_refresh:
                logger.warning("TikTok token needs refresh")
                # Note: TikTok token refresh should be handled by platform_routes
            
            # Verify file exists
            if not os.path.exists(video_path):
                raise FileNotFoundError(f"Video file not found: {video_path}")
            
            file_size = os.path.getsize(video_path)
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Initialize upload
                logger.info("Step 1: Initializing TikTok upload...")
                
                init_response = await client.post(
                    f"{self.api_url}/v2/post/publish/video/init/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "post_info": {
                            "title": title[:150],  # TikTok limit
                            "privacy_level": privacy_level,
                            "disable_duet": disable_duet,
                            "disable_stitch": disable_stitch,
                            "disable_comment": disable_comment,
                            "video_cover_timestamp_ms": 1000  # Use frame at 1 second as cover
                        },
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "video_size": file_size,
                            "chunk_size": file_size,  # Upload in single chunk
                            "total_chunk_count": 1
                        }
                    }
                )
                
                init_data = init_response.json()
                
                if init_data.get("error"):
                    error_msg = init_data["error"].get("message", "Unknown error")
                    raise Exception(f"TikTok init failed: {error_msg}")
                
                publish_id = init_data["data"]["publish_id"]
                upload_url = init_data["data"]["upload_url"]
                
                logger.info(f"Upload initialized: {publish_id}")
                
                # Step 2: Upload video file
                logger.info("Step 2: Uploading video file...")
                
                with open(video_path, 'rb') as video_file:
                    upload_response = await client.put(
                        upload_url,
                        headers={
                            "Content-Type": "video/mp4"
                        },
                        content=video_file.read()
                    )
                
                if upload_response.status_code != 200:
                    raise Exception(f"File upload failed with status {upload_response.status_code}")
                
                logger.info("File uploaded successfully")
                
                # Step 3: Check publish status
                logger.info("Step 3: Checking publish status...")
                
                status_response = await client.post(
                    f"{self.api_url}/v2/post/publish/status/fetch/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "publish_id": publish_id
                    }
                )
                
                status_data = status_response.json()
                
                if status_data.get("error"):
                    error_msg = status_data["error"].get("message", "Unknown error")
                    raise Exception(f"TikTok status check failed: {error_msg}")
                
                publish_status = status_data["data"]["status"]
                
                if publish_status == "PUBLISH_COMPLETE":
                    video_id = status_data["data"].get("video_id", publish_id)
                    share_url = status_data["data"].get("share_url", f"https://www.tiktok.com/@user/video/{video_id}")
                    
                    logger.info(f"✅ TikTok upload successful: {share_url}")
                    
                    return {
                        'success': True,
                        'platform': 'tiktok',
                        'video_id': video_id,
                        'video_url': share_url,
                        'publish_id': publish_id,
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                else:
                    # Video is processing
                    logger.info(f"TikTok video processing: {publish_status}")
                    
                    return {
                        'success': True,
                        'platform': 'tiktok',
                        'video_id': publish_id,
                        'status': publish_status,
                        'note': 'Video is processing on TikTok. Check status later.',
                        'uploaded_at': datetime.utcnow().isoformat()
                    }
                
        except Exception as e:
            logger.error(f"❌ TikTok upload failed: {e}", exc_info=True)
            
            # Update connection status if auth error
            if "invalid_token" in str(e) or "unauthorized" in str(e).lower():
                from database.connection import get_db
                db = next(get_db())
                platform_connection.status = "expired"
                platform_connection.last_error = str(e)
                db.commit()
            
            return {
                'success': False,
                'platform': 'tiktok',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def verify_connection(self, platform_connection) -> bool:
        """
        Verify TikTok connection is valid.
        
        Args:
            platform_connection: PlatformConnection to verify
            
        Returns:
            True if connection is valid, False otherwise
        """
        if not self.client_key or not self.client_secret:
            return False
        
        try:
            import asyncio
            
            access_token = platform_connection.access_token
            
            async def check():
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.api_url}/v2/user/info/",
                        headers={
                            "Authorization": f"Bearer {access_token}"
                        },
                        params={
                            "fields": "display_name"
                        }
                    )
                    data = response.json()
                    return data.get("error") is None
            
            return asyncio.run(check())
            
        except Exception as e:
            logger.error(f"TikTok connection verification failed: {e}")
            return False


# Async helper for sync contexts
import asyncio

def upload_tiktok_sync(platform_connection, video_path, title, **kwargs):
    """Synchronous wrapper for async upload_video method"""
    engine = TikTokUploadEngine()
    return asyncio.run(engine.upload_video(platform_connection, video_path, title, **kwargs))
