# 📖 Complete Project Transformation Documentation
## From YouTube Automation Bot to Full-Stack SaaS Platform

**Last Updated:** January 27, 2026  
**Author:** Development Team  
**Purpose:** Complete context for AI agents and developers working on this project

---

## 📚 Table of Contents

1. [Project Evolution Overview](#project-evolution-overview)
2. [Original Architecture (Python Bot)](#original-architecture-python-bot)
3. [SaaS Transformation (Next.js + Python)](#saas-transformation-nextjs--python)
4. [Technical Deep Dive](#technical-deep-dive)
5. [Video Generation Pipeline](#video-generation-pipeline)
6. [AI Services & APIs](#ai-services--apis)
7. [Frontend Architecture](#frontend-architecture)
8. [Data Flow & Integration](#data-flow--integration)
9. [Future Roadmap](#future-roadmap)

---

## 1. Project Evolution Overview

### **What It Was Before:**
A **command-line Python automation bot** that generates YouTube Shorts/TikTok videos automatically. It was designed for personal use by content creators who wanted to automate their entire video production pipeline.

**Original Use Case:**
```bash
# User would run this command
python main.py --topic "why smart people stay poor"

# Bot would automatically:
# 1. Generate script
# 2. Create voiceover
# 3. Find stock footage
# 4. Assemble video with effects
# 5. Generate thumbnail
# 6. Upload to YouTube
```

### **What We're Building Now:**
A **full-stack SaaS platform** (like FacelessReels.com or InVideo) where users can:
- Sign up with OAuth (Google/GitHub)
- Create video series through a beautiful 6-step wizard
- Customize every aspect (niche, voice, style, captions)
- Manage multiple series from a dashboard
- Auto-publish to Instagram, TikTok, YouTube
- Track analytics and performance

**Key Difference:**
- **Before:** One-off script for tech-savvy users
- **Now:** Multi-tenant SaaS with UI for non-technical creators

---

## 2. Original Architecture (Python Bot)

### **Tech Stack:**
- **Language:** Python 3.10+
- **Main Framework:** Custom orchestration in `main.py`
- **Video Processing:** MoviePy + FFmpeg
- **Configuration:** YAML files (`config.yaml`)

### **Engine Architecture:**

The bot is organized into **9 specialized engines**, each handling a specific part of video creation:

#### **2.1 Topic Engine** (`engines/topic_engine.py`)
**Purpose:** Automatically discover viral video topics

**Data Sources:**
- YouTube Autocomplete API
- Google Trends API
- Top-performing finance videos analysis

**Selection Criteria:**
- Identity threat hooks ("why you're still broke")
- Evergreen topics (always relevant)
- High RPM potential (profitable niches)
- Avoids geo-specific terms (wants global audience)

**Output Example:**
```json
{
  "topic": "The Dark Truth About Why Smart People Stay Poor",
  "hook_type": "identity_threat",
  "estimated_rpm": 15.2,
  "search_volume": 12500
}
```

#### **2.2 Script Engine** (`engines/script_engine.py`)
**Purpose:** Generate engaging video scripts using AI

**AI Model:** GPT-4 (via OpenAI API)

**Script Structure:**
```
1. Hook (first 3 seconds) - Must grab attention
2. Problem (15 seconds) - Amplify pain point
3. Mechanism (30 seconds) - Explain the "why"
4. Proof (20 seconds) - Real examples/data
5. CTA (10 seconds) - Like/subscribe/comment
```

**Psychological Triggers:**
- Loss aversion ("you're losing $X every day")
- Social proof ("97% of people don't know this")
- Urgency ("this is happening right now")
- Identity threat ("this is why you're still...")

**Output Format:**
```json
{
  "topic": "Why Credit Cards Keep You Poor",
  "full_script": "Listen. Your credit card company is robbing you blind...",
  "word_count": 285,
  "estimated_duration": "60 seconds",
  "hook": "Your credit card company is robbing you...",
  "segments": [...]
}
```

#### **2.3 TTS Engine** (`engines/tts_engine.py`)
**Purpose:** Convert script to human-like voiceover

**Primary Provider:** **ElevenLabs API**
- Model: `eleven_multilingual_v2`
- Voice ID: Configurable (default: calm male narrator)
- Voice Settings:
  - **Stability:** 0.82 (high = calm, steady voice)
  - **Similarity Boost:** 0.70
  - **Style:** 0.0 (neutral, not expressive)
  - **Speaker Boost:** Enabled

**Fallback Provider:** **Edge TTS** (Microsoft's free TTS)
- Used when ElevenLabs quota exceeded
- Voices: `en-US-GuyNeural`, `en-US-DavisNeural`

**Special Features:**
- **Conversational Mode:** Two-speaker dialogue
  - Young voice (curious): UgBBYS2sOqTuMpoF3BR0
  - Old voice (experienced): NOpBlnGInO9m6vDvFkFC
- **Natural Pauses:** Adds strategic pauses for pacing
- **Chunking:** Handles scripts >10,000 characters

**Character Limit Handling:**
```python
# ElevenLabs has 10,000 char limit
if len(script) > 9500:
    # Split into chunks at sentence boundaries
    chunks = split_into_chunks(script, max_chars=9500)
    # Generate each chunk separately
    # Concatenate audio files
```

**Output:**
```json
{
  "audio_path": "temp/20260127_120530/voiceover.mp3",
  "duration_seconds": 67.3,
  "voice_id": "21m00Tcm4TlvDq8ikWAM",
  "model": "eleven_multilingual_v2",
  "script_word_count": 312
}
```

#### **2.4 Stock Video Engine** (`engines/stock_video_engine.py`)
**Purpose:** Find relevant stock footage matching the topic

**Video Sources:**
- **Pexels API** (primary, free)
- **Pixabay API** (fallback, also free)

**Search Strategy:**
1. Extract keywords from topic ("credit cards" → ["money", "credit", "finance"])
2. Search both APIs for matching videos
3. Rank by quality score:
   - **Duration score:** Longer videos preferred (max at 2 min)
   - **Resolution score:** 1920x1080+ preferred
   - **Combined:** 70% duration + 30% resolution

**Video Selection Logic:**
```python
# If best video is >= 60 seconds:
#   Use ONLY that one video (loop/trim to fit)
# If best video is < 60 seconds:
#   Add more videos until total >= 60 seconds
#   This gives enough footage to work with

Example:
- Best video: 45 seconds
- Second video: 30 seconds
- Total: 75 seconds (enough to loop/trim)
```

**Download Process:**
- Downloads HD video files (1920x1080)
- Saves to temp directory
- Returns metadata (duration, resolution, URL)

#### **2.5 Soundtrack Engine** (`engines/soundtrack_engine.py`)
**Purpose:** Select background music matching the mood

**Music Library:**
Located in `assets/music/` directory

**Available Tracks:**
- `calm.mp3` - For educational/serious topics
- `suspense.mp3` - For dark truths/exposés
- `upbeat.mp3` - For motivational content
- `ambient.mp3` - For deep dives

**Selection Logic:**
```python
# Analyzes script for mood keywords
if "scam" or "dark truth" in topic:
    music = "suspense.mp3"
elif "success" or "wealth" in topic:
    music = "upbeat.mp3"
else:
    music = "calm.mp3"
```

**Audio Mixing:**
- Background music at 15% volume (subtle)
- Voiceover at 100% volume (clear)
- Uses ducking: music fades slightly during speech

#### **2.6 Video Assembly Engine** (`engines/video_assembly_engine.py`)
**Purpose:** Combine all elements into final video

**Tech Stack:**
- **MoviePy** - Python video editing library
- **FFmpeg** - Video encoding/processing

**🎬 Ken Burns Effect Implementation:**

This is a **critical feature** that makes static images look dynamic.

**What is Ken Burns Effect?**
Named after documentary filmmaker Ken Burns, it's a slow pan + zoom on still images to create movement.

**Our Implementation:**
```python
def _add_effects(self, video_clips):
    """Add zoom and fade effects"""
    zoom_intensity = 1.1  # 10% zoom over clip duration
    
    for clip in video_clips:
        # Apply gradual zoom (Ken Burns effect)
        def zoom_effect(get_frame, t):
            # Calculate zoom scale based on time
            progress = t / clip.duration  # 0 to 1
            scale = 1.0 + (zoom_intensity - 1.0) * progress
            
            # Get frame and resize
            frame = get_frame(t)
            h, w = frame.shape[:2]
            new_h, new_w = int(h * scale), int(w * scale)
            
            # Resize and center-crop to original size
            resized = cv2.resize(frame, (new_w, new_h))
            # Crop from center
            start_y = (new_h - h) // 2
            start_x = (new_w - w) // 2
            cropped = resized[start_y:start_y+h, start_x:start_x+w]
            
            return cropped
        
        # Apply the zoom function to clip
        clip = clip.fl(zoom_effect)
        
        # Add fade in/out
        clip = clip.fadein(0.5).fadeout(0.5)
```

**Effect Parameters:**
- **Zoom Start:** 1.0x (original size)
- **Zoom End:** 1.1x (10% larger)
- **Duration:** Entire clip length
- **Fade In:** 0.5 seconds
- **Fade Out:** 0.5 seconds

**Why This Matters:**
Without Ken Burns, stock footage looks static and boring. With it:
- Creates sense of motion
- Keeps viewer engaged
- Professional cinematic feel
- Mimics high-end documentaries

**Export Settings (Optimized for 8-core CPU, 16GB RAM):**
```python
final_video.write_videofile(
    output_path,
    fps=30,
    codec='libx264',        # H.264 for compatibility
    audio_codec='aac',      # AAC audio
    threads=6,              # Use 6 of 8 cores
    preset='veryfast',      # Encoding speed
    bitrate='5000k',        # High quality (5 Mbps)
    ffmpeg_params=['-crf', '23']  # Quality (lower = better)
)
```

#### **2.7 Thumbnail Engine** (`engines/thumbnail_engine.py`)
**Purpose:** Generate click-worthy thumbnails using AI

**AI Image Generation:**
**Provider:** DeepInfra (PrunaAI models)
**Current Model:** Gemini 3 Pro Image Preview
- **Why?** Best at rendering text within images
- **Endpoint:** `https://api.deepinfra.com/v1/inference`

**Thumbnail Psychology Strategy:**

**Visual Elements:**
1. **Subject:** Anonymous person (NOT celebrities)
   - Photorealistic human face
   - Natural expression (shock, concern, realization)
   - Relatable to viewer
   
2. **Text Overlay:** Power words in BOLD
   - Examples: "BROKE", "SCAM", "TRAP", "NEVER"
   - Large, high-contrast font
   - Limited to 3-5 words max

3. **Color Psychology:**
   - Red/Orange: Urgency, danger
   - Blue/Purple: Trust, authority
   - Yellow: Attention, warning

**Prompt Engineering:**
```python
prompt = f"""
Photorealistic YouTube thumbnail, 1920x1080:

SUBJECT: Close-up of anonymous adult (not a celebrity), 
wearing {clothing}. Expression: {emotion} (shocked, concerned).
Realistic skin texture, dramatic lighting.

TEXT OVERLAY: "{hook_text}" in BOLD, large font, 
high contrast against background.

BACKGROUND: {context} - subtle blur, draws eye to subject.

STYLE: Professional, clean, high CTR design.
DO NOT depict any real celebrities or politicians.
"""
```

**Anti-Repetition System:**
To avoid similar-looking thumbnails:
- Tracks last 20 thumbnails in `thumbnail_meta.json`
- Avoids reusing same power words
- Rotates between emotion types
- Varies subject clothing/context

**Tear Effect (35% probability):**
```python
# Sometimes adds subtle tear for emotional impact
if random.random() < 0.35:
    prompt += "\nSingle tear rolling down cheek (subtle, not overdone)"
```

**Output:**
```json
{
  "thumbnail_path": "output/20260127_120530/thumbnail.png",
  "prompt_used": "Photorealistic close-up...",
  "hook_text": "STILL BROKE?",
  "emotion": "concerned_realization",
  "generation_time": 8.2
}
```

#### **2.8 SEO Engine** (`engines/seo_engine.py`)
**Purpose:** Generate optimized metadata for YouTube

**Components Generated:**

**1. Title (60-70 characters):**
```
Format: [Emotional Hook] - [Benefit/Solution]
Example: "Why Smart People Stay Poor (The Truth No One Tells You)"
```

**2. Description (5000 chars max):**
```markdown
Structure:
- Hook paragraph (first 150 chars visible)
- What viewer will learn (bullet points)
- Timestamps (for longer videos)
- Call to action
- Social links
- Hashtags
```

**3. Tags (30-40 tags):**
- Primary keywords (3-5)
- Secondary keywords (10-15)
- Long-tail variations (15-20)
- Niche-specific tags

**4. Hashtags (3-5):**
- `#PersonalFinance`
- `#MoneyPsychology`
- `#FinancialFreedom`

**5. Category:**
- `Education` (most common)
- `Howto & Style`
- `People & Blogs`

**Output Example:**
```json
{
  "title": "Why Credit Cards Keep You Poor (Banks Don't Want You To Know)",
  "description": "Your credit card is costing you $8,347 per year...\n\nIn this video:\n• How minimum payments trap you\n• The hidden fees they don't advertise\n• Smart strategies to break free\n\n👇 RESOURCES:\nDebt calculator: [link]\n\n#PersonalFinance #DebtFree",
  "tags": [
    "credit card debt",
    "personal finance",
    "money psychology",
    "how to get out of debt",
    "financial freedom",
    ...
  ],
  "category": "Education",
  "estimated_ctr": 8.7,
  "estimated_rpm": 15.20
}
```

#### **2.9 Upload Engine** (`engines/upload_engine.py`)
**Purpose:** Automatically upload videos to platforms

**Supported Platforms:**
- **YouTube** (via YouTube Data API v3)
- Instagram Reels (planned)
- TikTok (planned)

**YouTube Upload Process:**
```python
# 1. Authenticate with OAuth 2.0
credentials = get_authenticated_service()

# 2. Prepare video metadata
body = {
    'snippet': {
        'title': seo_data['title'],
        'description': seo_data['description'],
        'tags': seo_data['tags'],
        'categoryId': '22'  # People & Blogs
    },
    'status': {
        'privacyStatus': 'public',  # or 'private', 'unlisted'
        'selfDeclaredMadeForKids': False
    }
}

# 3. Upload video file
media = MediaFileUpload(video_path, 
                       chunksize=1024*1024,  # 1MB chunks
                       resumable=True)

request = youtube.videos().insert(
    part='snippet,status',
    body=body,
    media_body=media
)

# 4. Execute with retry logic
response = request.execute()
```

**Upload Record Tracking:**
Saves to `output/upload_records.json`:
```json
{
  "20260127_120530": {
    "youtube": {
      "video_id": "dQw4w9WgXcQ",
      "url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "uploaded_at": "2026-01-27T12:05:30Z",
      "status": "public"
    }
  }
}
```

### **2.10 KPI Monitor** (`engines/kpi_monitor.py`)
**Purpose:** Track video performance analytics

**Metrics Tracked:**
- Views
- Watch time
- CTR (Click-Through Rate)
- AVD (Average View Duration)
- Likes/Comments ratio
- RPM (Revenue per Mille)

---

## 3. SaaS Transformation (Next.js + Python)

### **Why We're Adding a Frontend:**

**Problems with CLI-only approach:**
1. **No user interface** - Requires technical knowledge
2. **No multi-user support** - Can't sell as SaaS
3. **No user management** - No accounts, billing, limits
4. **No visual feedback** - Users can't see progress
5. **Not scalable** - Can't onboard customers easily

**Solution: Build a Modern SaaS Platform**

### **New Tech Stack:**

**Frontend:**
- **Framework:** Next.js 14.2.18 (React)
- **Language:** TypeScript
- **Styling:** Tailwind CSS
- **UI Library:** Headless UI, Lucide React (icons)
- **State Management:** React Context API
- **Routing:** Next.js App Router

**Backend (Existing):**
- **Kept:** All 9 Python engines
- **Added:** REST API layer (coming soon)
- **Integration:** Node.js child_process to call Python scripts

**Database (Coming Soon):**
- **Primary:** PostgreSQL
- **ORM:** Prisma
- **Purpose:** User accounts, series, videos, billing

**Authentication (Planned):**
- **Provider:** NextAuth.js
- **Methods:** Google OAuth, GitHub OAuth, Email/Password
- **Session:** JWT tokens

**Deployment (Future):**
- **Frontend:** Vercel
- **Backend:** Railway / DigitalOcean
- **Storage:** AWS S3 (for videos)
- **CDN:** Cloudflare

---

## 4. Technical Deep Dive

### **4.1 Ken Burns Method (Zoom/Pan Effect)**

**Mathematical Implementation:**

The Ken Burns effect creates the illusion of camera movement on still images.

**Core Algorithm:**
```python
# Time-based zoom calculation
def calculate_zoom(t, duration, start_scale=1.0, end_scale=1.1):
    """
    t = current time in clip (0 to duration)
    duration = total clip length
    start_scale = initial size (1.0 = 100%)
    end_scale = final size (1.1 = 110%)
    """
    # Linear interpolation
    progress = t / duration  # 0.0 to 1.0
    current_scale = start_scale + (end_scale - start_scale) * progress
    return current_scale

# Apply to each frame
def apply_zoom(frame, scale):
    height, width = frame.shape[:2]
    
    # Calculate new dimensions
    new_height = int(height * scale)
    new_width = int(width * scale)
    
    # Resize image
    resized = cv2.resize(frame, (new_width, new_height))
    
    # Crop to center (maintains original aspect ratio)
    crop_y = (new_height - height) // 2
    crop_x = (new_width - width) // 2
    
    cropped = resized[crop_y:crop_y + height, 
                     crop_x:crop_x + width]
    
    return cropped
```

**Variations:**
- **Zoom In:** start_scale=1.0, end_scale=1.2
- **Zoom Out:** start_scale=1.2, end_scale=1.0
- **Pan Right:** Shift crop_x from left to right
- **Pan Left:** Shift crop_x from right to left

**Performance Optimization:**
```python
# Pre-calculate zoom levels
zoom_cache = [calculate_zoom(t, duration) 
              for t in np.linspace(0, duration, fps * duration)]

# Use cached values during render
frame = apply_zoom(original_frame, zoom_cache[frame_number])
```

### **4.2 ElevenLabs API Deep Dive**

**API Endpoint:**
```
POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}
```

**Request Headers:**
```http
xi-api-key: YOUR_API_KEY
Content-Type: application/json
```

**Request Body:**
```json
{
  "text": "Your credit card is robbing you blind. Here's how.",
  "model_id": "eleven_multilingual_v2",
  "voice_settings": {
    "stability": 0.82,
    "similarity_boost": 0.70,
    "style": 0.0,
    "use_speaker_boost": true
  }
}
```

**Response:**
Binary audio stream (MP3 format)

**Voice Settings Explained:**

**1. Stability (0.0 - 1.0):**
- **Low (0.0-0.4):** Expressive, emotional, varies more
- **Medium (0.5-0.7):** Balanced
- **High (0.8-1.0):** Calm, consistent, professional
- **Our Setting:** 0.82 (very stable for educational content)

**2. Similarity Boost (0.0 - 1.0):**
- Controls how closely voice matches original sample
- **Low:** More generic
- **High:** More true to voice sample
- **Our Setting:** 0.70 (good match)

**3. Style (0.0 - 1.0):**
- **0.0:** Neutral, monotone
- **0.5:** Moderate expressiveness
- **1.0:** Highly expressive, dramatic
- **Our Setting:** 0.0 (neutral for clarity)

**4. Speaker Boost:**
- Enhances voice clarity
- **Our Setting:** Enabled (clearer audio)

**Character Limits:**
```python
FREE_TIER_LIMIT = 10_000  # characters per month
PRO_TIER_LIMIT = 500_000  # characters per month

# Our typical video script
AVERAGE_SCRIPT = 300  # words
AVERAGE_CHARS = 1800  # characters

# Max videos per month
free_videos = 10_000 / 1800 = 5.5 videos
pro_videos = 500_000 / 1800 = 277 videos
```

**Pricing:**
- Free: $0/month (10k chars)
- Starter: $5/month (30k chars)
- Creator: $22/month (100k chars)
- Pro: $99/month (500k chars)

### **4.3 Image Generation (Thumbnails)**

**Current Provider: DeepInfra (PrunaAI)**

**API Endpoint:**
```
POST https://api.deepinfra.com/v1/inference/prunaai/gemini-3-pro-image-preview
```

**Request:**
```json
{
  "prompt": "Photorealistic YouTube thumbnail, 1920x1080: Close-up of shocked person looking at credit card bill. Bold text overlay: 'STILL BROKE?' Professional lighting, high contrast.",
  "width": 1920,
  "height": 1080,
  "num_inference_steps": 30,
  "guidance_scale": 7.5
}
```

**Response:**
```json
{
  "images": ["base64_encoded_image_data"],
  "inference_time": 8.2
}
```

**Why Gemini 3 Pro Image Preview?**
- **Best text rendering:** Accurately renders text in images
- **Fast:** ~8 seconds per image
- **Quality:** Photorealistic output
- **Cost:** $0.002 per image (very cheap)

**Alternative Providers (Future):**
- **DALL-E 3:** Better quality, more expensive ($0.040/image)
- **Midjourney:** Best artistic quality (no API yet)
- **Stable Diffusion:** Open source, self-host option

### **4.4 Pexels/Pixabay Stock Video APIs**

**Pexels API:**
```http
GET https://api.pexels.com/videos/search
Authorization: YOUR_PEXELS_API_KEY
```

**Query Parameters:**
```
?query=money+finance
&per_page=15
&orientation=portrait  (for vertical videos)
&size=medium  (or large for HD)
```

**Response:**
```json
{
  "videos": [
    {
      "id": 123456,
      "width": 1080,
      "height": 1920,
      "duration": 15,
      "video_files": [
        {
          "quality": "hd",
          "file_type": "video/mp4",
          "width": 1080,
          "height": 1920,
          "link": "https://player.vimeo.com/..."
        }
      ]
    }
  ]
}
```

**Rate Limits:**
- **Pexels:** 200 requests/hour (free)
- **Pixabay:** 5000 requests/hour (free)

**Download Strategy:**
```python
# 1. Search for videos
results = pexels.search("money credit cards", per_page=15)

# 2. Filter by criteria
videos = [v for v in results if 
          v.width >= 1080 and 
          v.duration >= 10]

# 3. Sort by quality
videos.sort(key=lambda v: v.duration * v.width, reverse=True)

# 4. Download best video
best_video = videos[0]
download_video(best_video.video_files[0].link, "temp/video1.mp4")
```

---

## 5. Video Generation Pipeline

### **Complete End-to-End Flow:**

```
┌─────────────────────────────────────────────────────────┐
│                    USER INPUT                           │
│  "Create video about credit card debt"                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 1: Topic Generation (topic_engine.py)            │
│  • Analyzes search trends                               │
│  • Finds viral angles                                   │
│  • Output: "Why Credit Cards Keep You Poor"             │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 2: Script Generation (script_engine.py)          │
│  • GPT-4 generates 60-90 second script                  │
│  • Uses psychological hooks                             │
│  • Output: 300-word engaging script                     │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 3: Voiceover (tts_engine.py)                     │
│  • ElevenLabs converts script to audio                  │
│  • Calm, professional voice                             │
│  • Output: voiceover.mp3 (67 seconds)                   │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 4: Stock Footage (stock_video_engine.py)         │
│  • Searches Pexels/Pixabay                              │
│  • Downloads HD vertical video                          │
│  • Output: 1-3 video clips (1080x1920)                  │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 5: Background Music (soundtrack_engine.py)       │
│  • Selects appropriate track                            │
│  • Adjusts volume (15% background)                      │
│  • Output: background.mp3                               │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 6: Video Assembly (video_assembly_engine.py)     │
│  • Combines all elements                                │
│  • Applies Ken Burns effect (zoom)                      │
│  • Adds fade in/out                                     │
│  • Syncs audio to video                                 │
│  • Output: final_video.mp4 (1080x1920, 67 sec)          │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 7: Thumbnail (thumbnail_engine.py)               │
│  • AI generates clickable image                         │
│  • Photorealistic person + text                         │
│  • Output: thumbnail.png (1920x1080)                    │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 8: SEO Metadata (seo_engine.py)                  │
│  • Generates optimized title                            │
│  • Creates description with keywords                    │
│  • Selects 30-40 tags                                   │
│  • Output: metadata.json                                │
└─────────────────────────────────────────────────────────┘
                        ↓
┌─────────────────────────────────────────────────────────┐
│  STAGE 9: Upload (upload_engine.py)                     │
│  • Uploads to YouTube                                   │
│  • Sets to public/scheduled                             │
│  • Output: Video live on channel                        │
└─────────────────────────────────────────────────────────┘
```

**Total Processing Time:**
- Topic: 2 seconds
- Script: 15-30 seconds (GPT-4)
- Voiceover: 10-20 seconds (ElevenLabs)
- Stock footage: 5-10 seconds (download)
- Music: 1 second (file copy)
- Assembly: 60-120 seconds (rendering)
- Thumbnail: 8-12 seconds (AI generation)
- SEO: 10 seconds (GPT-4)
- Upload: 30-60 seconds (network speed)

**Grand Total: 3-5 minutes per video**

---

## 6. AI Services & APIs

### **6.1 OpenAI GPT-4**

**Used For:**
- Script generation
- SEO title/description
- Topic refinement

**Model:** `gpt-4` (not gpt-4-turbo yet)

**Typical Prompt for Scripts:**
```
You are an expert YouTube scriptwriter specializing in viral short-form content.

Topic: "Why Credit Cards Keep You Poor"
Style: James Jani-style investigation
Duration: 60 seconds
Hook type: Identity threat

Requirements:
1. Start with attention-grabbing hook (first 3 seconds)
2. Use specific numbers and data
3. Create "aha moments"
4. End with strong CTA
5. Write for 8th grade reading level
6. Use second person ("you")

Generate script:
```

**Response:**
```
Listen. Your credit card company makes $8,347 per year... off YOU.

Here's the dirty secret they don't want you to know.

That "minimum payment" on your statement? It's a trap. 
Pay only that, and you'll be in debt for 23 years.

On a $5,000 balance, you'll pay $11,680 in interest alone.

But it gets worse. Every time you swipe, they take 3% 
from the merchant. Who pays? You do. In higher prices.

The game is rigged. The question is... will you keep playing?

Drop a comment if you're ready to break free.
```

**Cost:**
- GPT-4: $0.03/1K tokens (input), $0.06/1K tokens (output)
- Average script: ~800 tokens total
- **Cost per video: ~$0.04**

### **6.2 ElevenLabs TTS**

**Model:** `eleven_multilingual_v2`

**Advantages:**
- Most natural-sounding TTS available
- Emotional variation support
- Multiple languages
- Custom voice cloning (paid feature)

**Limitations:**
- 10k character free tier (5-6 videos)
- Requires API key
- Not real-time (takes 10-20 sec)

**Fallback:** Microsoft Edge TTS
- Free, unlimited
- Lower quality
- Limited voices

### **6.3 DeepInfra (Image Generation)**

**Model:** PrunaAI Gemini 3 Pro Image Preview

**Parameters:**
```python
{
  "width": 1920,
  "height": 1080,
  "num_inference_steps": 30,  # Quality (higher = better)
  "guidance_scale": 7.5,       # Prompt adherence
  "negative_prompt": "blurry, low quality, distorted, cartoon"
}
```

**Cost:** $0.002 per image (very cheap)

**Alternatives:**
- OpenAI DALL-E 3: $0.040/image (better quality)
- Stability AI SDXL: $0.003/image
- Self-hosted Stable Diffusion: Free (requires GPU)

### **6.4 Pexels & Pixabay**

**Pexels:**
- Free HD videos
- No attribution required
- 200 requests/hour limit
- Good for generic footage

**Pixabay:**
- Free HD videos
- No attribution required
- 5000 requests/hour limit
- More variety

**Legal:** Both are 100% royalty-free for commercial use

---

## 7. Frontend Architecture

### **7.1 File Structure**

```
app/
├── layout.tsx              # Root layout (common UI)
├── page.tsx                # Landing page
├── globals.css             # Global styles
├── login/
│   └── page.tsx           # Login/signup page
├── dashboard/
│   └── page.tsx           # Main dashboard
└── create/
    ├── layout.tsx         # Wizard layout
    ├── page.tsx           # Step 1: Niche selection
    ├── style/
    │   └── page.tsx       # Step 2: Visual style
    ├── voice/
    │   └── page.tsx       # Step 3: Voice & music
    ├── captions/
    │   └── page.tsx       # Step 4: Caption style
    ├── details/
    │   └── page.tsx       # Step 5: Series details
    └── platforms/
        └── page.tsx       # Step 6: Connect platforms

components/
├── Sidebar.tsx            # Shared sidebar navigation
├── Breadcrumb.tsx         # Breadcrumb navigation
├── MobileMenuButton.tsx   # Mobile hamburger menu
└── landing/
    ├── Hero.tsx           # Hero section
    ├── VideoShowcase.tsx  # Video examples
    ├── SocialProof.tsx    # Testimonials/stats
    ├── HowItWorks.tsx     # Process steps
    ├── Pricing.tsx        # Pricing tiers
    ├── FAQ.tsx            # Common questions
    └── CTA.tsx            # Final call-to-action

context/
└── WizardContext.tsx      # State management for wizard

lib/
└── utils.ts               # Helper functions
```

### **7.2 Design System**

**Colors:**
```css
/* Primary (Emerald Green) */
--emerald-50: #ecfdf5;
--emerald-500: #22c55e;
--emerald-600: #16a34a;
--emerald-700: #15803d;

/* Secondary (Teal) */
--teal-500: #14b8a6;
--teal-600: #0d9488;

/* Accent (Purple) */
--purple-600: #9333ea;
--purple-700: #7e22ce;

/* Neutrals */
--gray-50: #f9fafb;
--gray-900: #111827;
```

**Why Emerald?**
- Originally copied FacelessReels (purple theme)
- Changed to emerald green for unique branding
- Emerald = growth, money, success (fits niche)

**Typography:**
- **Font:** System font stack (Inter-like)
- **Headings:** Bold, 2xl-4xl
- **Body:** Regular, base-lg
- **Code:** Monospace

**Spacing:**
- **Corners:** rounded-2xl (16px)
- **Shadows:** shadow-lg with color tints
- **Padding:** Consistent 4-6-8 scale

### **7.3 Wizard Flow (6 Steps)**

**Step 1: Choose Niche**
- 7 predefined niches:
  1. Scary Stories (Storytelling)
  2. History (Storytelling)
  3. True Crime (Storytelling)
  4. Stoic Motivation (Storytelling)
  5. Random Facts (5 Things You Didn't Know)
  6. Good Morals (Storytelling)
  7. Psychology (Storytelling)

**Step 2: Visual Style**
- 10 art styles:
  - Cinematic
  - Dark Comic
  - Anime
  - Minimalist
  - Horror
  - Documentary
  - Cartoon
  - Photorealistic
  - Abstract
  - Retro

**Step 3: Voice & Music**
- 6 AI voices (male/female, young/old)
- 6 background music tracks

**Step 4: Caption Style**
- 8 preset caption designs
- Font, color, animation options

**Step 5: Series Details**
- Series name
- Description
- Posting schedule (daily/weekly)
- Time of day to post

**Step 6: Connect Platforms**
- Instagram OAuth
- TikTok OAuth
- YouTube OAuth

**State Management:**
```typescript
interface WizardData {
  niche: string
  format: string
  style: string
  voice: string
  music: string
  captionStyle: string
  seriesName: string
  description: string
  schedule: string
  postTime: string
  platforms: string[]
}
```

Stored in React Context, persists across steps.

### **7.4 Dashboard Layout**

**Sidebar Navigation:**
- Series (main page)
- Videos (all generated videos)
- Guides (tutorials/docs)
- Settings (account/preferences)
- Billing (subscription/usage)

**Main Content Area:**
- Breadcrumb navigation (always visible)
- Page title + description
- Data table or cards
- Action buttons (Create Series)

**Series Table Columns:**
- Name (clickable to edit)
- Type (niche badge)
- Created (date)
- Published (video count)
- Actions (Pause/Delete buttons)

**Mobile Responsiveness:**
- Sidebar: Hidden on mobile, accessible via hamburger
- Tables: Convert to cards on small screens
- Breadcrumbs: Horizontal scroll on mobile

---

## 8. Data Flow & Integration

### **8.1 Current State (Development)**

**Frontend and Backend are SEPARATE:**

```
┌──────────────────┐         ┌──────────────────┐
│   Next.js        │         │   Python Bot     │
│   (Frontend)     │         │   (Backend)      │
│                  │         │                  │
│   localhost:3000 │    ?    │   CLI scripts    │
│                  │         │                  │
│   NOT CONNECTED  │         │   NOT CONNECTED  │
└──────────────────┘         └──────────────────┘
```

**How They'll Be Integrated (Future):**

```
┌──────────────────────────────────────────────────────┐
│                   USER BROWSER                       │
│                                                      │
│   Clicks "Create Series" → Fills wizard → Submit    │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              Next.js API Route                       │
│         /app/api/create-series/route.ts              │
│                                                      │
│   export async function POST(request) {             │
│     const data = await request.json()               │
│                                                      │
│     // Call Python backend                          │
│     const python = spawn('python', [                │
│       'main.py',                                     │
│       '--niche', data.niche,                         │
│       '--voice', data.voice,                         │
│       '--schedule', data.schedule                    │
│     ])                                               │
│                                                      │
│     return json({ jobId: '123' })                   │
│   }                                                  │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              Python Backend                          │
│              main.py                                 │
│                                                      │
│   1. Generate script                                │
│   2. Create voiceover                               │
│   3. Find stock footage                             │
│   4. Assemble video                                 │
│   5. Generate thumbnail                             │
│   6. Create SEO metadata                            │
│   7. Save to database                               │
│   8. Upload to YouTube                              │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              PostgreSQL Database                     │
│                                                      │
│   Tables:                                           │
│   • users (auth, subscription)                       │
│   • series (user_id, niche, settings)                │
│   • videos (series_id, status, url)                  │
│   • jobs (progress tracking)                         │
└──────────────────────────────────────────────────────┘
                        ↓
┌──────────────────────────────────────────────────────┐
│              Real-time Updates                       │
│              (WebSockets or Server-Sent Events)      │
│                                                      │
│   Frontend polls: GET /api/job/123                  │
│   Response: { status: 'rendering', progress: 67% }  │
│                                                      │
│   When done: { status: 'complete', videoUrl: '...' }│
└──────────────────────────────────────────────────────┘
```

### **8.2 Database Schema (Planned)**

```sql
-- Users table
CREATE TABLE users (
  id UUID PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  name VARCHAR(255),
  avatar_url TEXT,
  subscription_tier VARCHAR(50), -- 'free', 'pro', 'premium'
  credits_remaining INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Series table
CREATE TABLE series (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  name VARCHAR(255) NOT NULL,
  niche VARCHAR(100),
  format VARCHAR(100),
  visual_style VARCHAR(100),
  voice_id VARCHAR(100),
  music_track VARCHAR(100),
  caption_style VARCHAR(100),
  posting_schedule VARCHAR(50), -- 'daily', 'weekly'
  post_time TIME,
  status VARCHAR(50), -- 'active', 'paused', 'deleted'
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Videos table
CREATE TABLE videos (
  id UUID PRIMARY KEY,
  series_id UUID REFERENCES series(id),
  topic VARCHAR(255),
  script_path TEXT,
  video_path TEXT,
  thumbnail_path TEXT,
  youtube_url TEXT,
  instagram_url TEXT,
  tiktok_url TEXT,
  status VARCHAR(50), -- 'processing', 'ready', 'published', 'failed'
  progress INTEGER DEFAULT 0, -- 0-100
  created_at TIMESTAMP DEFAULT NOW(),
  published_at TIMESTAMP
);

-- Platform connections
CREATE TABLE platform_connections (
  id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(id),
  platform VARCHAR(50), -- 'youtube', 'instagram', 'tiktok'
  access_token TEXT,
  refresh_token TEXT,
  expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Processing jobs
CREATE TABLE jobs (
  id UUID PRIMARY KEY,
  video_id UUID REFERENCES videos(id),
  stage VARCHAR(50), -- 'script', 'voiceover', 'assembly', etc.
  status VARCHAR(50), -- 'pending', 'processing', 'complete', 'failed'
  progress INTEGER DEFAULT 0,
  error_message TEXT,
  created_at TIMESTAMP DEFAULT NOW(),
  completed_at TIMESTAMP
);
```

### **8.3 Authentication Flow (Planned)**

```typescript
// NextAuth configuration
// app/api/auth/[...nextauth]/route.ts

import NextAuth from 'next-auth'
import GoogleProvider from 'next-auth/providers/google'
import GitHubProvider from 'next-auth/providers/github'

export const authOptions = {
  providers: [
    GoogleProvider({
      clientId: process.env.GOOGLE_CLIENT_ID,
      clientSecret: process.env.GOOGLE_CLIENT_SECRET
    }),
    GitHubProvider({
      clientId: process.env.GITHUB_CLIENT_ID,
      clientSecret: process.env.GITHUB_CLIENT_SECRET
    })
  ],
  callbacks: {
    async session({ session, token }) {
      // Add user ID to session
      session.user.id = token.sub
      return session
    }
  }
}

export const handler = NextAuth(authOptions)
export { handler as GET, handler as POST }
```

**User Flow:**
1. User clicks "Sign in with Google"
2. Redirected to Google OAuth consent screen
3. User approves permissions
4. Redirected back to app with auth code
5. NextAuth exchanges code for tokens
6. Creates/updates user in database
7. Sets session cookie
8. User now authenticated

---

## 9. Future Roadmap

### **Phase 1: MVP (Current - Month 1)**
- ✅ Landing page design
- ✅ 6-step wizard UI
- ✅ Dashboard layout
- ✅ Sidebar navigation
- ✅ Mobile responsiveness
- ⏳ Authentication (Google/GitHub OAuth)
- ⏳ Database setup (PostgreSQL + Prisma)

### **Phase 2: Backend Integration (Month 2)**
- Connect frontend to Python engines
- Create API routes for video generation
- Real-time progress tracking
- Job queue system (Bull MQ or similar)
- Error handling and retries
- Video preview in dashboard

### **Phase 3: Platform Integrations (Month 3)**
- YouTube OAuth and auto-upload
- Instagram Reels API integration
- TikTok API integration
- Scheduling system (cron jobs)
- Multi-platform publishing

### **Phase 4: Monetization (Month 4)**
- Stripe payment integration
- Subscription tiers (Free/Pro/Premium)
- Credit system (pay-per-video)
- Usage analytics dashboard
- Billing portal

### **Phase 5: Advanced Features (Month 5-6)**
- Custom voice cloning (ElevenLabs)
- Brand kit (logos, colors, fonts)
- A/B testing thumbnails
- Analytics dashboard (views, CTR, RPM)
- Team collaboration features
- Video templates library

### **Phase 6: Scale & Optimize (Month 7+)**
- CDN integration for faster video delivery
- Queue workers for parallel processing
- Cache layer (Redis) for performance
- Rate limiting and abuse prevention
- Admin dashboard for support
- Affiliate program

---

## 10. Key Takeaways for AI Agents

### **When Working on This Project:**

1. **Two Separate Codebases:**
   - **Frontend:** Next.js (TypeScript, no Python)
   - **Backend:** Python (no Node.js modules)
   - They don't run in same process

2. **Ken Burns is Critical:**
   - It's what makes videos look professional
   - Without it, videos appear static
   - Located in `video_assembly_engine.py`

3. **ElevenLabs is Primary TTS:**
   - Edge TTS is fallback only
   - Voice settings matter (stability, style)
   - Character limits must be respected

4. **Thumbnails Use DeepInfra:**
   - Gemini 3 Pro Image Preview model
   - Best for text rendering in images
   - Cost-effective ($0.002/image)

5. **Stock Video Strategy:**
   - Pexels first, Pixabay second
   - Prefer longer clips (can loop)
   - Always vertical format (1080x1920)

6. **Current Frontend Has NO Backend:**
   - It's just UI mockups
   - No actual video generation yet
   - Integration coming in Phase 2

7. **Design System:**
   - Emerald green theme (not purple)
   - No Sparkles icons (use unique icons)
   - Sidebar always visible (mobile hamburger)
   - Breadcrumbs on every page

8. **7 Specific Niches Only:**
   - Scary Stories
   - History
   - True Crime
   - Stoic Motivation
   - Random Facts
   - Good Morals
   - Psychology

### **Common Pitfalls to Avoid:**

❌ Don't try to run Python in Next.js app  
❌ Don't install Node modules in Python venv  
❌ Don't assume backend is connected (it's not)  
❌ Don't use purple theme (changed to emerald)  
❌ Don't add more than 7 niches  
❌ Don't forget mobile responsiveness  

✅ Keep frontend and backend separate for now  
✅ Use TypeScript for frontend code  
✅ Use Python for backend code  
✅ Test on mobile screens  
✅ Follow existing design system  
✅ Read ARCHITECTURE.md for setup instructions  

---

## 11. Quick Reference

### **Environment Variables Needed:**

```bash
# OpenAI (for scripts)
OPENAI_API_KEY=sk-...

# ElevenLabs (for voiceovers)
ELEVENLABS_API_KEY=...

# DeepInfra (for thumbnails)
DEEPINFRA_API_KEY=...

# Pexels (for stock videos)
PEXELS_API_KEY=...

# Pixabay (for stock videos - optional)
PIXABAY_API_KEY=...

# YouTube (for uploads - optional)
YOUTUBE_CLIENT_ID=...
YOUTUBE_CLIENT_SECRET=...

# NextAuth (for authentication - coming soon)
NEXTAUTH_SECRET=...
NEXTAUTH_URL=http://localhost:3000

# Database (coming soon)
DATABASE_URL=postgresql://...
```

### **Common Commands:**

```bash
# Frontend
npm install          # Install dependencies
npm run dev          # Start dev server (port 3000)
npm run build        # Build for production
npx tsc --noEmit     # Check TypeScript errors

# Backend
python -m venv .venv          # Create virtual env
.venv\\scripts\\activate       # Activate (Windows)
pip install -r requirements.txt  # Install deps
python main.py --topic "..."  # Generate video
python automated_workflow.py  # Batch generation
```

### **Important Files:**

- `config.yaml` - Python bot configuration
- `main.py` - Main orchestrator for video generation
- `app/create/layout.tsx` - Wizard flow UI
- `app/dashboard/page.tsx` - Main dashboard
- `components/Sidebar.tsx` - Shared navigation
- `engines/video_assembly_engine.py` - Ken Burns effect

---

## 12. Conclusion

This document provides **100% context** for any AI agent or developer working on this project. It covers:

- ✅ What the project was (Python CLI bot)
- ✅ What it's becoming (Next.js SaaS platform)
- ✅ How every engine works (9 Python modules)
- ✅ Ken Burns effect implementation
- ✅ All AI APIs used (ElevenLabs, OpenAI, DeepInfra)
- ✅ Complete frontend architecture
- ✅ Future integration plans
- ✅ Database schema design
- ✅ Development workflow

**Next Steps:**
1. Read ARCHITECTURE.md for setup
2. Review this document for context
3. Check existing code before making changes
4. Test both frontend and backend separately
5. Plan integration carefully (Phase 2)

**Questions?**
Refer to the relevant section above or check the source code directly. All engines are well-documented with inline comments.

---

**Document Version:** 1.0  
**Last Updated:** January 27, 2026  
**Status:** Complete and Ready for AI Agent Use 🚀
