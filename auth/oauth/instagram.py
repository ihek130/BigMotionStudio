"""
Instagram OAuth - Connect Instagram accounts for Reels posting
Uses Meta (Facebook) Graph API for Instagram Business/Creator accounts
"""

import os
import secrets
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from database import get_db, User, PlatformConnection
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/oauth/instagram", tags=["Instagram OAuth"])

# =============================================================================
# Configuration
# =============================================================================

META_APP_ID = os.getenv("META_APP_ID")
META_APP_SECRET = os.getenv("META_APP_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# Meta OAuth URLs
META_AUTH_URL = "https://www.facebook.com/v18.0/dialog/oauth"
META_TOKEN_URL = "https://graph.facebook.com/v18.0/oauth/access_token"
META_GRAPH_URL = "https://graph.facebook.com/v18.0"

# OAuth scopes for Instagram Business
INSTAGRAM_SCOPES = [
    "instagram_basic",
    "instagram_content_publish",
    "pages_show_list",
    "pages_read_engagement",
    "business_management"
]

# Temporary state storage (use Redis in production)
oauth_states = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class InstagramConnectResponse(BaseModel):
    """OAuth authorization URL response"""
    auth_url: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# =============================================================================
# OAuth Endpoints
# =============================================================================

@router.get("/connect", response_model=InstagramConnectResponse)
async def instagram_connect(
    user: User = Depends(get_current_active_user)
):
    """
    Get Instagram OAuth authorization URL.
    Uses Facebook OAuth to access Instagram Business/Creator accounts.
    """
    if not META_APP_ID or not META_APP_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Instagram OAuth not configured. Please set META_APP_ID and META_APP_SECRET."
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Store state for verification
    oauth_states[state] = {
        "user_id": str(user.id),
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Build authorization URL
    redirect_uri = f"{BACKEND_URL}/api/oauth/instagram/callback"
    scope = ",".join(INSTAGRAM_SCOPES)
    
    auth_url = (
        f"{META_AUTH_URL}"
        f"?client_id={META_APP_ID}"
        f"&redirect_uri={redirect_uri}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&state={state}"
    )
    
    return InstagramConnectResponse(auth_url=auth_url)


@router.get("/callback")
async def instagram_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle Instagram/Meta OAuth callback.
    Exchanges code for tokens, gets Instagram Business account, stores connection.
    """
    # Handle OAuth errors
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=instagram_{error}"
        )
    
    if not code or not state:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=missing_params"
        )
    
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
        async with httpx.AsyncClient() as client:
            redirect_uri = f"{BACKEND_URL}/api/oauth/instagram/callback"
            
            # Exchange code for short-lived token
            token_response = await client.get(
                META_TOKEN_URL,
                params={
                    "client_id": META_APP_ID,
                    "client_secret": META_APP_SECRET,
                    "redirect_uri": redirect_uri,
                    "code": code
                }
            )
            
            token_data = token_response.json()
            
            if "error" in token_data:
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/dashboard/settings?error=token_exchange_failed"
                )
            
            short_token = token_data["access_token"]
            
            # Exchange for long-lived token
            long_token_response = await client.get(
                META_TOKEN_URL,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": META_APP_ID,
                    "client_secret": META_APP_SECRET,
                    "fb_exchange_token": short_token
                }
            )
            
            long_token_data = long_token_response.json()
            access_token = long_token_data.get("access_token", short_token)
            expires_in = long_token_data.get("expires_in", 5184000)  # ~60 days
            
            # Get Facebook pages connected to user
            pages_response = await client.get(
                f"{META_GRAPH_URL}/me/accounts",
                params={"access_token": access_token}
            )
            
            pages_data = pages_response.json()
            
            if not pages_data.get("data"):
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/dashboard/settings?error=no_pages_found"
                )
            
            # Find Instagram Business account connected to a page
            instagram_account = None
            page_token = None
            
            for page in pages_data["data"]:
                page_id = page["id"]
                page_access_token = page["access_token"]
                
                # Get Instagram Business Account for this page
                ig_response = await client.get(
                    f"{META_GRAPH_URL}/{page_id}",
                    params={
                        "fields": "instagram_business_account",
                        "access_token": page_access_token
                    }
                )
                
                ig_data = ig_response.json()
                
                if "instagram_business_account" in ig_data:
                    instagram_account = ig_data["instagram_business_account"]["id"]
                    page_token = page_access_token
                    break
            
            if not instagram_account:
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/dashboard/settings?error=no_instagram_business"
                )
            
            # Get Instagram account details
            ig_details_response = await client.get(
                f"{META_GRAPH_URL}/{instagram_account}",
                params={
                    "fields": "id,username,profile_picture_url,followers_count",
                    "access_token": page_token
                }
            )
            
            ig_details = ig_details_response.json()
            
            username = ig_details.get("username", "Instagram User")
            profile_pic = ig_details.get("profile_picture_url")
        
        # Calculate token expiry
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if connection already exists
        existing = db.query(PlatformConnection).filter(
            PlatformConnection.user_id == user_id,
            PlatformConnection.platform == "instagram",
            PlatformConnection.instagram_user_id == instagram_account
        ).first()
        
        if existing:
            # Update existing connection
            existing.access_token = page_token
            existing.access_token_expires_at = expires_at
            existing.status = "active"
            existing.platform_username = username
            existing.profile_image_url = profile_pic
        else:
            # Create new connection
            connection = PlatformConnection(
                user_id=user_id,
                platform="instagram",
                platform_user_id=instagram_account,
                platform_username=username,
                channel_name=username,
                profile_image_url=profile_pic,
                access_token=page_token,
                access_token_expires_at=expires_at,
                instagram_user_id=instagram_account,
                status="active"
            )
            db.add(connection)
        
        db.commit()
        
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?success=instagram_connected"
        )
        
    except Exception as e:
        print(f"Instagram OAuth error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed"
        )


@router.delete("/disconnect/{connection_id}", response_model=MessageResponse)
async def instagram_disconnect(
    connection_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect an Instagram account.
    """
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "instagram"
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    db.delete(connection)
    db.commit()
    
    return MessageResponse(message="Instagram account disconnected successfully")


@router.get("/accounts")
async def list_instagram_accounts(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List connected Instagram accounts.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "instagram"
    ).all()
    
    return [conn.to_dict() for conn in connections]


# =============================================================================
# Token Refresh Helper
# =============================================================================

async def refresh_instagram_token(connection: PlatformConnection, db: Session) -> bool:
    """
    Refresh Instagram/Meta long-lived token.
    
    Note: Meta long-lived tokens can be refreshed before expiry
    to extend their lifetime by another 60 days.
    
    Args:
        connection: PlatformConnection with Instagram tokens
        db: Database session
        
    Returns:
        True if refresh successful, False otherwise
    """
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                META_TOKEN_URL,
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": META_APP_ID,
                    "client_secret": META_APP_SECRET,
                    "fb_exchange_token": connection.access_token
                }
            )
            
            data = response.json()
            
            if "error" in data:
                connection.status = "expired"
                connection.last_error = data.get("error", {}).get("message", "Token refresh failed")
                db.commit()
                return False
            
            connection.access_token = data["access_token"]
            connection.access_token_expires_at = datetime.utcnow() + timedelta(
                seconds=data.get("expires_in", 5184000)
            )
            connection.status = "active"
            db.commit()
            
            return True
            
    except Exception as e:
        connection.status = "error"
        connection.last_error = str(e)
        db.commit()
        return False
