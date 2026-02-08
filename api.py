"""
FastAPI Backend - SaaS Video Generation API
Receives requests from Next.js frontend and triggers video generation.
"""

import os
import sys
import uuid
import asyncio
from datetime import datetime
from typing import Optional, Dict, List
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from saas_generator import SaaSVideoGenerator, create_settings_from_frontend
from engines.models import UserSeriesSettings

# Auth imports
from database import engine, Base, get_db, User
from auth.routes import router as auth_router
from auth.platform_routes import router as platform_router
from auth.oauth.youtube import router as youtube_oauth_router
from auth.oauth.tiktok import router as tiktok_oauth_router
from auth.oauth.instagram import router as instagram_oauth_router
from auth.dependencies import get_current_active_user, require_can_generate_video

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
# Application Lifespan
# ═══════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan events."""
    global generator
    
    # Startup
    logger.info("🚀 Starting ReelFlow API...")
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    logger.info("✅ Database tables created")
    
    # Initialize video generator
    generator = SaaSVideoGenerator()
    logger.info("✅ Video generator initialized")
    
    yield
    
    # Shutdown
    logger.info("👋 Shutting down ReelFlow API...")


# Initialize FastAPI app
app = FastAPI(
    title="ReelFlow Video Generation API",
    description="AI-powered short-form video generation platform with multi-platform posting",
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware for Next.js frontend
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        FRONTEND_URL,
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        # Add production domain here
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ═══════════════════════════════════════════════════════════
# Include Auth Routers
# ═══════════════════════════════════════════════════════════

app.include_router(auth_router)
app.include_router(platform_router)
app.include_router(youtube_oauth_router)
app.include_router(tiktok_oauth_router)
app.include_router(instagram_oauth_router)

# Initialize video generator (singleton)
generator: Optional[SaaSVideoGenerator] = None

# Job tracking (deprecated - DB-based tracking used now)
# jobs: Dict[str, Dict] = {}


# ═══════════════════════════════════════════════════════════
# Pydantic Models (Request/Response)
# ═══════════════════════════════════════════════════════════

class CreateSeriesRequest(BaseModel):
    """Request model matching frontend WizardContext"""
    user_id: str
    niche: str
    nicheFormat: str = "storytelling"
    style: str
    voiceId: str
    musicId: str
    captionStyle: str
    videoDuration: int = 60
    seriesName: str
    description: str
    postingTimes: List[str] = ["09:00"]  # Array of posting times (1 for Launch/Grow, 2 for Scale)
    timezone: str = "UTC"  # User's timezone (e.g., "Asia/Karachi")
    platforms: List[str] = ["youtube"]


class GenerateVideoRequest(BaseModel):
    """Request to generate a single video for a series"""
    user_id: str
    series_id: str
    topic: Optional[str] = None  # Optional specific topic


class JobResponse(BaseModel):
    """Response with job ID for tracking"""
    job_id: str
    status: str
    message: str


class JobStatusResponse(BaseModel):
    """Response with job status details"""
    job_id: str
    status: str  # 'pending', 'processing', 'completed', 'failed'
    progress: int  # 0-100
    stage: str  # Current stage
    result: Optional[Dict] = None
    error: Optional[str] = None


class VideoResponse(BaseModel):
    """Response with generated video details"""
    project_id: str
    video_path: str
    thumbnail_path: str
    title: str
    description: str
    tags: List[str]
    duration_seconds: float
    scene_count: int
    generation_time_seconds: float


# ═══════════════════════════════════════════════════════════
# API Endpoints
# ═══════════════════════════════════════════════════════════

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "status": "online",
        "service": "ReelFlow Video Generation API",
        "version": "2.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Detailed health check"""
    return {
        "status": "healthy",
        "generator_ready": generator is not None
    }


@app.post("/api/series/create", response_model=JobResponse)
async def create_series(
    request: CreateSeriesRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new video series and start generating first video.
    Saves series to database and triggers background video generation.
    """
    from database.models import Series as SeriesModel, Video as VideoModel, Job as JobModel
    
    try:
        # CHECK SERIES LIMIT - Prevent creating more series than purchased
        active_series_count = db.query(SeriesModel).filter(
            SeriesModel.user_id == str(current_user.id),
            SeriesModel.status == "active"
        ).count()
        
        series_limit = current_user.plan_limits["series_limit"]
        
        if active_series_count >= series_limit:
            raise HTTPException(
                status_code=403,
                detail=f"Series limit reached ({series_limit}). Please upgrade your plan to create more series."
            )
        
        logger.info(f"User {current_user.email} creating series {active_series_count + 1}/{series_limit}")
        
        # Create series in database
        series = SeriesModel(
            user_id=str(current_user.id),
            name=request.seriesName,
            description=request.description,
            niche=request.niche,
            niche_format=request.nicheFormat,
            visual_style=request.style,
            voice_id=request.voiceId,
            music_track=request.musicId,
            caption_style=request.captionStyle,
            video_duration=request.videoDuration,
            posting_times=request.postingTimes,
            timezone=request.timezone,
            platforms=request.platforms,
            status="active"
        )
        db.add(series)
        db.commit()
        db.refresh(series)
        
        logger.info(f"Created series: {series.name} (ID: {series.id}) for user {current_user.email}")
        
        # Create first video record
        video = VideoModel(
            series_id=str(series.id),
            status="generating",
            progress=0,
            current_stage="initializing"
        )
        db.add(video)
        db.commit()
        db.refresh(video)
        
        # Create job for tracking
        job = JobModel(
            video_id=str(video.id),
            job_type="video_generation",
            status="pending",
            stage="initializing"
        )
        db.add(job)
        db.commit()
        db.refresh(job)
        
        logger.info(f"Created video {video.id} and job {job.id} for series {series.id}")
        
        # Trigger background video generation
        background_tasks.add_task(
            process_video_generation_db,
            job_id=str(job.id),
            video_id=str(video.id),
            series_id=str(series.id),
            user_id=str(current_user.id)
        )
        
        return JobResponse(
            job_id=str(job.id),
            status="pending",
            message=f"Series '{request.seriesName}' created! Generating first video..."
        )
        
    except Exception as e:
        logger.error(f"Failed to create series: {e}")
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Failed to create series: {str(e)}")


@app.get("/api/series")
async def list_series(
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all series for the current user with limit info.
    """
    from database.models import Series as SeriesModel
    
    series_list = db.query(SeriesModel).filter(
        SeriesModel.user_id == str(current_user.id)
    ).order_by(SeriesModel.created_at.desc()).all()
    
    active_count = sum(1 for s in series_list if s.status == "active")
    series_limit = current_user.plan_limits["series_limit"]
    
    return {
        "series": [s.to_dict() for s in series_list],
        "active_count": active_count,
        "series_limit": series_limit,
        "can_create_more": active_count < series_limit
    }


@app.patch("/api/user/upgrade-series")
async def upgrade_series_count(
    new_count: int,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upgrade user's series count.
    Note: Normally handled by Polar checkout/webhook flow.
    This endpoint is kept for admin use only.
    """
    if not current_user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    if new_count < 1:
        raise HTTPException(status_code=400, detail="Series count must be at least 1")
    
    if new_count <= current_user.series_purchased:
        raise HTTPException(status_code=400, detail="New count must be greater than current count")
    
    # Update user's series count
    current_user.series_purchased = new_count
    db.commit()
    
    logger.info(f"User {current_user.email} upgraded to {new_count} series")
    
    return {
        "success": True,
        "series_purchased": new_count,
        "message": f"Successfully upgraded to {new_count} series"
    }


@app.patch("/api/series/{series_id}/status")
async def update_series_status(
    series_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Toggle series between active and paused."""
    from database.models import Series as SeriesModel
    
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    series.status = "paused" if series.status == "active" else "active"
    db.commit()
    
    return {"success": True, "status": series.status}


@app.delete("/api/series/{series_id}")
async def delete_series(
    series_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Delete a series and all its videos."""
    from database.models import Series as SeriesModel
    
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    db.delete(series)
    db.commit()
    
    return {"success": True, "message": "Series deleted"}


@app.post("/api/series/{series_id}/generate")
async def generate_video_for_series(
    series_id: str,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
    current_user: User = Depends(require_can_generate_video)
):
    """Manually trigger video generation for a series."""
    from database.models import Series as SeriesModel, Video as VideoModel, Job as JobModel
    
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    if series.status != "active":
        raise HTTPException(status_code=400, detail="Series is paused. Resume it first.")
    
    # Increment video counter
    current_user.videos_generated_this_month += 1
    current_user.videos_generated_total += 1
    current_user.last_video_at = datetime.now()
    db.commit()
    
    # Create video record
    video = VideoModel(
        series_id=str(series.id),
        status="generating",
        progress=0,
        current_stage="initializing"
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Create job for tracking
    job = JobModel(
        video_id=str(video.id),
        job_type="video_generation",
        status="pending",
        stage="initializing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger background generation
    background_tasks.add_task(
        process_video_generation_db,
        job_id=str(job.id),
        video_id=str(video.id),
        series_id=str(series.id),
        user_id=str(current_user.id)
    )
    
    return {
        "job_id": str(job.id),
        "video_id": str(video.id),
        "status": "pending",
        "message": "Video generation started"
    }


@app.patch("/api/series/{series_id}/videos/{video_id}/metadata")
async def update_video_metadata(
    series_id: str,
    video_id: str,
    title: Optional[str] = None,
    description: Optional[str] = None,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Update video title and description."""
    from database.models import Video as VideoModel, Series as SeriesModel
    
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    video = db.query(VideoModel).filter(
        VideoModel.id == video_id,
        VideoModel.series_id == series_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    if title is not None:
        video.title = title
    if description is not None:
        video.description = description
    
    db.commit()
    
    return {"success": True, "message": "Metadata updated"}


@app.get("/api/series/{series_id}")
async def get_series(
    series_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get series details with videos.
    """
    from database.models import Series as SeriesModel, Video as VideoModel
    
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Get videos for this series
    videos = db.query(VideoModel).filter(
        VideoModel.series_id == series_id
    ).order_by(VideoModel.created_at.desc()).all()
    
    series_dict = series.to_dict()
    series_dict['videos'] = [v.to_dict() for v in videos]
    
    return series_dict


@app.get("/api/series/{series_id}/videos/{video_id}")
async def get_video(
    series_id: str,
    video_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Get individual video details.
    """
    from database.models import Video as VideoModel, Series as SeriesModel
    
    # Verify series belongs to user
    series = db.query(SeriesModel).filter(
        SeriesModel.id == series_id,
        SeriesModel.user_id == str(current_user.id)
    ).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Get video
    video = db.query(VideoModel).filter(
        VideoModel.id == video_id,
        VideoModel.series_id == series_id
    ).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    return video.to_dict()


# ═══════════════════════════════════════════════════════════
# PLATFORM UPLOAD ENDPOINTS
# ═══════════════════════════════════════════════════════════

@app.post("/api/video/{video_id}/upload")
async def upload_video_to_platforms(
    video_id: str,
    background_tasks: BackgroundTasks,
    platforms: List[str] = None,  # Optional: override series platforms
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Upload generated video to platforms.
    Can be called manually or automatically after generation.
    
    Args:
        video_id: Video to upload
        platforms: Optional list to override series platforms
    """
    from database.models import Video as VideoModel, Series as SeriesModel, Job as JobModel
    
    # Get video
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Get series
    series = db.query(SeriesModel).filter(SeriesModel.id == video.series_id).first()
    
    if not series:
        raise HTTPException(status_code=404, detail="Series not found")
    
    # Verify ownership
    if series.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Check video is ready
    if video.status != "ready":
        raise HTTPException(
            status_code=400,
            detail=f"Video is not ready for upload. Current status: {video.status}"
        )
    
    # Determine platforms to upload to
    target_platforms = platforms if platforms else series.platforms
    
    if not target_platforms or len(target_platforms) == 0:
        raise HTTPException(
            status_code=400,
            detail="No platforms specified. Connect platforms in series settings."
        )
    
    # Create upload job
    job = JobModel(
        video_id=video_id,
        job_type="platform_upload",
        status="pending",
        stage="initializing"
    )
    db.add(job)
    db.commit()
    db.refresh(job)
    
    # Trigger background upload
    background_tasks.add_task(
        process_platform_upload,
        job_id=str(job.id),
        video_id=video_id,
        series_id=str(series.id),
        platforms=target_platforms
    )
    
    return {
        "message": "Upload started",
        "job_id": str(job.id),
        "video_id": video_id,
        "platforms": target_platforms
    }


async def process_platform_upload(
    job_id: str,
    video_id: str,
    series_id: str,
    platforms: List[str]
):
    """
    Background task to upload video to platforms.
    """
    from engines.platform_upload_orchestrator import PlatformUploadOrchestrator
    from database.models import Video as VideoModel, Series as SeriesModel, Job as JobModel
    
    db: Session = next(get_db())
    job = None
    
    try:
        # Get records
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
        series = db.query(SeriesModel).filter(SeriesModel.id == series_id).first()
        
        if not job or not video or not series:
            logger.error(f"Upload job {job_id} missing records")
            return
        
        # Update job
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Starting platform upload for video {video_id}")
        
        # Upload to platforms
        orchestrator = PlatformUploadOrchestrator()
        
        results = orchestrator.upload_to_platforms(
            video_record=video,
            series_record=series,
            platforms=platforms,
            db=db,
            scheduled_time=video.scheduled_for
        )
        
        # Update job
        job.status = "completed" if results['success'] else "failed"
        job.progress = 100
        job.stage = "complete"
        job.completed_at = datetime.utcnow()
        job.result = results
        db.commit()
        
        logger.info(f"Platform upload completed: {results}")
        
    except Exception as e:
        logger.error(f"Platform upload failed: {e}", exc_info=True)
        
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
    
    finally:
        db.close()


@app.get("/api/video/{video_id}/upload-status")
async def get_upload_status(
    video_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get upload status for a video"""
    from database.models import Video as VideoModel, Series as SeriesModel
    
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    series = db.query(SeriesModel).filter(SeriesModel.id == video.series_id).first()
    
    if not series or series.user_id != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return {
        "video_id": video_id,
        "youtube": {
            "uploaded": video.youtube_id is not None,
            "video_id": video.youtube_id,
            "url": video.youtube_url,
            "published_at": video.youtube_published_at.isoformat() if video.youtube_published_at else None
        },
        "tiktok": {
            "uploaded": video.tiktok_id is not None,
            "video_id": video.tiktok_id,
            "url": video.tiktok_url,
            "published_at": video.tiktok_published_at.isoformat() if video.tiktok_published_at else None
        },
        "instagram": {
            "uploaded": video.instagram_id is not None,
            "media_id": video.instagram_id,
            "url": video.instagram_url,
            "published_at": video.instagram_published_at.isoformat() if video.instagram_published_at else None
        }
    }


# Legacy endpoint removed - use POST /api/series/{series_id}/generate instead


@app.post("/api/video/generate-sync", response_model=VideoResponse)
async def generate_video_sync(
    request: CreateSeriesRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Synchronous video generation (for testing).
    Waits for completion before returning.
    """
    if not generator:
        raise HTTPException(status_code=503, detail="Generator not initialized")
    
    try:
        # Convert request to settings
        settings = create_settings_from_frontend(request.dict())
        
        # Generate video (blocking)
        result = generator.generate_video(settings, topic=None)
        
        return VideoResponse(
            project_id=result.project_id,
            video_path=result.video_path,
            thumbnail_path=result.thumbnail_path,
            title=result.title,
            description=result.description,
            tags=result.tags,
            duration_seconds=result.duration_seconds,
            scene_count=result.scene_count,
            generation_time_seconds=result.generation_time_seconds
        )
        
    except Exception as e:
        logger.error(f"Video generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Legacy job polling endpoint removed - use database-backed video status polling instead


@app.get("/api/videos")
async def list_all_user_videos(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    List all videos across all series for the current user.
    """
    from database.models import Video as VideoModel, Series as SeriesModel

    videos = (
        db.query(VideoModel)
        .join(SeriesModel, VideoModel.series_id == SeriesModel.id)
        .filter(SeriesModel.user_id == str(current_user.id))
        .order_by(VideoModel.created_at.desc())
        .all()
    )

    result = []
    for v in videos:
        vd = v.to_dict()
        vd["seriesName"] = v.series.name if v.series else "Unknown"
        vd["seriesId"] = v.series_id
        result.append(vd)

    return {"videos": result}


@app.get("/api/videos/{video_id}/thumbnail")
async def get_video_thumbnail(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Serve video thumbnail image (first scene image).
    """
    from fastapi.responses import FileResponse
    from database.models import Video as VideoModel
    
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    if str(video.series.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized")
    
    # Try explicit thumbnail_path first
    if video.thumbnail_path and os.path.exists(video.thumbnail_path):
        return FileResponse(video.thumbnail_path, media_type="image/png")
    
    # Fallback: look for thumbnail.png or first scene in project dir
    if video.project_dir:
        output_dir = os.path.join("output", video.project_dir)
        thumb_path = os.path.join(output_dir, "thumbnail.png")
        if os.path.exists(thumb_path):
            return FileResponse(thumb_path, media_type="image/png")
        
        # Last resort: first scene image from temp
        temp_scene = os.path.join("temp", video.project_dir, "scenes", "scene_01.png")
        if os.path.exists(temp_scene):
            return FileResponse(temp_scene, media_type="image/png")
    
    raise HTTPException(status_code=404, detail="Thumbnail not found")


@app.get("/api/videos/{video_id}/stream")
async def stream_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Stream video file from temp folder for preview.
    Only works before video is uploaded to platforms.
    """
    from fastapi.responses import FileResponse
    from database.models import Video as VideoModel
    
    # Get video record
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Verify ownership
    if str(video.series.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to view this video")
    
    # Check if video file exists
    if not video.video_path or not os.path.exists(video.video_path):
        raise HTTPException(status_code=404, detail="Video file not found. It may have been uploaded and deleted.")
    
    # Stream video file
    return FileResponse(
        video.video_path,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Disposition": f'inline; filename="video_{video_id}.mp4"'
        }
    )


@app.get("/api/videos/{video_id}/download")
async def download_video(
    video_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Download video file.
    """
    from fastapi.responses import FileResponse
    from database.models import Video as VideoModel
    
    # Get video record
    video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
    
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    
    # Verify ownership
    if str(video.series.user_id) != str(current_user.id):
        raise HTTPException(status_code=403, detail="Not authorized to download this video")
    
    # Check if video file exists
    if not video.video_path or not os.path.exists(video.video_path):
        raise HTTPException(status_code=404, detail="Video file not found. It may have been uploaded and deleted.")
    
    # Download video file
    filename = f"{video.title or 'video'}_{video_id}.mp4".replace(' ', '_')
    return FileResponse(
        video.video_path,
        media_type="video/mp4",
        filename=filename,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"'
        }
    )

# Legacy endpoint removed - use GET /api/videos instead


# ═══════════════════════════════════════════════════════════
# Background Task Processing
# ═══════════════════════════════════════════════════════════

async def process_video_generation_db(
    job_id: str,
    video_id: str,
    series_id: str,
    user_id: str
):
    """
    Background task to generate video with database tracking.
    Updates job, video, and series status as it progresses.
    """
    from sqlalchemy.orm import Session
    from database.models import Series as SeriesModel, Video as VideoModel, Job as JobModel
    
    db: Session = next(get_db())
    
    try:
        # Get job, video, and series from database
        job = db.query(JobModel).filter(JobModel.id == job_id).first()
        video = db.query(VideoModel).filter(VideoModel.id == video_id).first()
        series = db.query(SeriesModel).filter(SeriesModel.id == series_id).first()
        
        if not job or not video or not series:
            logger.error(f"Job {job_id}, Video {video_id}, or Series {series_id} not found")
            return
        
        # Update job status
        job.status = "processing"
        job.started_at = datetime.utcnow()
        db.commit()
        
        # Create settings from series
        settings = UserSeriesSettings(
            user_id=user_id,
            series_id=series_id,
            series_name=series.name,
            series_description=series.description or "",
            niche=series.niche,
            niche_format=series.niche_format,
            visual_style=series.visual_style,
            voice_id=series.voice_id,
            music_track=series.music_track,
            caption_style=series.caption_style,
            video_duration=series.video_duration,
        )
        
        logger.info(f"Starting video generation for series {series.name}")
        
        # Run generation (blocking, but in background thread)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: generator.generate_video(settings, topic=None)
        )
        
        logger.info(f"Video generation completed: {result.project_id}")
        
        # Update video with results
        video.status = "ready"
        video.progress = 100
        video.current_stage = "complete"
        video.project_dir = result.project_id
        video.video_path = result.video_path
        video.thumbnail_path = result.thumbnail_path
        video.title = result.title
        video.description = result.description
        video.tags = result.tags
        video.duration_seconds = result.duration_seconds
        video.scene_count = result.scene_count
        video.generation_time_seconds = result.generation_time_seconds
        db.commit()
        
        # Update job with result
        job.status = "completed"
        job.progress = 100
        job.stage = "complete"
        job.completed_at = datetime.utcnow()
        job.result = {
            "project_id": result.project_id,
            "video_path": result.video_path,
            "thumbnail_path": result.thumbnail_path,
            "title": result.title,
            "duration_seconds": result.duration_seconds,
        }
        db.commit()
        
        # Update series stats
        series.videos_generated += 1
        series.last_video_at = datetime.utcnow()
        db.commit()
        
        logger.info(f"Successfully generated video {video.id} for series {series.name}")
        
        # ═══════════════════════════════════════════════════════════
        # AUTO-UPLOAD TO PLATFORMS (If series has platforms configured)
        # ═══════════════════════════════════════════════════════════
        
        if series.platforms and len(series.platforms) > 0:
            logger.info(f"Auto-uploading to platforms: {series.platforms}")
            
            try:
                from engines.platform_upload_orchestrator import PlatformUploadOrchestrator
                
                orchestrator = PlatformUploadOrchestrator()
                
                # Check if video has scheduled time
                upload_time = video.scheduled_for if video.scheduled_for else None
                
                # Upload to all configured platforms
                upload_results = orchestrator.upload_to_platforms(
                    video_record=video,
                    series_record=series,
                    platforms=series.platforms,
                    db=db,
                    scheduled_time=upload_time
                )
                
                logger.info(f"Upload results: {upload_results['platforms_succeeded']} succeeded, {upload_results['platforms_failed']} failed")
                
                # Store upload results in job
                job.result['upload_results'] = upload_results
                db.commit()
                
            except Exception as upload_error:
                logger.error(f"Platform upload failed: {upload_error}", exc_info=True)
                # Don't fail the entire job if upload fails
                job.result['upload_error'] = str(upload_error)
                db.commit()
        
    except Exception as e:
        logger.error(f"Video generation failed for job {job_id}: {e}", exc_info=True)
        
        # Update job as failed
        if job:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            db.commit()
        
        # Update video as failed
        if video:
            video.status = "failed"
            video.error_message = str(e)
            db.commit()
    
    finally:
        db.close()


# ═══════════════════════════════════════════════════════════
# Polar.sh Payment Endpoints
# ═══════════════════════════════════════════════════════════

# Plan → Polar product ID mapping
POLAR_PRODUCT_MAP = {
    "launch": os.getenv("POLAR_PRODUCT_LAUNCH", ""),
    "grow": os.getenv("POLAR_PRODUCT_GROW", ""),
    "scale": os.getenv("POLAR_PRODUCT_SCALE", ""),
}

# Plan base prices (cents)
PLAN_PRICES = {
    "launch": 1900,
    "grow": 3900,
    "scale": 6900,
}


class CheckoutRequest(BaseModel):
    """Request to create a Polar checkout session"""
    plan: str  # launch, grow, scale
    series_count: int = 1  # 1 = base, 2+ = extra series
    billing_period: str = "monthly"  # monthly or yearly


class CheckoutResponse(BaseModel):
    """Checkout session response"""
    checkout_url: str
    checkout_id: str


@app.post("/api/checkout/create", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a Polar checkout session for plan purchase.
    Supports extra series (each extra series = 100% of base price).
    """
    from polar_sdk import Polar
    from polar_sdk.models import CheckoutCreate
    
    # Validate plan
    if request.plan not in POLAR_PRODUCT_MAP:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {request.plan}")
    
    product_id = POLAR_PRODUCT_MAP[request.plan]
    if not product_id:
        raise HTTPException(status_code=500, detail="Payment not configured for this plan")
    
    # Series count validation
    series_count = max(1, request.series_count)
    if request.plan == "launch" and series_count > 1:
        raise HTTPException(status_code=400, detail="Launch plan only supports 1 series")
    
    access_token = os.getenv("POLAR_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
    
    try:
        polar = Polar(access_token=access_token)
        
        # Create checkout with product + metadata
        checkout = polar.checkouts.create(request=CheckoutCreate(
            product_id=product_id,
            success_url=f"{frontend_url}/dashboard/billing/success?checkout_id={{CHECKOUT_ID}}",
            customer_email=current_user.email,
            metadata={
                "user_id": str(current_user.id),
                "plan": request.plan,
                "series_count": str(series_count),
                "billing_period": request.billing_period,
            }
        ))
        
        logger.info(f"Checkout created for {current_user.email}: plan={request.plan}, series={series_count}, checkout_id={checkout.id}")
        
        return CheckoutResponse(
            checkout_url=checkout.url,
            checkout_id=checkout.id
        )
        
    except Exception as e:
        logger.error(f"Failed to create checkout: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to create checkout session")


@app.get("/api/checkout/{checkout_id}/verify")
async def verify_checkout(
    checkout_id: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify a checkout session status (called from success page).
    If checkout is confirmed/succeeded, activate the user's plan.
    """
    from polar_sdk import Polar
    
    access_token = os.getenv("POLAR_ACCESS_TOKEN", "")
    if not access_token:
        raise HTTPException(status_code=500, detail="Payment system not configured")
    
    try:
        polar = Polar(access_token=access_token)
        checkout = polar.checkouts.get(id=checkout_id)
        
        logger.info(f"Checkout {checkout_id} status: {checkout.status}, metadata: {checkout.metadata}")
        
        # Check if this checkout belongs to the current user
        metadata = checkout.metadata or {}
        checkout_user_id = metadata.get("user_id", "")
        
        if checkout_user_id != str(current_user.id):
            raise HTTPException(status_code=403, detail="This checkout doesn't belong to you")
        
        # Safely extract status string from Polar enum
        raw_status = checkout.status
        if hasattr(raw_status, 'value'):
            status = str(raw_status.value).lower()
        else:
            status = str(raw_status).lower()
            # Strip enum class prefix if present (e.g. "checkoutstatus.succeeded")
            if '.' in status:
                status = status.rsplit('.', 1)[-1]
        
        if status in ("succeeded", "confirmed"):
            # Activate the plan
            plan = metadata.get("plan", "launch")
            series_count = int(metadata.get("series_count", "1"))
            
            current_user.plan = plan
            current_user.series_purchased = series_count
            current_user.plan_started_at = datetime.utcnow()
            
            # Store Polar customer info if available
            if checkout.customer_id:
                current_user.polar_customer_id = str(checkout.customer_id)
            if checkout.subscription_id:
                current_user.polar_subscription_id = str(checkout.subscription_id)
            
            db.commit()
            
            logger.info(f"User {current_user.email} activated: plan={plan}, series={series_count}")
            
            return {
                "status": "success",
                "plan": plan,
                "series_count": series_count,
                "message": f"Welcome to the {plan.title()} plan!"
            }
        
        return {
            "status": status,
            "message": "Payment is still being processed. Please wait a moment."
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to verify checkout {checkout_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Failed to verify checkout")


@app.post("/api/webhooks/polar")
async def polar_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Handle Polar webhook events.
    Processes checkout.created, order.created, subscription events.
    """
    webhook_secret = os.getenv("POLAR_WEBHOOK_SECRET", "")
    
    try:
        body = await request.body()
        headers = dict(request.headers)
        
        # Validate webhook signature if secret is configured
        if webhook_secret and webhook_secret != "your-webhook-secret-here":
            from polar_sdk.webhooks import validate_event, WebhookVerificationError
            try:
                event = validate_event(body, headers, webhook_secret)
            except WebhookVerificationError:
                logger.warning("Webhook signature verification failed")
                raise HTTPException(status_code=403, detail="Invalid webhook signature")
        else:
            # Parse without verification (dev mode)
            import json
            event_data = json.loads(body)
            # Create a simple namespace for event access
            class SimpleEvent:
                def __init__(self, data):
                    self.TYPE = data.get("type", "")
                    self.data = data.get("data", {})
            event = SimpleEvent(event_data)
        
        event_type = ""
        if hasattr(event, 'TYPE'):
            raw_type = event.TYPE
            if hasattr(raw_type, 'value'):
                event_type = str(raw_type.value)
            else:
                event_type = str(raw_type)
        elif hasattr(event, 'type'):
            event_type = str(event.type)
        logger.info(f"Polar webhook received: {event_type}")
        
        # Handle checkout completed
        if event_type in ("checkout.created", "checkout.updated"):
            data = event.data
            
            # Get metadata from the checkout
            metadata = {}
            if hasattr(data, 'metadata'):
                metadata = data.metadata or {}
            elif isinstance(data, dict):
                metadata = data.get("metadata", {})
            
            # Get status — handle both Polar enum and raw dict
            checkout_status = ""
            if hasattr(data, 'status'):
                raw_st = data.status
                if hasattr(raw_st, 'value'):
                    checkout_status = str(raw_st.value).lower()
                else:
                    checkout_status = str(raw_st).lower()
                    if '.' in checkout_status:
                        checkout_status = checkout_status.rsplit('.', 1)[-1]
            elif isinstance(data, dict):
                checkout_status = str(data.get("status", "")).lower()
            
            logger.info(f"Checkout webhook: status={checkout_status}, metadata={metadata}")
            
            if checkout_status in ("succeeded", "confirmed"):
                user_id = metadata.get("user_id", "")
                plan = metadata.get("plan", "")
                series_count = int(metadata.get("series_count", "1"))
                
                if user_id and plan:
                    user = db.query(User).filter(User.id == user_id).first()
                    if user:
                        user.plan = plan
                        user.series_purchased = series_count
                        user.plan_started_at = datetime.utcnow()
                        
                        # Store customer/subscription IDs
                        customer_id = None
                        subscription_id = None
                        if hasattr(data, 'customer_id'):
                            customer_id = data.customer_id
                        elif isinstance(data, dict):
                            customer_id = data.get("customer_id")
                        if hasattr(data, 'subscription_id'):
                            subscription_id = data.subscription_id
                        elif isinstance(data, dict):
                            subscription_id = data.get("subscription_id")
                        
                        if customer_id:
                            user.polar_customer_id = str(customer_id)
                        if subscription_id:
                            user.polar_subscription_id = str(subscription_id)
                        
                        db.commit()
                        logger.info(f"Webhook: Activated {user.email} → plan={plan}, series={series_count}")
        
        # Handle order created (backup for checkout)
        elif event_type == "order.created":
            data = event.data
            metadata = {}
            if hasattr(data, 'metadata'):
                metadata = data.metadata or {}
            elif isinstance(data, dict):
                metadata = data.get("metadata", {})
            
            user_id = metadata.get("user_id", "")
            plan = metadata.get("plan", "")
            series_count = int(metadata.get("series_count", "1"))
            
            if user_id and plan:
                user = db.query(User).filter(User.id == user_id).first()
                if user:
                    user.plan = plan
                    user.series_purchased = series_count
                    user.plan_started_at = datetime.utcnow()
                    db.commit()
                    logger.info(f"Order webhook: Activated {user.email} → plan={plan}, series={series_count}")
        
        # Handle subscription canceled — give grace period until end of billing cycle
        elif event_type in ("subscription.canceled", "subscription.revoked"):
            data = event.data
            
            # Find user by subscription ID
            subscription_id = None
            if hasattr(data, 'id'):
                subscription_id = str(data.id)
            elif isinstance(data, dict):
                subscription_id = str(data.get("id", ""))
            
            if subscription_id:
                user = db.query(User).filter(User.polar_subscription_id == subscription_id).first()
                if user:
                    # For "revoked" (e.g. refund) → immediate downgrade
                    if event_type == "subscription.revoked":
                        user.plan = "free"
                        user.series_purchased = 0
                        user.plan_expires_at = None
                        db.commit()
                        logger.info(f"Subscription revoked: {user.email} → free plan (immediate)")
                    else:
                        # Canceled → keep plan active until current period ends
                        # Try to get current_period_end from Polar data
                        period_end = None
                        if hasattr(data, 'current_period_end'):
                            period_end = data.current_period_end
                        elif isinstance(data, dict):
                            period_end = data.get("current_period_end")
                        
                        if period_end:
                            from dateutil import parser as dt_parser
                            try:
                                user.plan_expires_at = dt_parser.parse(str(period_end)).replace(tzinfo=None)
                            except Exception:
                                # Fallback: expire in 30 days
                                from datetime import timedelta
                                user.plan_expires_at = datetime.utcnow() + timedelta(days=30)
                        else:
                            # No period_end data — default 30 day grace
                            from datetime import timedelta
                            user.plan_expires_at = datetime.utcnow() + timedelta(days=30)
                        
                        db.commit()
                        logger.info(f"Subscription canceled: {user.email} → plan active until {user.plan_expires_at}")
        
        return {"received": True}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {e}", exc_info=True)
        # Return 200 to prevent Polar from retrying
        return {"received": True, "error": str(e)}


@app.get("/api/user/plan")
async def get_user_plan(
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get current user's plan details."""
    return {
        "plan": current_user.plan,
        "series_purchased": current_user.series_purchased,
        "plan_limits": current_user.plan_limits,
        "videos_remaining": current_user.videos_remaining,
        "videos_generated_this_month": current_user.videos_generated_this_month,
        "plan_started_at": str(current_user.plan_started_at) if current_user.plan_started_at else None,
        "is_free": current_user.plan == "free",
    }


# ═══════════════════════════════════════════════════════════
# Run Server
# ═══════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
