"""
Video Generation & Upload Scheduler
====================================
Automatically generates and uploads videos based on series schedule.

Features:
- Generates videos 1.5 hours before scheduled upload time (optimized for minimal server storage)
- Respects plan frequency limits (3x/week, daily, 2x/day)
- Handles multiple series per user
- Background task processing
- Automatic retry on failure

Run as background service:
    python scheduler.py

Or via cron/Task Scheduler:
    0 * * * * python scheduler.py  # Run every hour
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from zoneinfo import ZoneInfo
import logging

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from database.connection import get_db, init_db
from database.models.user import User
from database.models.series import Series
from database.models.video import Video
from database.models.job import Job
from api import process_video_generation_db

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class VideoScheduler:
    """Manages automated video generation and upload scheduling"""
    
    GENERATION_LEAD_TIME = timedelta(hours=1.5)  # Generate 1.5 hours before upload (optimized for server efficiency)
    
    def __init__(self):
        # Use a fresh session per scheduling cycle instead of one long-lived session
        pass
    
    def _get_db(self):
        """Get a fresh database session for each operation."""
        return next(get_db())
        
    def get_plan_posting_frequency(self, plan: str) -> Dict:
        """Get posting frequency for each plan"""
        frequencies = {
            "launch": {
                "videos_per_week": 3,
                "videos_per_day": 0,  # Not daily
                "days_between": 2,  # ~every 2-3 days
            },
            "grow": {
                "videos_per_week": 7,
                "videos_per_day": 1,
                "days_between": 1,  # Daily
            },
            "scale": {
                "videos_per_week": 14,
                "videos_per_day": 2,
                "days_between": 0.5,  # Twice daily
            }
        }
        return frequencies.get(plan, frequencies["launch"])
    
    def _local_to_utc(self, naive_dt: datetime, tz_name: str) -> datetime:
        """Convert a naive datetime (in user's local timezone) to naive UTC datetime"""
        try:
            local_tz = ZoneInfo(tz_name)
            # Attach the user's timezone to the naive datetime
            local_dt = naive_dt.replace(tzinfo=local_tz)
            # Convert to UTC and strip tzinfo for consistency
            utc_dt = local_dt.astimezone(timezone.utc).replace(tzinfo=None)
            return utc_dt
        except Exception as e:
            logger.warning(f"Invalid timezone '{tz_name}', treating as UTC: {e}")
            return naive_dt
    
    def calculate_next_scheduled_time(
        self, 
        series: Series, 
        user: User,
        last_video_time: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate next scheduled upload time based on plan and posting_times.
        Posting times are in the user's local timezone (series.timezone).
        Returns a naive UTC datetime.
        
        Args:
            series: Series configuration with posting_times and timezone
            user: User with plan (launch/grow/scale)
            last_video_time: When last video was scheduled/published (UTC)
            
        Returns:
            Next datetime (UTC) to schedule video upload
        """
        now = datetime.utcnow()
        posting_times = series.posting_times or ["09:00"]  # Default 9 AM
        tz_name = getattr(series, 'timezone', None) or "UTC"
        frequency = self.get_plan_posting_frequency(user.plan)
        
        # Helper: given a naive local date+time → naive UTC
        def next_local_slot(base_date_utc: datetime, time_str: str) -> datetime:
            """Build a local datetime from a UTC base date + local time string, then convert to UTC."""
            hour, minute = map(int, time_str.split(':'))
            # Convert base_date from UTC to local so we get the correct local date
            try:
                local_tz = ZoneInfo(tz_name)
                base_local = base_date_utc.replace(tzinfo=timezone.utc).astimezone(local_tz).replace(tzinfo=None)
            except Exception:
                base_local = base_date_utc
            local_dt = base_local.replace(hour=hour, minute=minute, second=0, microsecond=0)
            return self._local_to_utc(local_dt, tz_name)
        
        # Launch plan: 3x per week (e.g., Mon/Wed/Fri at first posting_time)
        if user.plan == "launch":
            time_str = posting_times[0]
            
            if not last_video_time:
                next_time = next_local_slot(now, time_str)
                if next_time <= now:
                    next_time = next_local_slot(now + timedelta(days=1), time_str)
                return next_time
            
            # Schedule ~2-3 days after last video
            candidate = last_video_time + timedelta(days=frequency["days_between"])
            next_time = next_local_slot(candidate, time_str)
            
            while next_time <= now:
                candidate += timedelta(days=frequency["days_between"])
                next_time = next_local_slot(candidate, time_str)
            
            return next_time
        
        # Grow plan: Daily at first posting_time
        elif user.plan == "grow":
            time_str = posting_times[0]
            
            if not last_video_time:
                next_time = next_local_slot(now, time_str)
                if next_time <= now:
                    next_time = next_local_slot(now + timedelta(days=1), time_str)
                return next_time
            
            candidate = last_video_time + timedelta(days=1)
            next_time = next_local_slot(candidate, time_str)
            
            while next_time <= now:
                candidate += timedelta(days=1)
                next_time = next_local_slot(candidate, time_str)
            
            return next_time
        
        # Scale plan: 2x daily at posting_times[0] and posting_times[1]
        elif user.plan == "scale":
            time_slots = posting_times if len(posting_times) >= 2 else [posting_times[0], "21:00"]
            
            if not last_video_time:
                for time_str in time_slots:
                    next_time = next_local_slot(now, time_str)
                    if next_time > now:
                        return next_time
                return next_local_slot(now + timedelta(days=1), time_slots[0])
            
            # Find next slot after last video
            for time_str in time_slots:
                next_time = next_local_slot(last_video_time, time_str)
                if next_time > last_video_time and next_time > now:
                    return next_time
            
            return next_local_slot(last_video_time + timedelta(days=1), time_slots[0])
        
        # Default: daily
        return now + timedelta(days=1)
    
    def should_generate_now(self, scheduled_upload_time: datetime) -> bool:
        """Check if video should be generated now (1.5 hours before upload)"""
        now = datetime.utcnow()
        generation_time = scheduled_upload_time - self.GENERATION_LEAD_TIME
        
        # Generate if we're past the generation start time but before the upload time
        # This gives a wide window: from 1.5 hours before upload until upload time itself
        return generation_time <= now <= scheduled_upload_time
    
    def get_videos_to_generate(self) -> List[Dict]:
        """Find videos that need to be generated now"""
        videos_to_generate = []
        db = self._get_db()
        
        try:
            # Get all active series
            series_list = db.query(Series).filter(
                Series.status == "active"
            ).all()
            
            logger.info(f"Checking {len(series_list)} active series for scheduling")
            
            for series in series_list:
                # Get series owner
                user = db.query(User).filter(User.id == series.user_id).first()
                if not user:
                    logger.warning(f"Series '{series.name}' has no owner, skipping")
                    continue
                
                # Auto-reset monthly usage if needed
                if user.check_monthly_reset():
                    db.commit()
                
                # Check if user can generate more videos this month
                if not user.can_generate_video:
                    logger.info(f"User {user.email} has reached monthly limit ({user.videos_generated_this_month}/{user.plan_limits['videos_per_month']}), skipping all series")
                    continue
                
                # Get last scheduled video for this series
                last_video = db.query(Video).filter(
                    Video.series_id == series.id,
                    Video.scheduled_for.isnot(None)
                ).order_by(Video.scheduled_for.desc()).first()
                
                last_video_time = last_video.scheduled_for if last_video else None
                tz_name = getattr(series, 'timezone', None) or 'UTC'
                logger.info(f"Series '{series.name}': plan={user.plan}, posting_times={series.posting_times}, timezone={tz_name}, last_video_at={last_video_time}")
                
                # Calculate next scheduled upload time
                next_upload_time = self.calculate_next_scheduled_time(
                    series,
                    user,
                    last_video_time
                )
                
                generation_time = next_upload_time - self.GENERATION_LEAD_TIME
                now = datetime.utcnow()
                logger.info(f"Series '{series.name}': next_upload={next_upload_time}, generation_window={generation_time} to {next_upload_time}, now={now}")
                
                # Duplicate guard — check if a video is already generating/scheduled for this time slot
                existing = db.query(Video).filter(
                    Video.series_id == series.id,
                    Video.scheduled_for == next_upload_time,
                    Video.status.in_(["generating", "ready", "published"])
                ).first()
                
                if existing:
                    logger.info(f"Series '{series.name}': video already exists for slot {next_upload_time} (status={existing.status}), skipping")
                    continue
                
                # Check if we should generate now
                if self.should_generate_now(next_upload_time):
                    logger.info(f"Series '{series.name}' ready for generation (upload at {next_upload_time})")
                    
                    videos_to_generate.append({
                        "series": series,
                        "user": user,
                        "scheduled_upload_time": next_upload_time
                    })
                else:
                    time_until_gen = generation_time - now
                    logger.info(f"Series '{series.name}': NOT in generation window. Generation starts in {time_until_gen}")
        finally:
            db.close()
        
        return videos_to_generate
    
    async def generate_scheduled_video(
        self,
        series: Series,
        user: User,
        scheduled_upload_time: datetime
    ) -> Optional[str]:
        """
        Generate a video for scheduled upload.
        
        Returns:
            job_id if successful, None if failed
        """
        db = self._get_db()
        try:
            # Re-fetch entities in this session to avoid detached instance errors
            series = db.query(Series).filter(Series.id == series.id).first()
            user = db.query(User).filter(User.id == user.id).first()
            
            if not series or not user:
                logger.error("Series or user not found in generate_scheduled_video")
                return None
            
            # Create video record
            video = Video(
                series_id=str(series.id),
                status="generating",
                progress=0,
                current_stage="initializing",
                scheduled_for=scheduled_upload_time
            )
            db.add(video)
            db.commit()
            db.refresh(video)
            
            logger.info(f"Created video {video.id} scheduled for {scheduled_upload_time}")
            
            # Create job for tracking
            job = Job(
                video_id=str(video.id),
                job_type="scheduled_video_generation",
                status="pending",
                stage="initializing"
            )
            db.add(job)
            db.commit()
            db.refresh(job)
            
            logger.info(f"Created job {job.id} for video {video.id}")
            
            # Trigger background video generation
            await process_video_generation_db(
                job_id=str(job.id),
                video_id=str(video.id),
                series_id=str(series.id),
                user_id=str(user.id)
            )
            
            # Re-fetch to update stats (process_video_generation_db uses its own session)
            series = db.query(Series).filter(Series.id == series.id).first()
            user = db.query(User).filter(User.id == user.id).first()
            
            # Update series stats
            if series:
                series.last_video_at = datetime.utcnow()
                series.next_video_at = self.calculate_next_scheduled_time(
                    series,
                    user,
                    scheduled_upload_time
                )
                series.videos_generated += 1
                db.commit()
            
            logger.info(f"✅ Video generation completed for series '{series.name}'")
            
            return str(job.id)
            
        except Exception as e:
            logger.error(f"Failed to generate video for series '{series.name}': {e}")
            db.rollback()
            return None
        finally:
            db.close()
    
    async def run_scheduling_cycle(self):
        """Run one scheduling cycle - check and generate videos"""
        logger.info("="*60)
        logger.info("Starting scheduling cycle")
        logger.info("="*60)
        
        try:
            # Find videos that need generation
            videos_to_generate = self.get_videos_to_generate()
            
            if not videos_to_generate:
                logger.info("No videos scheduled for generation at this time")
                return
            
            logger.info(f"Found {len(videos_to_generate)} videos to generate")
            
            # Generate each video
            for item in videos_to_generate:
                await self.generate_scheduled_video(
                    series=item["series"],
                    user=item["user"],
                    scheduled_upload_time=item["scheduled_upload_time"]
                )
                
                # Small delay between generations
                await asyncio.sleep(5)
            
            logger.info(f"✅ Scheduling cycle complete - generated {len(videos_to_generate)} videos")
            
        except Exception as e:
            logger.error(f"Scheduling cycle error: {e}")
        finally:
            logger.info("="*60)
    
    def close(self):
        """No-op: sessions are now per-operation, no long-lived session to close."""
        pass


async def run_scheduler_service():
    """Run scheduler as continuous background service"""
    logger.info("🚀 Video Scheduler Service Starting")
    logger.info("Checking for scheduled videos every hour")
    logger.info("Videos will be generated 6 hours before scheduled upload time")
    logger.info("="*60)
    
    scheduler = VideoScheduler()
    
    try:
        while True:
            await scheduler.run_scheduling_cycle()
            
            # Wait 1 hour before next check
            logger.info(f"Next check in 1 hour at {(datetime.now() + timedelta(hours=1)).strftime('%Y-%m-%d %H:%M:%S')}")
            await asyncio.sleep(3600)  # 1 hour
            
    except KeyboardInterrupt:
        logger.info("\n⚠️  Scheduler stopped by user")
    except Exception as e:
        logger.error(f"❌ Scheduler error: {e}")
    finally:
        scheduler.close()


async def run_scheduler_once():
    """Run scheduler once (for cron/manual execution)"""
    logger.info("🚀 Running one-time scheduling check")
    
    init_db()  # Ensure database is initialized
    scheduler = VideoScheduler()
    
    try:
        await scheduler.run_scheduling_cycle()
    finally:
        scheduler.close()


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Video Generation Scheduler")
    parser.add_argument(
        "--mode",
        choices=["service", "once"],
        default="once",
        help="Run as continuous service or one-time check (default: once)"
    )
    
    args = parser.parse_args()
    
    if args.mode == "service":
        asyncio.run(run_scheduler_service())
    else:
        asyncio.run(run_scheduler_once())
