"""
Auth Routes - User authentication API endpoints
"""

import os
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from database import get_db, User
from auth.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_verification_token,
    generate_reset_token,
    get_verification_expiry,
    get_reset_expiry
)
from auth.dependencies import get_current_user, get_current_active_user
from auth.email import send_reset_email, send_verification_email

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


# =============================================================================
# Request/Response Models
# =============================================================================

class SignupRequest(BaseModel):
    """User registration request"""
    email: EmailStr
    password: str
    name: Optional[str] = None


class LoginRequest(BaseModel):
    """User login request"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """JWT token response"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds


class UserResponse(BaseModel):
    """User profile response"""
    id: str
    email: str
    name: Optional[str]
    avatar_url: Optional[str]
    plan: str
    series_purchased: int  # Number of series user has paid for
    is_admin: bool = False
    is_verified: bool = False
    email_verified: bool
    videos_remaining: int
    videos_generated_total: int
    videos_generated_this_month: int = 0
    total_videos_generated: int = 0
    plan_limits: dict
    created_at: str

    class Config:
        from_attributes = True


class LoginResponse(BaseModel):
    """Login response with tokens and user data"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user: UserResponse


class ForgotPasswordRequest(BaseModel):
    """Forgot password request"""
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    """Reset password request"""
    token: str
    new_password: str


class RefreshTokenRequest(BaseModel):
    """Refresh token request"""
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    """Change password request"""
    current_password: str
    new_password: str


class MessageResponse(BaseModel):
    """Generic message response"""
    message: str
    success: bool = True


# =============================================================================
# Auth Endpoints
# =============================================================================

@router.post("/signup", response_model=LoginResponse)
async def signup(
    request: SignupRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Register a new user account.
    
    - Creates user with hashed password
    - Sends verification email (background)
    - Returns JWT tokens with user data
    """
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == request.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists"
        )
    
    # Validate password strength
    if len(request.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Create user (free plan by default - must pay to upgrade)
    user = User(
        email=request.email.lower(),
        password_hash=hash_password(request.password),
        name=request.name,
        plan="free",
        series_purchased=0,
        verification_token=generate_verification_token(),
        verification_token_expires=get_verification_expiry(),
        email_verified=False  # Will be True after email verification
    )
    
    db.add(user)
    db.commit()
    db.refresh(user)
    
    # Send verification email (background task)
    # background_tasks.add_task(send_verification_email, user.email, user.verification_token)
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Build user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        plan=user.plan,
        series_purchased=user.series_purchased,
        is_admin=user.is_admin,
        is_verified=user.email_verified,
        email_verified=user.email_verified,
        videos_remaining=user.videos_remaining,
        videos_generated_total=user.videos_generated_total,
        videos_generated_this_month=user.videos_generated_this_month,
        total_videos_generated=user.videos_generated_total,
        plan_limits=user.plan_limits,
        created_at=user.created_at.isoformat()
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24,  # 24 hours
        user=user_response
    )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate user and return JWT tokens with user data.
    """
    # Find user
    user = db.query(User).filter(User.email == request.email.lower()).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Check password
    if not user.password_hash or not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password"
        )
    
    # Update last login
    user.last_login_at = datetime.utcnow()
    db.commit()
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    # Build user response
    user_response = UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        plan=user.plan,
        series_purchased=user.series_purchased,
        is_admin=user.is_admin,
        is_verified=user.email_verified,
        email_verified=user.email_verified,
        videos_remaining=user.videos_remaining,
        videos_generated_total=user.videos_generated_total,
        videos_generated_this_month=user.videos_generated_this_month,
        total_videos_generated=user.videos_generated_total,
        plan_limits=user.plan_limits,
        created_at=user.created_at.isoformat()
    )
    
    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24,  # 24 hours
        user=user_response
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: Session = Depends(get_db)
):
    """
    Get new access token using refresh token.
    """
    payload = verify_token(request.refresh_token, token_type="refresh")
    
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token"
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    # Generate new tokens
    access_token = create_access_token({"sub": str(user.id)})
    new_refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=new_refresh_token,
        expires_in=60 * 60 * 24  # 24 hours
    )


@router.get("/me", response_model=UserResponse)
async def get_me(user: User = Depends(get_current_active_user)):
    """
    Get current authenticated user's profile.
    """
    return UserResponse(
        id=str(user.id),
        email=user.email,
        name=user.name,
        avatar_url=user.avatar_url,
        plan=user.plan,
        series_purchased=user.series_purchased,
        is_admin=user.is_admin,
        is_verified=user.email_verified,
        email_verified=user.email_verified,
        videos_remaining=user.videos_remaining,
        videos_generated_total=user.videos_generated_total,
        videos_generated_this_month=user.videos_generated_this_month,
        total_videos_generated=user.videos_generated_total,
        plan_limits=user.plan_limits,
        created_at=user.created_at.isoformat()
    )


@router.post("/forgot-password", response_model=MessageResponse)
async def forgot_password(
    request: ForgotPasswordRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """
    Request password reset email.
    Always returns success (to prevent email enumeration).
    """
    user = db.query(User).filter(User.email == request.email.lower()).first()
    
    if user and user.password_hash:  # Only for password users
        # Generate reset token
        user.reset_token = generate_reset_token()
        user.reset_token_expires = get_reset_expiry()
        db.commit()
        
        # Send reset email (background task)
        background_tasks.add_task(send_reset_email, user.email, user.reset_token)
    
    # Always return success (security: don't reveal if email exists)
    return MessageResponse(
        message="If an account exists with this email, you will receive a password reset link."
    )


@router.post("/reset-password", response_model=MessageResponse)
async def reset_password(
    request: ResetPasswordRequest,
    db: Session = Depends(get_db)
):
    """
    Reset password using reset token from email.
    """
    # Find user with valid reset token
    user = db.query(User).filter(
        User.reset_token == request.token,
        User.reset_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    user.reset_token = None
    user.reset_token_expires = None
    db.commit()
    
    return MessageResponse(message="Password has been reset successfully. You can now log in.")


@router.post("/verify-email", response_model=MessageResponse)
async def verify_email(
    token: str,
    db: Session = Depends(get_db)
):
    """
    Verify email address using token from email.
    """
    user = db.query(User).filter(
        User.verification_token == token,
        User.verification_token_expires > datetime.utcnow()
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )
    
    user.email_verified = True
    user.verification_token = None
    user.verification_token_expires = None
    db.commit()
    
    return MessageResponse(message="Email verified successfully!")


@router.post("/change-password", response_model=MessageResponse)
async def change_password(
    request: ChangePasswordRequest,
    user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user.
    """
    # Verify current password
    if not user.password_hash or not verify_password(request.current_password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters long"
        )
    
    # Update password
    user.password_hash = hash_password(request.new_password)
    db.commit()
    
    return MessageResponse(message="Password changed successfully")


@router.post("/logout", response_model=MessageResponse)
async def logout():
    """
    Logout user (client should delete tokens).
    Server-side we could blacklist tokens if needed.
    """
    # With JWT, logout is handled client-side by deleting tokens
    # For additional security, implement token blacklist in Redis
    return MessageResponse(message="Logged out successfully")


# =============================================================================
# OAuth Endpoints (Google, GitHub)
# =============================================================================

FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

class GoogleAuthRequest(BaseModel):
    """Google OAuth token request"""
    credential: str  # Google ID token


class GitHubAuthRequest(BaseModel):
    """GitHub OAuth code request"""
    code: str


@router.get("/google")
async def google_auth_redirect():
    """
    Redirect to Google OAuth consent screen.
    """
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback")
    
    if not GOOGLE_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth not configured"
        )
    
    # Build Google OAuth URL
    params = {
        "client_id": GOOGLE_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "response_type": "code",
        "scope": "openid email profile",
        "access_type": "offline",
        "prompt": "consent"
    }
    
    from urllib.parse import urlencode
    auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=auth_url)


@router.get("/google/callback")
async def google_auth_callback(
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle Google OAuth callback.
    Exchange code for tokens and create/login user.
    """
    from fastapi.responses import RedirectResponse
    import httpx
    
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={error}")
    
    if not code:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_code")
    
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
    GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
    REDIRECT_URI = os.getenv("GOOGLE_REDIRECT_URI", f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/google/callback")
    
    try:
        # Exchange code for tokens
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": GOOGLE_CLIENT_ID,
                    "client_secret": GOOGLE_CLIENT_SECRET,
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI
                }
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                return RedirectResponse(url=f"{FRONTEND_URL}/login?error={token_data.get('error_description', 'token_error')}")
            
            # Get user info
            user_response = await client.get(
                "https://www.googleapis.com/oauth2/v2/userinfo",
                headers={"Authorization": f"Bearer {token_data['access_token']}"}
            )
            user_data = user_response.json()
        
        google_id = user_data.get("id")
        email = user_data.get("email")
        name = user_data.get("name")
        avatar = user_data.get("picture")
        
        # Find or create user
        user = db.query(User).filter(User.google_id == google_id).first()
        
        if not user:
            existing_user = db.query(User).filter(User.email == email.lower()).first()
            
            if existing_user:
                existing_user.google_id = google_id
                if not existing_user.avatar_url:
                    existing_user.avatar_url = avatar
                user = existing_user
            else:
                user = User(
                    email=email.lower(),
                    name=name,
                    avatar_url=avatar,
                    google_id=google_id,
                    email_verified=True,
                    plan="free",
                    series_purchased=0
                )
                db.add(user)
        
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        # Redirect to frontend with tokens
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?access_token={access_token}&refresh_token={refresh_token}"
        )
        
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={str(e)[:50]}")


@router.get("/github")
async def github_auth_redirect():
    """
    Redirect to GitHub OAuth consent screen.
    """
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    REDIRECT_URI = os.getenv("GITHUB_REDIRECT_URI", f"{os.getenv('BACKEND_URL', 'http://localhost:8000')}/api/auth/github/callback")
    
    if not GITHUB_CLIENT_ID:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="GitHub OAuth not configured"
        )
    
    from urllib.parse import urlencode
    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": REDIRECT_URI,
        "scope": "user:email"
    }
    
    auth_url = f"https://github.com/login/oauth/authorize?{urlencode(params)}"
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=auth_url)


@router.get("/github/callback")
async def github_auth_callback(
    code: str = None,
    error: str = None,
    db: Session = Depends(get_db)
):
    """
    Handle GitHub OAuth callback.
    """
    from fastapi.responses import RedirectResponse
    import httpx
    
    if error:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={error}")
    
    if not code:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error=no_code")
    
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    
    try:
        async with httpx.AsyncClient() as client:
            # Exchange code for token
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                return RedirectResponse(url=f"{FRONTEND_URL}/login?error={token_data.get('error')}")
            
            github_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"}
            )
            user_data = user_response.json()
            
            # Get email
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={"Authorization": f"Bearer {github_token}", "Accept": "application/json"}
            )
            emails_data = emails_response.json()
            primary_email = next((e["email"] for e in emails_data if e["primary"]), user_data.get("email"))
        
        github_id = str(user_data["id"])
        name = user_data.get("name") or user_data.get("login")
        avatar = user_data.get("avatar_url")
        
        # Find or create user
        user = db.query(User).filter(User.github_id == github_id).first()
        
        if not user:
            existing_user = db.query(User).filter(User.email == primary_email.lower()).first()
            
            if existing_user:
                existing_user.github_id = github_id
                if not existing_user.avatar_url:
                    existing_user.avatar_url = avatar
                user = existing_user
            else:
                user = User(
                    email=primary_email.lower(),
                    name=name,
                    avatar_url=avatar,
                    github_id=github_id,
                    email_verified=True,
                    plan="free",
                    series_purchased=0
                )
                db.add(user)
        
        user.last_login_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        
        # Generate tokens
        access_token = create_access_token({"sub": str(user.id)})
        refresh_token = create_refresh_token({"sub": str(user.id)})
        
        return RedirectResponse(
            url=f"{FRONTEND_URL}/login?access_token={access_token}&refresh_token={refresh_token}"
        )
        
    except Exception as e:
        return RedirectResponse(url=f"{FRONTEND_URL}/login?error={str(e)[:50]}")


@router.post("/google/token", response_model=TokenResponse)
async def google_auth(
    request: GoogleAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with Google OAuth.
    Creates account if doesn't exist.
    """
    try:
        # Verify Google token
        from google.oauth2 import id_token
        from google.auth.transport import requests as google_requests
        
        GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
        
        idinfo = id_token.verify_oauth2_token(
            request.credential,
            google_requests.Request(),
            GOOGLE_CLIENT_ID
        )
        
        google_id = idinfo.get("sub")
        email = idinfo.get("email")
        name = idinfo.get("name")
        avatar = idinfo.get("picture")
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid Google token: {str(e)}"
        )
    
    # Find or create user
    user = db.query(User).filter(User.google_id == google_id).first()
    
    if not user:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == email.lower()).first()
        
        if existing_user:
            # Link Google to existing account
            existing_user.google_id = google_id
            if not existing_user.avatar_url:
                existing_user.avatar_url = avatar
            user = existing_user
        else:
            # Create new user
            user = User(
                email=email.lower(),
                name=name,
                avatar_url=avatar,
                google_id=google_id,
                email_verified=True,  # Google emails are pre-verified
                plan="free"
            )
            db.add(user)
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24
    )


@router.post("/github", response_model=TokenResponse)
async def github_auth(
    request: GitHubAuthRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate with GitHub OAuth.
    Creates account if doesn't exist.
    """
    import httpx
    
    GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
    GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
    
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                data={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": request.code
                },
                headers={"Accept": "application/json"}
            )
            token_data = token_response.json()
            
            if "error" in token_data:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"GitHub OAuth error: {token_data.get('error_description', token_data['error'])}"
                )
            
            github_token = token_data["access_token"]
            
            # Get user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/json"
                }
            )
            user_data = user_response.json()
            
            # Get primary email
            emails_response = await client.get(
                "https://api.github.com/user/emails",
                headers={
                    "Authorization": f"Bearer {github_token}",
                    "Accept": "application/json"
                }
            )
            emails_data = emails_response.json()
            
            primary_email = next(
                (e["email"] for e in emails_data if e["primary"]),
                user_data.get("email")
            )
            
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"GitHub authentication failed: {str(e)}"
        )
    
    github_id = str(user_data["id"])
    name = user_data.get("name") or user_data.get("login")
    avatar = user_data.get("avatar_url")
    
    # Find or create user
    user = db.query(User).filter(User.github_id == github_id).first()
    
    if not user:
        # Check if email already exists
        existing_user = db.query(User).filter(User.email == primary_email.lower()).first()
        
        if existing_user:
            # Link GitHub to existing account
            existing_user.github_id = github_id
            if not existing_user.avatar_url:
                existing_user.avatar_url = avatar
            user = existing_user
        else:
            # Create new user
            user = User(
                email=primary_email.lower(),
                name=name,
                avatar_url=avatar,
                github_id=github_id,
                email_verified=True,  # GitHub emails are verified
                plan="free"
            )
            db.add(user)
    
    user.last_login_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    
    # Generate tokens
    access_token = create_access_token({"sub": str(user.id)})
    refresh_token = create_refresh_token({"sub": str(user.id)})
    
    return TokenResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=60 * 60 * 24
    )
