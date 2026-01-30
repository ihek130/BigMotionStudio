'use client'

import { useState, useRef, useEffect } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useRouter } from 'next/navigation'
import { ArrowRight, ArrowLeft, Play, Pause, Volume2 } from 'lucide-react'

const voices = [
  { id: 'bm_lewis', name: 'Lewis', gender: 'Male', tone: 'Deep & Commanding', preview: '/audio/previews/bm_lewis.wav' },
  { id: 'bm_harry', name: 'Harry', gender: 'Male', tone: 'Warm & Engaging', preview: '/audio/previews/bm_harry.wav' },
  { id: 'am_eric', name: 'Eric', gender: 'Male', tone: 'Professional & Clear', preview: '/audio/previews/am_eric.wav' },
  { id: 'am_ethan', name: 'Ethan', gender: 'Male', tone: 'Friendly & Energetic', preview: '/audio/previews/am_ethan.wav' },
  { id: 'bm_oliver', name: 'Oliver', gender: 'Male', tone: 'Smooth & Sophisticated', preview: '/audio/previews/bm_oliver.wav' },
  { id: 'af_aria', name: 'Aria', gender: 'Female', tone: 'Calm & Soothing', preview: '/audio/previews/af_aria.wav' },
  { id: 'af_bella', name: 'Bella', gender: 'Female', tone: 'Bright & Enthusiastic', preview: '/audio/previews/af_bella.wav' },
  { id: 'af_lily', name: 'Lily', gender: 'Female', tone: 'Gentle & Warm', preview: '/audio/previews/af_lily.wav' },
  { id: 'af_zoey', name: 'Zoey', gender: 'Female', tone: 'Energetic & Youthful', preview: '/audio/previews/af_zoey.wav' },
]

const musicTracks = [
  { 
    id: 'dark-suspense', 
    name: 'Dark Suspense', 
    mood: 'Mysterious', 
    genre: 'Cinematic',
    file: 'dark-tension-mystery-ambient-electronic-373332.mp3'
  },
  { 
    id: 'upbeat-energy', 
    name: 'Upbeat Energy', 
    mood: 'Energetic', 
    genre: 'Electronic',
    file: 'trailer-rising-tension-heartbeat-amp-clocks-400971.mp3'
  },
  { 
    id: 'chill-vibes', 
    name: 'Chill Vibes', 
    mood: 'Relaxed', 
    genre: 'Lo-Fi',
    file: 'suspenseful-ambient-soundscape-360821.mp3'
  },
  { 
    id: 'epic-adventure', 
    name: 'Epic Adventure', 
    mood: 'Dramatic', 
    genre: 'Orchestral',
    file: 'terrifying-building-atmosphere-pulsing-noise-amp-orchestra-400974.mp3'
  },
  { 
    id: 'ambient-space', 
    name: 'Ambient Space', 
    mood: 'Atmospheric', 
    genre: 'Ambient',
    file: 'ambient-space-arpeggio-350710.mp3'
  },
  { 
    id: 'thriller-tension', 
    name: 'Thriller Tension', 
    mood: 'Suspenseful', 
    genre: 'Thriller',
    file: 'building-thriller-tension-amp-clocks-400973.mp3'
  },
  { 
    id: 'horror-ambience', 
    name: 'Horror Ambience', 
    mood: 'Terrifying', 
    genre: 'Horror',
    file: 'pulse-of-terror-intense-horror-ambience-360839.mp3'
  },
  { 
    id: 'blood-woodlands', 
    name: 'Dark Woods', 
    mood: 'Eerie', 
    genre: 'Dark',
    file: 'shadow-of-the-blood-thirsty-woodlands-250736.mp3'
  },
  { 
    id: 'none', 
    name: 'No Music', 
    mood: 'Voice Only', 
    genre: 'Silent',
    file: null
  },
]

export default function VoiceMusicPage() {
  const [selectedVoice, setSelectedVoice] = useState<string>('')
  const [selectedMusic, setSelectedMusic] = useState<string>('')
  const [playingVoice, setPlayingVoice] = useState<string>('')
  const [playingMusic, setPlayingMusic] = useState<string>('')
  const voiceAudioRef = useRef<HTMLAudioElement | null>(null)
  const musicAudioRef = useRef<HTMLAudioElement | null>(null)
  const { updateData, data } = useWizard()
  const router = useRouter()

  // Handle voice audio playback
  const handlePlayPreview = (voiceId: string, previewUrl: string) => {
    // If already playing this voice, stop it
    if (playingVoice === voiceId) {
      voiceAudioRef.current?.pause()
      setPlayingVoice('')
      return
    }

    // Stop any currently playing audio
    if (voiceAudioRef.current) {
      voiceAudioRef.current.pause()
    }

    // Create new audio and play
    const audio = new Audio(previewUrl)
    voiceAudioRef.current = audio
    
    audio.onended = () => setPlayingVoice('')
    audio.onerror = () => {
      console.error('Failed to load audio preview')
      setPlayingVoice('')
    }
    
    audio.play()
    setPlayingVoice(voiceId)
  }

  // Handle music preview playback
  const handlePlayMusic = (musicId: string, musicFile: string | null) => {
    if (!musicFile) return // No music option

    // If already playing this music, stop it
    if (playingMusic === musicId) {
      musicAudioRef.current?.pause()
      setPlayingMusic('')
      return
    }

    // Stop any currently playing music
    if (musicAudioRef.current) {
      musicAudioRef.current.pause()
    }

    // Create new audio and play
    const audio = new Audio(`/music/${musicFile}`)
    musicAudioRef.current = audio
    
    // Play for 10 seconds only (preview)
    audio.onended = () => setPlayingMusic('')
    audio.onerror = () => {
      console.error('Failed to load music preview')
      setPlayingMusic('')
    }
    
    audio.play()
    setPlayingMusic(musicId)
    
    // Stop after 10 seconds
    setTimeout(() => {
      if (audio && !audio.paused) {
        audio.pause()
        setPlayingMusic('')
      }
    }, 10000)
  }

  // Cleanup audio on unmount
  useEffect(() => {
    return () => {
      if (voiceAudioRef.current) {
        voiceAudioRef.current.pause()
      }
      if (musicAudioRef.current) {
        musicAudioRef.current.pause()
      }
    }
  }, [])

  const handleContinue = () => {
    if (selectedVoice && selectedMusic) {
      updateData({ voiceId: selectedVoice, musicId: selectedMusic })
      router.push('/create/captions')
    }
  }

  const handleBack = () => {
    router.push('/create/style')
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-4">
        <h1 className="text-xl sm:text-2xl font-bold mb-1">
          Choose{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Voice & Music
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Select the voice narrator and background music for your {data.niche} series
        </p>
      </div>

      {/* Voice and Music side by side */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
        {/* Voice Selection */}
        <div>
          <h2 className="text-sm font-bold mb-3 flex items-center space-x-2">
            <Volume2 className="w-4 h-4 text-emerald-600" />
            <span>AI Voice</span>
          </h2>
          <div className="grid grid-cols-3 gap-2">
            {voices.map((voice) => (
              <div
                key={voice.id}
                onClick={() => setSelectedVoice(voice.id)}
                className={`group relative p-2.5 rounded-xl border-2 transition-all duration-300 text-left cursor-pointer ${
                  selectedVoice === voice.id
                    ? 'border-emerald-500 bg-gradient-to-br from-emerald-50 to-teal-50 shadow-md shadow-emerald-100/50'
                    : 'border-gray-200 bg-white hover:border-emerald-300 hover:shadow-md'
                }`}
              >
                {/* Selected indicator */}
                {selectedVoice === voice.id && (
                  <div className="absolute top-1.5 right-1.5 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center shadow">
                    <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}

                <h3 className="text-xs font-bold text-gray-900 mb-1">{voice.name}</h3>
                <p className="text-[10px] text-gray-500 mb-2 line-clamp-1">{voice.tone}</p>

                {/* Play Preview Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation()
                    handlePlayPreview(voice.id, voice.preview)
                  }}
                  className={`flex items-center space-x-1 px-2 py-1 rounded-md transition-colors text-[10px] ${
                    playingVoice === voice.id
                      ? 'bg-emerald-500 text-white'
                      : 'bg-emerald-100 hover:bg-emerald-200 text-emerald-700'
                  }`}
                >
                  {playingVoice === voice.id ? (
                    <><Pause className="w-3 h-3" /><span>Stop</span></>
                  ) : (
                    <><Play className="w-3 h-3" /><span>Play</span></>
                  )}
                </button>
              </div>
            ))}
          </div>
        </div>

        {/* Music Selection */}
        <div>
          <h2 className="text-sm font-bold mb-3 flex items-center space-x-2">
            <svg className="w-4 h-4 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3" />
            </svg>
            <span>Background Music</span>
          </h2>
          <div className="grid grid-cols-2 gap-2">
            {musicTracks.map((track) => (
              <div
                key={track.id}
                onClick={() => setSelectedMusic(track.id)}
                className={`group relative p-2.5 rounded-xl border-2 transition-all duration-300 text-left cursor-pointer ${
                  selectedMusic === track.id
                    ? 'border-emerald-500 bg-gradient-to-br from-emerald-50 to-teal-50 shadow-md shadow-emerald-100/50'
                    : 'border-gray-200 bg-white hover:border-emerald-300 hover:shadow-md'
                }`}
              >
                {/* Selected indicator */}
                {selectedMusic === track.id && (
                  <div className="absolute top-1.5 right-1.5 w-4 h-4 bg-emerald-500 rounded-full flex items-center justify-center shadow">
                    <svg className="w-2.5 h-2.5 text-white" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                  </div>
                )}

                <h3 className="text-xs font-bold text-gray-900 mb-0.5">{track.name}</h3>
                <div className="flex items-center space-x-2 text-[10px] mb-2">
                  <span className="text-gray-500">{track.mood}</span>
                  <span className="text-gray-300">•</span>
                  <span className="text-gray-500">{track.genre}</span>
                </div>

                {/* Play Preview Button */}
                {track.file && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation()
                      handlePlayMusic(track.id, track.file)
                    }}
                    className={`flex items-center space-x-1 px-2 py-1 rounded-md transition-colors text-[10px] ${
                      playingMusic === track.id
                        ? 'bg-emerald-500 text-white'
                        : 'bg-emerald-100 hover:bg-emerald-200 text-emerald-700'
                    }`}
                  >
                    {playingMusic === track.id ? (
                      <><Pause className="w-3 h-3" /><span>Stop</span></>
                    ) : (
                      <><Play className="w-3 h-3" /><span>Play</span></>
                    )}
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          className="group px-5 py-2.5 bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-700 rounded-xl font-semibold transition-all flex items-center space-x-2 hover:shadow-md text-sm"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Back</span>
        </button>
        <button
          onClick={handleContinue}
          disabled={!selectedVoice || !selectedMusic}
          className={`group px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2 text-sm ${
            selectedVoice && selectedMusic
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <span>Continue to Captions</span>
          <ArrowRight className={`w-4 h-4 ${selectedVoice && selectedMusic ? 'group-hover:translate-x-1' : ''} transition-transform`} />
        </button>
      </div>
    </div>
  )
}
