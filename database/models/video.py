"""
Video Model - Individual generated video
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, Float, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..connection import Base


class Video(Base):
    """
    Individual generated video.
    Tracks generation status, file paths, and platform publishing.
    """
    __tablename__ = "videos"
    
    # Primary key (using String for SQLite compatibility)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Parent series
    series_id = Column(String(36), ForeignKey("series.id", ondelete="CASCADE"), nullable=False)
    
    # Video content
    topic = Column(String(500), nullable=True)
    title = Column(String(255), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(JSON, default=[])
    
    # File paths (relative to output directory)
    project_dir = Column(String(255), nullable=True)  # e.g., "20260127_143052"
    video_path = Column(Text, nullable=True)
    thumbnail_path = Column(Text, nullable=True)
    script_path = Column(Text, nullable=True)
    
    # Video metadata
    duration_seconds = Column(Float, nullable=True)
    scene_count = Column(Integer, nullable=True)
    
    # Generation status
    status = Column(String(50), default="pending")  # pending, generating, ready, published, failed
    progress = Column(Integer, default=0)  # 0-100
    current_stage = Column(String(100), nullable=True)  # script, voiceover, images, assembly
    error_message = Column(Text, nullable=True)
    
    # Platform publishing status
    youtube_id = Column(String(50), nullable=True)
    youtube_url = Column(Text, nullable=True)
    youtube_published_at = Column(DateTime, nullable=True)
    
    tiktok_id = Column(String(100), nullable=True)
    tiktok_url = Column(Text, nullable=True)
    tiktok_published_at = Column(DateTime, nullable=True)
    
    instagram_id = Column(String(100), nullable=True)
    instagram_url = Column(Text, nullable=True)
    instagram_published_at = Column(DateTime, nullable=True)
    
    # Scheduling
    scheduled_for = Column(DateTime, nullable=True)
    
    # Performance metrics (updated by KPI monitor)
    views = Column(Integer, default=0)
    likes = Column(Integer, default=0)
    comments = Column(Integer, default=0)
    shares = Column(Integer, default=0)
    watch_time_hours = Column(Float, default=0)
    
    # Timing
    generation_time_seconds = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    series = relationship("Series", back_populates="videos")
    
    def __repr__(self):
        return f"<Video {self.id} - {self.status}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "seriesId": str(self.series_id),
            "topic": self.topic,
            "title": self.title,
            "description": self.description,
            "tags": self.tags,
            "videoPath": self.video_path,
            "thumbnailPath": self.thumbnail_path,
            "durationSeconds": self.duration_seconds,
            "status": self.status,
            "progress": self.progress,
            "currentStage": self.current_stage,
            "youtubeUrl": self.youtube_url,
            "youtubeId": self.youtube_id,
            "youtubePublishedAt": self.youtube_published_at.isoformat() if self.youtube_published_at else None,
            "tiktokUrl": self.tiktok_url,
            "tiktokId": self.tiktok_id,
            "tiktokPublishedAt": self.tiktok_published_at.isoformat() if self.tiktok_published_at else None,
            "instagramUrl": self.instagram_url,
            "instagramId": self.instagram_id,
            "instagramPublishedAt": self.instagram_published_at.isoformat() if self.instagram_published_at else None,
            "scheduledFor": self.scheduled_for.isoformat() if self.scheduled_for else None,
            "views": self.views,
            "likes": self.likes,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
