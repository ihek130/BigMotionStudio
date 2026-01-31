"""
Job Model - Background job tracking for video generation
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON

from ..connection import Base


class Job(Base):
    """
    Background job for tracking video generation progress.
    Allows frontend to poll for status updates.
    """
    __tablename__ = "jobs"
    
    # Primary key (using String for SQLite compatibility)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Related video (if applicable)
    video_id = Column(String(36), ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    
    # Job type
    job_type = Column(String(50), nullable=False)  # video_generation, upload, thumbnail
    
    # Status tracking
    status = Column(String(50), default="pending")  # pending, processing, completed, failed, cancelled
    progress = Column(Integer, default=0)  # 0-100
    
    # Current stage (for video generation)
    stage = Column(String(100), nullable=True)  # script, voiceover, images, assembly, upload
    stage_progress = Column(Integer, default=0)  # Progress within current stage
    
    # Stage breakdown
    stages_completed = Column(JSON, default=[])  # List of completed stages
    current_stage_started_at = Column(DateTime, nullable=True)
    
    # Result
    result = Column(JSON, nullable=True)  # Job result data
    error_message = Column(Text, nullable=True)
    error_details = Column(JSON, nullable=True)  # Stack trace, etc.
    
    # Retry handling
    attempts = Column(Integer, default=0)
    max_attempts = Column(Integer, default=3)
    last_attempt_at = Column(DateTime, nullable=True)
    
    # Timing
    created_at = Column(DateTime, default=datetime.utcnow)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    
    def __repr__(self):
        return f"<Job {self.id} - {self.job_type} - {self.status}>"
    
    @property
    def duration_seconds(self):
        """Get job duration in seconds"""
        if not self.started_at:
            return None
        end = self.completed_at or datetime.utcnow()
        return (end - self.started_at).total_seconds()
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "videoId": str(self.video_id) if self.video_id else None,
            "jobType": self.job_type,
            "status": self.status,
            "progress": self.progress,
            "stage": self.stage,
            "stageProgress": self.stage_progress,
            "stagesCompleted": self.stages_completed,
            "result": self.result,
            "errorMessage": self.error_message,
            "durationSeconds": self.duration_seconds,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
