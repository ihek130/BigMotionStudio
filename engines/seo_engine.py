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
    def __init__(self, config: Dict):
        self.config = config
        self.client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.model = config.get('model', 'gpt-4.1')
    
    def generate_seo_metadata(self, script_data: Dict, video_metadata: Dict, niche: str = None) -> Dict:
        """Generate all SEO metadata"""
        logger.info("Generating SEO metadata...")
        
        topic = script_data.get('topic', '')
        script_text = script_data.get('full_script', '')
        niche = niche or 'general'
        
        # Generate title
        title = self._generate_title(topic, script_text)
        
        # Generate description
        description = self._generate_description(topic, script_text, niche)
        
        # Generate tags
        tags = self._generate_tags(topic, script_text)
        
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
    
    def _generate_title(self, topic: str, script_text: str) -> str:
        """Generate CTR-optimized title using PROVEN viral formulas"""
        rules = self.config.get('rules', {})
        max_length = rules.get('title_max_length', 70)
        title_variations = rules.get('title_variations', {})
        
        # Calculate weighted random selection (60% Jani, 25% Ramsey, 15% Psychology)
        import random
        rand = random.randint(1, 100)
        
        if rand <= 60:
            # James Jani Style (60%)
            style_type = "james_jani"
            prompt = f"""Create a YouTube video title using James Jani's PROVEN 9.4M view formula.

Topic: {topic}

Script excerpt: {script_text[:500]}

EXACT FORMULAS TO USE:
1. "The Dark Truth About [Finance Topic]"
2. "The $[Amount] [Finance Topic] Nobody Talks About"
3. "The Fake [Person/Industry]: [Revelation]"
4. "I Confronted [Financial Industry/Scammers]"
5. "The Insane World of [Finance Topic]"

Rules:
- Maximum {max_length} characters
- Use words: Dark, Truth, Fake, Insane, Exposed, Lie
- Include specific dollar amounts if relevant
- Finance/money topic ONLY
- Documentary investigation tone
- NO clickbait, just dramatic truth
- Avoid repeating the exact phrase "The Dark Truth About" if possible; vary wording while keeping the same energy.

Examples:
- "The Dark Truth About Financial Advisors"
- "The $30 Billion Retirement Scam"
- "I Confronted the Credit Card Industry"

Return only the title, nothing else."""

        elif rand <= 85:
            # Ramsey Show Style (25%)
            style_type = "ramsey_show"
            prompt = f"""Create a YouTube video title using The Ramsey Show's PROVEN 100K+ view formula.

Topic: {topic}

Script excerpt: {script_text[:500]}

EXACT FORMULAS TO USE:
1. "I Owe $[Amount] Because of [Mistake]"
2. "[Age]-Year-Old [Problem] — Here's Why"
3. "[Person] [Action] — Am I Crazy?"
4. "The IRS Says I Owe [Amount]"

Rules:
- Maximum {max_length} characters
- Use SPECIFIC dollar amounts
- Use real-life problem scenarios
- Conversational, relatable tone
- Age-based situations work great
- Finance/debt problems ONLY

Examples:
- "I Owe $180,000 in Student Loans — Here's Why"
- "35-Year-Old Living at Home — Am I Crazy?"
- "She Lost $50,000 to a Financial Guru"

Return only the title, nothing else."""

        else:
            # Identity Threat Psychology (15%)
            style_type = "identity_threat"
            prompt = f"""Create a YouTube video title using identity threat psychology.

Topic: {topic}

Script excerpt: {script_text[:500]}

Rules:
- Maximum {max_length} characters
- Challenge viewer's beliefs/identity
- Use contradiction or reversal
- Natural, readable phrasing
- Should make viewer question themselves
- Finance/money psychology focus

Examples:
- "Why Smart People Stay Broke (It's Not What You Think)"
- "You're Saving Money Wrong (Here's Why)"
- "If You Think You're Good With Money, You're Not"

Return only the title, nothing else."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.7),
                max_tokens=100
            )
            
            title = response.choices[0].message.content.strip().strip('"')
            
            # Ensure within length limit
            if len(title) > max_length:
                title = title[:max_length-3] + '...'
            
            logger.info(f"Generated {style_type} style title: {title}")
            return title
            
        except Exception as e:
            logger.error(f"Error generating title: {e}")
            return topic[:max_length]
    
    def _generate_description(self, topic: str, script_text: str, niche: str = 'general') -> str:
        """Generate video description with niche-specific hashtags"""
        rules = self.config.get('rules', {})
        desc_length = rules.get('description_length', [150, 300])
        
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
                temperature=self.config.get('temperature', 0.7),
                max_tokens=400
            )
            
            description = response.choices[0].message.content.strip()
            
            # Add niche-specific hashtags for Shorts
            niche_hashtags = self._get_niche_hashtags(niche)
            description += f"\n\n{niche_hashtags}"
            
            return description
            
        except Exception as e:
            logger.error(f"Error generating description: {e}")
            return f"Learn about {topic} and improve your financial psychology."
    
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
    
    def _generate_tags(self, topic: str, script_text: str) -> List[str]:
        """Generate relevant tags from topic/script.

        Hardcoding other channels as tags is usually low-signal and can confuse targeting.
        """
        prompt = f"""Generate 12-18 YouTube tags for a personal finance + money psychology investigation video.

Topic: {topic}

Rules:
- Tags must be relevant to THIS topic
- Mix broad + specific phrases (e.g., "bank fees", "hidden fees", "money psychology")
- Avoid unrelated creator/channel names
- No hashtags, just comma-separated tags

Return comma-separated tags only."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.config.get('temperature', 0.7),
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
            # Reasonable fallback
            base = ["personal finance", "money psychology", "financial literacy", "investing", "saving money"]
            return base
    
    def _generate_chapters(self, script_data: Dict) -> List[Dict]:
        """Generate video chapters"""
        if not self.config.get('rules', {}).get('chapters_enabled', True):
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
