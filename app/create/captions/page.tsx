'use client'

import { useState } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useRouter } from 'next/navigation'
import { ArrowRight, ArrowLeft } from 'lucide-react'

const captionStyles = [
  {
    id: 'modern-bold',
    name: 'Modern Bold',
    description: 'Bold text with clean lines',
    textStyle: 'text-sm font-black text-white uppercase tracking-wide',
    bg: 'bg-gradient-to-br from-gray-900 to-gray-700',
    animation: 'animate-word-pop',
  },
  {
    id: 'neon-glow',
    name: 'Neon Glow',
    description: 'Glowing vibrant colors',
    textStyle: 'text-sm font-bold text-cyan-400',
    bg: 'bg-gradient-to-br from-gray-900 to-black',
    animation: 'animate-neon-flicker',
    glow: true,
  },
  {
    id: 'minimal-clean',
    name: 'Minimal Clean',
    description: 'Simple, readable text',
    textStyle: 'text-sm font-medium text-white lowercase',
    bg: 'bg-gradient-to-br from-gray-800 to-gray-600',
    animation: 'animate-typewriter',
  },
  {
    id: 'youtube-style',
    name: 'YouTube Style',
    description: 'Classic white on black',
    textStyle: 'text-sm font-bold text-white bg-black/80 px-2 py-0.5 rounded',
    bg: 'bg-gradient-to-br from-red-600 to-red-800',
    animation: 'animate-karaoke',
  },
  {
    id: 'colorful-pop',
    name: 'Colorful Pop',
    description: 'Multi-colored gradient',
    textStyle: 'text-sm font-black bg-gradient-to-r from-pink-500 via-purple-500 to-cyan-500 bg-clip-text text-transparent uppercase',
    bg: 'bg-gradient-to-br from-gray-900 to-gray-800',
    animation: 'animate-rainbow-wave',
  },
  {
    id: 'outlined',
    name: 'Outlined',
    description: 'White with black outline',
    textStyle: 'text-sm font-black text-white uppercase',
    bg: 'bg-gradient-to-br from-blue-600 to-purple-700',
    animation: 'animate-shake-pop',
    outline: true,
  },
  {
    id: 'boxed',
    name: 'Boxed',
    description: 'Text in colored boxes',
    textStyle: 'text-xs font-bold text-white bg-black/80 px-2 py-1 rounded-md',
    bg: 'bg-gradient-to-br from-emerald-500 to-teal-600',
    animation: 'animate-slide-bounce',
  },
  {
    id: 'no-captions',
    name: 'No Captions',
    description: 'Voice-over only',
    textStyle: 'text-xs font-medium text-gray-400 italic',
    bg: 'bg-gradient-to-br from-gray-600 to-gray-800',
    animation: 'animate-pulse-slow',
  },
]

export default function CaptionsPage() {
  const [selectedCaption, setSelectedCaption] = useState<string>('')
  const { updateData, data } = useWizard()
  const router = useRouter()

  const handleContinue = () => {
    if (selectedCaption) {
      updateData({ captionStyle: selectedCaption })
      router.push('/create/details')
    }
  }

  const handleBack = () => {
    router.push('/create/voice')
  }

  return (
    <div className="max-w-5xl mx-auto">
      {/* Custom animations - More aggressive */}
      <style jsx>{`
        @keyframes word-pop {
          0%, 100% { transform: scale(1) rotate(0deg); }
          25% { transform: scale(1.15) rotate(-2deg); }
          50% { transform: scale(0.95) rotate(0deg); }
          75% { transform: scale(1.1) rotate(2deg); }
        }
        @keyframes neon-flicker {
          0%, 100% { 
            text-shadow: 0 0 5px #22d3ee, 0 0 10px #22d3ee, 0 0 20px #22d3ee, 0 0 40px #06b6d4;
            opacity: 1;
          }
          10%, 30% { 
            text-shadow: none;
            opacity: 0.8;
          }
          20% { 
            text-shadow: 0 0 5px #22d3ee, 0 0 10px #22d3ee, 0 0 20px #22d3ee, 0 0 40px #06b6d4, 0 0 60px #06b6d4;
            opacity: 1;
          }
          50% {
            text-shadow: 0 0 10px #22d3ee, 0 0 20px #22d3ee, 0 0 40px #22d3ee, 0 0 80px #06b6d4;
          }
        }
        @keyframes typewriter {
          0%, 100% { width: 0; opacity: 0; }
          10% { width: 100%; opacity: 1; }
          90% { width: 100%; opacity: 1; }
          95% { opacity: 0; }
        }
        @keyframes karaoke {
          0% { background-position: -100% 0; }
          50%, 100% { background-position: 200% 0; }
        }
        @keyframes rainbow-wave {
          0% { filter: hue-rotate(0deg) saturate(1.5); transform: scale(1); }
          25% { filter: hue-rotate(90deg) saturate(2); transform: scale(1.1); }
          50% { filter: hue-rotate(180deg) saturate(1.5); transform: scale(1); }
          75% { filter: hue-rotate(270deg) saturate(2); transform: scale(1.1); }
          100% { filter: hue-rotate(360deg) saturate(1.5); transform: scale(1); }
        }
        @keyframes shake-pop {
          0%, 100% { transform: translateX(0) scale(1); }
          10% { transform: translateX(-4px) scale(1.05); }
          20% { transform: translateX(4px) scale(1.1); }
          30% { transform: translateX(-4px) scale(1.05); }
          40% { transform: translateX(4px) scale(1.1); }
          50% { transform: translateX(0) scale(1.15); }
          60% { transform: translateX(0) scale(1); }
        }
        @keyframes slide-bounce {
          0%, 100% { transform: translateY(8px); opacity: 0; }
          10% { transform: translateY(0); opacity: 1; }
          20% { transform: translateY(-4px); }
          30% { transform: translateY(0); }
          90% { transform: translateY(0); opacity: 1; }
        }
        @keyframes pulse-slow {
          0%, 100% { opacity: 0.3; }
          50% { opacity: 0.6; }
        }
        .animate-word-pop { animation: word-pop 0.8s ease-in-out infinite; }
        .animate-neon-flicker { animation: neon-flicker 2s ease-in-out infinite; }
        .animate-typewriter { animation: typewriter 2.5s steps(20) infinite; overflow: hidden; white-space: nowrap; }
        .animate-karaoke { 
          background: linear-gradient(90deg, #fbbf24 50%, #fff 50%);
          background-size: 200% 100%;
          -webkit-background-clip: text;
          background-clip: text;
          -webkit-text-fill-color: transparent;
          animation: karaoke 1.5s linear infinite;
        }
        .animate-rainbow-wave { animation: rainbow-wave 1.5s ease-in-out infinite; }
        .animate-shake-pop { animation: shake-pop 1.2s ease-in-out infinite; }
        .animate-slide-bounce { animation: slide-bounce 2s ease-in-out infinite; }
        .animate-pulse-slow { animation: pulse-slow 2s ease-in-out infinite; }
      `}</style>

      {/* Header */}
      <div className="text-center mb-5">
        <h1 className="text-xl sm:text-2xl font-bold mb-1">
          Choose{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Caption Style
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Select how captions will appear. Captions boost engagement and accessibility.
        </p>
      </div>

      {/* Caption Style Grid - Compact horizontal cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-6">
        {captionStyles.map((caption) => (
          <button
            key={caption.id}
            onClick={() => setSelectedCaption(caption.id)}
            className={`group relative rounded-xl border-2 transition-all duration-300 overflow-hidden ${
              selectedCaption === caption.id
                ? 'border-emerald-500 shadow-lg shadow-emerald-100/50 scale-105'
                : 'border-gray-200 hover:border-emerald-300 hover:shadow-md'
            }`}
          >
            {/* Compact Preview with animated text */}
            <div className={`h-16 ${caption.bg} relative overflow-hidden flex items-center justify-center px-3`}>
              <span 
                className={`${caption.textStyle} ${caption.animation}`}
                style={caption.outline ? { textShadow: '-1px -1px 0 #000, 1px -1px 0 #000, -1px 1px 0 #000, 1px 1px 0 #000' } : {}}
              >
                {caption.id === 'no-captions' ? '🔇' : 'Caption'}
              </span>

              {/* Selected indicator */}
              {selectedCaption === caption.id && (
                <div className="absolute top-1.5 right-1.5 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="p-2 bg-white">
              <h3 className="font-semibold text-gray-900 text-xs">{caption.name}</h3>
              <p className="text-[10px] text-gray-500 line-clamp-1">{caption.description}</p>
            </div>
          </button>
        ))}
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
          disabled={!selectedCaption}
          className={`group px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2 text-sm ${
            selectedCaption
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <span>Continue to Details</span>
          <ArrowRight className={`w-4 h-4 ${selectedCaption ? 'group-hover:translate-x-1' : ''} transition-transform`} />
        </button>
      </div>
    </div>
  )
}
