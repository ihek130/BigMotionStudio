"""
Scene Image Engine - AI Image Generation for Each Scene
Generates unique AI images for every scene using DeepInfra API.
Handles centered composition for 9:16 cropping.
NO STOCK VIDEOS - Everything is dynamically generated.
"""

import os
import io
import logging
import time
import base64
import requests
from typing import Dict, List, Optional
from PIL import Image
import cv2
import numpy as np

from .models import (
    UserSeriesSettings, ScriptData, Scene, Character,
    VISUAL_STYLE_PROMPTS, NICHE_PROMPTS
)

logger = logging.getLogger(__name__)


class SceneImageEngine:
    """
    Generates AI images for each scene in the script.
    Uses DeepInfra API with centered composition for 9:16 cropping.
    """
    
    def __init__(self):
        self.deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        self.base_url = 'https://api.deepinfra.com/v1/inference'
        
        # Model configuration
        self.model = os.getenv('IMAGE_MODEL', 'black-forest-labs/FLUX-1-schnell')
        
        # Generation settings (generate in square, then crop to 9:16)
        self.generation_width = 1024
        self.generation_height = 1024
        
        # Final output dimensions (9:16 for shorts)
        self.output_width = 1080
        self.output_height = 1920
        
        # Quality settings
        self.inference_steps = 25
        self.guidance_scale = self.config.get('guidance_scale', 7.5)
        
        # Character consistency tracking
        self.character_image_cache = {}  # name -> base64 image for reference
    
    def generate_scene_images(
        self,
        script_data: ScriptData,
        settings: UserSeriesSettings,
        output_dir: str
    ) -> ScriptData:
        """
        Generate AI images for all scenes in the script.
        
        Args:
            script_data: Script with scenes and character definitions
            settings: User's series configuration
            output_dir: Directory to save generated images
        
        Returns:
            ScriptData with image paths filled in
        """
        logger.info(f"Generating {len(script_data.scenes)} scene images in {settings.visual_style} style")
        
        os.makedirs(output_dir, exist_ok=True)
        
        # Get style and niche guidance
        style_prompt = VISUAL_STYLE_PROMPTS.get(settings.visual_style, VISUAL_STYLE_PROMPTS["realistic"])
        niche_guidance = NICHE_PROMPTS.get(settings.niche, NICHE_PROMPTS["psychology"])
        
        # Build character reference dictionary
        character_refs = {c.name: c for c in script_data.characters}
        
        # Generate image for each scene
        for i, scene in enumerate(script_data.scenes):
            logger.info(f"Generating scene {scene.scene_number}/{len(script_data.scenes)}: {scene.mood}")
            
            try:
                # Build the complete prompt for this scene
                prompt = self._build_scene_prompt(
                    scene=scene,
                    character_refs=character_refs,
                    style_prompt=style_prompt,
                    niche_guidance=niche_guidance,
                    settings=settings
                )
                
                # Generate the image
                raw_image_path = os.path.join(output_dir, f"scene_{scene.scene_number:02d}_raw.png")
                success = self._generate_image(prompt, raw_image_path)
                
                if success:
                    # Crop to 9:16 aspect ratio
                    cropped_image_path = os.path.join(output_dir, f"scene_{scene.scene_number:02d}.png")
                    self._crop_to_9_16(raw_image_path, cropped_image_path)
                    
                    scene.image_path = raw_image_path
                    scene.cropped_image_path = cropped_image_path
                    
                    logger.info(f"Scene {scene.scene_number} generated successfully")
                else:
                    logger.error(f"Failed to generate scene {scene.scene_number}")
                    # Use a placeholder or retry logic here
                    
            except Exception as e:
                logger.error(f"Error generating scene {scene.scene_number}: {e}")
                continue
            
            # Small delay to avoid rate limiting
            time.sleep(0.5)
        
        return script_data
    
    def _build_scene_prompt(
        self,
        scene: Scene,
        character_refs: Dict[str, Character],
        style_prompt: str,
        niche_guidance: Dict,
        settings: UserSeriesSettings
    ) -> str:
        """Build a comprehensive prompt for scene image generation"""
        
        # Get character descriptions for this scene
        character_descriptions = []
        for char_name in scene.characters_in_scene:
            if char_name in character_refs:
                char = character_refs[char_name]
                character_descriptions.append(f"{char.name}: {char.description}")
        
        characters_text = "\n".join(character_descriptions) if character_descriptions else "No specific characters"
        
        # Build the prompt with centered composition emphasis
        prompt = f"""{style_prompt} illustration, vertical composition optimized for center-crop to 9:16 aspect ratio.

SCENE: {scene.visual_description}

CAMERA: {scene.camera_angle}
MOOD: {scene.mood}
ATMOSPHERE: {niche_guidance['mood_palette']}

CHARACTERS (if any):
{characters_text}

CRITICAL COMPOSITION RULES:
- ALL important subjects CENTERED horizontally in frame
- Characters positioned in center 60% of image width
- Head and body fully visible (no awkward cropping)
- Leave generous space on left and right edges (will be cropped)
- If multiple characters, group them CLOSE TOGETHER in center
- Background can extend to edges, but subjects MUST be centered
- Vertical layout preferred (elements stacked, not spread horizontally)

STYLE: {settings.visual_style.replace('-', ' ').title()}
- Match the {settings.visual_style} aesthetic precisely
- Consistent with previous scenes in this series

DO NOT include:
- Text or watermarks
- Real celebrities or public figures
- NSFW content
- Anything at extreme left/right edges that would be cut off
"""
        
        return prompt
    
    def _build_negative_prompt(self, settings: UserSeriesSettings) -> str:
        """Build negative prompt to avoid unwanted elements"""
        return (
            "text, watermark, signature, logo, words, letters, "
            "blurry, low quality, distorted, deformed, ugly, "
            "cropped, cut off, out of frame, "
            "celebrity, real person, politician, "
            "nsfw, nude, explicit, violent gore, "
            "split image, multiple frames, collage, "
            "wide angle, panoramic, horizontal layout"
        )
    
    def _generate_image(self, prompt: str, output_path: str) -> bool:
        """Generate image using DeepInfra API"""
        
        if not self.deepinfra_key:
            logger.error("DEEPINFRA_API_KEY not set")
            return False
        
        try:
            headers = {
                "Authorization": f"Bearer {self.deepinfra_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "prompt": prompt,
                "width": self.generation_width,
                "height": self.generation_height,
                "num_inference_steps": self.inference_steps,
                "guidance_scale": self.guidance_scale,
                "num_outputs": 1,
            }
            
            # Add negative prompt for models that support it
            negative_prompt = self._build_negative_prompt(None)
            if "flux" not in self.model.lower():
                payload["negative_prompt"] = negative_prompt
            
            response = requests.post(
                f"{self.base_url}/{self.model}",
                headers=headers,
                json=payload,
                timeout=120
            )
            
            if response.status_code != 200:
                logger.error(f"DeepInfra API error: {response.status_code} - {response.text}")
                return False
            
            result = response.json()
            
            # Handle different response formats
            if 'images' in result and len(result['images']) > 0:
                image_data = result['images'][0]
                
                # Could be base64 or URL
                if image_data.startswith('http'):
                    # Download from URL
                    img_response = requests.get(image_data)
                    image_bytes = img_response.content
                else:
                    # Base64 decode
                    # Remove data URL prefix if present
                    if ',' in image_data:
                        image_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(image_data)
                
                # Save image
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                
                return True
            
            elif 'output' in result:
                # Some models return 'output' instead of 'images'
                image_data = result['output']
                if isinstance(image_data, list):
                    image_data = image_data[0]
                
                if image_data.startswith('http'):
                    img_response = requests.get(image_data)
                    image_bytes = img_response.content
                else:
                    if ',' in image_data:
                        image_data = image_data.split(',')[1]
                    image_bytes = base64.b64decode(image_data)
                
                os.makedirs(os.path.dirname(output_path), exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(image_bytes)
                
                return True
            
            else:
                logger.error(f"Unexpected response format: {result.keys()}")
                return False
                
        except Exception as e:
            logger.error(f"Error generating image: {e}")
            return False
    
    def _crop_to_9_16(self, input_path: str, output_path: str) -> bool:
        """
        Crop image from center to 9:16 aspect ratio.
        Uses intelligent cropping to keep subjects centered.
        """
        try:
            # Load image
            img = Image.open(input_path)
            original_width, original_height = img.size
            
            # Target aspect ratio (9:16 = 0.5625)
            target_aspect = 9 / 16
            current_aspect = original_width / original_height
            
            if current_aspect > target_aspect:
                # Image is wider than 9:16, crop width from center
                new_width = int(original_height * target_aspect)
                new_height = original_height
                left = (original_width - new_width) // 2
                top = 0
                right = left + new_width
                bottom = original_height
            else:
                # Image is taller than 9:16, crop height from center
                new_width = original_width
                new_height = int(original_width / target_aspect)
                left = 0
                top = (original_height - new_height) // 2
                right = original_width
                bottom = top + new_height
            
            # Crop from center
            cropped = img.crop((left, top, right, bottom))
            
            # Resize to final output dimensions
            final = cropped.resize((self.output_width, self.output_height), Image.Resampling.LANCZOS)
            
            # Save with high quality
            final.save(output_path, quality=95)
            
            logger.info(f"Cropped {input_path} -> {output_path} ({self.output_width}x{self.output_height})")
            return True
            
        except Exception as e:
            logger.error(f"Error cropping image: {e}")
            return False
    
    def _crop_with_face_detection(self, input_path: str, output_path: str) -> bool:
        """
        Advanced cropping with face detection to ensure characters stay in frame.
        Falls back to center crop if no faces detected.
        """
        try:
            # Load with OpenCV for face detection
            img = cv2.imread(input_path)
            if img is None:
                return self._crop_to_9_16(input_path, output_path)
            
            height, width = img.shape[:2]
            
            # Try to detect faces
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, 1.1, 4)
            
            if len(faces) > 0:
                # Calculate center of all detected faces
                face_centers_x = [x + w//2 for (x, y, w, h) in faces]
                face_centers_y = [y + h//2 for (x, y, w, h) in faces]
                avg_center_x = sum(face_centers_x) // len(face_centers_x)
                avg_center_y = sum(face_centers_y) // len(face_centers_y)
                
                logger.info(f"Detected {len(faces)} face(s), centering crop on faces")
            else:
                # No faces detected, use image center
                avg_center_x = width // 2
                avg_center_y = height // 2
            
            # Calculate crop box centered on faces/characters
            target_aspect = 9 / 16
            current_aspect = width / height
            
            if current_aspect > target_aspect:
                # Crop width, center on faces
                new_width = int(height * target_aspect)
                new_height = height
                left = max(0, avg_center_x - new_width // 2)
                left = min(left, width - new_width)  # Don't go out of bounds
                top = 0
            else:
                # Crop height, center on faces
                new_width = width
                new_height = int(width / target_aspect)
                left = 0
                top = max(0, avg_center_y - new_height // 2)
                top = min(top, height - new_height)
            
            # Crop
            cropped = img[top:top+new_height, left:left+new_width]
            
            # Resize to output dimensions
            final = cv2.resize(cropped, (self.output_width, self.output_height), 
                             interpolation=cv2.INTER_LANCZOS4)
            
            # Save
            cv2.imwrite(output_path, final, [cv2.IMWRITE_JPEG_QUALITY, 95])
            
            return True
            
        except Exception as e:
            logger.error(f"Face detection crop failed, using center crop: {e}")
            return self._crop_to_9_16(input_path, output_path)
    
    def generate_thumbnail(
        self,
        script_data: ScriptData,
        settings: UserSeriesSettings,
        output_path: str
    ) -> str:
        """
        Generate a thumbnail image for the video.
        Uses the hook text and creates a compelling visual.
        """
        style_prompt = VISUAL_STYLE_PROMPTS.get(settings.visual_style, VISUAL_STYLE_PROMPTS["realistic"])
        niche_guidance = NICHE_PROMPTS.get(settings.niche, NICHE_PROMPTS["psychology"])
        
        # Get main character if any
        main_char = script_data.characters[0] if script_data.characters else None
        char_desc = main_char.description if main_char else "anonymous person"
        
        prompt = f"""{style_prompt} YouTube thumbnail, horizontal 16:9 aspect ratio.

HOOK TEXT TO REPRESENT VISUALLY: "{script_data.hook_text}"
TOPIC: {script_data.topic}

SUBJECT: {char_desc}
- Expression: shocked, concerned, or intrigued
- Looking at camera or slightly off-camera
- Close-up or medium shot
- Centered in frame

MOOD: {niche_guidance['mood_palette']}

STYLE:
- High contrast, eye-catching
- Professional thumbnail quality
- Clean composition with clear focal point
- Space for text overlay if needed

DO NOT include:
- Any text or words in the image
- Real celebrities
- Low quality or blurry elements
"""
        
        # Generate at 16:9 for thumbnail
        original_dims = (self.generation_width, self.generation_height)
        self.generation_width = 1280
        self.generation_height = 720
        
        raw_path = output_path.replace('.png', '_raw.png')
        success = self._generate_image(prompt, raw_path)
        
        # Restore dimensions
        self.generation_width, self.generation_height = original_dims
        
        if success:
            # For thumbnail, just resize to standard size (no cropping needed)
            img = Image.open(raw_path)
            img = img.resize((1280, 720), Image.Resampling.LANCZOS)
            img.save(output_path, quality=95)
            
            # Clean up raw
            if os.path.exists(raw_path):
                os.remove(raw_path)
            
            return output_path
        
        return None
