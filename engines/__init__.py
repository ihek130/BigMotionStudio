"""Engine module initialization"""

# ============================================
# SHARED ENGINES (Used by SaaS)
# ============================================
from .soundtrack_engine import SoundtrackEngine
from .thumbnail_engine import ThumbnailEngine
from .seo_engine import SEOEngine

# ============================================
# SAAS ENGINES (Scene-Based Generation)
# ============================================
from .models import (
    UserSeriesSettings,
    Character,
    Scene,
    ScriptData,
    GeneratedVideo,
    VISUAL_STYLE_PROMPTS,
    NICHE_PROMPTS,
    CAPTION_STYLE_CONFIG
)
from .scene_script_engine import SceneScriptEngine
from .scene_image_engine import SceneImageEngine
from .audixa_tts_engine import AudixaTTSEngine
from .scene_video_assembly_engine import SceneVideoAssemblyEngine
from .caption_engine import CaptionEngine, ASS_STYLE_CONFIG

# ============================================
# PLATFORM UPLOAD ENGINES (Multi-Tenant SaaS)
# ============================================
from .youtube_upload_engine import YouTubeUploadEngine
from .instagram_upload_engine import InstagramUploadEngine
from .tiktok_upload_engine import TikTokUploadEngine
from .platform_upload_orchestrator import PlatformUploadOrchestrator

__all__ = [
    # Shared Engines
    'SoundtrackEngine',
    'ThumbnailEngine',
    'SEOEngine',
    
    # SaaS Engines
    'UserSeriesSettings',
    'Character',
    'Scene',
    'ScriptData',
    'GeneratedVideo',
    'VISUAL_STYLE_PROMPTS',
    'NICHE_PROMPTS',
    'CAPTION_STYLE_CONFIG',
    'ASS_STYLE_CONFIG',
    'SceneScriptEngine',
    'SceneImageEngine',
    'AudixaTTSEngine',
    'SceneVideoAssemblyEngine',
    'CaptionEngine',
    
    # Platform Upload Engines
    'YouTubeUploadEngine',
    'InstagramUploadEngine',
    'TikTokUploadEngine',
    'PlatformUploadOrchestrator',
]
