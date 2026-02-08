"""
SEO Engine - YouTube SEO Optimization
Generates titles, descriptions, tags, and chapters
"""

import os
import json
from typing import Dict, List
from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class SEOEngine:
    def __init__(self):
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = os.getenv('OPENAI_MODEL', 'gpt-4o')
    
    def generate_seo_metadata(self, script_data: Dict, video_metadata: Dict, niche: str = None) -> Dict:
        """Generate all SEO metadata"""
        logger.info("Generating SEO metadata...")
        
        topic = script_data.get('topic', '')
        script_text = script_data.get('full_script', '')
        niche = niche or 'general'
        
        # Generate title
        title = self._generate_title(topic, script_text, niche)
        
        # Generate description
        description = self._generate_description(topic, script_text, niche)
        
        # Generate tags
        tags = self._generate_tags(topic, script_text, niche)
        
        # Generate chapters
        chapters = self._generate_chapters(script_data)
        
        metadata = {
            'title': title,
            'description': description,
            'tags': tags,
            'chapters': chapters
        }
        
        logger.info("SEO metadata generated")
        return metadata
    
    def _get_niche_label(self, niche: str) -> str:
        """Get human-readable niche label for prompts."""
        labels = {
            'scary-stories': 'horror and scary stories',
            'true-crime': 'true crime and mystery',
            'history': 'history and historical events',
            'psychology': 'psychology and human behavior',
            'stoic-motivation': 'stoic philosophy and motivation',
            'random-fact': 'interesting facts and trivia',
            'good-morals': 'moral lessons and inspiration',
        }
        return labels.get(niche, niche.replace('-', ' '))
    
    def _generate_title(self, topic: str, script_text: str, niche: str = 'general') -> str:
        """Generate CTR-optimized title using viral formulas adapted to the niche"""
        max_length = 70
        niche_label = self._get_niche_label(niche)
        
        prompt = f"""Create a YouTube Shorts title that maximizes click-through rate.

Niche/Genre: {niche_label}
Topic: {topic}
Script excerpt: {script_text[:500]}

Rules:
- Maximum {max_length} characters
- Use curiosity gap, dramatic tension, or identity challenge
- MUST be relevant to the "{niche_label}" niche — do NOT reference unrelated topics
- Use power words appropriate for this niche (e.g., shocking, untold, hidden, secret, terrifying, mind-blowing)
- No clickbait, just dramatic truth
- Vary phrasing — avoid repetitive sentence structures
- Return ONLY the title, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=100
            )
            
            title = response.choices[0].message.content.strip().strip('"')
            
            # Ensure within length limit
            if len(title) > max_length:
                title = title[:max_length-3] + '...'
            
            logger.info(f"Generated title for niche '{niche}': {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return topic[:max_length]
    
    def _generate_description(self, topic: str, script_text: str, niche: str = 'general') -> str:
        """Generate video description with niche-specific hashtags"""
        rules = {}
        desc_length = [150, 300]
        
        prompt = f"""Create a YouTube video description for this video.

Topic: {topic}

Script excerpt: {script_text[:800]}

Rules:
- Length: {desc_length[0]}-{desc_length[1]} characters
- Natural sentences with semantic keywords
- Hint at the main insight without spoiling
- Include 1-2 timestamps for key moments
- No spammy keywords
- Professional tone

Structure:
1. Hook sentence (what the video reveals)
2. Context/problem setup
3. What viewers will learn
4. Optional: Timestamps

Return only the description text."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=400
            )
            
            description = response.choices[0].message.content.strip()
            
            # Add niche-specific hashtags for Shorts
            niche_hashtags = self._get_niche_hashtags(niche)
            description += f"\n\n{niche_hashtags}"
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            niche_label = self._get_niche_label(niche)
            return f"Discover fascinating insights about {topic}. #Shorts #{niche_label.replace(' ', '')}"
    
    def _get_niche_hashtags(self, niche: str) -> str:
        """Get niche-specific hashtags for Shorts"""
        hashtag_map = {
            'scary-stories': '#Shorts #HorrorStories #ScaryStories #TrueHorror #CreepyTales #ParanormalStories #HorrorShorts #ScaryShorts',
            'true-crime': '#Shorts #TrueCrime #CrimeStories #TrueCrimeStories #Mystery #Investigation #CrimeShorts #TrueCrimeShorts',
            'history': '#Shorts #History #HistoryFacts #HistoricalEvents #HistoryShorts #LearnHistory #HistoryLessons',
            'psychology': '#Shorts #Psychology #MindFacts #HumanBehavior #PsychologyFacts #MentalHealth #PsychologyShorts',
            'stoic-motivation': '#Shorts #Motivation #Stoicism #StoicPhilosophy #Mindset #SelfImprovement #MotivationalShorts #StoicWisdom',
            'random-fact': '#Shorts #Facts #DidYouKnow #Trivia #InterestingFacts #AmazingFacts #FactsShorts #LearnSomethingNew',
            'good-morals': '#Shorts #Morals #LifeLessons #Wisdom #Inspiration #Values #MoralStories #InspirationalShorts'
        }
        return hashtag_map.get(niche, '#Shorts #Viral #Trending #Entertainment')
    
    def _generate_tags(self, topic: str, script_text: str, niche: str = 'general') -> List[str]:
        """Generate relevant tags from topic/script, adapted to the niche."""
        niche_label = self._get_niche_label(niche)
        
        prompt = f"""Generate 12-18 YouTube tags for a {niche_label} video.

Topic: {topic}

Rules:
- Tags must be relevant to THIS topic and the "{niche_label}" niche
- Mix broad + specific phrases
- Avoid unrelated creator/channel names
- No hashtags, just comma-separated tags

Return comma-separated tags only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7,
                max_tokens=120
            )

            text = response.choices[0].message.content.strip()
            tags = [t.strip().strip('"') for t in text.split(',') if t.strip()]
            # De-dupe while preserving order
            seen = set()
            out = []
            for t in tags:
                key = t.lower()
                if key in seen:
                    continue
                seen.add(key)
                out.append(t)
            out = out[:20]
            logger.info(f"Generated {len(out)} tags")
            return out

        except Exception as e:
            logger.error(f"Error generating tags: {e}")
            # Niche-aware fallback
            fallback_map = {
                'scary-stories': ["scary stories", "horror", "creepy", "paranormal", "true scary stories"],
                'true-crime': ["true crime", "crime stories", "mystery", "investigation", "unsolved cases"],
                'history': ["history", "historical events", "world history", "history facts", "learn history"],
                'psychology': ["psychology", "human behavior", "mind facts", "psychology facts", "mental health"],
                'stoic-motivation': ["stoicism", "motivation", "self improvement", "philosophy", "mindset"],
                'random-fact': ["facts", "did you know", "trivia", "interesting facts", "amazing facts"],
                'good-morals': ["life lessons", "moral stories", "inspiration", "wisdom", "values"],
            }
            return fallback_map.get(niche, ["shorts", "viral", "trending", "entertainment", "facts"])
    
    def _generate_chapters(self, script_data: Dict) -> List[Dict]:
        """Generate video chapters"""
        if not True:  # chapters always enabled
            return []
        
        timed_script = script_data.get('timed_script', [])
        if not timed_script:
            return []
        
        # Identify natural chapter breaks
        sections = script_data.get('sections', {})
        
        chapters = []
        
        # Intro (hook + open loop)
        if sections.get('hook'):
            chapters.append({
                'time': '0:00',
                'time_seconds': 0,
                'title': 'The Problem'
            })
        
        # Main content
        body_start = sum([
            len(sections.get('hook', [])),
            len(sections.get('open_loop', []))
        ])
        
        if body_start < len(timed_script):
            body_time = timed_script[body_start]['start_time']
            chapters.append({
                'time': self._seconds_to_timestamp(body_time),
                'time_seconds': int(body_time),
                'title': 'Why This Happens'
            })
        
        # Resolution
        if sections.get('resolution'):
            resolution_start = len(timed_script) - len(sections['resolution'])
            if resolution_start > 0 and resolution_start < len(timed_script):
                resolution_time = timed_script[resolution_start]['start_time']
                chapters.append({
                    'time': self._seconds_to_timestamp(resolution_time),
                    'time_seconds': int(resolution_time),
                    'title': 'What This Means'
                })
        
        return chapters
    
    def _seconds_to_timestamp(self, seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes}:{secs:02d}"
    
    def save_metadata(self, metadata: Dict, output_path: str):
        """Save SEO metadata to file"""
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, indent=2, ensure_ascii=False)
        
        logger.info(f"SEO metadata saved to {output_path}")
