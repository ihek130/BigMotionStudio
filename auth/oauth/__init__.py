"""
Platform OAuth Module - YouTube, TikTok, Instagram OAuth flows
"""

from .youtube import router as youtube_router
from .tiktok import router as tiktok_router
from .instagram import router as instagram_router

__all__ = [
    'youtube_router',
    'tiktok_router', 
    'instagram_router'
]
