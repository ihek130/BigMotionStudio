"""
Data Models - Core data structures for the SaaS video generation pipeline
All generation is driven by UserSeriesSettings - NOTHING is hardcoded
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional
from enum import Enum


class Niche(str, Enum):
    """Available content niches - maps to frontend selection"""
    SCARY_STORIES = "scary-stories"
    HISTORY = "history"
    TRUE_CRIME = "true-crime"
    STOIC_MOTIVATION = "stoic-motivation"
    RANDOM_FACTS = "random-fact"
    GOOD_MORALS = "good-morals"
    PSYCHOLOGY = "psychology"


class VisualStyle(str, Enum):
    """Visual art styles for AI image generation"""
    DARK_COMIC = "dark-comic"
    ANIME = "anime"
    LEGO = "lego"
    REALISTIC = "realistic"
    CYBERPUNK = "cyberpunk"
    THREE_D_RENDER = "3d-render"
    WATERCOLOR = "watercolor"
    MINIMALIST = "minimalist"
    FANTASY = "fantasy"
    RETRO = "retro"


class VoiceId(str, Enum):
    """Available AI voices - maps to Audixa voice IDs"""
    # Male voices
    BM_LEWIS = "bm_lewis"      # Lewis - Deep & Commanding
    BM_HARRY = "bm_harry"      # Harry - Warm & Engaging
    AM_ERIC = "am_eric"        # Eric - Professional & Clear
    AM_ETHAN = "am_ethan"      # Ethan - Friendly & Energetic
    BM_OLIVER = "bm_oliver"    # Oliver - Smooth & Sophisticated
    # Female voices
    AF_ARIA = "af_aria"        # Aria - Calm & Soothing
    AF_BELLA = "af_bella"      # Bella - Bright & Enthusiastic
    AF_LILY = "af_lily"        # Lily - Gentle & Warm
    AF_ZOEY = "af_zoey"        # Zoey - Energetic & Youthful


class MusicTrack(str, Enum):
    """Background music options"""
    SUSPENSE = "suspense"
    UPBEAT = "upbeat"
    CHILL = "chill"
    EPIC = "epic"
    AMBIENT = "ambient"
    NONE = "none"


class CaptionStyle(str, Enum):
    """Caption/subtitle styles"""
    MODERN_BOLD = "modern-bold"
    NEON_GLOW = "neon-glow"
    MINIMAL_CLEAN = "minimal-clean"
    YOUTUBE_STYLE = "youtube-style"
    COLORFUL_POP = "colorful-pop"
    OUTLINED = "outlined"
    BOXED = "boxed"
    NO_CAPTIONS = "no-captions"


@dataclass
class UserSeriesSettings:
    """
    Complete user configuration for a video series.
    This is the SINGLE SOURCE OF TRUTH for all generation.
    Passed from frontend through API to all engines.
    """
    # User & Series Identity
    user_id: str
    series_id: str
    series_name: str
    series_description: str
    
    # Content Settings
    niche: str  # One of Niche enum values
    niche_format: str = "storytelling"  # 'storytelling' or '5-things'
    
    # Visual Settings
    visual_style: str = "realistic"  # One of VisualStyle enum values
    
    # Audio Settings
    voice_id: str = "bm_lewis"  # One of VoiceId enum values
    music_track: str = "ambient"  # One of MusicTrack enum values
    
    # Caption Settings
    caption_style: str = "modern-bold"  # One of CaptionStyle enum values
    
    # Video Settings
    video_duration: int = 60  # Duration in seconds (30, 60, 90, 180)
    
    # Schedule Settings
    posting_schedule: str = "daily"
    posting_time: str = "09:00"
    
    # Platform Settings
    platforms: List[str] = field(default_factory=lambda: ["youtube"])
    
    def get_word_count_target(self) -> tuple:
        """Calculate target word count based on duration.
        
        Uses ~2.8 words/sec to ensure voiceover fills the target duration
        even with slower TTS speeds (0.85-0.95x). Slightly over-generating
        is better than under-generating — assembly enforces exact duration.
        """
        base = int(self.video_duration * 2.8)
        return (int(base * 0.9), int(base * 1.1))
    
    def get_scene_count_range(self) -> tuple:
        """Calculate expected number of scenes (3-5 seconds per scene)"""
        min_scenes = self.video_duration // 5
        max_scenes = self.video_duration // 3
        return (min_scenes, max_scenes)


@dataclass
class Character:
    """Character definition for consistency across scenes"""
    name: str
    description: str  # Detailed visual description for AI
    role: str  # 'protagonist', 'antagonist', 'narrator', etc.
    
    # For consistent AI generation
    age_range: str = ""  # e.g., "30s", "elderly"
    gender: str = ""
    clothing: str = ""  # Specific clothing for consistency
    distinctive_features: str = ""  # Beard, glasses, scars, etc.


@dataclass 
class Scene:
    """A single scene in the video (3-5 seconds)"""
    scene_number: int
    duration: float  # Duration in seconds
    
    # Script content
    narration: str  # What is spoken during this scene
    
    # Visual description for AI image generation
    visual_description: str
    characters_in_scene: List[str]  # Character names present
    camera_angle: str  # e.g., "close-up", "medium shot", "wide shot"
    mood: str  # e.g., "suspenseful", "hopeful", "dark"
    
    # Generated content (filled during processing)
    image_path: Optional[str] = None
    cropped_image_path: Optional[str] = None  # After 9:16 crop
    start_time: Optional[float] = None  # Timestamp in final video
    end_time: Optional[float] = None


@dataclass
class ScriptData:
    """Complete script with scene segmentation"""
    # Metadata
    topic: str
    title: str
    
    # Full script
    full_script: str
    word_count: int
    estimated_duration: float
    
    # Characters for consistency
    characters: List[Character]
    
    # Scene breakdown
    scenes: List[Scene]
    
    # Thumbnail hook
    hook_text: str  # 2-3 word thumbnail text


@dataclass
class GeneratedVideo:
    """Final generated video output"""
    project_id: str
    user_settings: UserSeriesSettings
    
    # Generated files
    video_path: str
    thumbnail_path: str
    
    # Metadata for upload
    title: str
    description: str
    tags: List[str]
    hashtags: List[str]
    
    # Metrics
    duration_seconds: float
    scene_count: int
    generation_time_seconds: float


# Style prompt mappings for AI image generation
VISUAL_STYLE_PROMPTS = {
    "dark-comic": "dark noir comic book style, dramatic shadows, high contrast, graphic novel aesthetic, bold ink lines, moody atmosphere",
    "anime": "Japanese anime style, vibrant colors, expressive eyes, clean line art, dynamic poses, manga-inspired",
    "lego": "LEGO minifigure style, plastic brick-built characters, colorful blocks, playful 3D render, toy aesthetic",
    "realistic": "photorealistic, hyperrealistic, natural lighting, detailed textures, cinematic photography, 8K quality",
    "cyberpunk": "cyberpunk aesthetic, neon lights, futuristic cityscape, rain-soaked streets, holographic elements, sci-fi",
    "3d-render": "clean 3D render, Pixar-style, smooth surfaces, professional CGI, ambient occlusion, studio lighting",
    "watercolor": "watercolor painting style, soft edges, color bleeding, artistic brush strokes, dreamy atmosphere",
    "minimalist": "minimalist vector art, simple shapes, flat design, limited color palette, clean composition",
    "fantasy": "epic fantasy art, magical atmosphere, ethereal lighting, detailed fantasy illustration, otherworldly",
    "retro": "80s/90s retro aesthetic, synthwave colors, VHS grain, vintage design, nostalgic vibes, neon pink and blue",
}

# Niche-specific content guidance
NICHE_PROMPTS = {
    "scary-stories": {
        "tone": "suspenseful, eerie, mysterious, unsettling",
        "setting_examples": "dark forests, abandoned buildings, foggy streets, dimly lit rooms",
        "character_types": "mysterious stranger, frightened protagonist, supernatural entity",
        "mood_palette": "dark, shadowy, blue-black tones, occasional red accents",
    },
    "history": {
        "tone": "educational, dramatic, reverent, epic",
        "setting_examples": "ancient ruins, battlefields, royal courts, historical landmarks",
        "character_types": "historical figures, soldiers, scholars, royalty",
        "mood_palette": "sepia tones, warm browns, aged textures, classical lighting",
    },
    "true-crime": {
        "tone": "investigative, tense, documentary, serious",
        "setting_examples": "crime scenes, courtrooms, police stations, suburban neighborhoods",
        "character_types": "detective, suspect, victim, witness, journalist",
        "mood_palette": "desaturated colors, harsh lighting, noir shadows, newspaper aesthetic",
    },
    "stoic-motivation": {
        "tone": "wise, calm, profound, empowering",
        "setting_examples": "mountain peaks, ancient temples, sunrise/sunset, classical architecture",
        "character_types": "philosopher, mentor, warrior, thinker",
        "mood_palette": "golden hour lighting, marble textures, classical statues, warm tones",
    },
    "random-fact": {
        "tone": "curious, surprising, educational, engaging",
        "setting_examples": "laboratories, nature scenes, space, underwater, cities",
        "character_types": "scientist, explorer, narrator, various subjects",
        "mood_palette": "bright, colorful, high contrast, attention-grabbing",
    },
    "good-morals": {
        "tone": "heartwarming, inspiring, thoughtful, uplifting",
        "setting_examples": "family homes, parks, schools, community gatherings",
        "character_types": "kind stranger, wise elder, child learning, helpful neighbor",
        "mood_palette": "warm, soft lighting, pastel accents, welcoming atmosphere",
    },
    "psychology": {
        "tone": "analytical, intriguing, thought-provoking, scientific",
        "setting_examples": "brain imagery, therapy offices, abstract mindscapes, laboratories",
        "character_types": "psychologist, patient, the mind personified, ordinary people",
        "mood_palette": "clean clinical whites, neural blues, gradient backgrounds, modern",
    },
}

# Music track mappings to actual file paths
MUSIC_TRACK_FILES = {
    "dark-suspense": "assets/music/dark-tension-mystery-ambient-electronic-373332.mp3",
    "upbeat-energy": "assets/music/trailer-rising-tension-heartbeat-amp-clocks-400971.mp3",
    "chill-vibes": "assets/music/suspenseful-ambient-soundscape-360821.mp3",
    "epic-adventure": "assets/music/terrifying-building-atmosphere-pulsing-noise-amp-orchestra-400974.mp3",
    "ambient-space": "assets/music/ambient-space-arpeggio-350710.mp3",
    "thriller-tension": "assets/music/building-thriller-tension-amp-clocks-400973.mp3",
    "horror-ambience": "assets/music/pulse-of-terror-intense-horror-ambience-360839.mp3",
    "blood-woodlands": "assets/music/shadow-of-the-blood-thirsty-woodlands-250736.mp3",
    # Legacy mappings for backward compatibility
    "suspense": "assets/music/dark-tension-mystery-ambient-electronic-373332.mp3",
    "upbeat": "assets/music/trailer-rising-tension-heartbeat-amp-clocks-400971.mp3",
    "chill": "assets/music/suspenseful-ambient-soundscape-360821.mp3",
    "epic": "assets/music/terrifying-building-atmosphere-pulsing-noise-amp-orchestra-400974.mp3",
    "ambient": "assets/music/ambient-space-arpeggio-350710.mp3",
    "none": None,
}

# Caption style configurations
CAPTION_STYLE_CONFIG = {
    "modern-bold": {
        "font": "Arial-Bold",
        "font_size": 72,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 4,
        "animation": "word-by-word",
        "position": "center",
    },
    "neon-glow": {
        "font": "Arial-Bold",
        "font_size": 64,
        "color": "#00FFFF",
        "stroke_color": "#FF00FF",
        "stroke_width": 2,
        "animation": "glow-pulse",
        "position": "center",
        "glow": True,
    },
    "minimal-clean": {
        "font": "Arial",
        "font_size": 56,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 2,
        "animation": "fade",
        "position": "center",
    },
    "youtube-style": {
        "font": "Arial-Bold",
        "font_size": 60,
        "color": "white",
        "bg_color": "black",
        "bg_opacity": 0.8,
        "animation": "karaoke",
        "position": "center",
    },
    "colorful-pop": {
        "font": "Arial-Black",
        "font_size": 68,
        "color": "gradient",
        "gradient_colors": ["#FF6B6B", "#9B59B6", "#3498DB"],
        "stroke_color": "black",
        "stroke_width": 3,
        "animation": "bounce",
        "position": "center",
    },
    "outlined": {
        "font": "Arial-Bold",
        "font_size": 70,
        "color": "white",
        "stroke_color": "black",
        "stroke_width": 6,
        "animation": "slide",
        "position": "center",
    },
    "boxed": {
        "font": "Arial-Bold",
        "font_size": 54,
        "color": "white",
        "bg_color": "#000000",
        "bg_opacity": 0.9,
        "padding": 12,
        "animation": "box-slide",
        "position": "center",
    },
    "no-captions": {
        "enabled": False,
    },
}
