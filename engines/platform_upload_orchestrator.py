"""
Platform Upload Orchestrator
Coordinates video uploads to multiple platforms (YouTube, TikTok, Instagram).
Handles partial failures and database updates.
"""

import os
from datetime import datetime
from typing import List, Dict
import logging
from sqlalchemy.orm import Session

from .youtube_upload_engine import YouTubeUploadEngine
from .instagram_upload_engine import InstagramUploadEngine
from .tiktok_upload_engine import TikTokUploadEngine

logger = logging.getLogger(__name__)


class PlatformUploadOrchestrator:
    """
    Orchestrates video uploads to multiple platforms.
    Handles partial failures - if YouTube succeeds but TikTok fails, that's OK.
    """
    
    def __init__(self):
        self.youtube_engine = YouTubeUploadEngine()
        self.instagram_engine = InstagramUploadEngine()
        self.tiktok_engine = TikTokUploadEngine()
    
    def upload_to_platforms(
        self,
        video_record,
        series_record,
        platforms: List[str],
        db: Session,
        scheduled_time: datetime = None
    ) -> Dict:
        """
        Upload video to specified platforms.
        
        Args:
            video_record: Video database record
            series_record: Series database record (for metadata)
            platforms: List of platform names ['youtube', 'tiktok', 'instagram']
            db: Database session
            scheduled_time: Optional scheduled publish time
            
        Returns:
            Dict with results per platform
        """
        from database.models import PlatformConnection
        
        logger.info(f"Starting upload to platforms: {platforms}")
        
        # Get user ID from series
        user_id = series_record.user_id
        
        # Get video file paths
        video_path = video_record.video_path
        thumbnail_path = video_record.thumbnail_path
        
        # Verify video file exists
        if not video_path or not os.path.exists(video_path):
            logger.error(f"Video file not found: {video_path}")
            return {
                'success': False,
                'error': 'Video file not found',
                'results': {}
            }
        
        # Prepare metadata
        title = video_record.title or f"{series_record.name} - {video_record.topic}"
        description = video_record.description or series_record.description or ""
        tags = video_record.tags or []
        
        # Caption for Instagram/TikTok (shorter, with hashtags)
        caption = self._create_caption(title, description, tags)
        
        results = {}
        overall_success = False
        
        # Upload to each platform
        for platform in platforms:
            try:
                # Get platform connection
                connection = db.query(PlatformConnection).filter(
                    PlatformConnection.user_id == user_id,
                    PlatformConnection.platform == platform,
                    PlatformConnection.status == "active"
                ).first()
                
                if not connection:
                    logger.warning(f"No active {platform} connection for user {user_id}")
                    results[platform] = {
                        'success': False,
                        'error': f'{platform.title()} not connected',
                        'error_type': 'NoConnection'
                    }
                    continue
                
                # Auto-refresh token if expired or about to expire
                if connection.needs_refresh or connection.is_expired:
                    logger.info(f"Token for {platform} needs refresh, attempting...")
                    try:
                        refresh_success = self._refresh_token(connection, platform, db)
                        if not refresh_success:
                            logger.warning(f"Token refresh failed for {platform}, attempting upload anyway")
                    except Exception as refresh_err:
                        logger.warning(f"Token refresh error for {platform}: {refresh_err}")
                
                # Upload based on platform
                if platform == 'youtube':
                    result = self._upload_to_youtube(
                        connection,
                        video_path,
                        thumbnail_path,
                        title,
                        description,
                        tags,
                        scheduled_time
                    )
                    
                    # Update video record with YouTube data
                    if result['success']:
                        video_record.youtube_id = result['video_id']
                        video_record.youtube_url = result['video_url']
                        video_record.youtube_published_at = datetime.utcnow()
                        overall_success = True
                
                elif platform == 'instagram':
                    result = self._upload_to_instagram(
                        connection,
                        video_path,
                        caption
                    )
                    
                    # Update video record with Instagram data
                    if result['success']:
                        video_record.instagram_id = result.get('media_id')
                        video_record.instagram_url = result.get('video_url')
                        video_record.instagram_published_at = datetime.utcnow()
                        overall_success = True
                
                elif platform == 'tiktok':
                    result = self._upload_to_tiktok(
                        connection,
                        video_path,
                        title,
                        description
                    )
                    
                    # Update video record with TikTok data
                    if result['success']:
                        video_record.tiktok_id = result.get('video_id')
                        video_record.tiktok_url = result.get('video_url')
                        video_record.tiktok_published_at = datetime.utcnow()
                        overall_success = True
                
                else:
                    result = {
                        'success': False,
                        'error': f'Unknown platform: {platform}'
                    }
                
                results[platform] = result
                
                # Commit after each successful upload
                if result['success']:
                    db.commit()
                    logger.info(f"✅ {platform.title()} upload successful")
                else:
                    logger.warning(f"⚠️ {platform.title()} upload failed: {result.get('error')}")
                
            except Exception as e:
                logger.error(f"❌ Error uploading to {platform}: {e}", exc_info=True)
                results[platform] = {
                    'success': False,
                    'error': str(e),
                    'error_type': type(e).__name__
                }
        
        # Update video status
        if overall_success:
            video_record.status = "published"
            
            # Clear scheduled_for if it was scheduled
            if scheduled_time and video_record.scheduled_for:
                logger.info(f"Video published at scheduled time: {scheduled_time}")
            
            # 🗑️ CLEANUP: Delete temp files after successful upload
            self._cleanup_temp_files(video_record)
        
        db.commit()
        
        # Summary
        success_count = sum(1 for r in results.values() if r.get('success'))
        total_count = len(results)
        
        logger.info(f"Upload complete: {success_count}/{total_count} platforms successful")
        
        return {
            'success': overall_success,
            'platforms_attempted': list(results.keys()),
            'platforms_succeeded': [p for p, r in results.items() if r.get('success')],
            'platforms_failed': [p for p, r in results.items() if not r.get('success')],
            'results': results
        }
    
    def _refresh_token(self, connection, platform: str, db: Session) -> bool:
        """
        Refresh OAuth token for a platform connection before upload.
        
        Args:
            connection: PlatformConnection record
            platform: Platform name (youtube, tiktok, instagram)
            db: Database session
            
        Returns:
            True if refresh succeeded, False otherwise
        """
        import asyncio
        import concurrent.futures
        
        try:
            if platform == "youtube":
                from auth.oauth.youtube import refresh_youtube_token
                return refresh_youtube_token(connection, db)
            
            elif platform == "tiktok":
                from auth.oauth.tiktok import refresh_tiktok_token
                
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            refresh_tiktok_token(connection, db)
                        )
                        return future.result(timeout=30)
                else:
                    return asyncio.run(refresh_tiktok_token(connection, db))
            
            elif platform == "instagram":
                from auth.oauth.instagram import refresh_instagram_token
                
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    loop = None
                
                if loop and loop.is_running():
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        future = pool.submit(
                            asyncio.run,
                            refresh_instagram_token(connection, db)
                        )
                        return future.result(timeout=30)
                else:
                    return asyncio.run(refresh_instagram_token(connection, db))
            
            return False
            
        except Exception as e:
            logger.error(f"Token refresh failed for {platform}: {e}", exc_info=True)
            return False
    
    def _cleanup_temp_files(self, video_record) -> None:
        """
        Delete temporary video files after successful upload to platforms.
        Keeps database record but removes files to save storage.
        """
        import shutil
        
        try:
            # Get project directory
            project_dir = os.path.dirname(video_record.video_path) if video_record.video_path else None
            
            if project_dir and os.path.exists(project_dir):
                logger.info(f"🗑️ Deleting temp files from: {project_dir}")
                
                # Delete entire project folder
                shutil.rmtree(project_dir)
                logger.info(f"✅ Temp files deleted successfully")
                
                # Clear file paths in database (keep URLs)
                video_record.video_path = None
                video_record.thumbnail_path = None
                video_record.script_path = None
                
            else:
                logger.warning(f"Project directory not found or already deleted: {project_dir}")
                
        except Exception as e:
            logger.error(f"Failed to cleanup temp files: {e}", exc_info=True)
            # Don't fail upload if cleanup fails
    
    def _upload_to_youtube(
        self,
        connection,
        video_path: str,
        thumbnail_path: str,
        title: str,
        description: str,
        tags: list,
        scheduled_time: datetime = None
    ) -> Dict:
        """Upload to YouTube"""
        return self.youtube_engine.upload_video(
            platform_connection=connection,
            video_path=video_path,
            title=title,
            description=description,
            tags=tags,
            thumbnail_path=thumbnail_path,
            scheduled_time=scheduled_time,
            category_id="26",  # Entertainment
            privacy_status="public",
            made_for_kids=False
        )
    
    def _upload_to_instagram(
        self,
        connection,
        video_path: str,
        caption: str
    ) -> Dict:
        """Upload to Instagram"""
        import asyncio
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # We're inside an async context (e.g., FastAPI background task)
            # Create a new thread to run the async upload
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.instagram_engine.upload_video(
                        platform_connection=connection,
                        video_path=video_path,
                        caption=caption,
                        share_to_feed=True
                    )
                )
                return future.result(timeout=300)
        else:
            return asyncio.run(
                self.instagram_engine.upload_video(
                    platform_connection=connection,
                    video_path=video_path,
                    caption=caption,
                    share_to_feed=True
                )
            )
    
    def _upload_to_tiktok(
        self,
        connection,
        video_path: str,
        title: str,
        description: str
    ) -> Dict:
        """Upload to TikTok"""
        import asyncio
        
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop and loop.is_running():
            # We're inside an async context (e.g., FastAPI background task)
            # Create a new thread to run the async upload
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(
                    asyncio.run,
                    self.tiktok_engine.upload_video(
                        platform_connection=connection,
                        video_path=video_path,
                        title=title,
                        description=description,
                        privacy_level="PUBLIC_TO_EVERYONE",
                        disable_comment=False
                    )
                )
                return future.result(timeout=300)
        else:
            return asyncio.run(
                self.tiktok_engine.upload_video(
                    platform_connection=connection,
                    video_path=video_path,
                    title=title,
                    description=description,
                    privacy_level="PUBLIC_TO_EVERYONE",
                    disable_comment=False
                )
            )
    
    def _create_caption(self, title: str, description: str, tags: list) -> str:
        """Create short caption for Instagram/TikTok"""
        # Use first sentence of description or title
        caption = title[:100]
        
        # Add hashtags from tags
        if tags:
            hashtags = ' '.join([f'#{tag.replace(" ", "")}' for tag in tags[:10]])
            caption = f"{caption}\n\n{hashtags}"
        
        return caption[:2200]  # Instagram/TikTok limit
    
    def verify_platforms(self, user_id: str, platforms: List[str], db: Session) -> Dict:
        """
        Verify which platforms are connected and active.
        
        Args:
            user_id: User ID
            platforms: List of platform names to check
            db: Database session
            
        Returns:
            Dict with status per platform
        """
        from database.models import PlatformConnection
        
        status = {}
        
        for platform in platforms:
            connection = db.query(PlatformConnection).filter(
                PlatformConnection.user_id == user_id,
                PlatformConnection.platform == platform,
                PlatformConnection.status == "active"
            ).first()
            
            status[platform] = {
                'connected': connection is not None,
                'active': connection.status == "active" if connection else False,
                'needs_refresh': connection.needs_refresh if connection else False
            }
        
        return status
