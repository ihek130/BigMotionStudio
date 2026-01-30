# ShortsAI - Full-Stack Architecture

## 🏗️ Project Structure

```
Youtube-Automation-Bot/
├── Frontend (Next.js 14)
│   ├── app/                    # Next.js app directory
│   │   ├── layout.tsx         # Root layout
│   │   ├── page.tsx           # Homepage
│   │   └── globals.css        # Global styles
│   ├── components/            # React components
│   │   ├── landing/          # Landing page sections
│   │   └── layout/           # Header, Footer
│   ├── lib/                  # Utilities
│   └── package.json          # Node.js dependencies
│
└── Backend (Python)
    ├── engines/              # Video generation engines
    │   ├── script_engine.py
    │   ├── thumbnail_engine.py
    │   ├── tts_engine.py
    │   └── video_assembly_engine.py
    ├── .venv/               # Python virtual environment
    └── requirements.txt     # Python dependencies
```

## 🚀 Running the Application

### Frontend (Next.js)
```bash
# Install dependencies (first time only)
npm install

# Start development server
npm run dev

# Runs at: http://localhost:3000
```

### Backend (Python)
```bash
# Activate virtual environment
.venv\scripts\activate

# Install dependencies (if needed)
pip install -r requirements.txt

# Run video generation
python automated_workflow.py
```

## 🔄 How They Work Together

### Current Setup (Development):
- **Frontend**: Runs on port 3000 (Node.js)
- **Backend**: Python scripts run independently

### Future Integration (Production):
We'll create API routes that bridge them:

```typescript
// app/api/generate-video/route.ts
import { spawn } from 'child_process';

export async function POST(request: Request) {
  const { niche, style } = await request.json();
  
  // Call Python backend
  const python = spawn('python', [
    'engines/video_assembly_engine.py',
    '--niche', niche,
    '--style', style
  ]);
  
  // Return video URL when done
  return Response.json({ videoUrl: '/output/video.mp4' });
}
```

Frontend calls this:
```typescript
// components/create/VideoGenerator.tsx
const response = await fetch('/api/generate-video', {
  method: 'POST',
  body: JSON.stringify({ niche: 'horror', style: 'dark-comic' })
});
const { videoUrl } = await response.json();
```

## 📦 Dependencies

### Frontend (Node.js - No Virtual Env)
- Next.js 14
- React 18
- Tailwind CSS
- Framer Motion
- TypeScript

### Backend (Python - Uses .venv)
- OpenAI (for scripts)
- ElevenLabs/Audixa (for TTS)
- FFmpeg (for video)
- PIL/Pillow (for images)

## 🎯 Development Workflow

1. **Start Frontend**: `npm run dev` (no .venv needed)
2. **Start Backend**: Activate `.venv` then run Python scripts
3. **Test Integration**: Frontend calls API → API calls Python → Returns result

## 🌐 Accessing the App

- **Frontend**: http://localhost:3000
- **API Routes** (coming soon): http://localhost:3000/api/*

---

**Note**: Python and Node.js run in **completely separate processes**. No need to install npm in .venv or Python in node_modules!
