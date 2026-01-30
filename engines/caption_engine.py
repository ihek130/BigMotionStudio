"""
Caption Engine - Deepgram Transcription + Dynamic ASS Subtitle Generation
Generates accurate word-timed captions with user-selected styling
"""

import os
import json
import logging
import requests
from typing import Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class WordTiming:
    """Single word with precise timing"""
    word: str
    start: float  # seconds
    end: float    # seconds
    confidence: float = 1.0


# =============================================================================
# ASS STYLE CONFIGURATIONS
# Maps frontend caption styles to ASS (Advanced SubStation Alpha) format
# =============================================================================

ASS_STYLE_CONFIG = {
    "modern-bold": {
        "fontname": "Arial",
        "fontsize": 72,
        "primary_color": "&H00FFFFFF",   # White
        "outline_color": "&H00000000",   # Black
        "back_color": "&H80000000",      # Semi-transparent black
        "bold": -1,  # -1 = true
        "outline": 4,
        "shadow": 2,
        "alignment": 2,  # Bottom center
        "margin_v": 60,
        "blur": 0,
        "animation": "pop",  # Word appears with slight scale
    },
    "neon-glow": {
        "fontname": "Arial",
        "fontsize": 68,
        "primary_color": "&H00FFFF00",   # Cyan (BGR format)
        "outline_color": "&H00FF00FF",   # Magenta
        "back_color": "&H00000000",      # Transparent
        "bold": -1,
        "outline": 3,
        "shadow": 0,
        "alignment": 5,  # Center
        "margin_v": 40,
        "blur": 15,  # Glow effect
        "animation": "glow",
    },
    "minimal-clean": {
        "fontname": "Arial",
        "fontsize": 56,
        "primary_color": "&H00FFFFFF",   # White
        "outline_color": "&H00000000",   # Black
        "back_color": "&H00000000",
        "bold": 0,
        "outline": 2,
        "shadow": 1,
        "alignment": 2,
        "margin_v": 50,
        "blur": 0,
        "animation": "fade",
    },
    "youtube-style": {
        "fontname": "Arial",
        "fontsize": 64,
        "primary_color": "&H00FFFFFF",   # White
        "outline_color": "&H00000000",   # Black  
        "back_color": "&HC8000000",      # Semi-transparent black box
        "bold": -1,
        "outline": 0,
        "shadow": 0,
        "alignment": 2,
        "margin_v": 55,
        "blur": 0,
        "border_style": 3,  # Opaque box
        "animation": "karaoke",
    },
    "colorful-pop": {
        "fontname": "Arial",
        "fontsize": 70,
        "primary_color": "&H006B6BFF",   # Coral/Red (BGR)
        "secondary_color": "&H00B659B9", # Purple (for karaoke)
        "outline_color": "&H00000000",   # Black
        "back_color": "&H00000000",
        "bold": -1,
        "outline": 4,
        "shadow": 0,
        "alignment": 5,
        "margin_v": 40,
        "blur": 0,
        "animation": "bounce",
        "gradient_colors": ["&H006B6BFF", "&H00B659B9", "&H00DB9834"],  # RGB reversed
    },
    "outlined": {
        "fontname": "Arial",
        "fontsize": 74,
        "primary_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&H00000000",
        "bold": -1,
        "outline": 8,  # Thick outline
        "shadow": 0,
        "alignment": 2,
        "margin_v": 60,
        "blur": 0,
        "animation": "slide",
    },
    "boxed": {
        "fontname": "Arial",
        "fontsize": 54,
        "primary_color": "&H00FFFFFF",
        "outline_color": "&H00000000",
        "back_color": "&HE6000000",      # Nearly opaque black box
        "bold": -1,
        "outline": 0,
        "shadow": 0,
        "alignment": 2,
        "margin_v": 50,
        "blur": 0,
        "border_style": 3,  # Opaque box
        "animation": "box-slide",
    },
    "no-captions": {
        "enabled": False,
    },
}


class CaptionEngine:
    """
    Generates accurate word-timed captions using Deepgram API
    and renders them as styled ASS subtitles
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.deepgram_api_key = self.config.get('deepgram_api_key') or os.getenv('DEEPGRAM_API_KEY')
        
        if not self.deepgram_api_key:
            logger.warning("Deepgram API key not configured - using fallback timing")
        
        # Video dimensions for positioning
        self.video_width = 1080
        self.video_height = 1920
        
        # Caption settings
        self.words_per_group = self.config.get('words_per_group', 4)  # Words shown at once
        self.min_display_time = self.config.get('min_display_time', 0.3)  # Minimum time per word group
    
    def transcribe_audio(self, audio_path: str) -> List[WordTiming]:
        """
        Transcribe audio using Deepgram API to get word-level timestamps
        
        Args:
            audio_path: Path to audio file (mp3, wav, etc.)
        
        Returns:
            List of WordTiming objects with precise timing
        """
        if not self.deepgram_api_key:
            logger.warning("No Deepgram API key - returning empty transcription")
            return []
        
        logger.info(f"Transcribing audio with Deepgram: {audio_path}")
        
        try:
            # Read audio file
            with open(audio_path, 'rb') as audio_file:
                audio_data = audio_file.read()
            
            # Determine content type
            ext = os.path.splitext(audio_path)[1].lower()
            content_types = {
                '.mp3': 'audio/mp3',
                '.wav': 'audio/wav',
                '.m4a': 'audio/m4a',
                '.ogg': 'audio/ogg',
                '.flac': 'audio/flac',
            }
            content_type = content_types.get(ext, 'audio/mp3')
            
            # Deepgram API request
            url = "https://api.deepgram.com/v1/listen"
            params = {
                "model": "nova-2",       # Best model
                "language": "en",
                "punctuate": "true",
                "utterances": "false",
                "smart_format": "true",
            }
            
            headers = {
                "Authorization": f"Token {self.deepgram_api_key}",
                "Content-Type": content_type,
            }
            
            response = requests.post(
                url,
                params=params,
                headers=headers,
                data=audio_data,
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"Deepgram API error: {response.status_code} - {response.text}")
                return []
            
            result = response.json()
            
            # Extract word timings
            words = []
            channels = result.get('results', {}).get('channels', [])
            
            if channels:
                alternatives = channels[0].get('alternatives', [])
                if alternatives:
                    word_data = alternatives[0].get('words', [])
                    
                    for w in word_data:
                        words.append(WordTiming(
                            word=w.get('word', ''),
                            start=w.get('start', 0),
                            end=w.get('end', 0),
                            confidence=w.get('confidence', 1.0)
                        ))
            
            logger.info(f"Transcribed {len(words)} words from audio")
            return words
            
        except Exception as e:
            logger.error(f"Error transcribing audio: {e}")
            return []
    
    def generate_captions(
        self,
        audio_path: str,
        caption_style: str,
        output_path: str,
        script_text: str = None
    ) -> Optional[str]:
        """
        Generate styled ASS subtitle file from audio
        
        Args:
            audio_path: Path to voiceover audio
            caption_style: Style name (modern-bold, neon-glow, etc.)
            output_path: Path to save .ass file
            script_text: Optional script text for fallback timing
        
        Returns:
            Path to generated ASS file, or None if captions disabled
        """
        # Check if captions are disabled
        style_config = ASS_STYLE_CONFIG.get(caption_style, {})
        if style_config.get('enabled') is False:
            logger.info("Captions disabled for this style")
            return None
        
        # Get word timings from Deepgram
        word_timings = self.transcribe_audio(audio_path)
        
        # Fallback: estimate timing from script if Deepgram fails
        if not word_timings and script_text:
            word_timings = self._estimate_word_timings(script_text, audio_path)
        
        if not word_timings:
            logger.warning("No word timings available - skipping captions")
            return None
        
        # Generate ASS file
        ass_content = self._generate_ass_file(word_timings, caption_style)
        
        # Write to file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        
        logger.info(f"Generated captions: {output_path}")
        return output_path
    
    def _generate_ass_file(
        self,
        word_timings: List[WordTiming],
        caption_style: str
    ) -> str:
        """Generate complete ASS subtitle file content"""
        
        style_config = ASS_STYLE_CONFIG.get(caption_style, ASS_STYLE_CONFIG["modern-bold"])
        
        # ASS file header
        header = f"""[Script Info]
Title: ReelFlow Captions
ScriptType: v4.00+
PlayResX: {self.video_width}
PlayResY: {self.video_height}
ScaledBorderAndShadow: yes

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
"""
        
        # Create style line
        style_line = self._create_style_line(caption_style, style_config)
        
        # Create highlight style for karaoke effect
        highlight_style = self._create_highlight_style(caption_style, style_config)
        
        # Dialogue events
        events_header = """
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
        
        # Generate dialogue lines based on animation type
        animation = style_config.get('animation', 'pop')
        dialogues = self._create_dialogues(word_timings, caption_style, style_config, animation)
        
        return header + style_line + highlight_style + events_header + dialogues
    
    def _create_style_line(self, style_name: str, config: Dict) -> str:
        """Create ASS style definition line"""
        
        border_style = config.get('border_style', 1)
        secondary_color = config.get('secondary_color', config.get('primary_color'))
        
        return f"""Style: {style_name},{config.get('fontname', 'Arial')},{config.get('fontsize', 64)},{config.get('primary_color', '&H00FFFFFF')},{secondary_color},{config.get('outline_color', '&H00000000')},{config.get('back_color', '&H80000000')},{config.get('bold', -1)},0,0,0,100,100,0,0,{border_style},{config.get('outline', 3)},{config.get('shadow', 1)},{config.get('alignment', 2)},40,40,{config.get('margin_v', 50)},1
"""
    
    def _create_highlight_style(self, style_name: str, config: Dict) -> str:
        """Create highlight style for karaoke/word highlight effects"""
        
        # Highlighted word uses secondary or accent color
        highlight_color = config.get('secondary_color', "&H0000FFFF")  # Yellow default
        
        return f"""Style: {style_name}-highlight,{config.get('fontname', 'Arial')},{config.get('fontsize', 64)},{highlight_color},{highlight_color},{config.get('outline_color', '&H00000000')},{config.get('back_color', '&H80000000')},{config.get('bold', -1)},0,0,0,100,100,0,0,1,{config.get('outline', 3)},{config.get('shadow', 1)},{config.get('alignment', 2)},40,40,{config.get('margin_v', 50)},1
"""
    
    def _create_dialogues(
        self,
        word_timings: List[WordTiming],
        style_name: str,
        style_config: Dict,
        animation: str
    ) -> str:
        """Create dialogue events with animation effects"""
        
        dialogues = []
        
        # Group words for display
        word_groups = self._group_words(word_timings)
        
        for group in word_groups:
            start_time = self._format_time(group['start'])
            end_time = self._format_time(group['end'])
            text = group['text']
            words = group['words']
            
            # Apply animation effects based on style
            if animation == "karaoke":
                # Word-by-word highlight using karaoke timing
                dialogue = self._create_karaoke_dialogue(
                    words, style_name, start_time, end_time
                )
            elif animation == "glow":
                # Neon glow with blur effect
                animated_text = self._add_glow_effect(text, style_config)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            elif animation == "bounce":
                # Pop/bounce entrance
                animated_text = self._add_bounce_effect(text)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            elif animation == "slide":
                # Slide in from side
                animated_text = self._add_slide_effect(text)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            elif animation == "fade":
                # Simple fade in/out
                animated_text = self._add_fade_effect(text)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            elif animation == "pop":
                # Scale pop effect (default)
                animated_text = self._add_pop_effect(text)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            elif animation == "box-slide":
                # Box background with slide
                animated_text = self._add_box_slide_effect(text)
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{animated_text}"
            else:
                # No animation
                dialogue = f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{text}"
            
            dialogues.append(dialogue)
        
        return "\n".join(dialogues)
    
    def _group_words(self, word_timings: List[WordTiming]) -> List[Dict]:
        """Group words for display (show N words at a time)"""
        
        groups = []
        current_group = []
        
        for i, word in enumerate(word_timings):
            current_group.append(word)
            
            # Check if we should end this group
            end_group = False
            
            # End on punctuation
            if word.word and word.word[-1] in '.!?,;:':
                end_group = True
            
            # End after N words
            elif len(current_group) >= self.words_per_group:
                end_group = True
            
            # End if this is the last word
            elif i == len(word_timings) - 1:
                end_group = True
            
            if end_group and current_group:
                groups.append({
                    'start': current_group[0].start,
                    'end': current_group[-1].end + 0.1,  # Small buffer
                    'text': ' '.join(w.word for w in current_group),
                    'words': current_group,
                })
                current_group = []
        
        return groups
    
    def _create_karaoke_dialogue(
        self,
        words: List[WordTiming],
        style_name: str,
        start_time: str,
        end_time: str
    ) -> str:
        """Create karaoke-style word-by-word highlight"""
        
        # Use \k timing for karaoke effect
        karaoke_text = ""
        for word in words:
            # Duration in centiseconds
            duration_cs = int((word.end - word.start) * 100)
            karaoke_text += f"{{\\kf{duration_cs}}}{word.word} "
        
        return f"Dialogue: 0,{start_time},{end_time},{style_name},,0,0,0,,{karaoke_text.strip()}"
    
    def _add_glow_effect(self, text: str, style_config: Dict) -> str:
        """Add neon glow effect with blur"""
        blur = style_config.get('blur', 15)
        return f"{{\\blur{blur}\\fad(100,100)}}{text}"
    
    def _add_bounce_effect(self, text: str) -> str:
        """Add bounce/pop entrance effect"""
        # Scale from 120% to 100% with bounce
        return f"{{\\fscx120\\fscy120\\t(0,100,\\fscx100\\fscy100)\\fad(80,80)}}{text}"
    
    def _add_slide_effect(self, text: str) -> str:
        """Add slide-in effect"""
        # Slide from right to center
        return f"{{\\move(600,0,0,0,0,150)\\fad(0,100)}}{text}"
    
    def _add_fade_effect(self, text: str) -> str:
        """Add simple fade in/out"""
        return f"{{\\fad(150,150)}}{text}"
    
    def _add_pop_effect(self, text: str) -> str:
        """Add scale pop effect (default modern-bold)"""
        return f"{{\\fscx105\\fscy105\\t(0,80,\\fscx100\\fscy100)\\fad(60,80)}}{text}"
    
    def _add_box_slide_effect(self, text: str) -> str:
        """Add box background with slide effect"""
        return f"{{\\fad(100,100)\\move(0,10,0,0,0,100)}}{text}"
    
    def _format_time(self, seconds: float) -> str:
        """Convert seconds to ASS time format (H:MM:SS.cc)"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        centisecs = int((seconds % 1) * 100)
        return f"{hours}:{minutes:02d}:{secs:02d}.{centisecs:02d}"
    
    def _estimate_word_timings(
        self,
        script_text: str,
        audio_path: str
    ) -> List[WordTiming]:
        """
        Fallback: Estimate word timings when Deepgram is unavailable
        Uses character count as proxy for timing
        """
        try:
            from moviepy.editor import AudioFileClip
            audio = AudioFileClip(audio_path)
            duration = audio.duration
            audio.close()
        except:
            duration = 60  # Default fallback
        
        words = script_text.split()
        if not words:
            return []
        
        # Estimate timing based on word length
        total_chars = sum(len(w) for w in words)
        time_per_char = duration / total_chars if total_chars > 0 else 0.1
        
        timings = []
        current_time = 0
        
        for word in words:
            word_duration = len(word) * time_per_char
            word_duration = max(0.15, word_duration)  # Minimum 150ms per word
            
            timings.append(WordTiming(
                word=word,
                start=current_time,
                end=current_time + word_duration,
                confidence=0.5  # Low confidence for estimates
            ))
            
            current_time += word_duration
        
        return timings
    
    def burn_captions_ffmpeg(
        self,
        video_path: str,
        ass_path: str,
        output_path: str
    ) -> str:
        """
        Burn ASS captions into video using FFmpeg
        
        Args:
            video_path: Input video file
            ass_path: ASS subtitle file
            output_path: Output video with burned captions
        
        Returns:
            Path to output video
        """
        import subprocess
        
        logger.info(f"Burning captions into video: {output_path}")
        
        # Escape path for FFmpeg filter
        ass_path_escaped = ass_path.replace('\\', '/').replace(':', '\\:')
        
        cmd = [
            'ffmpeg', '-y',
            '-i', video_path,
            '-vf', f"ass='{ass_path_escaped}'",
            '-c:a', 'copy',
            '-c:v', 'libx264',
            '-preset', 'fast',
            '-crf', '20',
            output_path
        ]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode != 0:
                logger.error(f"FFmpeg error: {result.stderr}")
                raise Exception(f"FFmpeg failed: {result.stderr}")
            
            logger.info(f"Captions burned successfully: {output_path}")
            return output_path
            
        except subprocess.TimeoutExpired:
            logger.error("FFmpeg caption burn timed out")
            raise
        except Exception as e:
            logger.error(f"Error burning captions: {e}")
            raise


# Export for use in other modules
__all__ = ['CaptionEngine', 'ASS_STYLE_CONFIG', 'WordTiming']
