"""
TikTok OAuth - Connect TikTok accounts for video posting
"""

import os
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
import httpx

from database import get_db, User, PlatformConnection
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/oauth/tiktok", tags=["TikTok OAuth"])

# =============================================================================
# Configuration
# =============================================================================

TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY")
TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")

# TikTok OAuth URLs
TIKTOK_AUTH_URL = "https://www.tiktok.com/v2/auth/authorize/"
TIKTOK_TOKEN_URL = "https://open.tiktokapis.com/v2/oauth/token/"
TIKTOK_USER_INFO_URL = "https://open.tiktokapis.com/v2/user/info/"

# OAuth scopes for TikTok
TIKTOK_SCOPES = [
    "user.info.basic",
    "user.info.profile",
    "video.upload",
    "video.publish"
]

# Temporary state storage (use Redis in production)
oauth_states = {}


# =============================================================================
# Request/Response Models
# =============================================================================

class TikTokConnectResponse(BaseModel):
    """OAuth authorization URL response"""
    auth_url: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# =============================================================================
# OAuth Endpoints
# =============================================================================

@router.get("/connect", response_model=TikTokConnectResponse)
async def tiktok_connect(
    user: User = Depends(get_current_active_user)
):
    """
    Get TikTok OAuth authorization URL.
    User should be redirected to this URL to authorize.
    """
    if not TIKTOK_CLIENT_KEY or not TIKTOK_CLIENT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="TikTok OAuth not configured. Please set TIKTOK_CLIENT_KEY and TIKTOK_CLIENT_SECRET."
        )
    
    # Generate state for CSRF protection
    state = secrets.token_urlsafe(32)
    
    # Generate code verifier for PKCE (43 characters, base64url encoded)
    code_verifier = secrets.token_urlsafe(43)
    
    # Generate code challenge from verifier (SHA256 hash, base64url encoded)
    code_challenge_bytes = hashlib.sha256(code_verifier.encode('utf-8')).digest()
    code_challenge = base64.urlsafe_b64encode(code_challenge_bytes).decode('utf-8').rstrip('=')
    
    # Store state for verification
    oauth_states[state] = {
        "user_id": str(user.id),
        "code_verifier": code_verifier,
        "created_at": datetime.utcnow().isoformat()
    }
    
    # Build authorization URL with PKCE parameters
    redirect_uri = f"{BACKEND_URL}/api/oauth/tiktok/callback"
    scope = ",".join(TIKTOK_SCOPES)
    
    auth_url = (
        f"{TIKTOK_AUTH_URL}"
        f"?client_key={TIKTOK_CLIENT_KEY}"
        f"&scope={scope}"
        f"&response_type=code"
        f"&redirect_uri={redirect_uri}"
        f"&state={state}"
        f"&code_challenge={code_challenge}"
        f"&code_challenge_method=S256"
    )
    
    return TikTokConnectResponse(auth_url=auth_url)


@router.get("/callback")
async def tiktok_callback(
    code: Optional[str] = None,
    state: Optional[str] = None,
    error: Optional[str] = None,
    error_description: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Handle TikTok OAuth callback.
    Exchanges code for tokens and stores connection.
    """
    # Handle OAuth errors
    if error:
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=tiktok_{error}"
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
            # Exchange code for tokens with PKCE code_verifier
            redirect_uri = f"{BACKEND_URL}/api/oauth/tiktok/callback"
            code_verifier = state_data["code_verifier"]
            
            token_response = await client.post(
                TIKTOK_TOKEN_URL,
                data={
                    "client_key": TIKTOK_CLIENT_KEY,
                    "client_secret": TIKTOK_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": redirect_uri,
                    "code_verifier": code_verifier
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            token_data = token_response.json()
            
            if "error" in token_data:
                return RedirectResponse(
                    url=f"{FRONTEND_URL}/dashboard/settings?error=token_exchange_failed"
                )
            
            access_token = token_data["access_token"]
            refresh_token = token_data.get("refresh_token")
            expires_in = token_data.get("expires_in", 86400)
            open_id = token_data.get("open_id")
            
            # Get user info
            user_response = await client.get(
                TIKTOK_USER_INFO_URL,
                params={"fields": "open_id,union_id,avatar_url,display_name"},
                headers={"Authorization": f"Bearer {access_token}"}
            )
            
            user_data = user_response.json().get("data", {}).get("user", {})
            
            display_name = user_data.get("display_name", "TikTok User")
            avatar_url = user_data.get("avatar_url")
            union_id = user_data.get("union_id")
        
        # Calculate token expiry
        expires_at = datetime.utcnow() + timedelta(seconds=expires_in)
        
        # Check if connection already exists
        existing = db.query(PlatformConnection).filter(
            PlatformConnection.user_id == user_id,
            PlatformConnection.platform == "tiktok",
            PlatformConnection.tiktok_open_id == open_id
        ).first()
        
        if existing:
            # Update existing connection
            existing.access_token = access_token
            existing.refresh_token = refresh_token or existing.refresh_token
            existing.access_token_expires_at = expires_at
            existing.status = "active"
            existing.platform_username = display_name
            existing.profile_image_url = avatar_url
        else:
            # Create new connection
            connection = PlatformConnection(
                user_id=user_id,
                platform="tiktok",
                platform_user_id=open_id,
                platform_username=display_name,
                channel_name=display_name,
                profile_image_url=avatar_url,
                access_token=access_token,
                refresh_token=refresh_token,
                access_token_expires_at=expires_at,
                tiktok_open_id=open_id,
                tiktok_union_id=union_id,
                status="active"
            )
            db.add(connection)
        
        db.commit()
        
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?success=tiktok_connected"
        )
        
    except Exception as e:
        print(f"TikTok OAuth error: {e}")
        return RedirectResponse(
            url=f"{FRONTEND_URL}/dashboard/settings?error=oauth_failed"
        )


@router.delete("/disconnect/{connection_id}", response_model=MessageResponse)
async def tiktok_disconnect(
    connection_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a TikTok account.
    """
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "tiktok"
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    db.delete(connection)
    db.commit()
    
    return MessageResponse(message="TikTok account disconnected successfully")


@router.get("/accounts")
async def list_tiktok_accounts(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    List connected TikTok accounts.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == "tiktok"
    ).all()
    
    return [conn.to_dict() for conn in connections]


# =============================================================================
# Token Refresh Helper
# =============================================================================

async def refresh_tiktok_token(connection: PlatformConnection, db: Session) -> bool:
    """
    Refresh TikTok access token using refresh token.
    
    Args:
        connection: PlatformConnection with TikTok tokens
        db: Database session
        
    Returns:
        True if refresh successful, False otherwise
    """
    if not connection.refresh_token:
        return False
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                TIKTOK_TOKEN_URL,
                data={
                    "client_key": TIKTOK_CLIENT_KEY,
                    "client_secret": TIKTOK_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": connection.refresh_token
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            data = response.json()
            
            if "error" in data:
                connection.status = "expired"
                connection.last_error = data.get("error_description", data["error"])
                db.commit()
                return False
            
            connection.access_token = data["access_token"]
            connection.refresh_token = data.get("refresh_token", connection.refresh_token)
            connection.access_token_expires_at = datetime.utcnow() + timedelta(
                seconds=data.get("expires_in", 86400)
            )
            connection.status = "active"
            db.commit()
            
            return True
            
    except Exception as e:
        connection.status = "error"
        connection.last_error = str(e)
        db.commit()
        return False
