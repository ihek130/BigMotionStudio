"""
Auth Module - Authentication and Authorization for ReelFlow SaaS
"""

from .security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    verify_token,
    generate_verification_token,
    generate_reset_token
)
from .dependencies import (
    get_current_user,
    get_current_active_user,
    require_plan,
    require_verified_email
)

__all__ = [
    # Security
    'hash_password',
    'verify_password',
    'create_access_token',
    'create_refresh_token',
    'verify_token',
    'generate_verification_token',
    'generate_reset_token',
    
    # Dependencies
    'get_current_user',
    'get_current_active_user',
    'require_plan',
    'require_verified_email'
]
