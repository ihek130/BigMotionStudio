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
    
    async def _query_creator_info(self, client: httpx.AsyncClient, access_token: str) -> Dict:
        """
        Query TikTok creator info to get valid privacy levels and settings.
        Required by TikTok before posting (content sharing guidelines compliance).
        """
        logger.info("Querying TikTok creator info...")
        response = await client.post(
            f"{self.api_url}/v2/post/publish/creator_info/query/",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json; charset=UTF-8"
            }
        )
        data = response.json()
        if data.get("error", {}).get("code", "ok") != "ok":
            error_msg = data["error"].get("message", "Unknown error")
            raise Exception(f"Creator info query failed: {error_msg}")
        
        creator_data = data.get("data", {})
        logger.info(f"Creator info: username={creator_data.get('creator_username')}, "
                     f"privacy_options={creator_data.get('privacy_level_options')}, "
                     f"max_duration={creator_data.get('max_video_post_duration_sec')}s")
        return creator_data
    
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
        0. Query creator info (required by content sharing guidelines)
        1. Initialize upload and get upload URL
        2. Upload video file to provided URL
        3. Check publish status
        
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
                # Step 0: Query creator info (required by TikTok content sharing guidelines)
                creator_info = await self._query_creator_info(client, access_token)
                
                # Validate privacy level against creator's allowed options
                allowed_privacy = creator_info.get("privacy_level_options", ["SELF_ONLY"])
                if privacy_level not in allowed_privacy:
                    old_level = privacy_level
                    # Fall back: prefer SELF_ONLY, then first available option
                    privacy_level = "SELF_ONLY" if "SELF_ONLY" in allowed_privacy else allowed_privacy[0]
                    logger.warning(f"Privacy level '{old_level}' not available, using '{privacy_level}' "
                                   f"(allowed: {allowed_privacy})")
                
                # Respect creator's interaction settings
                if creator_info.get("duet_disabled"):
                    disable_duet = True
                if creator_info.get("stitch_disabled"):
                    disable_stitch = True
                if creator_info.get("comment_disabled"):
                    disable_comment = True
                
                # Step 1: Initialize upload
                logger.info("Step 1: Initializing TikTok upload...")
                
                # Build post_info with required fields per TikTok Content Posting API
                post_info = {
                    "title": title[:2200],  # TikTok max caption length in UTF-16 runes
                    "privacy_level": privacy_level,
                    "disable_duet": disable_duet,
                    "disable_stitch": disable_stitch,
                    "disable_comment": disable_comment,
                    "video_cover_timestamp_ms": 1000,
                    # Required: brand content disclosure fields
                    "brand_content_toggle": False,
                    "brand_organic_toggle": False,
                    # Mark as AI-generated content (required for compliance)
                    "is_aigc": True,
                }
                
                init_response = await client.post(
                    f"{self.api_url}/v2/post/publish/video/init/",
                    headers={
                        "Authorization": f"Bearer {access_token}",
                        "Content-Type": "application/json; charset=UTF-8"
                    },
                    json={
                        "post_info": post_info,
                        "source_info": {
                            "source": "FILE_UPLOAD",
                            "video_size": file_size,
                            "chunk_size": file_size,  # Upload in single chunk
                            "total_chunk_count": 1
                        }
                    }
                )
                
                init_data = init_response.json()
                
                # Check for error (TikTok returns error.code != "ok" on failure)
                error_info = init_data.get("error", {})
                if error_info.get("code", "ok") != "ok":
                    error_msg = error_info.get("message", "Unknown error")
                    error_code = error_info.get("code", "unknown")
                    raise Exception(f"TikTok init failed ({error_code}): {error_msg}")
                
                publish_id = init_data["data"]["publish_id"]
                upload_url = init_data["data"]["upload_url"]
                
                logger.info(f"Upload initialized: {publish_id}")
                
                # Step 2: Upload video file with required Content-Range header
                logger.info("Step 2: Uploading video file...")
                
                with open(video_path, 'rb') as video_file:
                    upload_response = await client.put(
                        upload_url,
                        headers={
                            "Content-Type": "video/mp4",
                            "Content-Length": str(file_size),
                            "Content-Range": f"bytes 0-{file_size - 1}/{file_size}"
                        },
                        content=video_file
                    )
                
                if upload_response.status_code not in (200, 201):
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
                
                status_error = status_data.get("error", {})
                if status_error.get("code", "ok") != "ok":
                    error_msg = status_error.get("message", "Unknown error")
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
                try:
                    platform_connection.status = "expired"
                    platform_connection.last_error = str(e)
                    db.commit()
                finally:
                    db.close()
            
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
