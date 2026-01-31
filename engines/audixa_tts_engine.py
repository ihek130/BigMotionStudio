"""
Audixa TTS Engine - AI Voice Generation
Generates voiceovers using Audixa SDK based on user's voice selection.
Maps frontend voice IDs to Audixa voice configurations.
"""

import os
import logging
from typing import Dict, Optional
from pydub import AudioSegment
import audixa

from .models import UserSeriesSettings, ScriptData, VoiceId

logger = logging.getLogger(__name__)


# Voice ID mappings to Audixa API voice identifiers
# These are the actual Audixa voice IDs
AUDIXA_VOICE_MAP = {
    "bm_lewis": {
        "voice_id": "bm_lewis",
        "name": "Lewis",
        "description": "Deep & Commanding",
        "gender": "male",
        "settings": {
            "emotion": "neutral",  # Calm/eerie delivery for horror
            "temperature": 0.75,   # Adds expressiveness variation
            "speed": 0.95,         # Slightly slower for suspense
        }
    },
    "bm_harry": {
        "voice_id": "bm_harry",
        "name": "Harry",
        "description": "Warm & Engaging",
        "gender": "male",
        "settings": {
            "emotion": "happy",
            "temperature": 0.7,
            "speed": 1.0,
        }
    },
    "am_eric": {
        "voice_id": "am_eric",
        "name": "Eric",
        "description": "Professional & Clear",
        "gender": "male",
        "settings": {
            "emotion": "neutral",
            "temperature": 0.65,
            "speed": 1.0,
        }
    },
    "am_ethan": {
        "voice_id": "am_ethan",
        "name": "Ethan",
        "description": "Friendly & Energetic",
        "gender": "male",
        "settings": {
            "emotion": "happy",
            "temperature": 0.75,
            "speed": 1.05,
        }
    },
    "bm_oliver": {
        "voice_id": "bm_oliver",
        "name": "Oliver",
        "description": "Smooth & Sophisticated",
        "gender": "male",
        "settings": {
            "emotion": "neutral",
            "temperature": 0.65,
            "speed": 1.0,
        }
    },
    "af_aria": {
        "voice_id": "af_aria",
        "name": "Aria",
        "description": "Calm & Soothing",
        "gender": "female",
        "settings": {
            "emotion": "neutral",
            "temperature": 0.6,
            "speed": 0.95,
        }
    },
    "af_bella": {
        "voice_id": "af_bella",
        "name": "Bella",
        "description": "Bright & Enthusiastic",
        "gender": "female",
        "settings": {
            "emotion": "happy",
            "temperature": 0.75,
            "speed": 1.05,
        }
    },
    "af_lily": {
        "voice_id": "af_lily",
        "name": "Lily",
        "description": "Gentle & Warm",
        "gender": "female",
        "settings": {
            "emotion": "neutral",
            "temperature": 0.65,
            "speed": 1.0,
        }
    },
    "af_zoey": {
        "voice_id": "af_zoey",
        "name": "Zoey",
        "description": "Energetic & Youthful",
        "gender": "female",
        "settings": {
            "emotion": "surprised",
            "temperature": 0.8,
            "speed": 1.1,
        }
    },
}


class AudixaTTSEngine:
    """
    Generates voiceovers using Audixa SDK.
    Voice selection is driven by user's frontend choice.
    """
    
    def __init__(self):
        self.api_key = os.getenv('AUDIXA_API_KEY')
        
        # Initialize Audixa SDK with API key
        if self.api_key:
            audixa.set_api_key(self.api_key)
        else:
            logger.warning("AUDIXA_API_KEY not set - TTS will fail")
        
        # Default settings
        self.default_model = 'base'
        self.max_chars_per_request = 10000
    
    def generate_voiceover(
        self,
        script_data: ScriptData,
        settings: UserSeriesSettings,
        output_path: str
    ) -> Dict:
        """
        Generate voiceover from script using user's selected voice.
        
        Args:
            script_data: Script with full text
            settings: User settings containing voice_id
            output_path: Path to save the audio file
        
        Returns:
            Dict with audio_path, duration, and metadata
        """
        logger.info(f"Generating voiceover with voice: {settings.voice_id}")
        
        # Get voice configuration (fallback to bm_lewis if voice not found)
        voice_config = AUDIXA_VOICE_MAP.get(settings.voice_id, AUDIXA_VOICE_MAP["bm_lewis"])
        
        script_text = script_data.full_script
        
        # Add natural pauses for better pacing
        script_text = self._add_natural_pauses(script_text)
        
        # Generate with Audixa API
        try:
            success = self._generate_with_audixa(
                text=script_text,
                voice_config=voice_config,
                output_path=output_path
            )
            
            if success:
                return self._get_audio_metadata(output_path, voice_config)
            else:
                raise Exception("Audixa TTS generation failed")
                
        except Exception as e:
            logger.error(f"Audixa TTS failed: {e}")
            raise Exception(f"TTS generation failed: {e}")
    
    def _generate_with_audixa(
        self,
        text: str,
        voice_config: Dict,
        output_path: str,
        max_retries: int = 3
    ) -> bool:
        """Generate audio using Audixa SDK"""
        
        if not self.api_key:
            logger.error("AUDIXA_API_KEY not set")
            raise Exception("AUDIXA_API_KEY not configured")
        
        import time
        
        for attempt in range(max_retries):
            try:
                # Ensure output directory exists
                output_dir = os.path.dirname(output_path)
                if output_dir:
                    os.makedirs(output_dir, exist_ok=True)
                
                # Handle long scripts by chunking
                if len(text) > self.max_chars_per_request:
                    return self._generate_chunked(text, voice_config, output_path)
                
                # Generate audio using Audixa SDK
                # SDK outputs WAV by default, we'll convert to MP3
                temp_wav_path = output_path.replace('.mp3', '.wav')
                
                logger.info(f"Generating TTS with voice {voice_config['voice_id']}, text length: {len(text)} (attempt {attempt + 1}/{max_retries})")
                
                # Get voice settings
                voice_settings = voice_config.get("settings", {})
                speed = voice_settings.get("speed", 1.0)
                
                # Build API parameters based on model
                # Base model only supports: text, voice, model, speed
                # Advance model supports: emotion, temperature, top_p, do_sample
                tts_params = {
                    "text": text,
                    "filepath": temp_wav_path,
                    "voice": voice_config["voice_id"],
                    "model": self.default_model,
                    "speed": speed,
                }
                
                # Add advanced parameters only for Advance model
                if self.default_model == "advance":
                    emotion = voice_settings.get("emotion", "neutral")
                    temperature = voice_settings.get("temperature", 0.7)
                    tts_params["emotion"] = emotion
                    tts_params["temperature"] = temperature
                
                # Log the exact parameters for debugging
                logger.info(f"TTS params: voice={tts_params['voice']}, model={tts_params['model']}, speed={tts_params['speed']}, text_len={len(tts_params['text'])}")
                logger.info(f"Text first 100 chars: {repr(tts_params['text'][:100])}")
                
                audixa.tts_to_file(**tts_params)
                
                # Convert WAV to MP3
                audio = AudioSegment.from_wav(temp_wav_path)
                audio.export(output_path, format="mp3", bitrate="192k")
                
                # Clean up temp WAV file
                if os.path.exists(temp_wav_path):
                    os.remove(temp_wav_path)
                
                logger.info(f"Voiceover saved to {output_path}")
                return True
                
            except Exception as e:
                # Log detailed error info
                import traceback
                logger.warning(f"Audixa TTS attempt {attempt + 1} failed: {e}")
                logger.debug(f"Full traceback: {traceback.format_exc()}")
                if attempt < max_retries - 1:
                    wait_time = (attempt + 1) * 2  # 2, 4, 6 seconds
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"All {max_retries} attempts failed for Audixa TTS")
                    raise
    
    def _generate_chunked(
        self,
        text: str,
        voice_config: Dict,
        output_path: str
    ) -> bool:
        """Generate audio in chunks for long scripts using Audixa SDK"""
        
        import tempfile
        
        chunks = self._split_text_into_chunks(text, self.max_chars_per_request)
        logger.info(f"Splitting script into {len(chunks)} chunks")
        
        audio_segments = []
        temp_files = []
        
        try:
            for i, chunk in enumerate(chunks):
                logger.info(f"Generating chunk {i+1}/{len(chunks)}")
                
                # Create temp file for this chunk
                temp_wav = tempfile.NamedTemporaryFile(suffix='.wav', delete=False)
                temp_wav.close()
                temp_files.append(temp_wav.name)
                
                # Generate audio using Audixa SDK
                audixa.tts_to_file(
                    chunk,
                    temp_wav.name,
                    voice=voice_config["voice_id"],
                    model=self.default_model,
                )
                
                # Load as AudioSegment
                audio = AudioSegment.from_wav(temp_wav.name)
                audio_segments.append(audio)
            
            # Concatenate all chunks
            final_audio = audio_segments[0]
            for segment in audio_segments[1:]:
                final_audio = final_audio + segment
            
            # Export as MP3
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            final_audio.export(output_path, format="mp3", bitrate="192k")
            
            return True
            
        finally:
            # Clean up temp files
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
    
    def _split_text_into_chunks(self, text: str, max_chars: int) -> list:
        """Split text at sentence boundaries"""
        
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        chunks = []
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk) + len(sentence) < max_chars:
                current_chunk += sentence + " "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + " "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks
    
    def _add_natural_pauses(self, text: str) -> str:
        """Add natural pauses for better pacing and sanitize text"""
        
        import re
        
        # First, sanitize the text - fix common encoding issues
        text = self._sanitize_text(text)
        
        # Add pause after periods (longer pause)
        text = re.sub(r'\.(\s+)', r'. \1', text)
        
        # Add slight pause after commas
        text = re.sub(r',(\s+)', r', \1', text)
        
        # Add dramatic pause after ellipses
        text = re.sub(r'\.\.\.', '... ', text)
        
        # Add pause after question marks
        text = re.sub(r'\?(\s+)', r'? \1', text)
        
        return text
    
    def _sanitize_text(self, text: str) -> str:
        """Sanitize text to fix encoding issues and remove problematic characters"""
        
        import re
        
        # First, try to fix mojibake (UTF-8 decoded as Latin-1/Windows-1252)
        # These are common corruption patterns when UTF-8 is misinterpreted
        try:
            # Try to fix double-encoded UTF-8
            fixed = text.encode('latin-1').decode('utf-8')
            text = fixed
        except (UnicodeDecodeError, UnicodeEncodeError):
            pass  # Already proper UTF-8
        
        # Fix common encoding corruption patterns (string replacements)
        replacements = {
            # Mojibake patterns (UTF-8 misread as Windows-1252)
            'â€"': '-',    # em-dash corrupted
            'â€"': '-',    # en-dash corrupted  
            'â€™': "'",    # right single quote corrupted
            'â€˜': "'",    # left single quote corrupted
            'â€œ': '"',    # left double quote corrupted
            'â€': '"',     # right double quote corrupted (partial)
            'â€¦': '...',  # ellipsis corrupted
            # Unicode characters to ASCII equivalents
            '\u2014': '-', # em-dash
            '\u2013': '-', # en-dash
            '\u2019': "'", # right single quote
            '\u2018': "'", # left single quote
            '\u201c': '"', # left double quote
            '\u201d': '"', # right double quote
            '\u2026': '...', # ellipsis
            '\u00e2': '',  # Remove lone â character (broken encoding artifact)
            '\u0080': '',  # Remove control character
            '\u0099': '',  # Remove control character
            '\u009c': '',  # Remove control character
            '\u0093': '',  # Remove control character
            '\u0094': '',  # Remove control character
        }
        
        for bad, good in replacements.items():
            text = text.replace(bad, good)
        
        # PRESERVE emphasis and emotion for TTS expressiveness
        # Only remove truly problematic characters (emojis, special symbols)
        # Keep: letters, numbers, punctuation, spaces, exclamation marks, question marks
        # This allows multiple !!! and ??? for emphasis
        text = re.sub(r'[^\w\s.,!?\'\"\-;:()\\/]', '', text)
        
        # Clean up excessive spaces (but preserve punctuation)
        text = re.sub(r' +', ' ', text)
        
        return text.strip()
    
    def _get_audio_metadata(self, audio_path: str, voice_config: Dict) -> Dict:
        """Get audio file metadata"""
        
        audio = AudioSegment.from_file(audio_path)
        duration_seconds = len(audio) / 1000.0
        
        return {
            "audio_path": audio_path,
            "duration_seconds": duration_seconds,
            "voice_id": voice_config.get("voice_id", "unknown"),
            "voice_name": voice_config.get("name", "Unknown"),
            "format": "mp3",
        }
    
    def generate_scene_audio(
        self,
        script_data: ScriptData,
        settings: UserSeriesSettings,
        output_dir: str
    ) -> Dict:
        """
        Generate audio for each scene separately for precise timing.
        Useful for exact scene-audio synchronization.
        
        Returns dict mapping scene_number to audio info.
        """
        os.makedirs(output_dir, exist_ok=True)
        
        voice_config = AUDIXA_VOICE_MAP.get(settings.voice_id, AUDIXA_VOICE_MAP["bm_lewis"])
        scene_audio = {}
        
        for scene in script_data.scenes:
            audio_path = os.path.join(output_dir, f"scene_{scene.scene_number:02d}_audio.mp3")
            
            try:
                success = self._generate_with_audixa(
                    text=scene.narration,
                    voice_config=voice_config,
                    output_path=audio_path
                )
                
                if not success:
                    raise Exception(f"Audixa API failed for scene {scene.scene_number}")
                
                # Get duration
                audio = AudioSegment.from_file(audio_path)
                duration = len(audio) / 1000.0
                
                scene_audio[scene.scene_number] = {
                    "audio_path": audio_path,
                    "duration_seconds": duration,
                    "narration": scene.narration,
                }
                
            except Exception as e:
                logger.error(f"Failed to generate audio for scene {scene.scene_number}: {e}")
                raise
        
        return scene_audio
