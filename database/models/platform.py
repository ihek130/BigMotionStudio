"""
Platform Connection Model - OAuth tokens for YouTube, TikTok, Instagram
"""

import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Text, ForeignKey, Boolean
from sqlalchemy.orm import relationship

from ..connection import Base


class PlatformConnection(Base):
    """
    OAuth connection to a social platform.
    Stores encrypted tokens for posting videos.
    """
    __tablename__ = "platform_connections"
    
    # Primary key (using String for SQLite compatibility)
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Owner
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # Platform identification
    platform = Column(String(50), nullable=False)  # youtube, tiktok, instagram
    
    # Account info
    platform_user_id = Column(String(255), nullable=True)  # Platform's user ID
    platform_username = Column(String(255), nullable=True)  # Display name
    channel_name = Column(String(255), nullable=True)  # Channel/page name
    channel_id = Column(String(255), nullable=True)  # Channel/page ID
    profile_image_url = Column(Text, nullable=True)
    
    # OAuth tokens (should be encrypted in production)
    access_token = Column(Text, nullable=False)
    refresh_token = Column(Text, nullable=True)
    token_type = Column(String(50), default="Bearer")
    scope = Column(Text, nullable=True)  # OAuth scopes granted
    
    # Token expiration
    access_token_expires_at = Column(DateTime, nullable=True)
    refresh_token_expires_at = Column(DateTime, nullable=True)
    
    # Connection status
    status = Column(String(50), default="active")  # active, expired, revoked, error
    last_used_at = Column(DateTime, nullable=True)
    last_error = Column(Text, nullable=True)
    
    # Platform-specific data
    # YouTube
    youtube_channel_id = Column(String(100), nullable=True)
    youtube_uploads_playlist_id = Column(String(100), nullable=True)
    
    # TikTok
    tiktok_open_id = Column(String(255), nullable=True)
    tiktok_union_id = Column(String(255), nullable=True)
    
    # Instagram / Meta
    instagram_user_id = Column(String(100), nullable=True)
    facebook_page_id = Column(String(100), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="platform_connections")
    
    def __repr__(self):
        return f"<PlatformConnection {self.platform} - {self.platform_username}>"
    
    @property
    def is_expired(self):
        """Check if access token is expired"""
        if not self.access_token_expires_at:
            return False
        return datetime.utcnow() > self.access_token_expires_at
    
    @property
    def needs_refresh(self):
        """Check if token should be refreshed (within 5 min of expiry)"""
        if not self.access_token_expires_at:
            return False
        from datetime import timedelta
        buffer = timedelta(minutes=5)
        return datetime.utcnow() > (self.access_token_expires_at - buffer)
    
    def to_dict(self):
        """Convert to dictionary for API responses (NO TOKENS!)"""
        return {
            "id": str(self.id),
            "platform": self.platform,
            "username": self.platform_username,
            "channelName": self.channel_name,
            "profileImageUrl": self.profile_image_url,
            "status": self.status,
            "isExpired": self.is_expired,
            "createdAt": self.created_at.isoformat() if self.created_at else None,
            "lastUsedAt": self.last_used_at.isoformat() if self.last_used_at else None,
        }
