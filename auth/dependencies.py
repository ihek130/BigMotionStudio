"""
FastAPI Dependencies - Authentication and authorization dependencies
"""

from typing import Optional, List
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from database import get_db, User
from .security import verify_token

# HTTP Bearer token scheme
security = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[User]:
    """
    Get current authenticated user from JWT token.
    Returns None if no token provided (for optional auth).
    
    Usage:
        @app.get("/profile")
        async def profile(user: User = Depends(get_current_user)):
            ...
    """
    if credentials is None:
        return None
    
    token = credentials.credentials
    payload = verify_token(token, token_type="access")
    
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload"
        )
    
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user


async def get_current_active_user(
    user: User = Depends(get_current_user)
) -> User:
    """
    Get current user and require authentication.
    Raises 401 if not authenticated.
    
    Usage:
        @app.post("/create-series")
        async def create_series(user: User = Depends(get_current_active_user)):
            ...
    """
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return user


def require_verified_email(user: User = Depends(get_current_active_user)) -> User:
    """
    Require user to have verified email.
    
    Usage:
        @app.post("/create-series")
        async def create_series(user: User = Depends(require_verified_email)):
            ...
    """
    if not user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Please check your inbox."
        )
    
    return user


def require_plan(allowed_plans: List[str]):
    """
    Factory function to create dependency that requires specific plans.
    
    Usage:
        @app.post("/generate-video")
        async def generate_video(user: User = Depends(require_plan(["launch", "grow", "scale"]))):
            ...
    """
    async def plan_checker(user: User = Depends(get_current_active_user)) -> User:
        if user.plan not in allowed_plans:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"This feature requires one of these plans: {', '.join(allowed_plans)}. "
                       f"Your current plan: {user.plan}",
                headers={"X-Upgrade-Required": "true"}
            )
        return user
    
    return plan_checker


def require_can_generate_video(user: User = Depends(get_current_active_user)) -> User:
    """
    Check if user can generate another video (within limits).
    
    Usage:
        @app.post("/generate-video")
        async def generate_video(user: User = Depends(require_can_generate_video)):
            ...
    """
    if not user.can_generate_video:
        limits = user.plan_limits
        
        if user.plan == "free":
            detail = (
                f"You've reached your free tier limit of {limits['videos_total']} videos. "
                "Upgrade to continue creating content!"
            )
        else:
            detail = (
                f"You've reached your monthly limit of {limits['videos_per_month']} videos. "
                "Your limit resets on the 1st of next month, or upgrade for more."
            )
        
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
            headers={"X-Upgrade-Required": "true", "X-Videos-Remaining": "0"}
        )
    
    return user


def require_platform_connected(platform: str):
    """
    Factory function to require a specific platform connection.
    
    Usage:
        @app.post("/upload-youtube")
        async def upload(user: User = Depends(require_platform_connected("youtube"))):
            ...
    """
    async def platform_checker(
        user: User = Depends(get_current_active_user),
        db: Session = Depends(get_db)
    ) -> User:
        from database import PlatformConnection
        
        connection = db.query(PlatformConnection).filter(
            PlatformConnection.user_id == user.id,
            PlatformConnection.platform == platform,
            PlatformConnection.status == "active"
        ).first()
        
        if connection is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Please connect your {platform.title()} account first.",
                headers={"X-Connect-Platform": platform}
            )
        
        return user
    
    return platform_checker
