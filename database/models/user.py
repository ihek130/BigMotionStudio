"""
User Model - Core user account for ReelFlow SaaS
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, Integer, DateTime, Text
from sqlalchemy.orm import relationship

from ..connection import Base


class User(Base):
    """
    User account model.
    Supports email/password auth and OAuth providers.
    """
    __tablename__ = "users"
    
    # Primary key (using String for SQLite compatibility)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Basic info
    email = Column(String(255), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=True)
    avatar_url = Column(Text, nullable=True)
    
    # Password (null for OAuth-only users)
    password_hash = Column(String(255), nullable=True)
    
    # Email verification
    email_verified = Column(Boolean, default=False)
    verification_token = Column(String(255), nullable=True)
    verification_token_expires = Column(DateTime, nullable=True)
    
    # Password reset
    reset_token = Column(String(255), nullable=True)
    reset_token_expires = Column(DateTime, nullable=True)
    
    # OAuth provider IDs (for social login)
    google_id = Column(String(255), unique=True, nullable=True)
    github_id = Column(String(255), unique=True, nullable=True)
    
    # Subscription & Billing
    plan = Column(String(50), default="free")  # free, launch, grow, scale
    is_admin = Column(Boolean, default=False)  # Admin has unlimited access
    series_purchased = Column(Integer, default=0)  # Number of series user paid for
    plan_started_at = Column(DateTime, nullable=True)
    plan_expires_at = Column(DateTime, nullable=True)
    polar_customer_id = Column(String(255), nullable=True)
    polar_subscription_id = Column(String(255), nullable=True)
    
    # Usage tracking
    videos_generated_total = Column(Integer, default=0)
    videos_generated_this_month = Column(Integer, default=0)
    last_video_at = Column(DateTime, nullable=True)
    usage_reset_at = Column(DateTime, nullable=True)  # When monthly counter resets
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login_at = Column(DateTime, nullable=True)
    
    # Relationships
    series = relationship("Series", back_populates="user", cascade="all, delete-orphan")
    platform_connections = relationship("PlatformConnection", back_populates="user", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<User {self.email}>"
    
    @property
    def plan_limits(self):
        """Get limits based on user's plan"""
        # Admin has unlimited everything (use large numbers for API compatibility)
        if self.is_admin:
            return {
                "videos_total": 999999,
                "videos_per_month": 999999,
                "series_limit": 999,
                "platforms": ["youtube", "tiktok", "instagram"],
            }
        
        limits = {
            "free": {
                "videos_total": 0,
                "videos_per_month": 0,
                "series_limit": 0,
                "platforms": [],
            },
            "launch": {
                "videos_total": 999999,
                "videos_per_month": 12 * max(1, self.series_purchased),  # 12 per series (3x/week each)
                "series_limit": max(1, self.series_purchased),
                "platforms": ["youtube", "tiktok", "instagram"],
            },
            "grow": {
                "videos_total": 999999,
                "videos_per_month": 30 * max(1, self.series_purchased),  # 30 per series (daily each)
                "series_limit": max(1, self.series_purchased),
                "platforms": ["youtube", "tiktok", "instagram"],
            },
            "scale": {
                "videos_total": 999999,
                "videos_per_month": 60 * max(1, self.series_purchased),  # 60 per series (2x/day each)
                "series_limit": max(1, self.series_purchased),
                "platforms": ["youtube", "tiktok", "instagram"],
            }
        }
        return limits.get(self.plan, limits["free"])
    
    @property
    def can_generate_video(self):
        """Check if user can generate another video"""
        # Admin has unlimited access
        if self.is_admin:
            return True
        
        limits = self.plan_limits
        
        # Monthly limit for all paid plans
        return self.videos_generated_this_month < limits["videos_per_month"]
    
    @property
    def videos_remaining(self):
        """Get remaining videos for current period"""
        # Admin has unlimited (use large number for API compatibility)
        if self.is_admin:
            return 999999
        
        limits = self.plan_limits
        return max(0, limits["videos_per_month"] - self.videos_generated_this_month)
