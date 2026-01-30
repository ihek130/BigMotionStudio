"""
YouTube OAuth - Connect YouTube channels for video posting
"""

import os
import json
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from database import get_db, User, PlatformConnection
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/oauth/youtube", tags=["YouTube OAuth"])

# =============================================================================
# Configuration
# =============================================================================

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# OAuth scopes for YouTube
YOUTUBE_SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.readonly"
]

# Temporary state storage (use Redis in production)
oauth_states = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class YouTubeConnectResponse(BaseModel):
    """OAuth authorization URL response"""
    auth_url: str


class YouTubeChannelResponse(BaseModel):
    """Connected YouTube channel info"""
    id: str
    platform: str = "youtube"
    channel_id: str
    channel_name: str
    profile_image_url: Optional[str]
    subscriber_count: Optional[int]
    status: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# =============================================================================
# OAuth Endpoints
# =============================================================================

@router.get("/connect", response_model=YouTubeConnectResponse)
async def youtube_connect(
    user: User = Depends(get_current_active_user)
):
    """
    Get YouTube OAuth authorization URL.
    User should be redirected to this URL to authorize.
    """
    if not YOUTUBE_CLIENT_ID or not YOUTUBE_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="YouTube OAuth not configured"
        )
    
    # Create OAuth flow
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": YOUTUBE_CLIENT_ID,
                "client_secret": YOUTUBE_CLIENT_SECRET,
                "redirect_uris": [f"{BACKEND_URL}/api/oauth/youtube/callback"],
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token"
            }
        },
        scopes=YOUTUBE_SCOPES
    )
    
    flow.redirect_uri = f"{BACKEND_URL}/api/oauth/youtube/callback"
    
    # Generate authorization URL with state
    import secrets
    state = secrets.token_urlsafe(32)
    
    authorization_url, _ = flow.authorization_url(
        access_type="offline",  # Get refresh token
        include_granted_scopes="true",
        state=state,
        prompt="consent"  # Force consent to get refresh token
    )
    
    # Store state for verification
    oauth_states[state] = {
        "user_id": str(user.id),
        "created_at": datetime.utcnow().isoformat(),
        "return_to": "create_series"  # Mark that this is from series creation
    }
    
    return YouTubeConnectResponse(auth_url=authorization_url)


@router.get("/callback")
async def youtube_callback(
    code: str,
    state: str,
    db: Session = Depends(get_db)
):
    """
    Handle YouTube OAuth callback.
    Exchanges code for tokens and stores connection.
    """
    # Verify state
    if state not in oauth_states:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=invalid_state"
        )
    
    state_data = oauth_states.pop(state)
    user_id = state_data["user_id"]
    
    # Get user
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=user_not_found"
        )
    
    try:
        # Create OAuth flow
        flow = Flow.from_client_config(
            {
                "web": {
                    "client_id": YOUTUBE_CLIENT_ID,
                    "client_secret": YOUTUBE_CLIENT_SECRET,
                    "redirect_uris": [f"{BACKEND_URL}/api/oauth/youtube/callback"],
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token"
                }
            },
            scopes=YOUTUBE_SCOPES
        )
        flow.redirect_uri = f"{BACKEND_URL}/api/oauth/youtube/callback"
        
        # Exchange code for tokens
        flow.fetch_token(code=code)
        credentials = flow.credentials
        
        # Get channel info
        youtube = build("youtube", "v3", credentials=credentials)
        channels_response = youtube.channels().list(
            part="snippet,statistics",
            mine=True
        ).execute()
        
        if not channels_response.get("items"):
            return RedirectResponse(
                url=f"{FRONTEND_URL}/dashboard/settings?error=no_channel"
            )
        
        channel = channels_response["items"][0]
        channel_id = channel["id"]
        channel_name = channel["snippet"]["title"]
        profile_image = channel["snippet"]["thumbnails"]["default"]["url"]
        
        # Check if connection already exists
        existing = db.query(PlatformConnection).filter(
            PlatformConnection.user_id == user_id,
            PlatformConnection.platform == "youtube",
            PlatformConnection.youtube_channel_id == channel_id
        ).first()
        
        if existing:
            # Update existing connection
            existing.access_token = credentials.token
            existing.refresh_token = credentials.refresh_token or existing.refresh_token
            existing.access_token_expires_at = credentials.expiry
            existing.status = "active"
            existing.channel_name = channel_name
            existing.profile_image_url = profile_image
        else:
            # Create new connection
            connection = PlatformConnection(
                user_id=user_id,
                platform="youtube",
                platform_user_id=channel_id,
                platform_username=channel_name,
                channel_name=channel_name,
                channel_id=channel_id,
                profile_image_url=profile_image,
                access_token=credentials.token,
                refresh_token=credentials.refresh_token,
                access_token_expires_at=credentials.expiry,
                youtube_channel_id=channel_id,
                status="active"
            )
            db.add(connection)
        
        db.commit()
        
        # Check if this was from series creation wizard
        return_to = state_data.get("return_to")
        if return_to == "create_series":
            return RedirectResponse(
                url=f"{FRONTEND_URL}/create/platforms?connected=youtube"
            )
        else:
            return RedirectResponse(
                url=f"{FRONTEND_URL}/dashboard/settings?success=youtube_connected"
            )
        
    except Exception as e:
        print(f"YouTube OAuth error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed"
        )


@router.delete("/disconnect/{connection_id}", response_model=MessageResponse)
async def youtube_disconnect(
    connection_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a YouTube channel.
    """
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "youtube"
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    db.delete(connection)
    db.commit()
    
    return MessageResponse(message="YouTube channel disconnected successfully")


@router.get("/channels")
async def list_youtube_channels(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List connected YouTube channels.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "youtube"
    ).all()
    
    return [conn.to_dict() for conn in connections]


# =============================================================================
# Token Refresh Helper
# =============================================================================

def refresh_youtube_token(connection: PlatformConnection, db: Session) -> bool:
    """
    Refresh YouTube access token using refresh token.
    
    Args:
        connection: PlatformConnection with YouTube tokens
        db: Database session
        
    Returns:
        True if refresh successful, False otherwise
    """
    if not connection.refresh_token:
        return False
    
    try:
        credentials = Credentials(
            token=connection.access_token,
            refresh_token=connection.refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=YOUTUBE_CLIENT_ID,
            client_secret=YOUTUBE_CLIENT_SECRET
        )
        
        if credentials.expired:
            from google.auth.transport.requests import Request
            credentials.refresh(Request())
            
            connection.access_token = credentials.token
            connection.access_token_expires_at = credentials.expiry
            connection.status = "active"
            db.commit()
        
        return True
        
    except Exception as e:
        connection.status = "expired"
        connection.last_error = str(e)
        db.commit()
        return False
