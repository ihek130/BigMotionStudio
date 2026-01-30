"""
Thumbnail Engine - AI-Generated Thumbnails
Creates psychologically-triggering thumbnails with PrunaAI via DeepInfra (text included in image)
"""

import os
import random
import base64
import json
import re
from datetime import datetime, timedelta
from typing import Dict
from openai import OpenAI
from PIL import Image
import requests
import io
import logging

logger = logging.getLogger(__name__)


class ThumbnailEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.deepinfra_key = os.getenv('DEEPINFRA_API_KEY')
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))  # For text extraction
        self.base_url = 'https://api.deepinfra.com/v1/inference'

        # History-aware anti-repetition
        self.output_dir = config.get('output_dir', 'output')
        self.history_lookback_days = int(config.get('history_lookback_days', 30))
        self.history_max_projects = int(config.get('history_max_projects', 50))
        self.meta_filename = config.get('meta_filename', 'thumbnail_meta.json')
        
        # Thumbnail subject strategy: default to non-celebrity, generic subject/symbol for clarity + trust.
        self.use_influential_personalities = bool(config.get('use_influential_personalities', False))
        self.personalities = [
            {
                'name': 'Generic Subject',
                'description': (
                    'Photorealistic close-up of an anonymous adult (not a real person, not a public figure). '
                    'Natural human face, believable skin texture, realistic lighting. '
                    'DO NOT depict or resemble any real celebrity or politician.'
                ),
                'clothing': 'simple dark hoodie or neutral business casual',
                'context': 'Anonymous subject representing the viewer'
            }
        ]
        self.max_recent_personalities = 0

        # Hook rotation
        self.trigger_types = config.get(
            'trigger_types',
            [
                'identity_threat',
                'loss_leak',
                'status_contrast',
                'anxiety_avoidance',
                'control_agency',
                'reversal',
            ],
        )
        self.power_words = set(
            w.upper()
            for w in config.get(
                'power_words',
                [
                    'POOR', 'BROKE', 'FAIL', 'FAILING', 'MISTAKE', 'WRONG', 'NEVER', 'STILL', 'NOT', 'ENOUGH',
                    'WHY', 'LOST', 'STUCK', 'DREAD', 'DEBT', 'LEAK', 'LEAKING', 'SCAM', 'TRAP', 'AUTOPILOT',
                    'CONTROL', 'ANXIETY'
                ],
            )
        )
        self.avoid_repeat_power_words = bool(config.get('avoid_repeat_power_words', True))
        self.max_recent_hooks = int(config.get('max_recent_hooks', 20))
        self.tears_probability = float(config.get('tears_probability', 0.35))
        
    def generate_thumbnail(self, script_data: Dict, video_metadata: Dict, output_path: str) -> Dict:
        """Generate CTR-optimized thumbnail with Gemini 3 Pro Image Preview (high-fidelity text rendering)"""
        logger.info("Generating thumbnail with Gemini 3 Pro Image Preview...")
        
        recent = self._load_recent_thumbnail_history()

        # Select influential personality (avoiding recent repeats)
        personality = self._select_personality(recent)
        
        # Extract key emotion and concept
        emotion = self._select_emotion(script_data)
        trigger_type = self._select_trigger_type(script_data, recent)
        text_hook = self._extract_core_concept(script_data, trigger_type, recent)
        
        # Generate complete thumbnail with Gemini 3 Pro Image Preview (including text)
        image_prompt = self._create_image_prompt(text_hook, emotion, script_data.get('topic', ''), personality)
        
        success = self._generate_gemini_image(image_prompt, output_path)
        
        if not success:
            logger.warning("Gemini image generation failed, using fallback")
            return self._create_fallback_thumbnail(output_path, text_hook)
        
        logger.info(f"Thumbnail generated with text: {text_hook} at {output_path}")

        # Persist metadata for future runs (anti-repetition)
        self._save_thumbnail_meta(output_path, {
            'created_at': datetime.now().isoformat(),
            'topic': script_data.get('topic', ''),
            'hook': text_hook,
            'emotion': emotion,
            'trigger_type': trigger_type,
            'personality': personality['name'],
        })
        
        return {
            'thumbnail_path': output_path,
            'emotion': emotion,
            'concept': text_hook,
            'trigger_type': trigger_type,
            'personality': personality['name'],
            'prompt': image_prompt
        }

    def _save_thumbnail_meta(self, thumbnail_path: str, data: Dict) -> None:
        try:
            folder = os.path.dirname(thumbnail_path)
            meta_path = os.path.join(folder, self.meta_filename)
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"Failed to write thumbnail meta: {e}")

    def _normalize_hook(self, text: str) -> str:
        text = (text or '').strip().upper()
        text = re.sub(r"[\"'“”‘’]", "", text)
        text = re.sub(r"\s+", " ", text)
        return text

    def _hook_tokens(self, text: str) -> list:
        norm = self._normalize_hook(text)
        tokens = [t.strip('?!.,:;') for t in norm.split(' ') if t.strip('?!.,:;')]
        return tokens

    def _load_recent_thumbnail_history(self) -> Dict:
        """Load recent hooks/power-words/personalities from output/*/thumbnail_meta.json (best-effort)."""
        history = {
            'hooks': [],
            'power_words': set(),
            'personalities': [],
        }

        if not os.path.exists(self.output_dir):
            return history

        projects = []
        for name in os.listdir(self.output_dir):
            project_path = os.path.join(self.output_dir, name)
            if not os.path.isdir(project_path):
                continue
            meta_path = os.path.join(project_path, self.meta_filename)
            if not os.path.exists(meta_path):
                continue
            dt = None
            try:
                dt = datetime.strptime(name, '%Y%m%d_%H%M%S')
            except Exception:
                pass
            if dt is None:
                try:
                    dt = datetime.fromtimestamp(os.path.getmtime(meta_path))
                except Exception:
                    dt = datetime.now()
            projects.append((dt, meta_path))

        cutoff = datetime.now() - timedelta(days=self.history_lookback_days)
        projects = [(dt, p) for (dt, p) in projects if dt >= cutoff]
        projects.sort(key=lambda x: x[0], reverse=True)
        projects = projects[: self.history_max_projects]

        for _, meta_path in projects:
            try:
                with open(meta_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                hook = self._normalize_hook(data.get('hook', ''))
                if hook:
                    history['hooks'].append(hook)
                for tok in self._hook_tokens(hook):
                    if tok in self.power_words:
                        history['power_words'].add(tok)
                # Track personality usage
                personality = data.get('personality')
                if personality:
                    history['personalities'].append(personality)
            except Exception:
                continue

        # Limit
        history['hooks'] = history['hooks'][: self.max_recent_hooks]
        history['personalities'] = history['personalities'][: self.max_recent_personalities]
        return history

    def _select_trigger_type(self, script_data: Dict, recent: Dict) -> str:
        topic = (script_data.get('topic') or '').lower()
        # Simple heuristic to bias trigger type by topic keywords
        if any(k in topic for k in ['inflation', 'lifestyle', 'spending', 'impulse']):
            return 'loss_leak'
        if any(k in topic for k in ['anxiety', 'stress', 'worry', 'fear']):
            return 'anxiety_avoidance'
        if any(k in topic for k in ['rich', 'wealth', 'status', 'joneses']):
            return 'status_contrast'
        # Otherwise rotate randomly
        return random.choice(self.trigger_types) if self.trigger_types else 'identity_threat'
    
    def _select_personality(self, recent: Dict) -> Dict:
        """Select influential personality avoiding recent repeats"""
        # If celebrity/public-figure prompting is disabled, always return the generic subject.
        if not self.use_influential_personalities:
            return self.personalities[0]

        recent_personalities = recent.get('personalities', [])

        available = [p for p in self.personalities if p['name'] not in recent_personalities]
        if not available:
            available = self.personalities

        selected = random.choice(available)
        logger.info(f"Selected personality: {selected['name']}")
        return selected
    
    def _select_emotion(self, script_data: Dict) -> str:
        """Select primary emotion for thumbnail"""
        emotions = self.config.get('emotions', [
            'concerned', 'shocked', 'skeptical', 'disappointed', 'guilty'
        ])
        
        # Analyze script for emotion keywords
        script_text = script_data.get('full_script', '').lower()
        
        emotion_scores = {}
        emotion_keywords = {
            'concerned': ['concern', 'worry', 'problem', 'issue', 'trouble'],
            'shocked': ['shock', 'surpris', 'unbeliev', 'stun', 'discover'],
            'skeptical': ['skeptic', 'doubt', 'question', 'really', 'actually'],
            'disappointed': ['disappoint', 'unfortunate', 'sad', 'regret'],
            'guilty': ['guilt', 'hide', 'secret', 'wrong', 'shouldn\'t']
        }
        
        for emotion in emotions:
            keywords = emotion_keywords.get(emotion, [])
            score = sum(1 for keyword in keywords if keyword in script_text)
            emotion_scores[emotion] = score
        
        # Select highest scoring emotion
        if emotion_scores and max(emotion_scores.values()) > 0:
            return max(emotion_scores, key=emotion_scores.get)
        
        # Default to confused or frustrated
        return random.choice(['confused', 'frustrated', 'disappointed'])
    
    def _extract_core_concept(self, script_data: Dict, trigger_type: str, recent: Dict) -> str:
        """Extract FRAGMENTED 2-3 word hook for thumbnail text using OpenAI GPT.

        Adds anti-repetition constraints using recent hooks/power-words.
        """
        topic = script_data.get('topic', '')

        recent_hooks = recent.get('hooks', []) if isinstance(recent, dict) else []
        recent_power_words = sorted(list(recent.get('power_words', set()))) if isinstance(recent, dict) else []

        trigger_guidance = {
            'identity_threat': 'Question competence/ego. Make the viewer feel personally called out.',
            'loss_leak': 'Imply silent financial loss or leakage without saying how to fix it.',
            'status_contrast': 'Imply fake wealth vs real wealth, appearance vs reality.',
            'anxiety_avoidance': 'Money dread/avoidance/shame. The feeling of not wanting to look.',
            'control_agency': 'Loss of control/autopilot decisions. Feeling trapped by habits.',
            'reversal': 'Contradiction/reversal (“good thing” that’s actually bad).',
        }.get(trigger_type, 'Money psychology curiosity gap with tension.')
        
        # Use OpenAI GPT for reliable text extraction (no <THINK> tags)
        try:
            prompt = f"""Extract a 2-3 word FRAGMENTED hook for a YouTube thumbnail.

Topic: "{topic}"

Trigger type: {trigger_type}
Trigger guidance: {trigger_guidance}

CRITICAL RULES:
1. MUST be INCOMPLETE/FRAGMENTED (not a full sentence)
2. Should create curiosity gap (raises questions, not answers)
3. Attack ego, identity, or create tension
4. MAX 3 WORDS - shorter is better for thumbnails
5. Avoid repeating recent hooks exactly
6. Avoid reusing the same strong/pain word if possible

FRAGMENTED EXAMPLES:
✅ "STILL POOR?" - (fragment that raises question)
✅ "Smart... Broke" - (incomplete contrast)
✅ "BUT WHY?" - (pure curiosity fragment)
✅ "NOT ENOUGH" - (incomplete statement)
✅ "NEVER Rich" - (fragment of larger truth)
✅ "TOO SMART?" - (questioning fragment)

❌ BAD (too complete): "Why You're Still Poor", "Smart People Stay Poor"

RECENT HOOKS TO AVOID (do NOT repeat these exactly):
{recent_hooks[:10]}

RECENT POWER WORDS TO AVOID IF POSSIBLE:
{recent_power_words[:15]}

Return ONLY 2-3 word FRAGMENT in CAPS. Make it punchy and provocative. No explanation, just the text."""

            response = self.openai_client.chat.completions.create(
                model="gpt-4.1",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.9,
                max_tokens=15
            )
            
            concept = response.choices[0].message.content.strip().strip('"').upper()
            
            # Ensure max 3 words
            words = concept.split()
            if len(words) > 3:
                concept = ' '.join(words[:3])

            # Avoid exact repeats
            norm = self._normalize_hook(concept)
            if norm in set(recent_hooks):
                # Light mutation to break exact repeat
                concept = concept.replace('?', '').strip() + "?"

            if self.avoid_repeat_power_words and recent_power_words:
                toks = self._hook_tokens(concept)
                if any(t in set(recent_power_words) for t in toks):
                    # Not fatal, but encourages variety; keep as-is if model insisted
                    pass
            
            return concept
            
        except Exception as e:
            logger.error(f"Error extracting concept: {e}")
            return "STILL POOR?"
    
    def _generate_visual_variations(self) -> Dict:
        """Generate visual variations for thumbnail diversity (backgrounds, lighting, etc.)"""
        backgrounds = [
            'dark blue gradient',
            'deep purple bokeh',
            'warm orange blurred',
            'teal and cyan gradient',
            'dark red dramatic',
            'charcoal grey with highlights'
        ]
        
        camera_angles = [
            'straight-on eye level',
            'slight low angle looking up',
            'slight high angle looking down',
            'three-quarter angle'
        ]
        
        lighting_styles = [
            'dramatic side lighting with rim light',
            'butterfly lighting from above',
            'split lighting half shadow',
            'rembrandt lighting with triangle highlight',
            'edge lighting with backlight glow'
        ]
        
        return {
            'background': random.choice(backgrounds),
            'camera_angle': random.choice(camera_angles),
            'lighting': random.choice(lighting_styles)
        }
    
    def _create_image_prompt(self, text_hook: str, emotion: str, topic: str = '', personality: Dict = None) -> str:
        """Create CINEMATIC thumbnail prompt - James Jani documentary style with influential personalities"""
        variations = self._generate_visual_variations()
        emotion_details = self._emotion_to_description(emotion)
        
        # Use default personality if none provided (fallback)
        if personality is None:
            personality = self.personalities[0]

        # Style rotation: 60% Cinematic, 25% Ramsey, 15% Alternative
        style_rand = random.randint(1, 100)
        
        if style_rand <= 60:
            # JAMES JANI CINEMATIC STYLE (60%)
            return self._create_jani_cinematic_prompt(text_hook, emotion, personality, variations, emotion_details, topic)
        elif style_rand <= 85:
            # RAMSEY SHOW YELLOW/BLUE STYLE (25%)
            return self._create_ramsey_style_prompt(text_hook, emotion, personality, variations, emotion_details, topic)
        else:
            # NEON INVESTIGATION STYLE (15%)
            return self._create_neon_investigation_prompt(text_hook, emotion, personality, variations, emotion_details, topic)
    
    def _create_jani_cinematic_prompt(self, text_hook: str, emotion: str, personality: Dict, variations: Dict, emotion_details: str, topic: str) -> str:
        """James Jani cinematic documentary style - dark, moody, premium with influential personalities"""
        
        prompt = f"""================================
CRITICAL REQUIREMENT - TEXT MUST APPEAR IN IMAGE:
YOU MUST RENDER THE TEXT: "{text_hook}"
TEXT POSITION: Center or bottom third
TEXT SIZE: LARGE - Bold, clean, readable
TEXT STYLE: Clean white sans-serif font (Helvetica/Arial Bold), thick dark brown/black outline for depth
SPELLING: EXACTLY "{text_hook}" - spell it perfectly
VISIBILITY: Every letter fully visible, sharp and clear
================================

CINEMATIC DOCUMENTARY STYLE (James Jani):

SUBJECT CONTEXT: {personality.get('context', 'Anonymous subject')}

ULTRA-REALISTIC PHOTOGRAPHIC REQUIREMENT:
{personality['description']}
MUST BE PHOTOREALISTIC - like a high-resolution photograph
Skin pores, hair texture, eye detail all visible at 4K quality
NO cartoonish or stylized features - 100% photorealistic human face

EXPRESSION & POSE:
{emotion_details} - specifically: concerned, serious, or contemplative expression
{personality['clothing']}
Eye contact with camera OR looking slightly off-camera (documentary subject feel)
{variations['camera_angle']} with cinematic framing

LIGHTING & COLOR GRADING:
Warm cinematic lighting (2800-3500K color temperature)
Dark brown/black gradient background with subtle vignette
Moody atmosphere - like a high-budget documentary
Rembrandt or split lighting creating dimension
Rich shadows, warm highlights on face

BACKGROUND:
Dark moody gradient (dark brown to black)
OR blurred dark office/library setting
Premium, sophisticated aesthetic
Depth of field - subject sharp, background softly blurred

VISUAL ELEMENTS:
Optional: Subtle document/money symbol partially visible in corner
Premium, polished, investigative journalism feel
NOT bright or cheerful - serious financial investigation tone

IMAGE STYLE:
Photorealistic 4K cinema quality, 16:9 ratio (1280x720px)
Color graded like James Jani video
Warm dark tones (browns, dark oranges, blacks)
Professional documentary aesthetic

REMEMBER: TEXT "{text_hook}" MUST APPEAR - CLEAN, READABLE, PROFESSIONAL"""
        
        logger.info(f"James Jani style thumbnail: {emotion}, text: {text_hook}")
        return prompt
    
    def _create_ramsey_style_prompt(self, text_hook: str, emotion: str, personality: Dict, variations: Dict, emotion_details: str, topic: str) -> str:
        """Ramsey Show style - yellow/blue, trustworthy, conversational with influential personalities"""
        
        prompt = f"""================================
CRITICAL REQUIREMENT - TEXT MUST APPEAR IN IMAGE:
YOU MUST RENDER THE TEXT: "{text_hook}"
TEXT POSITION: Center or upper third
TEXT SIZE: LARGE and BOLD
TEXT STYLE: Bold sans-serif, YELLOW color (#FFD700) with dark blue (#0047AB) outline
SPELLING: EXACTLY "{text_hook}" - spell it perfectly
VISIBILITY: Every letter fully visible and clear
================================

RAMSEY SHOW STYLE:

SUBJECT CONTEXT: {personality.get('context', 'Anonymous subject')}

ULTRA-REALISTIC PHOTOGRAPHIC REQUIREMENT:
{personality['description']}
MUST BE PHOTOREALISTIC - like a high-resolution photograph
Skin pores, hair texture, eye detail all visible at high quality
NO cartoonish or stylized features - 100% photorealistic human face

EXPRESSION & POSE:
{emotion_details} - specifically: concerned, worried, or frustrated expression
{personality['clothing']}
Direct eye contact with camera (conversational feel)
{variations['camera_angle']}

LIGHTING & COLOR:
Bright, clean, trustworthy lighting
Blue gradient background (#0047AB to lighter blue)
OR split-screen style with two people facing each other
Professional but approachable aesthetic

BACKGROUND:
Bright blue gradient OR
Clean studio setting with warm blue tones
Optional: Financial charts/graphs blurred in background
Trustworthy, professional, talk-show feel

IMAGE STYLE:
Photorealistic high quality, 16:9 ratio (1280x720px)
Bright, energetic color palette (yellow + blue primary)
Clean, professional, relatable
Financial advice show aesthetic

REMEMBER: TEXT "{text_hook}" IN YELLOW WITH BLUE OUTLINE"""
        
        logger.info(f"Ramsey Show style thumbnail: {emotion}, text: {text_hook}")
        return prompt
    
    def _create_neon_investigation_prompt(self, text_hook: str, emotion: str, personality: Dict, variations: Dict, emotion_details: str, topic: str) -> str:
        """Neon investigation style - green/cyan mystery with influential personalities"""
        
        visual_contrast = self._select_visual_contrast(topic)
        
        prompt = f"""================================
CRITICAL REQUIREMENT - TEXT MUST APPEAR IN IMAGE:
YOU MUST RENDER THE TEXT: "{text_hook}"
TEXT POSITION: Bottom third
TEXT SIZE: MASSIVE and BOLD
TEXT STYLE: Neon green (#00FF41) glowing effect with dark outline
SPELLING: EXACTLY "{text_hook}" - spell it perfectly
VISIBILITY: Every letter glowing and visible
================================

NEON INVESTIGATION STYLE:

CELEBRITY CONTEXT: {personality.get('context', 'Influential public figure')}

ULTRA-REALISTIC PHOTOGRAPHIC REQUIREMENT:
{personality['description']}
MUST BE PHOTOREALISTIC - like a high-resolution photograph of the ACTUAL celebrity
Skin pores, hair texture, eye detail all visible even with dramatic lighting
NO cartoonish or stylized features - 100% photorealistic human face
Exact facial proportions and features matching the real person

EXPRESSION & POSE:
{emotion_details} - specifically: skeptical or shocked expression
{personality['clothing']}
{variations['camera_angle']}
{variations['lighting']} with neon edge lighting

LIGHTING & COLOR:
Dark background (black or very dark blue)
Neon green or cyan rim lighting on subject
High contrast, dramatic shadows
Mystery/investigation aesthetic

BACKGROUND:
Pure black OR dark gradient
{visual_contrast}
Tech/investigation vibe
Optional: Subtle financial symbols in neon

IMAGE STYLE:
Photorealistic, 16:9 ratio (1280x720px)
Neon green (#00FF41) as accent color
Dark, mysterious, investigative
Modern tech documentary feel

REMEMBER: TEXT "{text_hook}" IN GLOWING NEON GREEN"""
        
        logger.info(f"Neon investigation style thumbnail: {emotion}, text: {text_hook}")
        return prompt

    def _select_visual_contrast(self, topic: str) -> str:
        """Pick contrast element based on topic hint when available (keeps same technique, more variety)."""
        topic = (topic or '').lower()

        mapping = [
            (['inflation', 'lifestyle', 'luxury', 'status', 'jones'], [
                'faint luxury items (watch, car) blurred behind subject creating contrast',
                'ghostly rich lifestyle imagery barely visible in background',
                'blurred shopping bags and credit card silhouettes in background',
            ]),
            (['debt', 'bills', 'payment', 'loan'], [
                'blurred overdue bills and red past-due stamps in background',
                'faint debt numbers and interest-rate symbols ghosted behind subject',
            ]),
            (['scam', 'fraud', 'trap'], [
                'faint warning triangle and scammer chat bubbles blurred behind subject',
                'ghostly “too good to be true” banner barely visible in background',
            ]),
            (['invest', 'market', 'stock', 'crypto'], [
                'subtle red/green market chart bokeh lights scattered in background',
                'faint upward arrow crossed out on one side creating dissonance',
            ]),
            (['anxiety', 'stress', 'worry', 'shame', 'avoid'], [
                'blurred notification bubbles and missed-payment alerts in background',
                'faint brain icon watermark on one side with crossed-out money on other side',
            ]),
        ]

        for keys, choices in mapping:
            if any(k in topic for k in keys):
                return random.choice(choices)

        # Default variety
        contrast_elements = [
            'subtle blurred money icons and dollar signs floating in background',
            'faint brain icon watermark on one side with crossed-out money on other side',
            'blurred wealthy successful silhouette in distant background creating contrast',
            'subtle dollar sign bokeh lights scattered in background',
            'ghostly rich lifestyle imagery barely visible in background',
        ]
        return random.choice(contrast_elements)
    
    def _emotion_to_description(self, emotion: str) -> str:
        """Convert emotion to intense visual description.

        Keeps psychological intensity but avoids always-crying sameness by sampling micro-expressions.
        """
        tears = random.random() < self.tears_probability
        tear_clause = " with subtle wetness in eyes" if not tears else " with VISIBLE TEARS and slightly wet cheeks"

        intensity = random.choice(['subtle', 'strong', 'extreme'])
        if intensity == 'subtle':
            pain = "micro-tension in brow, tight jaw, restrained distress"
        elif intensity == 'strong':
            pain = "furrowed brow, tense jaw, visible stress lines, pained mouth asymmetry"
        else:
            pain = "deep forehead wrinkles, clenched facial muscles, intense anguish, heavy stress lines"

        emotion_map = {
            'confused': f"deeply confused expression{tear_clause}, {pain}, tilted head, one hand near face in uncertainty, direct eye contact",

            'regretful': f"regretful and ashamed expression{tear_clause}, {pain}, eyes slightly downcast then back to camera, hand touching forehead as if replaying a mistake",

            'frustrated': f"frustrated expression{tear_clause}, {pain}, hands near temples or gripping hair lightly, exasperated mouth tension, direct eye contact",

            'shocked': f"shocked disbelief expression{tear_clause}, {pain}, widened eyes, mouth slightly open, frozen posture, direct eye contact",

            'disappointed': f"deeply disappointed expression{tear_clause}, {pain}, defeated posture, subtle frown, hand on forehead, direct eye contact",
        }
        return emotion_map.get(
            emotion,
            f"intensely troubled expression{tear_clause}, {pain}, stressed eyes, tense mouth, direct eye contact",
        )
    
    def _generate_gemini_image(self, prompt: str, output_path: str) -> bool:
        """Generate complete thumbnail using PrunaAI/p-image via DeepInfra (exceptional text rendering)"""
        try:
            import requests
            
            logger.info("Calling DeepInfra PrunaAI/p-image API...")
            
            # DeepInfra API for PrunaAI/p-image model
            response = requests.post(
                'https://api.deepinfra.com/v1/inference/PrunaAI/p-image',
                headers={
                    'Authorization': f'Bearer {self.deepinfra_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'prompt': prompt,
                    'width': 1280,
                    'height': 720
                },
                timeout=120
            )
            
            logger.info(f"DeepInfra response status: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"DeepInfra error response: {response.text}")
                return False
            
            result = response.json()
            logger.info(f"DeepInfra response keys: {list(result.keys())}")
            
            # Extract image from response
            # DeepInfra returns image in 'images' array or 'output' field
            image_data = None
            
            if 'images' in result and len(result['images']) > 0:
                image_data = result['images'][0]
            elif 'output' in result:
                if isinstance(result['output'], list):
                    image_data = result['output'][0]
                else:
                    image_data = result['output']
            
            if image_data:
                # Handle base64 or URL
                if isinstance(image_data, str):
                    if image_data.startswith('http'):
                        # Download from URL
                        img_response = requests.get(image_data, timeout=30)
                        image = Image.open(io.BytesIO(img_response.content))
                    else:
                        # Decode base64
                        if image_data.startswith('data:image'):
                            image_data = image_data.split(',')[1]
                        image_bytes = base64.b64decode(image_data)
                        image = Image.open(io.BytesIO(image_bytes))
                    
                    # Ensure exact size
                    if image.size != (1280, 720):
                        image = image.resize((1280, 720), Image.Resampling.LANCZOS)
                    
                    # Save
                    os.makedirs(os.path.dirname(output_path), exist_ok=True)
                    image.save(output_path, 'PNG')
                    
                    logger.info("PrunaAI/p-image thumbnail via DeepInfra generated successfully")
                    return True
            
            logger.error(f"No image found in response. Full response: {result}")
            return False
            
        except Exception as e:
            logger.error(f"Error generating image via DeepInfra: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False
    
    def _create_fallback_thumbnail(self, output_path: str, text: str = "WATCH NOW") -> Dict:
        """Create simple fallback thumbnail using PIL if Gemini generation fails"""
        from PIL import ImageDraw, ImageFont
        
        try:
            # Create gradient background
            image = Image.new('RGB', (1280, 720), color=(20, 20, 40))
            draw = ImageDraw.Draw(image)
            
            # Try to load a bold font
            font = None
            for font_name in ['C:/Windows/Fonts/impact.ttf', 'C:/Windows/Fonts/arialbd.ttf', 'arial.ttf']:
                try:
                    font = ImageFont.truetype(font_name, 120)
                    break
                except:
                    continue
            
            if font is None:
                font = ImageFont.load_default()
            
            # Center the text
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (1280 - text_width) // 2
            y = (720 - text_height) // 2
            
            # Draw text with stroke
            draw.text((x, y), text, font=font, fill='white', stroke_width=4, stroke_fill='black')
            
            # Save
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            image.save(output_path, 'PNG')
            
            return {
                'thumbnail_path': output_path,
                'emotion': 'neutral',
                'concept': text,
                'prompt': 'fallback'
            }
            
        except Exception as e:
            logger.error(f"Error creating fallback thumbnail: {e}")
            return {}
