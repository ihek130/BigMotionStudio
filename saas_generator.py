"""
SaaS Video Generation Pipeline - Main Orchestrator
Coordinates all engines to generate videos based on user settings.
Entry point for the backend API.
"""

import os
import sys
import logging
from datetime import datetime
from typing import Dict, Optional

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from engines.models import UserSeriesSettings, ScriptData, GeneratedVideo
from engines.scene_script_engine import SceneScriptEngine
from engines.scene_image_engine import SceneImageEngine
from engines.audixa_tts_engine import AudixaTTSEngine
from engines.scene_video_assembly_engine import SceneVideoAssemblyEngine
from engines.seo_engine import SEOEngine
from engines.soundtrack_engine import SoundtrackEngine

from utils import setup_logging, load_env, ensure_directories

logger = logging.getLogger(__name__)


class SaaSVideoGenerator:
    """
    Main orchestrator for the SaaS video generation pipeline.
    Takes user settings from frontend and generates complete video.
    """
    
    def __init__(self):
        """Initialize the video generator with all engines"""
        
        # Load environment variables
        load_env()
        
        # Setup logging (uses LOGS_DIR env var or 'logs' default)
        logs_dir = os.getenv('LOGS_DIR', 'logs')
        self.logger = setup_logging(logs_dir)
        
        # Initialize engines
        self.logger.info("Initializing SaaS video generation engines...")
        self._initialize_engines()
        
        # Directories (from environment or defaults)
        self.output_dir = os.getenv('OUTPUT_DIR', 'output')
        self.temp_dir = os.getenv('TEMP_DIR', 'temp')
        
        self.logger.info("SaaS Video Generator initialized successfully")
    
    def _initialize_engines(self):
        """Initialize all engine instances (they use their own env-based defaults)"""
        
        self.script_engine = SceneScriptEngine()
        self.image_engine = SceneImageEngine()
        self.tts_engine = AudixaTTSEngine()
        self.video_assembly_engine = SceneVideoAssemblyEngine()
        self.seo_engine = SEOEngine()
        self.soundtrack_engine = SoundtrackEngine()
    
    def generate_video(
        self,
        settings: UserSeriesSettings,
        topic: Optional[str] = None,
        project_id: Optional[str] = None,
        skip_validation: bool = False
    ) -> GeneratedVideo:
        """
        Generate a complete video based on user settings.
        
        This is the MAIN ENTRY POINT - called by the API.
        
        ⚠️ SERIES CONSISTENCY GUARANTEE:
        - settings.niche: FIXED per series (e.g., "scary-stories")
        - settings.visual_style: FIXED per series (e.g., "lego")
        - settings.voice_id: FIXED per series (e.g., "bm_lewis")
        - settings.music_track: FIXED per series
        - settings.caption_style: FIXED per series
        
        These settings are defined when the user creates a series and
        remain consistent for ALL videos generated in that series.
        
        Only the TOPIC varies per video - ensuring brand consistency
        while maintaining content freshness.
        
        Args:
            settings: User's complete series configuration (niche, style, voice, etc.)
            topic: Optional specific topic. If None, generates a unique topic automatically.
            project_id: Optional project identifier. If None, generates timestamp-based ID.
        
        Returns:
            GeneratedVideo with all generated content and metadata
        """
        import time
        start_time = time.time()
        
        # Generate project ID if not provided
        if not project_id:
            project_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        self.logger.info(f"═══════════════════════════════════════════════════════════")
        self.logger.info(f"Starting video generation: Project {project_id}")
        self.logger.info(f"User: {settings.user_id} | Series: {settings.series_name}")
        self.logger.info(f"Niche: {settings.niche} | Style: {settings.visual_style}")
        self.logger.info(f"Duration: {settings.video_duration}s | Voice: {settings.voice_id}")
        self.logger.info(f"═══════════════════════════════════════════════════════════")
        
        # Create project directories
        project_dir = os.path.join(self.output_dir, project_id)
        temp_dir = os.path.join(self.temp_dir, project_id)
        images_dir = os.path.join(temp_dir, "scenes")
        os.makedirs(project_dir, exist_ok=True)
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(images_dir, exist_ok=True)
        
        try:
            # ═══════════════════════════════════════════════════════════
            # STAGE 1: Script Generation with Scene Segmentation
            # ═══════════════════════════════════════════════════════════
            self.logger.info("Stage 1: Generating script with scene breakdown...")
            
            script_data = self.script_engine.generate_script(settings, topic)
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 1.5: PROFESSIONAL QUALITY VALIDATION
            # ═══════════════════════════════════════════════════════════
            if not skip_validation:
                self.logger.info("Stage 1.5: Validating script quality and viral potential...")
                
                validation_result = self.script_engine.validate_script_quality(script_data, settings)
                
                self.logger.info(f"Script Quality Score: {validation_result['score']}/100")
                self.logger.info(f"Niche Alignment: {'✅ PASS' if validation_result['niche_alignment'] else '❌ FAIL'}")
                self.logger.info(f"Hook Strength: {validation_result['hook_strength'].upper()}")
                self.logger.info(f"Retention Triggers: {validation_result['retention_triggers']}")
                
                if validation_result['warnings']:
                    for warning in validation_result['warnings']:
                        self.logger.warning(f"⚠️ {warning}")
                
                if not validation_result['passed']:
                    error_msg = f"Script failed quality validation (Score: {validation_result['score']}/100). Issues: {', '.join(validation_result['issues'])}"
                    self.logger.error(f"❌ {error_msg}")
                    raise ValueError(error_msg)
                
                self.logger.info("✅ Script validation PASSED - proceeding with generation")
            else:
                self.logger.info("⏭️ Script validation SKIPPED (skip_validation=True)")
            
            # Optionally enhance scene descriptions
            script_data = self.script_engine.enhance_scene_descriptions(script_data, settings)
            
            # Save script
            self.script_engine.save_script(
                script_data,
                os.path.join(project_dir, "script.json")
            )
            
            self.logger.info(f"Script generated: {script_data.word_count} words, {len(script_data.scenes)} scenes")
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 2: AI Image Generation for Each Scene
            # ═══════════════════════════════════════════════════════════
            self.logger.info("Stage 2: Generating AI images for each scene...")
            
            script_data = self.image_engine.generate_scene_images(
                script_data=script_data,
                settings=settings,
                output_dir=images_dir
            )
            
            self.logger.info(f"Generated {len([s for s in script_data.scenes if s.cropped_image_path])} scene images")
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 3: Voiceover Generation
            # ═══════════════════════════════════════════════════════════
            self.logger.info("Stage 3: Generating voiceover...")
            
            voiceover_path = os.path.join(temp_dir, "voiceover.mp3")
            voiceover_data = self.tts_engine.generate_voiceover(
                script_data=script_data,
                settings=settings,
                output_path=voiceover_path
            )
            
            self.logger.info(f"Voiceover generated: {voiceover_data['duration_seconds']:.2f}s")
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 4: Video Assembly
            # ═══════════════════════════════════════════════════════════
            self.logger.info("Stage 4: Assembling video...")
            
            video_path = os.path.join(project_dir, "final_video.mp4")
            video_data = self.video_assembly_engine.assemble_video(
                script_data=script_data,
                voiceover_data=voiceover_data,
                settings=settings,
                output_path=video_path
            )
            
            self.logger.info(f"Video assembled: {video_data['duration_seconds']:.2f}s")
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 5: Thumbnail (use first scene image — no extra credits)
            # ═══════════════════════════════════════════════════════════
            thumbnail_path = None
            try:
                first_scene = script_data.scenes[0] if script_data.scenes else None
                first_image = None
                if first_scene:
                    first_image = first_scene.cropped_image_path or first_scene.image_path
                
                if first_image and os.path.exists(first_image):
                    import shutil
                    thumbnail_path = os.path.join(project_dir, "thumbnail.png")
                    shutil.copy2(first_image, thumbnail_path)
                    self.logger.info(f"Thumbnail saved from first scene: {thumbnail_path}")
                else:
                    self.logger.warning("No scene image available for thumbnail")
            except Exception as thumb_err:
                self.logger.warning(f"Failed to save thumbnail: {thumb_err}")
                thumbnail_path = None
            
            # ═══════════════════════════════════════════════════════════
            # STAGE 6: SEO Metadata Generation
            # ═══════════════════════════════════════════════════════════
            self.logger.info("Stage 6: Generating SEO metadata...")
            
            seo_metadata = self.seo_engine.generate_seo_metadata(
                script_data={'topic': script_data.topic, 'full_script': script_data.full_script},
                video_metadata={'duration': video_data['duration_seconds']},
                niche=settings.niche
            )
            
            # Save SEO metadata
            self.seo_engine.save_metadata(
                seo_metadata,
                os.path.join(project_dir, "seo_metadata.json")
            )
            
            self.logger.info(f"SEO metadata generated: {seo_metadata.get('title', 'No title')[:50]}...")
            
            # ═══════════════════════════════════════════════════════════
            # COMPLETION
            # ═══════════════════════════════════════════════════════════
            generation_time = time.time() - start_time
            
            self.logger.info(f"═══════════════════════════════════════════════════════════")
            self.logger.info(f"Video generation complete!")
            self.logger.info(f"Project ID: {project_id}")
            self.logger.info(f"Total time: {generation_time:.2f} seconds")
            self.logger.info(f"Output: {project_dir}")
            self.logger.info(f"═══════════════════════════════════════════════════════════")
            
            # Build result
            result = GeneratedVideo(
                project_id=project_id,
                user_settings=settings,
                video_path=video_path,
                thumbnail_path=thumbnail_path,
                title=seo_metadata.get('title', script_data.title),
                description=seo_metadata.get('description', ''),
                tags=seo_metadata.get('tags', []),
                hashtags=seo_metadata.get('hashtags', []),
                duration_seconds=video_data['duration_seconds'],
                scene_count=len(script_data.scenes),
                generation_time_seconds=generation_time
            )
            
            # Cleanup temp directory (scene images, voiceover chunks, etc.)
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                    self.logger.info(f"Cleaned up temp directory: {temp_dir}")
            except Exception as cleanup_err:
                self.logger.warning(f"Failed to clean temp directory: {cleanup_err}")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error during video generation: {e}")
            raise


def create_settings_from_frontend(data: Dict) -> UserSeriesSettings:
    """
    Convert frontend form data to UserSeriesSettings.
    This is called by the API when receiving a request.
    """
    return UserSeriesSettings(
        user_id=data.get('user_id', 'anonymous'),
        series_id=data.get('series_id', 'default'),
        series_name=data.get('seriesName', 'My Series'),
        series_description=data.get('description', ''),
        niche=data.get('niche', 'psychology'),
        niche_format=data.get('nicheFormat', 'storytelling'),
        visual_style=data.get('style', 'realistic'),
        voice_id=data.get('voiceId', 'male-deep'),
        music_track=data.get('musicId', 'ambient'),
        caption_style=data.get('captionStyle', 'modern-bold'),
        video_duration=int(data.get('videoDuration', 60)),
        posting_schedule=data.get('postingSchedule', 'daily'),
        posting_time=data.get('postingTime', '09:00'),
        platforms=data.get('platforms', ['youtube']),
    )


# CLI interface for testing
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate video from settings')
    parser.add_argument('--niche', default='scary-stories', help='Content niche')
    parser.add_argument('--style', default='dark-comic', help='Visual style')
    parser.add_argument('--duration', type=int, default=60, help='Video duration in seconds')
    parser.add_argument('--voice', default='male-deep', help='Voice ID')
    parser.add_argument('--topic', default=None, help='Specific topic (optional)')
    
    args = parser.parse_args()
    
    # Create settings
    settings = UserSeriesSettings(
        user_id='cli-user',
        series_id='cli-test',
        series_name='CLI Test Series',
        series_description='Test series from command line',
        niche=args.niche,
        visual_style=args.style,
        voice_id=args.voice,
        video_duration=args.duration,
    )
    
    # Generate
    generator = SaaSVideoGenerator()
    result = generator.generate_video(settings, topic=args.topic)
    
    print(f"\n✅ Video generated successfully!")
    print(f"   Path: {result.video_path}")
    print(f"   Duration: {result.duration_seconds:.2f}s")
    print(f"   Scenes: {result.scene_count}")
    print(f"   Time: {result.generation_time_seconds:.2f}s")
