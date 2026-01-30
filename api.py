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
from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends
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

# Job tracking
jobs: Dict[str, Dict] = {}


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
        "generator_ready": generator is not None,
        "active_jobs": len([j for j in jobs.values() if j['status'] == 'processing']),
        "total_jobs": len(jobs)
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
    Upgrade user's series count (called after successful payment).
    This should be called from payment webhook or after Stripe checkout success.
    """
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


@app.post("/api/video/generate", response_model=JobResponse)
async def generate_video(
    request: GenerateVideoRequest,
    background_tasks: BackgroundTasks,
    db = Depends(get_db),
    current_user: User = Depends(require_can_generate_video)  # CHECK VIDEO LIMIT
):
    """
    Trigger video generation for a series.
    Enforces monthly video limits based on user's subscription plan.
    Returns immediately with job ID, processes in background.
    """
    # Increment video counter
    current_user.videos_generated_this_month += 1
    current_user.videos_generated_total += 1
    current_user.last_video_at = datetime.now()
    db.commit()
    
    logger.info(f"User {current_user.email} generating video {current_user.videos_generated_this_month}/{current_user.plan_limits['videos_per_month']}")
    
    job_id = str(uuid.uuid4())
    
    # Initialize job tracking
    jobs[job_id] = {
        "status": "pending",
        "progress": 0,
        "stage": "initializing",
        "result": None,
        "error": None,
        "created_at": datetime.now().isoformat()
    }
    
    # Start background task
    background_tasks.add_task(
        process_video_generation,
        job_id,
        request.user_id,
        request.series_id,
        request.topic
    )
    
    return JobResponse(
        job_id=job_id,
        status="pending",
        message="Video generation started"
    )


@app.post("/api/video/generate-sync", response_model=VideoResponse)
async def generate_video_sync(request: CreateSeriesRequest):
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


@app.get("/api/job/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of a video generation job"""
    if job_id not in jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    job = jobs[job_id]
    
    return JobStatusResponse(
        job_id=job_id,
        status=job["status"],
        progress=job["progress"],
        stage=job["stage"],
        result=job["result"],
        error=job["error"]
    )


@app.get("/api/videos/{user_id}")
async def list_user_videos(user_id: str):
    """List all generated videos for a user"""
    # In production, query database
    # For now, scan output directory
    
    output_dir = "output"
    videos = []
    
    if os.path.exists(output_dir):
        for project_id in os.listdir(output_dir):
            project_path = os.path.join(output_dir, project_id)
            if os.path.isdir(project_path):
                video_path = os.path.join(project_path, "final_video.mp4")
                if os.path.exists(video_path):
                    videos.append({
                        "project_id": project_id,
                        "video_path": video_path,
                        "created_at": datetime.fromtimestamp(
                            os.path.getctime(video_path)
                        ).isoformat()
                    })
    
    return {"videos": videos}


# ═══════════════════════════════════════════════════════════
# Background Task Processing
# ═══════════════════════════════════════════════════════════

async def process_video_generation(
    job_id: str,
    user_id: str,
    series_id: str,
    topic: Optional[str]
):
    """
    Background task to generate video.
    Updates job status as it progresses.
    """
    try:
        jobs[job_id]["status"] = "processing"
        
        # For demo, create default settings
        # In production, load from database based on series_id
        settings = UserSeriesSettings(
            user_id=user_id,
            series_id=series_id,
            series_name="Generated Series",
            series_description="",
            niche="scary-stories",
            visual_style="dark-comic",
            voice_id="male-deep",
            video_duration=60,
        )
        
        # Update progress stages
        stages = [
            ("script", 10),
            ("images", 40),
            ("voiceover", 60),
            ("assembly", 80),
            ("thumbnail", 90),
            ("seo", 95),
            ("complete", 100)
        ]
        
        # Run generation (blocking, but in background thread)
        result = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda: generator.generate_video(settings, topic)
        )
        
        # Update job with result
        jobs[job_id]["status"] = "completed"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["stage"] = "complete"
        jobs[job_id]["result"] = {
            "project_id": result.project_id,
            "video_path": result.video_path,
            "thumbnail_path": result.thumbnail_path,
            "title": result.title,
            "duration_seconds": result.duration_seconds,
            "scene_count": result.scene_count,
        }
        
    except Exception as e:
        logger.error(f"Job {job_id} failed: {e}")
        jobs[job_id]["status"] = "failed"
        jobs[job_id]["error"] = str(e)


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
            music_id=series.music_track,
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
