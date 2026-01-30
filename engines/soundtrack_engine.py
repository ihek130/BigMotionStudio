"""
Soundtrack Engine - Emotion-Matched Background Music
Selects music based on psychological tone and emotion
"""

import os
import json
import random
import requests
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)


class SoundtrackEngine:
    def __init__(self, config: Dict):
        self.config = config
        self.pixabay_api_key = os.getenv('PIXABAY_API_KEY')
        
        # Music ID to file mapping (matches frontend selection)
        self.music_files = {
            'dark-suspense': 'dark-tension-mystery-ambient-electronic-373332.mp3',
            'upbeat-energy': 'trailer-rising-tension-heartbeat-amp-clocks-400971.mp3',
            'chill-vibes': 'suspenseful-ambient-soundscape-360821.mp3',
            'epic-adventure': 'terrifying-building-atmosphere-pulsing-noise-amp-orchestra-400974.mp3',
            'ambient-space': 'ambient-space-arpeggio-350710.mp3',
            'thriller-tension': 'building-thriller-tension-amp-clocks-400973.mp3',
            'horror-ambience': 'pulse-of-terror-intense-horror-ambience-360839.mp3',
            'blood-woodlands': 'shadow-of-the-blood-thirsty-woodlands-250736.mp3',
            'none': None
        }
        
        # Emotion to music mapping
        self.emotion_keywords = {
            'shame': ['sad', 'melancholic', 'emotional', 'dark'],
            'regret': ['melancholic', 'sad', 'thoughtful', 'emotional'],
            'tension': ['tense', 'suspense', 'dark', 'dramatic'],
            'realization': ['hopeful', 'uplifting', 'soft', 'inspiring'],
            'frustration': ['dark', 'tense', 'dramatic'],
            'confusion': ['mysterious', 'ambient', 'thoughtful'],
            'calm': ['calm', 'peaceful', 'ambient', 'relaxing'],
            'neutral': ['ambient', 'background', 'soft']
        }
    
    def find_soundtrack(self, script_data: Dict, output_dir: str, user_music_id: str = None) -> Dict:
        """Find emotion-matched soundtrack from local files or use user selection"""
        logger.info("Finding soundtrack from local music library...")
        
        # If user selected a specific music track, use that
        if user_music_id and user_music_id != 'none':
            logger.info(f"User selected music: {user_music_id}")
            music_file = self.music_files.get(user_music_id)
            if music_file:
                music_path = os.path.join('assets/music', music_file)
                if os.path.exists(music_path):
                    try:
                        from pydub import AudioSegment
                        audio = AudioSegment.from_file(music_path)
                        duration = len(audio) / 1000.0
                    except:
                        duration = 180
                    
                    return {
                        'music_path': music_path,
                        'emotion': 'user-selected',
                        'track_id': user_music_id,
                        'track_name': music_file,
                        'duration': duration,
                        'source': 'user-selected'
                    }
        
        # If no music selected or 'none'
        if user_music_id == 'none':
            logger.info("User selected no music")
            return self._get_fallback_music()
        
        # Otherwise, detect emotion and auto-select
        # Determine primary emotion from script
        emotion = self._detect_primary_emotion(script_data)
        logger.info(f"Detected primary emotion: {emotion}")
        
        # Always use local music
        local_music = self._get_local_music(emotion)
        if local_music:
            logger.info(f"Using local music: {local_music['track_name']}")
            return local_music
        
        # If no emotion match, pick the best available track
        logger.info("No exact emotion match, selecting best available track...")
        fallback_music = self._get_best_local_track()
        if fallback_music:
            logger.info(f"Using fallback local music: {fallback_music['track_name']}")
            return fallback_music
        
        logger.warning("No local music found, using silent mode")
        return self._get_fallback_music()
    
    def _detect_primary_emotion(self, script_data: Dict) -> str:
        """Detect primary emotion from script"""
        script_text = script_data.get('full_script', '').lower()
        
        # Emotion keywords to detect
        emotion_patterns = {
            'shame': ['shame', 'embarrass', 'humiliat', 'ashamed'],
            'regret': ['regret', 'mistake', 'should have', 'wish', 'if only'],
            'tension': ['stress', 'anxiety', 'worry', 'nervous', 'pressure'],
            'realization': ['realize', 'understand', 'clarity', 'insight', 'aha'],
            'frustration': ['frustrat', 'angry', 'annoyed', 'irritat'],
            'confusion': ['confus', 'unclear', 'lost', 'puzzl']
        }
        
        # Count emotion keywords
        emotion_scores = {}
        for emotion, patterns in emotion_patterns.items():
            score = sum(1 for pattern in patterns if pattern in script_text)
            emotion_scores[emotion] = score
        
        # Get dominant emotion
        if emotion_scores and max(emotion_scores.values()) > 0:
            dominant_emotion = max(emotion_scores, key=emotion_scores.get)
            return dominant_emotion
        
        # Default to calm/neutral
        return 'calm'
    
    def _get_local_music(self, emotion: str) -> Dict:
        """Get music from local assets folder based on emotion"""
        music_dir = 'assets/music'
        
        if not os.path.exists(music_dir):
            return None
        
        # Emotion to filename pattern mapping (based on actual files in assets/music)
        # Files: ambient-space, building-thriller-tension, dark-tension-mystery, 
        #        pulse-of-terror, shadow-of-blood, suspenseful-ambient, 
        #        terrifying-building, trailer-rising-tension
        patterns = {
            'shame': ['dark', 'shadow', 'ambient'],
            'regret': ['dark', 'shadow', 'ambient', 'suspenseful'],
            'tension': ['tension', 'thriller', 'building', 'rising', 'pulse'],
            'realization': ['ambient', 'space', 'suspenseful'],
            'frustration': ['tension', 'thriller', 'terrifying'],
            'confusion': ['mystery', 'ambient', 'suspenseful'],
            'calm': ['ambient', 'space', 'suspenseful'],
            'neutral': ['ambient', 'space']
        }
        
        search_patterns = patterns.get(emotion, ['ambient', 'tension'])
        
        # Find matching files with scoring
        scored_files = []
        for filename in os.listdir(music_dir):
            if filename.endswith('.mp3'):
                filename_lower = filename.lower()
                # Count how many patterns match
                score = sum(1 for pattern in search_patterns if pattern in filename_lower)
                if score > 0:
                    scored_files.append((filename, score))
        
        if not scored_files:
            logger.info(f"No local music found for emotion: {emotion}")
            return None
        
        # Sort by score (best match first) and pick the best one
        scored_files.sort(key=lambda x: x[1], reverse=True)
        selected_file = scored_files[0][0]
        music_path = os.path.join(music_dir, selected_file)
        
        logger.info(f"Best match for '{emotion}': {selected_file} (score: {scored_files[0][1]})")
        
        # Get duration
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(music_path)
            duration = len(audio) / 1000.0
        except:
            duration = 180  # Default 3 minutes
        
        return {
            'music_path': music_path,
            'emotion': emotion,
            'track_id': f'local_{selected_file}',
            'track_name': selected_file,
            'duration': duration,
            'source': 'local'
        }
    
    def _get_best_local_track(self) -> Dict:
        """Get the best available local track as fallback"""
        music_dir = 'assets/music'
        
        if not os.path.exists(music_dir):
            return None
        
        # Get all mp3 files
        mp3_files = [f for f in os.listdir(music_dir) if f.endswith('.mp3')]
        
        if not mp3_files:
            return None
        
        # Prefer atmospheric/ambient tracks for general use
        preferred = ['ambient', 'suspenseful', 'dark']
        
        # Score each file
        scored_files = []
        for filename in mp3_files:
            filename_lower = filename.lower()
            score = sum(1 for p in preferred if p in filename_lower)
            scored_files.append((filename, score))
        
        # Sort by score and pick best (or random if all same score)
        scored_files.sort(key=lambda x: x[1], reverse=True)
        selected_file = scored_files[0][0]
        music_path = os.path.join(music_dir, selected_file)
        
        logger.info(f"Fallback track selected: {selected_file}")
        
        # Get duration
        try:
            from pydub import AudioSegment
            audio = AudioSegment.from_file(music_path)
            duration = len(audio) / 1000.0
        except:
            duration = 180
        
        return {
            'music_path': music_path,
            'emotion': 'neutral',
            'track_id': f'local_{selected_file}',
            'track_name': selected_file,
            'duration': duration,
            'source': 'local'
        }
    
    def _search_music(self, emotion: str) -> List[Dict]:
        """Search for music matching emotion"""
        keywords = self.emotion_keywords.get(emotion, ['ambient', 'background'])
        
        all_tracks = []
        
        # Search Pixabay Music
        if self.pixabay_api_key:
            for keyword in keywords[:2]:  # Try top 2 keywords
                tracks = self._search_pixabay_music(keyword)
                all_tracks.extend(tracks)
        
        # Filter by configuration rules
        filtered_tracks = self._filter_tracks(all_tracks)
        
        return filtered_tracks
    
    def _search_pixabay_music(self, query: str) -> List[Dict]:
        """Search Pixabay for music"""
        try:
            url = "https://pixabay.com/api/"
            params = {
                "key": self.pixabay_api_key,
                "q": query,
                "per_page": 20,
                "media_type": "music"
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            tracks = []
            for item in data.get('hits', []):
                # Debug: log available fields
                logger.info(f"Available fields in Pixabay response: {item.keys()}")
                
                # Try different URL fields
                audio_url = None
                for field in ['audio', 'pageURL', 'previewURL']:
                    if field in item and item[field]:
                        audio_url = item[field]
                        logger.info(f"Using {field}: {audio_url}")
                        break
                
                if not audio_url:
                    continue
                
                tracks.append({
                    'id': f"pixabay_music_{item['id']}",
                    'name': item.get('tags', 'Background Music'),
                    'url': audio_url,  # Full audio file
                    'duration': item.get('duration', 180),
                    'source': 'pixabay',
                    'tags': item.get('tags', ''),
                    'raw_item': item  # Keep for debugging
                })
            
            return tracks
            
        except Exception as e:
            logger.error(f"Error searching Pixabay music: {e}")
            return []
    
    def _filter_tracks(self, tracks: List[Dict]) -> List[Dict]:
        """Filter tracks based on rules"""
        filtered = []
        
        rules = self.config.get('rules', {})
        
        for track in tracks:
            tags_lower = track.get('tags', '').lower()
            
            # Check no vocals rule
            if rules.get('no_vocals', True):
                if 'vocal' in tags_lower or 'singing' in tags_lower:
                    continue
            
            # Check duration (prefer longer tracks)
            if track.get('duration', 0) < 60:  # Skip very short tracks
                continue
            
            filtered.append(track)
        
        return filtered
    
    def _select_best_track(self, tracks: List[Dict], script_data: Dict) -> Dict:
        """Select best track for video"""
        if not tracks:
            return None
        
        # Prefer tracks with duration close to video duration
        video_duration = script_data.get('estimated_duration_seconds', 360)
        
        # Score tracks
        for track in tracks:
            duration_diff = abs(track.get('duration', 180) - video_duration)
            track['score'] = 1.0 / (1.0 + duration_diff / 60.0)  # Closer duration = higher score
        
        # Sort by score
        tracks.sort(key=lambda x: x.get('score', 0), reverse=True)
        
        # Return top track
        return tracks[0]
    
    def _download_music(self, track: Dict, output_path: str) -> bool:
        """Download music track"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            response = requests.get(track['url'], stream=True, timeout=30)
            response.raise_for_status()
            
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            logger.info(f"Music downloaded to {output_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error downloading music: {e}")
            return False
    
    def _get_fallback_music(self) -> Dict:
        """Return fallback music config"""
        return {
            'music_path': None,
            'emotion': 'neutral',
            'track_id': 'fallback',
            'track_name': 'No Music',
            'duration': 0,
            'source': 'none'
        }
