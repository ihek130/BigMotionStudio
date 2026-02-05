"""
Instagram Upload Engine (Meta Graph API)
Uploads videos as Instagram Reels using Meta Business API.
"""

import os
import time
from datetime import datetime
from typing import Dict, Optional
import logging
import httpx

logger = logging.getLogger(__name__)


class InstagramUploadEngine:
    """
    Instagram Reels upload engine using Meta Graph API.
    Requires Instagram Business or Creator account connected to Facebook Page.
    """
    
    def __init__(self):
        self.graph_url = "https://graph.facebook.com/v21.0"
        self.max_poll_attempts = 60  # 5 minutes max wait
        self.poll_interval = 5  # seconds
    
    async def upload_video(
        self,
        platform_connection,
        video_path: str,
        caption: str,
        thumbnail_path: str = None,
        share_to_feed: bool = True
    ) -> Dict:
        """
        Upload video to Instagram as Reel.
        
        Instagram upload is a 2-step process:
        1. Create Container (uploads video and processes it)
        2. Publish Container (makes it live)
        
        Args:
            platform_connection: PlatformConnection with Instagram tokens
            video_path: Path to video file
            caption: Caption text (with hashtags)
            thumbnail_path: Optional custom thumbnail
            share_to_feed: Whether to share to main feed (not just Reels tab)
            
        Returns:
            Dict with upload result including media_id and permalink
        """
        try:
            logger.info(f"Starting Instagram Reel upload")
            
            # Get Instagram Business Account ID
            ig_account_id = platform_connection.instagram_user_id
            access_token = platform_connection.access_token
            
            if not ig_account_id:
                raise ValueError("Instagram Business Account ID not found in connection")
            
            # Check token expiry
            if platform_connection.needs_refresh:
                logger.warning("Instagram token needs refresh")
                # Token refresh handled by platform_routes refresh endpoint
            
            async with httpx.AsyncClient(timeout=300.0) as client:
                # Step 1: Upload video file and create container
                logger.info("Step 1: Creating Instagram media container...")
                
                # Upload video to a publicly accessible URL first
                # Note: Instagram requires a public URL, not local file
                # You'll need to upload to temporary storage (S3/CloudFlare/etc)
                # For now, we'll use direct URL upload if file is already hosted
                
                # Check if video_path is already a URL
                if video_path.startswith('http'):
                    video_url = video_path
                else:
                    # Need to upload to temp hosting first
                    # This is a placeholder - implement your file hosting
                    raise NotImplementedError(
                        "Instagram requires publicly accessible video URL. "
                        "Please upload video to cloud storage first and pass URL."
                    )
                
                # Create media container
                container_params = {
                    'media_type': 'REELS',
                    'video_url': video_url,
                    'caption': caption[:2200],  # Instagram limit
                    'share_to_feed': share_to_feed,
                    'access_token': access_token
                }
                
                # Add thumbnail if provided
                if thumbnail_path and thumbnail_path.startswith('http'):
                    container_params['thumb_offset'] = 0  # Use first frame or specific offset
                
                container_response = await client.post(
                    f"{self.graph_url}/{ig_account_id}/media",
                    data=container_params
                )
                
                container_data = container_response.json()
                
                if 'error' in container_data:
                    error_msg = container_data['error'].get('message', 'Unknown error')
                    raise Exception(f"Instagram container creation failed: {error_msg}")
                
                container_id = container_data['id']
                logger.info(f"Container created: {container_id}")
                
                # Step 2: Poll container status until ready
                logger.info("Step 2: Waiting for video processing...")
                
                for attempt in range(self.max_poll_attempts):
                    status_response = await client.get(
                        f"{self.graph_url}/{container_id}",
                        params={
                            'fields': 'status_code,status',
                            'access_token': access_token
                        }
                    )
                    
                    status_data = status_response.json()
                    status_code = status_data.get('status_code')
                    
                    if status_code == 'FINISHED':
                        logger.info("✅ Video processing complete")
                        break
                    elif status_code == 'ERROR':
                        raise Exception(f"Instagram processing failed: {status_data.get('status')}")
                    elif status_code == 'EXPIRED':
                        raise Exception("Instagram container expired")
                    
                    logger.info(f"Processing... ({status_code}) - attempt {attempt + 1}/{self.max_poll_attempts}")
                    await asyncio.sleep(self.poll_interval)
                else:
                    raise Exception("Instagram processing timeout - video took too long")
                
                # Step 3: Publish container
                logger.info("Step 3: Publishing Reel...")
                
                publish_response = await client.post(
                    f"{self.graph_url}/{ig_account_id}/media_publish",
                    data={
                        'creation_id': container_id,
                        'access_token': access_token
                    }
                )
                
                publish_data = publish_response.json()
                
                if 'error' in publish_data:
                    error_msg = publish_data['error'].get('message', 'Unknown error')
                    raise Exception(f"Instagram publish failed: {error_msg}")
                
                media_id = publish_data['id']
                
                # Get permalink
                media_response = await client.get(
                    f"{self.graph_url}/{media_id}",
                    params={
                        'fields': 'permalink,timestamp',
                        'access_token': access_token
                    }
                )
                
                media_data = media_response.json()
                permalink = media_data.get('permalink', f"https://www.instagram.com/reel/{media_id}")
                
                logger.info(f"✅ Instagram upload successful: {permalink}")
                
                return {
                    'success': True,
                    'platform': 'instagram',
                    'media_id': media_id,
                    'video_url': permalink,
                    'container_id': container_id,
                    'uploaded_at': datetime.utcnow().isoformat()
                }
                
        except NotImplementedError as e:
            logger.warning(f"⚠️ Instagram upload not fully implemented: {e}")
            return {
                'success': False,
                'platform': 'instagram',
                'error': str(e),
                'error_type': 'NotImplementedError',
                'note': 'Requires cloud file hosting implementation'
            }
            
        except Exception as e:
            logger.error(f"❌ Instagram upload failed: {e}", exc_info=True)
            
            # Update connection status if auth error
            if "invalid_token" in str(e) or "expired" in str(e).lower():
                from database.connection import get_db
                db = next(get_db())
                platform_connection.status = "expired"
                platform_connection.last_error = str(e)
                db.commit()
            
            return {
                'success': False,
                'platform': 'instagram',
                'error': str(e),
                'error_type': type(e).__name__
            }
    
    def verify_connection(self, platform_connection) -> bool:
        """
        Verify Instagram connection is valid.
        
        Args:
            platform_connection: PlatformConnection to verify
            
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            import asyncio
            
            ig_account_id = platform_connection.instagram_user_id
            access_token = platform_connection.access_token
            
            if not ig_account_id:
                return False
            
            async def check():
                async with httpx.AsyncClient() as client:
                    response = await client.get(
                        f"{self.graph_url}/{ig_account_id}",
                        params={
                            'fields': 'username',
                            'access_token': access_token
                        }
                    )
                    data = response.json()
                    return 'error' not in data
            
            return asyncio.run(check())
            
        except Exception as e:
            logger.error(f"Instagram connection verification failed: {e}")
            return False


# Async helper for sync contexts
import asyncio

def upload_instagram_sync(platform_connection, video_path, caption, **kwargs):
    """Synchronous wrapper for async upload_video method"""
    engine = InstagramUploadEngine()
    return asyncio.run(engine.upload_video(platform_connection, video_path, caption, **kwargs))
