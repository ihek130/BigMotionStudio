"""
Series Model - Video series configuration
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from ..connection import Base


class Series(Base):
    """
    Video series configuration.
    Each series generates videos on a schedule with consistent settings.
    """
    __tablename__ = "series"
    
    # Primary key (using String for SQLite compatibility)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Owner
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Series identity
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    
    # Content settings
    niche = Column(String(100), nullable=False)  # scary-stories, history, etc.
    niche_format = Column(String(50), default="storytelling")  # storytelling, 5-things
    
    # Visual settings
    visual_style = Column(String(100), default="realistic")
    
    # Audio settings
    voice_id = Column(String(100), default="bm_lewis")
    music_track = Column(String(100), default="ambient")
    
    # Caption settings
    caption_style = Column(String(100), default="modern-bold")
    
    # Video settings
    video_duration = Column(Integer, default=60)  # 30, 45, 60 seconds
    
    # Posting schedule
    posting_times = Column(JSON, default=["09:00"])  # Array of times
    timezone = Column(String(50), default="UTC")  # User's timezone (e.g., "Asia/Karachi")
    
    # Target platforms
    platforms = Column(JSON, default=["youtube"])  # youtube, tiktok, instagram
    
    # Status
    status = Column(String(50), default="active")  # active, paused, deleted
    
    # Stats
    videos_generated = Column(Integer, default=0)
    videos_published = Column(Integer, default=0)
    total_views = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_video_at = Column(DateTime, nullable=True)
    next_video_at = Column(DateTime, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="series")
    videos = relationship("Video", back_populates="series", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Series {self.name}>"
    
    def to_dict(self):
        """Convert to dictionary for API responses"""
        return {
            "id": str(self.id),
            "name": self.name,
            "description": self.description,
            "niche": self.niche,
            "nicheFormat": self.niche_format,
            "visualStyle": self.visual_style,
            "voiceId": self.voice_id,
            "musicTrack": self.music_track,
            "captionStyle": self.caption_style,
            "videoDuration": self.video_duration,
            "postingTimes": self.posting_times,
            "timezone": self.timezone or "UTC",
            "platforms": self.platforms,
            "status": self.status,
            "videosGenerated": self.videos_generated,
            "videosPublished": self.videos_published,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
        }
