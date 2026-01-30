"""
Scene Script Engine - Dynamic Script Generation with Scene Segmentation
Generates scripts based on user's niche, style, and duration settings.
Outputs scene-by-scene breakdown with visual descriptions for AI image generation.
NO HARDCODING - Everything driven by UserSeriesSettings.
"""

import os
import json
import logging
from typing import Dict, List
from openai import OpenAI

from .models import (
    UserSeriesSettings, ScriptData, Scene, Character,
    NICHE_PROMPTS, VISUAL_STYLE_PROMPTS
)

logger = logging.getLogger(__name__)


class SceneScriptEngine:
    """
    Generates scene-segmented scripts based on user settings.
    Each script is unique to the user's niche, style, and duration.
    PROFESSIONAL-GRADE: Viral optimization + factual research + quality validation
    """
    
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
        self.temperature = 0.85
        
        # Viral pattern library (proven formulas from top creators)
        self.viral_hooks = {
            "scary-stories": [
                "Nobody believed [X] until [Y] happened",
                "The [number] rule that could save your life",
                "What they found in [location] was never explained",
                "This [thing] has been hiding the truth for years",
                "If you see this, RUN immediately"
            ],
            "true-crime": [
                "The detective noticed ONE thing everyone missed",
                "[Number] clues that solved the impossible case",
                "What the killer didn't know changed everything",
                "The evidence that was hidden for [X] years",
                "This mistake led to the breakthrough"
            ],
            "history": [
                "The day that changed [civilization] forever",
                "What they didn't teach you about [event]",
                "The [number] secrets of [historical figure]",
                "How one decision altered history",
                "The truth behind [famous event]"
            ],
            "psychology": [
                "Your brain is tricking you right now",
                "The [number]-second rule that changes everything",
                "Why successful people do this every day",
                "This psychology trick works 100% of the time",
                "What your [X] says about your personality"
            ],
            "stoic-motivation": [
                "Marcus Aurelius used this [number] times daily",
                "The Stoic secret to [outcome]",
                "What [philosopher] knew that we forgot",
                "This ancient wisdom is more relevant today",
                "The [number] Stoic principles that will transform you"
            ]
        }
        
        # Diverse topic examples per niche (10-15 examples for variety)
        self.topic_examples = {
            "scary-stories": [
                "The Night Shift Worker Who Found the Hidden Room",
                "The Doll That Moved When Nobody Was Looking",
                "The Elevator That Stopped on Floor 13",
                "The Last Message From a Missing Hiker",
                "The House That Everyone Avoids on Maple Street",
                "The Antique Mirror That Showed the Wrong Reflection",
                "The Basement Door That Should Never Be Opened",
                "The Phone Call From Your Own Number",
                "The Shadow Figure That Follows You Home",
                "The Abandoned Hospital's Final Patient",
                "The Toy Store That Comes Alive at Midnight",
                "The Painting Where the Eyes Never Blink",
                "The School Janitor Who Disappeared 20 Years Ago",
                "The Attic Recording That No One Can Explain",
                "The Camping Trip That Ended in Silence"
            ],
            "true-crime": [
                "The Detective Who Noticed What Everyone Missed",
                "The Cold Case Solved by a Grocery Receipt",
                "The Serial Killer's One Fatal Mistake",
                "The Witness Who Changed Their Story Too Late",
                "The Evidence Hidden in Plain Sight for 30 Years",
                "The Phone Call That Cracked the Case Wide Open",
                "The Neighbor Everyone Thought They Knew",
                "The DNA Match That Shocked the Town",
                "The Confession Letter Found After 15 Years",
                "The Security Footage Everyone Overlooked",
                "The Criminal Who Left One Fingerprint Too Many",
                "The Journalist Who Solved What Police Couldn't",
                "The Mistake That Led Police to the Killer",
                "The Anonymous Tip That Changed Everything",
                "The Evidence That Was Hiding in the Trash"
            ],
            "history": [
                "The Day That Changed Ancient Rome Forever",
                "The Secret Message That Prevented World War III",
                "The Explorer Who Discovered a Lost Civilization",
                "The Invention That No One Believed Would Work",
                "The Battle That Lasted Only 38 Minutes",
                "The Queen Who Ruled in Disguise",
                "The Letter That Sparked a Revolution",
                "The Ancient Technology We Can't Replicate Today",
                "The Treaty That Was Signed by Accident",
                "The Soldier Who Saved Thousands with One Decision",
                "The Lost City Found by a Satellite Image",
                "The Plague Doctor Who Knew the Truth",
                "The Assassination Plot That Almost Succeeded",
                "The Ancient Artifact That Rewrote History Books",
                "The Explorer's Final Journal Entry"
            ],
            "psychology": [
                "Why Your Brain Lies to You Every Morning",
                "The 5-Second Rule That Changes Everything",
                "What Your Handwriting Says About Your Mind",
                "The Psychology Trick That Works 100% of the Time",
                "Why You Can't Resist Checking Your Phone",
                "The Color That Actually Changes Your Mood",
                "How Your Brain Predicts the Future",
                "The Memory Trick That Photographic Learners Use",
                "Why First Impressions Are Usually Wrong",
                "The Body Language Sign That Never Lies",
                "How Your Playlist Reveals Your Personality",
                "The Psychological Reason You Procrastinate",
                "Why We Remember Bad Memories More",
                "The Thinking Pattern of Successful People",
                "How Your Brain Creates False Memories"
            ],
            "stoic-motivation": [
                "What Marcus Aurelius Did Every Single Morning",
                "The Stoic Secret to Handling Rejection",
                "Seneca's Method for Conquering Fear",
                "The 3 Stoic Principles That Will Transform You",
                "What Epictetus Taught His Students About Control",
                "The Ancient Wisdom That Beats Modern Therapy",
                "How Stoics Deal with Difficult People",
                "The Morning Routine of Roman Philosophers",
                "What Stoicism Teaches About Social Media",
                "The One Question That Changes Your Perspective",
                "How Marcus Aurelius Ruled an Empire Calmly",
                "The Stoic Approach to Modern Anxiety",
                "What Happens When You Practice Negative Visualization",
                "The Ancient Technique for Mental Clarity",
                "How to Think Like a Stoic Warrior"
            ],
            "random-fact": [
                "The Scientific Reason Octopuses Have Blue Blood",
                "Why Honey Never Expires (Even After 3000 Years)",
                "The Country Where It's Illegal to Run Out of Gas",
                "How Mantis Shrimp Can See 16 Colors (We See 3)",
                "The City That Exists in Two Time Zones Simultaneously",
                "Why Airplane Food Tastes Different at 30,000 Feet",
                "The Plant That Can Eat Mice",
                "How Long It Would Take to Drive to the Moon",
                "The Fruit That's Radioactive (And You Eat It)",
                "Why Cats Can't Taste Sweet Things",
                "The Language That Has No Word for 'Left' or 'Right'",
                "How Your Fingerprints Were Formed Before Birth",
                "The Only Letter Not in Any US State Name",
                "Why Flamingos Stand on One Leg",
                "The Organ That Keeps Growing Your Entire Life"
            ],
            "good-morals": [
                "The Stranger Who Paid It Forward 100 Times",
                "What the Homeless Man Did with $10,000",
                "The Teacher Who Changed a Student's Entire Life",
                "The Small Act of Kindness That Saved a Life",
                "Why the CEO Started Cleaning Toilets",
                "The Nurse Who Stayed After Her Shift Ended",
                "What Happened When Everyone Helped One Stranger",
                "The Child Who Taught Adults About Compassion",
                "The Letter That Was 50 Years Too Late",
                "Why the Rich Man Gave Away His Fortune",
                "The Grocery Store Clerk's Secret Mission",
                "What the Old Man Left Behind for the Town",
                "The Neighbor Who Never Asked for Thanks",
                "The Promise That Was Kept for 30 Years",
                "Why Forgiveness Changed Everything"
            ]
        }
        
        # Retention triggers (keep viewers watching)
        self.retention_patterns = [
            "But wait, it gets worse",
            "What happens next will shock you",
            "Here's where it gets interesting",
            "This is where everything changed",
            "You won't believe what happened next",
            "The [number] thing that made all the difference"
        ]
    
    def _research_true_events(self, settings: UserSeriesSettings) -> str:
        """
        Research true events/facts for niches that require factual content.
        Returns factual context or empty string for fictional niches.
        """
        factual_niches = ['true-crime', 'history', 'psychology']
        
        if settings.niche not in factual_niches:
            return ""
        
        research_prompts = {
            "true-crime": """Research a lesser-known but fascinating true crime case that:
            - Has clear evidence and resolution
            - Happened between 1950-2020
            - Has unique investigative elements
            - Is verified and documented
            Return: Case name, year, key facts, and what made it unique (3-4 sentences).""",
            
            "history": """Research a historically accurate but lesser-known event that:
            - Had significant impact
            - Occurred in documented history
            - Has interesting human elements
            - Is verifiable through historical records
            Return: Event name, year, key facts, and historical significance (3-4 sentences).""",
            
            "psychology": """Research a scientifically proven psychological phenomenon that:
            - Has peer-reviewed research backing
            - Is relevant to everyday life
            - Has been replicated in studies
            - Is from established psychology
            Return: Phenomenon name, research basis, key findings, and practical implications (3-4 sentences)."""
        }
        
        if settings.niche not in research_prompts:
            return ""
        
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a factual researcher who only provides verified, accurate information with sources."},
                    {"role": "user", "content": research_prompts[settings.niche]}
                ],
                temperature=0.3,  # Lower temperature for factual accuracy
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.warning(f"Failed to research true events: {e}")
            return ""
    
    def generate_script(self, settings: UserSeriesSettings, topic: str = None) -> ScriptData:
        """
        Generate a complete script with scene segmentation.
        
        Args:
            settings: User's series configuration
            topic: Optional specific topic. If None, generates based on niche.
        
        Returns:
            ScriptData with full script, characters, and scene breakdown
        """
        logger.info(f"Generating script for niche: {settings.niche}, style: {settings.visual_style}, duration: {settings.video_duration}s")
        
        # Get niche-specific guidance
        niche_guidance = NICHE_PROMPTS.get(settings.niche, NICHE_PROMPTS["psychology"])
        style_guidance = VISUAL_STYLE_PROMPTS.get(settings.visual_style, VISUAL_STYLE_PROMPTS["realistic"])
        
        # Calculate targets
        word_range = settings.get_word_count_target()
        scene_range = settings.get_scene_count_range()
        
        # Generate topic if not provided
        if not topic:
            topic = self._generate_topic(settings, niche_guidance)
        
        logger.info(f"Topic: {topic}")
        
        # Generate the complete script with scene breakdown
        script_response = self._generate_script_with_scenes(
            settings=settings,
            topic=topic,
            niche_guidance=niche_guidance,
            style_guidance=style_guidance,
            word_range=word_range,
            scene_range=scene_range
        )
        
        # Parse and validate the response
        script_data = self._parse_script_response(script_response, topic, settings)
        
        logger.info(f"Script generated: {script_data.word_count} words, {len(script_data.scenes)} scenes")
        
        return script_data
    
    def _generate_topic(self, settings: UserSeriesSettings, niche_guidance: Dict) -> str:
        """Generate a viral topic based on the user's niche"""
        import random
        
        # Get research for factual niches
        factual_research = self._research_true_events(settings)
        research_context = f"\n\nFACTUAL RESEARCH (must be incorporated):\n{factual_research}" if factual_research else ""
        
        # Get viral hook patterns for this niche
        hook_patterns = self.viral_hooks.get(settings.niche, self.viral_hooks.get("psychology", []))
        patterns_text = "\n- ".join(hook_patterns)
        
        # Get diverse examples for this niche (randomize to show variety)
        topic_examples = self.topic_examples.get(settings.niche, self.topic_examples.get("psychology", []))
        # Show 5 random examples to prevent pattern repetition
        random_examples = random.sample(topic_examples, min(5, len(topic_examples)))
        examples_text = "\n- ".join(random_examples)
        
        prompt = f"""Generate ONE unique and viral video topic for the {settings.niche.replace('-', ' ')} niche.

⚠️ IMPORTANT: The user's series is configured with:
- Niche: {settings.niche.replace('-', ' ')} ← ALL videos must stay in this niche
- Visual Style: {settings.visual_style.replace('-', ' ')} ← ALL videos use this art style

This ensures consistency across all videos in their series.

VIRAL HOOK PATTERNS (use these formulas):
- {patterns_text}{research_context}

NICHE CONTEXT:
- Tone: {niche_guidance['tone']}
- Typical settings: {niche_guidance['setting_examples']}

EXAMPLE TOPICS (for inspiration only - create something NEW and different):
- {examples_text}

⚠️ THESE ARE JUST EXAMPLES - DO NOT COPY THEM!
Your topic should be completely original and different from these examples.
Use different settings, different angles, different story hooks.
Be creative and unique while staying within the {settings.niche} niche.

REQUIREMENTS:
1. Must be engaging and create immediate curiosity
2. Should work perfectly for a {settings.video_duration}-second video
3. Clear story hook or interesting angle
4. Not too broad or too narrow
5. MUST be unique and different from the examples above
6. Use viral pattern formulas to maximize engagement
7. MUST stay within the {settings.niche} niche (don't mix niches!)

FORMAT: Return ONLY the topic title (10-15 words max), nothing else.
"""
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,  # High temperature for creativity
            max_tokens=50
        )
        
        topic = response.choices[0].message.content.strip().strip('"')
        
        logger.info(f"Generated unique topic: {topic}")
        
        return topic
    
    def _generate_script_with_scenes(
        self,
        settings: UserSeriesSettings,
        topic: str,
        niche_guidance: Dict,
        style_guidance: str,
        word_range: tuple,
        scene_range: tuple
    ) -> Dict:
        """Generate the complete script with scene breakdown"""
        import random
        
        # Determine format based on niche
        is_storytelling = settings.niche_format == "storytelling"
        
        # Randomize setting selection to avoid repetition
        # Split settings into list and pick a random subset
        all_settings = niche_guidance['setting_examples'].split(', ')
        # Use 2-3 random settings instead of all 4 to add variety
        selected_settings = random.sample(all_settings, min(random.randint(2, 3), len(all_settings)))
        randomized_settings = ', '.join(selected_settings)
        
        # Get factual research for this topic if needed
        factual_research = self._research_true_events(settings)
        research_section = f"""
═══════════════════════════════════════════════════════════
FACTUAL RESEARCH (MUST USE - THIS IS VERIFIED):
═══════════════════════════════════════════════════════════
{factual_research}

⚠️ CRITICAL: This script MUST be based on these true facts.
Do not deviate from verified information.
""" if factual_research else """
═══════════════════════════════════════════════════════════
⚠️ CREATIVE STORYTELLING ALLOWED:
═══════════════════════════════════════════════════════════
This is {settings.niche} - create an engaging fictional story.
Make it feel real but it can be creative/dramatized.
"""
        
        # Get retention triggers
        retention_examples = "\n- ".join(self.retention_patterns[:3])
        
        prompt = f"""You are an expert viral short-form video scriptwriter specializing in {settings.niche.replace('-', ' ')}.

Generate a {settings.video_duration}-second VIRAL video script about: "{topic}"
{research_section}

═══════════════════════════════════════════════════════════
CONTENT SETTINGS (FROM USER - MUST MATCH):
═══════════════════════════════════════════════════════════
• Niche: {settings.niche.replace('-', ' ').title()} ⚠️ MUST STAY IN THIS NICHE
• Format: {settings.niche_format}
• Visual Style: {settings.visual_style.replace('-', ' ').title()}
• Video Duration: {settings.video_duration} seconds

═══════════════════════════════════════════════════════════
NICHE-SPECIFIC GUIDANCE:
═══════════════════════════════════════════════════════════
• Tone: {niche_guidance['tone']}
• Suggested Settings (feel free to use your own creative settings too): {randomized_settings}
• Character Types: {niche_guidance['character_types']}
• Visual Mood: {niche_guidance['mood_palette']}

⚠️ NOTE: These settings are just suggestions - be creative with your location choices!

═══════════════════════════════════════════════════════════
VISUAL STYLE GUIDANCE:
═══════════════════════════════════════════════════════════
{style_guidance}

═══════════════════════════════════════════════════════════
VIRAL OPTIMIZATION (CRITICAL FOR SUCCESS):
═══════════════════════════════════════════════════════════
1. HOOK (0-3 sec): Start with a pattern-interrupt statement that creates immediate curiosity
   - Use numbers, controversy, or bold claims
   - Examples: "Nobody knows this..." "The truth about..." "What they don't tell you..."

2. RETENTION TRIGGERS (throughout): Insert curiosity gaps every 10-15 seconds
   - Examples:
   - {retention_examples}

3. STORY STRUCTURE:
   - Opening: Bold hook that creates curiosity
   - Middle: Build tension with reveals and surprises  
   - Climax: Deliver the payoff
   - Close: Call-to-action or thought-provoking question

4. PACING: Rapid scene changes (3-5 sec each) to maintain attention

5. WORD CHOICE: Use active, emotional language. Avoid passive voice.

6. VOICEOVER EXPRESSIVENESS:
   - Use punctuation for dramatic effect: ellipses (...) for suspense, question marks (?) for mystery
   - Add emphasis with exclamation marks for shock/surprise
   - Vary sentence length: short punchy sentences for tension, longer ones for explanation
   - Use rhetorical questions to engage viewers
   - For scary-stories: Build suspense with pacing like "It was quiet... too quiet."

═══════════════════════════════════════════════════════════
SCRIPT REQUIREMENTS:
═══════════════════════════════════════════════════════════
1. TARGET WORD COUNT: {word_range[0]}-{word_range[1]} words
2. SCENE COUNT: {scene_range[0]}-{scene_range[1]} scenes (each scene 3-5 seconds)
3. HOOK: First 3 seconds must grab attention immediately
4. PACING: Each scene should be visually distinct
5. CHARACTER CONSISTENCY: If characters appear, describe them ONCE in detail, then reference by name
6. NICHE VALIDATION: Script must clearly belong to {settings.niche} niche
7. NARRATION STYLE: Write narration with natural speech patterns - use pauses (...), questions (?), and emphasis (!) for dramatic voiceover

═══════════════════════════════════════════════════════════
SCENE VISUAL RULES (CRITICAL FOR AI IMAGE GENERATION):
═══════════════════════════════════════════════════════════
Each scene's visual_description must:
• Describe what should be SHOWN (not just what's narrated)
• Include character positions and expressions
• Specify camera angle (close-up, medium, wide)
• Match the {settings.visual_style} art style
• IMPORTANT: Describe characters CENTERED in frame
• IMPORTANT: For 1-2 characters, they should be close together in center
• IMPORTANT: Leave space around edges (will be cropped to 9:16)

═══════════════════════════════════════════════════════════
OUTPUT FORMAT (JSON):
═══════════════════════════════════════════════════════════
Return a valid JSON object with this exact structure:

{{
  "title": "Video title (50-70 chars)",
  "hook_text": "2-3 word thumbnail hook in CAPS",
  "full_script": "Complete narration script as continuous text",
  "characters": [
    {{
      "name": "Character Name",
      "description": "Detailed visual description for AI: age, gender, clothing, distinctive features, expression style",
      "role": "protagonist/antagonist/narrator/supporting"
    }}
  ],
  "scenes": [
    {{
      "scene_number": 1,
      "duration": 4,
      "narration": "What is spoken during this scene",
      "visual_description": "Detailed description of what should be SHOWN. Include: setting, character positions, camera angle, mood, lighting. Remember {settings.visual_style} style.",
      "characters_in_scene": ["Character Name"],
      "camera_angle": "close-up/medium shot/wide shot",
      "mood": "suspenseful/hopeful/dark/tense/calm/etc"
    }}
  ]
}}

IMPORTANT:
- Return ONLY valid JSON, no markdown code blocks
- Ensure all scenes together cover the full script
- Scene durations should add up to approximately {settings.video_duration} seconds
- Characters must be described identically across all their scenes
"""

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a scriptwriter who outputs only valid JSON. No explanations, no markdown, just pure JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=self.temperature,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)
    
    def _parse_script_response(self, response: Dict, topic: str, settings: UserSeriesSettings) -> ScriptData:
        """Parse the GPT response into ScriptData"""
        
        # Parse characters
        characters = []
        for char_data in response.get('characters', []):
            characters.append(Character(
                name=char_data.get('name', 'Narrator'),
                description=char_data.get('description', ''),
                role=char_data.get('role', 'narrator'),
            ))
        
        # Parse scenes
        scenes = []
        for scene_data in response.get('scenes', []):
            scenes.append(Scene(
                scene_number=scene_data.get('scene_number', len(scenes) + 1),
                duration=float(scene_data.get('duration', 4)),
                narration=scene_data.get('narration', ''),
                visual_description=scene_data.get('visual_description', ''),
                characters_in_scene=scene_data.get('characters_in_scene', []),
                camera_angle=scene_data.get('camera_angle', 'medium shot'),
                mood=scene_data.get('mood', 'neutral'),
            ))
        
        # Calculate timestamps
        current_time = 0
        for scene in scenes:
            scene.start_time = current_time
            scene.end_time = current_time + scene.duration
            current_time = scene.end_time
        
        # Build ScriptData
        full_script = response.get('full_script', '')
        
        return ScriptData(
            topic=topic,
            title=response.get('title', topic),
            full_script=full_script,
            word_count=len(full_script.split()),
            estimated_duration=sum(s.duration for s in scenes),
            characters=characters,
            scenes=scenes,
            hook_text=response.get('hook_text', 'WATCH THIS'),
        )
    
    def save_script(self, script_data: ScriptData, output_path: str) -> None:
        """Save script data to JSON file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        # Convert dataclasses to dict
        data = {
            'topic': script_data.topic,
            'title': script_data.title,
            'full_script': script_data.full_script,
            'word_count': script_data.word_count,
            'estimated_duration': script_data.estimated_duration,
            'hook_text': script_data.hook_text,
            'characters': [
                {
                    'name': c.name,
                    'description': c.description,
                    'role': c.role,
                }
                for c in script_data.characters
            ],
            'scenes': [
                {
                    'scene_number': s.scene_number,
                    'duration': s.duration,
                    'narration': s.narration,
                    'visual_description': s.visual_description,
                    'characters_in_scene': s.characters_in_scene,
                    'camera_angle': s.camera_angle,
                    'mood': s.mood,
                    'start_time': s.start_time,
                    'end_time': s.end_time,
                }
                for s in script_data.scenes
            ],
        }
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        # Also save plain text script
        txt_path = output_path.replace('.json', '.txt')
        with open(txt_path, 'w', encoding='utf-8') as f:
            f.write(script_data.full_script)
        
        logger.info(f"Script saved to {output_path}")
    
    def enhance_scene_descriptions(self, script_data: ScriptData, settings: UserSeriesSettings) -> ScriptData:
        """
        Enhance scene descriptions with more specific visual details
        for better AI image generation.
        """
        style_guidance = VISUAL_STYLE_PROMPTS.get(settings.visual_style, VISUAL_STYLE_PROMPTS["realistic"])
        niche_guidance = NICHE_PROMPTS.get(settings.niche, NICHE_PROMPTS["psychology"])
        
        # Build character reference string
        char_refs = "\n".join([
            f"- {c.name}: {c.description}"
            for c in script_data.characters
        ])
        
        enhanced_scenes = []
        
        for scene in script_data.scenes:
            prompt = f"""Enhance this scene description for AI image generation.

ORIGINAL DESCRIPTION:
{scene.visual_description}

SCENE CONTEXT:
- Narration: "{scene.narration}"
- Characters present: {', '.join(scene.characters_in_scene)}
- Camera angle: {scene.camera_angle}
- Mood: {scene.mood}

CHARACTER REFERENCES (must match exactly):
{char_refs}

VISUAL STYLE: {settings.visual_style}
Style details: {style_guidance}

NICHE MOOD: {niche_guidance['mood_palette']}

═══════════════════════════════════════════════════════════
CRITICAL REQUIREMENTS:
═══════════════════════════════════════════════════════════
1. Characters must be CENTERED in the frame (image will be cropped to 9:16)
2. If multiple characters, they should be CLOSE TOGETHER in center
3. Important elements should NOT be at extreme edges
4. Match the {settings.visual_style} art style exactly
5. Include lighting, atmosphere, and color palette
6. Keep character appearances CONSISTENT with their descriptions

Return ONLY the enhanced visual description (2-3 sentences), nothing else.
"""
            
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.7,
                    max_tokens=200
                )
                
                scene.visual_description = response.choices[0].message.content.strip()
            except Exception as e:
                logger.warning(f"Failed to enhance scene {scene.scene_number}: {e}")
            
            enhanced_scenes.append(scene)
        
        script_data.scenes = enhanced_scenes
        return script_data
    
    def validate_script_quality(self, script_data: ScriptData, settings: UserSeriesSettings) -> Dict[str, any]:
        """
        Validate script quality and viral potential.
        Returns validation results with pass/fail and recommendations.
        """
        issues = []
        warnings = []
        score = 100
        
        # 1. Check niche alignment
        niche_keywords = {
            "scary-stories": ["dark", "night", "mysterious", "terrifying", "horror", "fear", "haunted", "shadow"],
            "true-crime": ["detective", "case", "evidence", "crime", "investigation", "suspect", "victim"],
            "history": ["ancient", "century", "historical", "war", "empire", "civilization", "year"],
            "psychology": ["brain", "mind", "behavior", "psychological", "study", "research", "mental"],
            "stoic-motivation": ["stoic", "wisdom", "philosophy", "discipline", "virtue", "Marcus", "Seneca"],
            "random-fact": ["fact", "know", "discover", "learn", "secret", "truth"],
            "good-morals": ["lesson", "moral", "kind", "help", "good", "compassion", "wisdom"]
        }
        
        niche_keys = niche_keywords.get(settings.niche, [])
        script_lower = script_data.full_script.lower()
        keyword_matches = sum(1 for kw in niche_keys if kw in script_lower)
        
        if keyword_matches == 0:
            issues.append(f"Script doesn't match {settings.niche} niche - no relevant keywords found")
            score -= 30
        elif keyword_matches < 2:
            warnings.append(f"Weak niche alignment - only {keyword_matches} keyword matches")
            score -= 10
        
        # 2. Check hook strength (first 20 words)
        first_20_words = " ".join(script_data.full_script.split()[:20]).lower()
        hook_triggers = ["never", "nobody", "secret", "truth", "shocking", "hidden", "what", "how", "why", "the"]
        has_strong_hook = any(trigger in first_20_words for trigger in hook_triggers)
        
        if not has_strong_hook:
            warnings.append("Opening hook could be stronger - consider using curiosity triggers")
            score -= 15
        
        # 3. Check word count
        target_min, target_max = settings.get_word_count_target()
        if script_data.word_count < target_min * 0.8:
            issues.append(f"Script too short: {script_data.word_count} words (target: {target_min}-{target_max})")
            score -= 20
        elif script_data.word_count > target_max * 1.2:
            issues.append(f"Script too long: {script_data.word_count} words (target: {target_min}-{target_max})")
            score -= 15
        
        # 4. Check scene count
        scene_min, scene_max = settings.get_scene_count_range()
        if len(script_data.scenes) < scene_min:
            warnings.append(f"Too few scenes: {len(script_data.scenes)} (recommended: {scene_min}-{scene_max})")
            score -= 10
        elif len(script_data.scenes) > scene_max * 1.5:
            warnings.append(f"Too many scenes: {len(script_data.scenes)} (recommended: {scene_min}-{scene_max})")
            score -= 10
        
        # 5. Check for retention triggers
        retention_words = ["but", "however", "wait", "shocking", "surprising", "incredible", "believe"]
        retention_count = sum(1 for word in retention_words if word in script_lower)
        
        if retention_count < 2:
            warnings.append("Low retention trigger count - script may not hold attention")
            score -= 10
        
        # 6. Check scene descriptions quality
        scenes_missing_descriptions = [s.scene_number for s in script_data.scenes if len(s.visual_description) < 50]
        if scenes_missing_descriptions:
            warnings.append(f"Scenes {scenes_missing_descriptions} have weak visual descriptions")
            score -= 5
        
        # Determine pass/fail
        passed = len(issues) == 0 and score >= 60
        
        return {
            "passed": passed,
            "score": max(0, score),
            "issues": issues,
            "warnings": warnings,
            "niche_alignment": keyword_matches >= 2,
            "hook_strength": "strong" if has_strong_hook else "weak",
            "word_count_valid": target_min * 0.8 <= script_data.word_count <= target_max * 1.2,
            "retention_triggers": retention_count
        }
