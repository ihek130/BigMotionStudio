"""
Scene Video Assembly Engine - Assembles AI-Generated Scene Images into Video
Stitches scene images with Ken Burns effect, syncs to voiceover, adds captions.
Replaces stock video workflow with dynamic AI-generated content.
"""

import os
import logging
import numpy as np
from typing import Dict, List, Optional
from moviepy.editor import (
    ImageClip, AudioFileClip, CompositeVideoClip,
    concatenate_videoclips, CompositeAudioClip, TextClip
)
from moviepy.video.fx.all import fadein, fadeout
import cv2

from .models import (
    UserSeriesSettings, ScriptData, Scene,
    MUSIC_TRACK_FILES, CAPTION_STYLE_CONFIG
)
from .caption_engine import CaptionEngine

logger = logging.getLogger(__name__)


class SceneVideoAssemblyEngine:
    """
    Assembles final video from AI-generated scene images.
    Each scene gets Ken Burns effect, proper transitions, and caption sync.
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        
        # Output settings
        self.output_width = 1080
        self.output_height = 1920
        self.fps = self.config.get('fps', 30)
        
        # Effect settings
        self.ken_burns_intensity = self.config.get('zoom_intensity', 1.08)  # 8% zoom
        self.crossfade_duration = self.config.get('crossfade_duration', 0.3)
        self.fade_in_duration = self.config.get('fade_in_duration', 0.5)
        self.fade_out_duration = self.config.get('fade_out_duration', 0.5)
        
        # Audio settings
        self.music_volume = self.config.get('music_volume', 0.12)  # 12% background
        self.music_fade_in = self.config.get('music_fade_in', 2.0)
        self.music_fade_out = self.config.get('music_fade_out', 3.0)
        
        # Encoding settings
        self.codec = self.config.get('codec', 'libx264')
        self.audio_codec = self.config.get('audio_codec', 'aac')
        self.bitrate = self.config.get('bitrate', '8000k')  # High quality for shorts
        self.threads = self.config.get('threads', 6)
    
    def assemble_video(
        self,
        script_data: ScriptData,
        voiceover_data: Dict,
        settings: UserSeriesSettings,
        output_path: str
    ) -> Dict:
        """
        Assemble final video from scene images and voiceover.
        Uses Deepgram for accurate word-timed captions with styled ASS subtitles.
        
        Args:
            script_data: Script with scene images (image paths set)
            voiceover_data: Dict with audio_path and duration
            settings: User settings (for music, captions)
            output_path: Final video output path
        
        Returns:
            Dict with video metadata
        """
        logger.info(f"Assembling video with {len(script_data.scenes)} scenes")
        
        try:
            # Load voiceover audio
            voiceover = AudioFileClip(voiceover_data['audio_path'])
            total_duration = voiceover.duration
            
            logger.info(f"Voiceover duration: {total_duration:.2f}s")
            
            # Calculate scene timings based on voiceover duration
            scenes_with_timing = self._calculate_scene_timings(
                script_data.scenes,
                total_duration
            )
            
            # Create video clips for each scene
            video_clips = self._create_scene_clips(scenes_with_timing)
            
            # Concatenate with crossfades
            video_sequence = self._concatenate_with_transitions(video_clips)
            
            # Add fade in/out to video
            video_sequence = video_sequence.fx(fadein, self.fade_in_duration)
            video_sequence = video_sequence.fx(fadeout, self.fade_out_duration)
            
            # Create audio mix (voiceover + background music)
            final_audio = self._create_audio_mix(
                voiceover,
                settings.music_track,
                total_duration
            )
            
            # Set audio to video
            final_video = video_sequence.set_audio(final_audio)
            
            # Export base video (without captions)
            base_output = output_path.replace('.mp4', '_base.mp4')
            logger.info(f"Exporting base video to {base_output}")
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            final_video.write_videofile(
                base_output,
                fps=self.fps,
                codec=self.codec,
                audio_codec=self.audio_codec,
                threads=self.threads,
                preset='fast',
                bitrate=self.bitrate,
                logger=None,
                ffmpeg_params=['-crf', '20']
            )
            
            # Cleanup moviepy clips before FFmpeg
            voiceover.close()
            final_video.close()
            if final_audio:
                final_audio.close()
            for clip in video_clips:
                clip.close()
            
            # Generate and burn captions using Deepgram + FFmpeg
            final_output = output_path
            if settings.caption_style != "no-captions":
                final_output = self._add_deepgram_captions(
                    base_output,
                    voiceover_data['audio_path'],
                    settings.caption_style,
                    script_data,
                    output_path
                )
                # Remove base video if captions were added
                if final_output != base_output and os.path.exists(base_output):
                    os.remove(base_output)
            else:
                # No captions - rename base to final
                os.rename(base_output, output_path)
                final_output = output_path
            
            logger.info(f"Video assembly complete: {final_output}")
            
            return {
                'video_path': final_output,
                'duration_seconds': total_duration,
                'resolution': f"{self.output_width}x{self.output_height}",
                'fps': self.fps,
                'scene_count': len(script_data.scenes),
                'caption_style': settings.caption_style,
            }
            
        except Exception as e:
            logger.error(f"Error assembling video: {e}")
            raise
    
    def _add_deepgram_captions(
        self,
        video_path: str,
        audio_path: str,
        caption_style: str,
        script_data: ScriptData,
        output_path: str
    ) -> str:
        """
        Generate captions using Deepgram and burn into video with FFmpeg.
        
        Args:
            video_path: Base video without captions
            audio_path: Voiceover audio for transcription
            caption_style: User's selected style
            script_data: Script for fallback timing
            output_path: Final output path
        
        Returns:
            Path to video with burned captions
        """
        logger.info(f"Adding Deepgram captions with style: {caption_style}")
        
        try:
            # Initialize caption engine
            caption_engine = CaptionEngine(self.config)
            
            # Get script text for fallback
            full_script = " ".join(scene.narration for scene in script_data.scenes)
            
            # Generate ASS subtitle file
            ass_path = output_path.replace('.mp4', '.ass')
            ass_file = caption_engine.generate_captions(
                audio_path=audio_path,
                caption_style=caption_style,
                output_path=ass_path,
                script_text=full_script
            )
            
            if ass_file:
                # Burn captions into video using FFmpeg
                final_path = caption_engine.burn_captions_ffmpeg(
                    video_path=video_path,
                    ass_path=ass_file,
                    output_path=output_path
                )
                
                # Clean up ASS file after burning
                if os.path.exists(ass_path):
                    os.remove(ass_path)
                
                return final_path
            else:
                # No captions generated - use base video
                logger.warning("No captions generated - using video without captions")
                os.rename(video_path, output_path)
                return output_path
                
        except Exception as e:
            logger.error(f"Error adding captions: {e}")
            # Fallback - use video without captions
            if os.path.exists(video_path):
                os.rename(video_path, output_path)
            return output_path
    
    def _calculate_scene_timings(
        self,
        scenes: List[Scene],
        total_duration: float
    ) -> List[Scene]:
        """
        Adjust scene timings to match actual voiceover duration.
        Distributes time proportionally based on narration length.
        
        RETENTION OPTIMIZATION:
        - Minimum 3 seconds per scene (viewer needs time to process)
        - Maximum 6 seconds per scene (prevents boredom)
        - Sweet spot: 3-5 seconds for viral retention
        """
        # Calculate total script length (by characters as proxy for time)
        total_chars = sum(len(s.narration) for s in scenes)
        
        if total_chars == 0:
            # Fallback: equal distribution with retention optimization
            per_scene_duration = total_duration / len(scenes)
            # Clamp to 3-6 second range
            per_scene_duration = max(3.0, min(6.0, per_scene_duration))
            
            current_time = 0
            for scene in scenes:
                scene.start_time = current_time
                scene.duration = per_scene_duration
                scene.end_time = current_time + per_scene_duration
                current_time = scene.end_time
            return scenes
        
        # Distribute time proportionally
        current_time = 0
        for scene in scenes:
            proportion = len(scene.narration) / total_chars
            scene.duration = total_duration * proportion
            
            # ⚠️ RETENTION OPTIMIZATION: Enforce 3-6 second range
            # Too short (< 3s) = viewer can't process image = confusion
            # Too long (> 6s) = static image gets boring = drop-off
            scene.duration = max(3.0, min(6.0, scene.duration))
            
            scene.start_time = current_time
            scene.end_time = current_time + scene.duration
            current_time = scene.end_time
        
        # Adjust timing to fit total duration
        actual_total = sum(s.duration for s in scenes)
        if actual_total != total_duration:
            # Scale all durations proportionally
            scale_factor = total_duration / actual_total
            current_time = 0
            for scene in scenes:
                scene.duration *= scale_factor
                # Re-clamp after scaling
                scene.duration = max(3.0, min(6.0, scene.duration))
                scene.start_time = current_time
                scene.end_time = current_time + scene.duration
                current_time = scene.end_time
            
            # Final adjustment: If still off, adjust last scene
            if scenes:
                time_diff = total_duration - current_time
                scenes[-1].duration += time_diff
                scenes[-1].end_time = total_duration
        
        # Log scene durations for quality check
        avg_duration = total_duration / len(scenes) if scenes else 0
        logger.info(f"Scene timing optimized: {len(scenes)} scenes, avg {avg_duration:.1f}s each")
        for scene in scenes:
            logger.debug(f"Scene {scene.scene_number}: {scene.duration:.2f}s")
        
        return scenes
    
    def _create_scene_clips(self, scenes: List[Scene]) -> List[ImageClip]:
        """Create video clips from scene images with Ken Burns effect"""
        
        clips = []
        
        for scene in scenes:
            # Use cropped image if available, otherwise original
            image_path = scene.cropped_image_path or scene.image_path
            
            if not image_path or not os.path.exists(image_path):
                logger.warning(f"Scene {scene.scene_number}: No image found, using placeholder")
                # Create black placeholder
                from moviepy.editor import ColorClip
                clip = ColorClip(
                    size=(self.output_width, self.output_height),
                    color=(0, 0, 0),
                    duration=scene.duration
                )
            else:
                # Load image and create clip
                clip = ImageClip(image_path, duration=scene.duration)
                
                # Ensure correct dimensions
                if clip.size != (self.output_width, self.output_height):
                    clip = clip.resize((self.output_width, self.output_height))
                
                # Apply Ken Burns effect (smooth zoom)
                clip = self._apply_ken_burns(clip, scene.duration)
            
            clips.append(clip)
        
        return clips
    
    def _apply_ken_burns(self, clip: ImageClip, duration: float) -> ImageClip:
        """
        Apply Ken Burns effect (gradual zoom) to image clip.
        Creates illusion of camera movement on still image.
        """
        
        zoom_intensity = self.ken_burns_intensity
        
        def zoom_effect(get_frame, t):
            """Apply gradual zoom based on time"""
            frame = get_frame(t)
            
            # Calculate zoom progress (0 to 1)
            progress = t / duration
            
            # Calculate current scale (linear interpolation)
            scale = 1.0 + (zoom_intensity - 1.0) * progress
            
            h, w = frame.shape[:2]
            new_h, new_w = int(h * scale), int(w * scale)
            
            # Resize (zoom in)
            resized = cv2.resize(frame, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
            
            # Crop from center to original size
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            cropped = resized[start_y:start_y+h, start_x:start_x+w]
            
            return cropped
        
        return clip.fl(zoom_effect)
    
    def _concatenate_with_transitions(self, clips: List[ImageClip]) -> CompositeVideoClip:
        """Concatenate clips with crossfade transitions"""
        
        if len(clips) == 0:
            raise ValueError("No clips to concatenate")
        
        if len(clips) == 1:
            return clips[0]
        
        # Apply crossfade to all but first clip
        processed_clips = [clips[0]]
        
        for clip in clips[1:]:
            # Add crossfade in
            clip = clip.crossfadein(self.crossfade_duration)
            processed_clips.append(clip)
        
        # Concatenate using compose method for smooth transitions
        final = concatenate_videoclips(processed_clips, method="compose")
        
        return final
    
    def _create_audio_mix(
        self,
        voiceover: AudioFileClip,
        music_track: str,
        total_duration: float
    ) -> CompositeAudioClip:
        """Mix voiceover with background music"""
        
        audio_clips = [voiceover]
        
        # Add background music if selected
        if music_track and music_track != "none":
            music_path = MUSIC_TRACK_FILES.get(music_track)
            
            if music_path and os.path.exists(music_path):
                music = AudioFileClip(music_path)
                
                # Loop if needed
                if music.duration < total_duration:
                    # Loop music
                    loops_needed = int(total_duration / music.duration) + 1
                    music = concatenate_audioclips([music] * loops_needed)
                
                # Trim to exact duration
                music = music.subclip(0, total_duration)
                
                # Set volume (background level)
                music = music.volumex(self.music_volume)
                
                # Add fade in/out
                music = music.audio_fadein(self.music_fade_in)
                music = music.audio_fadeout(self.music_fade_out)
                
                audio_clips.append(music)
        
        # Composite audio
        final_audio = CompositeAudioClip(audio_clips)
        
        return final_audio
    
    def _add_captions(
        self,
        video: CompositeVideoClip,
        scenes: List[Scene],
        caption_style: str
    ) -> CompositeVideoClip:
        """Add captions/subtitles to video based on scene narration"""
        
        style_config = CAPTION_STYLE_CONFIG.get(caption_style, CAPTION_STYLE_CONFIG["modern-bold"])
        
        if not style_config.get("enabled", True):
            return video
        
        caption_clips = []
        
        for scene in scenes:
            if not scene.narration:
                continue
            
            try:
                # Create text clip for this scene
                text_clip = TextClip(
                    scene.narration,
                    fontsize=style_config.get("font_size", 60),
                    color=style_config.get("color", "white"),
                    font=style_config.get("font", "Arial-Bold"),
                    stroke_color=style_config.get("stroke_color", "black"),
                    stroke_width=style_config.get("stroke_width", 3),
                    size=(self.output_width - 80, None),  # Leave margins
                    method='caption',
                    align='center'
                )
                
                # Position at bottom
                text_clip = text_clip.set_position(('center', 'bottom'))
                text_clip = text_clip.margin(bottom=150, opacity=0)
                
                # Set timing
                text_clip = text_clip.set_start(scene.start_time)
                text_clip = text_clip.set_duration(scene.duration)
                
                # Add fade in/out
                text_clip = text_clip.crossfadein(0.2).crossfadeout(0.2)
                
                caption_clips.append(text_clip)
                
            except Exception as e:
                logger.warning(f"Failed to create caption for scene {scene.scene_number}: {e}")
        
        if caption_clips:
            # Composite video with captions
            return CompositeVideoClip([video] + caption_clips)
        
        return video
    
    def _add_word_by_word_captions(
        self,
        video: CompositeVideoClip,
        scenes: List[Scene],
        caption_style: str
    ) -> CompositeVideoClip:
        """
        Advanced word-by-word caption animation.
        Words appear one at a time, synced to audio.
        """
        
        style_config = CAPTION_STYLE_CONFIG.get(caption_style, CAPTION_STYLE_CONFIG["modern-bold"])
        caption_clips = []
        
        for scene in scenes:
            words = scene.narration.split()
            if not words:
                continue
            
            # Calculate time per word
            time_per_word = scene.duration / len(words)
            
            for i, word in enumerate(words):
                word_start = scene.start_time + (i * time_per_word)
                word_duration = time_per_word * 1.2  # Slight overlap
                
                try:
                    word_clip = TextClip(
                        word,
                        fontsize=style_config.get("font_size", 72),
                        color=style_config.get("color", "white"),
                        font=style_config.get("font", "Arial-Bold"),
                        stroke_color=style_config.get("stroke_color", "black"),
                        stroke_width=style_config.get("stroke_width", 4),
                    )
                    
                    word_clip = word_clip.set_position('center')
                    word_clip = word_clip.set_start(word_start)
                    word_clip = word_clip.set_duration(min(word_duration, scene.end_time - word_start))
                    
                    caption_clips.append(word_clip)
                    
                except Exception as e:
                    logger.warning(f"Failed to create word caption: {e}")
        
        if caption_clips:
            return CompositeVideoClip([video] + caption_clips)
        
        return video


# Helper for audio concatenation (not in moviepy by default)
def concatenate_audioclips(clips):
    """Concatenate audio clips"""
    from moviepy.editor import concatenate_audioclips as _concat
    return _concat(clips)
