'use client'

import { useState, useEffect } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useRouter } from 'next/navigation'
import { ArrowRight, ArrowLeft } from 'lucide-react'
import Image from 'next/image'
import Head from 'next/head'

const styles = [
  {
    id: 'dark-comic',
    name: 'Dark Comic',
    description: 'Noir comic book style with dramatic shadows',
    preview: '/style-previews/dark-comic.png',
    gradient: 'from-gray-900 to-gray-700',
  },
  {
    id: 'anime',
    name: 'Anime',
    description: 'Japanese animation aesthetic',
    preview: '/style-previews/anime.png',
    gradient: 'from-pink-500 to-purple-600',
  },
  {
    id: 'lego',
    name: 'LEGO',
    description: 'Brick-built scenes and characters',
    preview: '/style-previews/lego.png',
    gradient: 'from-yellow-400 to-red-500',
  },
  {
    id: 'realistic',
    name: 'Photorealistic',
    description: 'Lifelike AI-generated imagery',
    preview: '/style-previews/realistic.png',
    gradient: 'from-emerald-500 to-teal-600',
  },
  {
    id: 'cyberpunk',
    name: 'Cyberpunk',
    description: 'Neon-lit futuristic scenes',
    preview: '/style-previews/cyberpunk.png',
    gradient: 'from-cyan-500 to-blue-600',
  },
  {
    id: '3d-render',
    name: '3D Render',
    description: 'Clean 3D rendered graphics',
    preview: '/style-previews/3d-render.png',
    gradient: 'from-orange-500 to-red-600',
  },
  {
    id: 'watercolor',
    name: 'Watercolor',
    description: 'Soft painted artistic style',
    preview: '/style-previews/watercolor.png',
    gradient: 'from-blue-400 to-indigo-500',
  },
  {
    id: 'minimalist',
    name: 'Minimalist',
    description: 'Simple, clean vector graphics',
    preview: '/style-previews/minimalist.png',
    gradient: 'from-gray-600 to-gray-800',
  },
  {
    id: 'fantasy',
    name: 'Fantasy Art',
    description: 'Epic fantasy illustrations',
    preview: '/style-previews/fantasy.png',
    gradient: 'from-purple-600 to-indigo-700',
  },
  {
    id: 'retro',
    name: 'Retro',
    description: '80s/90s vintage aesthetic',
    preview: '/style-previews/retro.png',
    gradient: 'from-pink-400 to-orange-500',
  },
]

export default function StyleSelectionPage() {
  const [selectedStyle, setSelectedStyle] = useState<string>('')
  const { updateData, data } = useWizard()
  const router = useRouter()

  // Preload all images on mount
  useEffect(() => {
    styles.forEach((style) => {
      const img = new window.Image()
      img.src = style.preview
    })
  }, [])

  const handleContinue = () => {
    if (selectedStyle) {
      updateData({ style: selectedStyle })
      router.push('/create/voice')
    }
  }

  const handleBack = () => {
    router.push('/create')
  }

  return (
    <div className="max-w-7xl mx-auto">
      {/* Header */}
      <div className="text-center mb-5">
        <h1 className="text-xl sm:text-2xl font-bold mb-2">
          Select Your{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Visual Style
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Choose the artistic style for your {data.niche} videos.
        </p>
      </div>

      {/* Style Grid - More compact */}
      <div className="grid grid-cols-3 sm:grid-cols-4 lg:grid-cols-5 gap-3 mb-6">
        {styles.map((style) => (
          <button
            key={style.id}
            onClick={() => setSelectedStyle(style.id)}
            className={`group relative rounded-xl border-2 transition-all duration-300 overflow-hidden ${
              selectedStyle === style.id
                ? 'border-emerald-500 shadow-lg shadow-emerald-100/50 scale-105'
                : 'border-gray-200 hover:border-emerald-300 hover:shadow-md'
            }`}
          >
            {/* Preview Image */}
            <div className="aspect-[3/4] relative overflow-hidden bg-gray-100">
              <Image
                src={style.preview}
                alt={`${style.name} style preview`}
                fill
                priority
                loading="eager"
                className="object-cover"
                sizes="(max-width: 640px) 33vw, (max-width: 1024px) 25vw, 20vw"
              />
              
              {/* Selected indicator */}
              {selectedStyle === style.id && (
                <div className="absolute top-2 right-2 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shadow-md z-10">
                  <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                </div>
              )}
            </div>

            {/* Info */}
            <div className="p-2 bg-white">
              <h3 className="font-semibold text-gray-900 text-xs">{style.name}</h3>
              <p className="text-[10px] text-gray-600 line-clamp-1">{style.description}</p>
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
          disabled={!selectedStyle}
          className={`group px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2 text-sm ${
            selectedStyle
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <span>Continue to Voice & Music</span>
          <ArrowRight className={`w-4 h-4 ${selectedStyle ? 'group-hover:translate-x-1' : ''} transition-transform`} />
        </button>
      </div>
    </div>
  )
}
