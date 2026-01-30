"""
Platform Routes - Unified endpoints for all platform connections
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db, User, PlatformConnection
from auth.dependencies import get_current_active_user

router = APIRouter(prefix="/api/platforms", tags=["Platform Connections"])


# =============================================================================
# Response Models
# =============================================================================

class PlatformConnectionResponse(BaseModel):
    """Platform connection info"""
    id: str
    platform: str
    username: str
    channel_name: Optional[str]
    profile_image_url: Optional[str]
    status: str
    connected_at: str


class AllConnectionsResponse(BaseModel):
    """All connected platforms"""
    youtube: List[PlatformConnectionResponse]
    tiktok: List[PlatformConnectionResponse]
    instagram: List[PlatformConnectionResponse]


class MessageResponse(BaseModel):
    """Generic message"""
    message: str
    success: bool = True


# =============================================================================
# Endpoints
# =============================================================================

@router.get("/connections", response_model=AllConnectionsResponse)
async def get_all_connections(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get all connected platforms for the current user.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.user_id == user.id
    ).all()
    
    result = {
        "youtube": [],
        "tiktok": [],
        "instagram": []
    }
    
    for conn in connections:
        conn_data = PlatformConnectionResponse(
            id=str(conn.id),
            platform=conn.platform,
            username=conn.platform_username or conn.channel_name or "Unknown",
            channel_name=conn.channel_name,
            profile_image_url=conn.profile_image_url,
            status=conn.status,
            connected_at=conn.created_at.isoformat()
        )
        
        if conn.platform in result:
            result[conn.platform].append(conn_data)
    
    return result


@router.delete("/disconnect/{platform}/{connection_id}", response_model=MessageResponse)
async def disconnect_platform(
    platform: str,
    connection_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect a specific platform connection.
    """
    if platform not in ["youtube", "tiktok", "instagram"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}"
        )
    
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == platform
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    db.delete(connection)
    db.commit()
    
    return MessageResponse(message=f"{platform.title()} disconnected successfully")


@router.get("/status")
async def get_platform_status(
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get connection status for all platforms.
    Returns which platforms are connected and active.
    """
    connections = db.query(PlatformConnection).filter(
        PlatformConnection.user_id == user.id
    ).all()
    
    status_map = {
        "youtube": {"connected": False, "count": 0, "active": 0},
        "tiktok": {"connected": False, "count": 0, "active": 0},
        "instagram": {"connected": False, "count": 0, "active": 0}
    }
    
    for conn in connections:
        if conn.platform in status_map:
            status_map[conn.platform]["connected"] = True
            status_map[conn.platform]["count"] += 1
            if conn.status == "active":
                status_map[conn.platform]["active"] += 1
    
    return status_map


@router.post("/refresh/{platform}/{connection_id}")
async def refresh_platform_token(
    platform: str,
    connection_id: str,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Manually refresh a platform's access token.
    """
    connection = db.query(PlatformConnection).filter(
        PlatformConnection.id == connection_id,
        PlatformConnection.user_id == user.id,
        PlatformConnection.platform == platform
    ).first()
    
    if not connection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Connection not found"
        )
    
    # Import appropriate refresh function
    success = False
    
    if platform == "youtube":
        from auth.oauth.youtube import refresh_youtube_token
        success = refresh_youtube_token(connection, db)
    elif platform == "tiktok":
        from auth.oauth.tiktok import refresh_tiktok_token
        import asyncio
        success = asyncio.get_event_loop().run_until_complete(
            refresh_tiktok_token(connection, db)
        )
    elif platform == "instagram":
        from auth.oauth.instagram import refresh_instagram_token
        import asyncio
        success = asyncio.get_event_loop().run_until_complete(
            refresh_instagram_token(connection, db)
        )
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid platform: {platform}"
        )
    
    if success:
        return MessageResponse(message="Token refreshed successfully")
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to refresh token. Please reconnect the platform."
        )
