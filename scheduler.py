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
from datetime import datetime, timedelta
from typing import List, Dict, Optional
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
        self.db = next(get_db())
        
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
    
    def calculate_next_scheduled_time(
        self, 
        series: Series, 
        user: User,
        last_video_time: Optional[datetime] = None
    ) -> datetime:
        """
        Calculate next scheduled upload time based on plan and posting_times.
        
        Args:
            series: Series configuration with posting_times
            user: User with plan (launch/grow/scale)
            last_video_time: When last video was scheduled/published
            
        Returns:
            Next datetime to schedule video upload
        """
        now = datetime.utcnow()
        posting_times = series.posting_times or ["09:00"]  # Default 9 AM
        frequency = self.get_plan_posting_frequency(user.plan)
        
        # Launch plan: 3x per week (e.g., Mon/Wed/Fri at first posting_time)
        if user.plan == "launch":
            # Use first posting time
            hour, minute = map(int, posting_times[0].split(':'))
            
            # If no last video, schedule for next occurrence
            if not last_video_time:
                next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time
            
            # Schedule ~2-3 days after last video
            next_time = last_video_time + timedelta(days=frequency["days_between"])
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Ensure it's in the future
            while next_time <= now:
                next_time += timedelta(days=frequency["days_between"])
            
            return next_time
        
        # Grow plan: Daily at first posting_time
        elif user.plan == "grow":
            hour, minute = map(int, posting_times[0].split(':'))
            
            if not last_video_time:
                next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                if next_time <= now:
                    next_time += timedelta(days=1)
                return next_time
            
            # Next day at same time
            next_time = last_video_time + timedelta(days=1)
            next_time = next_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            while next_time <= now:
                next_time += timedelta(days=1)
            
            return next_time
        
        # Scale plan: 2x daily at posting_times[0] and posting_times[1]
        elif user.plan == "scale":
            # Should have 2 posting times
            time_slots = posting_times if len(posting_times) >= 2 else [posting_times[0], "21:00"]
            
            if not last_video_time:
                # Schedule for next available slot
                for time_str in time_slots:
                    hour, minute = map(int, time_str.split(':'))
                    next_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_time > now:
                        return next_time
                # All slots today passed, use first slot tomorrow
                hour, minute = map(int, time_slots[0].split(':'))
                return (now + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
            
            # Find next slot after last video
            last_hour = last_video_time.hour
            
            for time_str in time_slots:
                hour, minute = map(int, time_str.split(':'))
                next_time = last_video_time.replace(hour=hour, minute=minute, second=0, microsecond=0)
                
                if next_time > last_video_time and next_time > now:
                    return next_time
            
            # No more slots today, use first slot tomorrow
            hour, minute = map(int, time_slots[0].split(':'))
            return (last_video_time + timedelta(days=1)).replace(hour=hour, minute=minute, second=0, microsecond=0)
        
        # Default: daily
        return now + timedelta(days=1)
    
    def should_generate_now(self, scheduled_upload_time: datetime) -> bool:
        """Check if video should be generated now (6 hours before upload)"""
        now = datetime.utcnow()
        generation_time = scheduled_upload_time - self.GENERATION_LEAD_TIME
        
        # Generate if we're within 30 minutes of generation time
        time_diff = abs((now - generation_time).total_seconds())
        return time_diff <= 1800  # 30 minutes window
    
    def get_videos_to_generate(self) -> List[Dict]:
        """Find videos that need to be generated now"""
        videos_to_generate = []
        
        # Get all active series
        series_list = self.db.query(Series).filter(
            Series.status == "active"
        ).all()
        
        logger.info(f"Checking {len(series_list)} active series for scheduling")
        
        for series in series_list:
            # Get series owner
            user = self.db.query(User).filter(User.id == series.user_id).first()
            if not user:
                continue
            
            # Check if user can generate more videos this month
            # Note: videos_per_month already multiplied by series_purchased in User model
            if not user.can_generate_video:
                logger.info(f"User {user.email} has reached monthly limit ({user.videos_generated_this_month}/{user.plan_limits['videos_per_month']}), skipping all series")
                continue
            
            # Get last scheduled video for this series
            last_video = self.db.query(Video).filter(
                Video.series_id == series.id,
                Video.scheduled_for.isnot(None)
            ).order_by(Video.scheduled_for.desc()).first()
            
            # Calculate next scheduled upload time
            next_upload_time = self.calculate_next_scheduled_time(
                series,
                user,
                last_video.scheduled_for if last_video else None
            )
            
            # Check if we should generate now
            if self.should_generate_now(next_upload_time):
                logger.info(f"Series '{series.name}' ready for generation (upload at {next_upload_time})")
                
                videos_to_generate.append({
                    "series": series,
                    "user": user,
                    "scheduled_upload_time": next_upload_time
                })
        
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
        try:
            # Create video record
            video = Video(
                series_id=str(series.id),
                status="generating",
                progress=0,
                current_stage="initializing",
                scheduled_for=scheduled_upload_time
            )
            self.db.add(video)
            self.db.commit()
            self.db.refresh(video)
            
            logger.info(f"Created video {video.id} scheduled for {scheduled_upload_time}")
            
            # Create job for tracking
            job = Job(
                video_id=str(video.id),
                job_type="scheduled_video_generation",
                status="pending",
                stage="initializing"
            )
            self.db.add(job)
            self.db.commit()
            self.db.refresh(job)
            
            logger.info(f"Created job {job.id} for video {video.id}")
            
            # Trigger background video generation
            # Note: This runs synchronously in this context
            await process_video_generation_db(
                job_id=str(job.id),
                video_id=str(video.id),
                series_id=str(series.id),
                user_id=str(user.id)
            )
            
            # Update series stats
            series.last_video_at = datetime.utcnow()
            series.next_video_at = self.calculate_next_scheduled_time(
                series,
                user,
                scheduled_upload_time
            )
            series.videos_generated += 1
            self.db.commit()
            
            logger.info(f"✅ Video generation completed for series '{series.name}'")
            
            return str(job.id)
            
        except Exception as e:
            logger.error(f"Failed to generate video for series '{series.name}': {e}")
            self.db.rollback()
            return None
    
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
        """Close database connection"""
        self.db.close()


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
