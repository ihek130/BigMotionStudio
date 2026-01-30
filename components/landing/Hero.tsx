'use client'

import { ArrowRight, Instagram, Youtube, Volume2, VolumeX } from 'lucide-react'
import Link from 'next/link'
import { useState, useRef, useEffect, createContext, useContext } from 'react'

const niches = [
  { emoji: '🔥', name: 'Horror', video: '/landing-samples/scary-stories.mp4', views: '2.3M' },
  { emoji: '🕵️', name: 'Crime', video: '/landing-samples/true-crime.mp4', views: '1.8M' },
  { emoji: '📚', name: 'History', video: '/landing-samples/history.mp4', views: '3.2M' },
  { emoji: '🧠', name: 'Psychology', video: '/landing-samples/psychology.mp4', views: '1.2M' },
  { emoji: '💪', name: 'Motivation', video: '/landing-samples/stoic-motivation.mp4', views: '4.1M' },
  { emoji: '💡', name: 'Facts', video: '/landing-samples/random-fact.mp4', views: '2.7M' },
  { emoji: '✨', name: 'Wisdom', video: '/landing-samples/good-morals.mp4', views: '1.5M' },
]

// Video cache context to share preloaded videos
const VideoCache = createContext<Map<string, string>>(new Map())

// Preload all videos and convert to blob URLs for instant playback
function usePreloadVideos() {
  const [videoCache, setVideoCache] = useState<Map<string, string>>(new Map())
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    const cache = new Map<string, string>()
    let isMounted = true

    async function preloadVideos() {
      const promises = niches.map(async (niche) => {
        try {
          const response = await fetch(niche.video)
          const blob = await response.blob()
          const blobUrl = URL.createObjectURL(blob)
          cache.set(niche.video, blobUrl)
        } catch (error) {
          // Fallback to original URL if fetch fails
          cache.set(niche.video, niche.video)
        }
      })

      await Promise.all(promises)
      
      if (isMounted) {
        setVideoCache(cache)
        setIsLoading(false)
      }
    }

    preloadVideos()

    return () => {
      isMounted = false
      // Cleanup blob URLs on unmount
      cache.forEach((blobUrl) => {
        if (blobUrl.startsWith('blob:')) {
          URL.revokeObjectURL(blobUrl)
        }
      })
    }
  }, [])

  return { videoCache, isLoading }
}

function VideoCard({ niche, index, setKey, cachedVideoUrl }: { niche: typeof niches[0], index: number, setKey: string, cachedVideoUrl?: string }) {
  const [isMuted, setIsMuted] = useState(true)
  const videoRef = useRef<HTMLVideoElement>(null)

  const toggleMute = (e: React.MouseEvent) => {
    e.stopPropagation()
    if (videoRef.current) {
      videoRef.current.muted = !videoRef.current.muted
      setIsMuted(!isMuted)
    }
  }

  // Use cached blob URL or original URL
  const videoSrc = cachedVideoUrl || niche.video

  return (
    <div
      key={`${setKey}-${index}`}
      className="flex-shrink-0 w-28 sm:w-32 aspect-[9/16] rounded-xl overflow-hidden cursor-pointer transition-transform duration-300 hover:scale-105 relative group"
    >
      {/* Video Background - preloaded */}
      <video
        ref={videoRef}
        src={videoSrc}
        className="absolute inset-0 w-full h-full object-cover"
        autoPlay
        loop
        muted
        playsInline
      />
      
      {/* Overlay for text readability */}
      <div className="absolute inset-0 bg-gradient-to-t from-black/70 via-black/20 to-black/30" />
      
      {/* Content */}
      <div className="absolute inset-0 flex flex-col items-center justify-center p-3 text-white">
        <div className="absolute top-2 right-2 px-1.5 py-0.5 bg-white/20 backdrop-blur-sm rounded-full text-[8px] font-medium border border-white/30">
          Sample
        </div>
        
        {/* Speaker Icon - shows on hover */}
        <button
          onClick={toggleMute}
          className="absolute top-2 left-2 p-1.5 bg-black/50 backdrop-blur-sm rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-black/70"
        >
          {isMuted ? (
            <VolumeX className="w-3 h-3 text-white" />
          ) : (
            <Volume2 className="w-3 h-3 text-white" />
          )}
        </button>
        
        <div className="text-2xl sm:text-3xl mb-1 drop-shadow-lg">{niche.emoji}</div>
        <h3 className="text-xs sm:text-sm font-bold mb-0.5 drop-shadow-lg">{niche.name}</h3>
        <div className="flex items-center space-x-1 text-[8px] sm:text-[10px] opacity-90">
          <svg className="w-2.5 h-2.5" fill="currentColor" viewBox="0 0 20 20">
            <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
            <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
          </svg>
          <span>{niche.views} views</span>
        </div>
      </div>
    </div>
  )
}

export default function Hero() {
  const { videoCache, isLoading } = usePreloadVideos()

  return (
    <section className="relative pt-20 pb-8 sm:pt-24 sm:pb-12 overflow-hidden">
      {/* Background gradient - Premium floral green */}
      <div className="absolute inset-0 bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50 opacity-70" />
      <div className="absolute inset-0" style={{
        backgroundImage: `radial-gradient(circle at 25% 25%, rgba(52, 211, 153, 0.08) 0%, transparent 50%),
                         radial-gradient(circle at 75% 75%, rgba(16, 185, 129, 0.08) 0%, transparent 50%),
                         radial-gradient(circle at 50% 50%, rgba(6, 78, 59, 0.03) 0%, transparent 100%)`
      }} />
      
      <div className="relative max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center max-w-4xl mx-auto">
          {/* Badge */}
          <div className="inline-flex items-center space-x-2 px-3 py-1.5 bg-white/90 backdrop-blur-sm border border-emerald-200 rounded-full mb-3 shadow-md shadow-emerald-100/50">
            <svg className="w-3.5 h-3.5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <span className="text-xs font-semibold bg-gradient-to-r from-emerald-700 to-teal-700 bg-clip-text text-transparent">
              Trusted by 307,000+ creators
            </span>
          </div>

          {/* Heading */}
          <h1 className="text-2xl sm:text-3xl lg:text-4xl font-bold mb-2">
            Create Viral{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Short-Form Videos
            </span>
            <br className="hidden sm:block" />
            <span className="block mt-1">On Complete Autopilot</span>
          </h1>

          {/* Description */}
          <p className="text-xs sm:text-sm text-gray-600 mb-3 max-w-md mx-auto">
            The AI that generates & posts to Instagram Reels, TikTok, and YouTube Shorts automatically—even while you sleep.
          </p>

          {/* Platform badges */}
          <div className="flex items-center justify-center space-x-3 mb-4">
            <div className="flex items-center space-x-1 text-gray-700">
              <div className="w-5 h-5 bg-gradient-to-br from-pink-500 to-purple-600 rounded flex items-center justify-center">
                <Instagram className="w-2.5 h-2.5 text-white" />
              </div>
              <span className="text-[10px] font-medium">Instagram</span>
            </div>
            <div className="flex items-center space-x-1 text-gray-700">
              <div className="w-5 h-5 bg-black rounded flex items-center justify-center">
                <svg className="w-2.5 h-2.5 text-white" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
                </svg>
              </div>
              <span className="text-[10px] font-medium">TikTok</span>
            </div>
            <div className="flex items-center space-x-1 text-gray-700">
              <div className="w-5 h-5 bg-red-600 rounded flex items-center justify-center">
                <Youtube className="w-2.5 h-2.5 text-white" />
              </div>
              <span className="text-[10px] font-medium">YouTube</span>
            </div>
          </div>

          {/* CTA Button - 1.5x bigger */}
          <div className="flex justify-center mb-6">
            <Link
              href="/login"
              className="group px-8 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-semibold rounded-xl transition-all hover:shadow-xl hover:shadow-emerald-500/30 transform hover:-translate-y-0.5 flex items-center space-x-2"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
              <span>Start Creating Now</span>
              <ArrowRight className="w-5 h-5 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </div>
        </div>

        {/* Video Showcase Section */}
        <div className="text-center mb-6">
          <h2 className="text-xl sm:text-2xl font-bold mb-2">
            Creates Videos for{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Any Niche
            </span>
          </h2>
          <p className="text-xs sm:text-sm text-gray-600 max-w-md mx-auto">
            From horror to history, motivation to wisdom—our AI creates engaging content for every topic
          </p>
        </div>

        {/* Infinite Looping Carousel */}
        <div className="relative overflow-hidden mb-6">
          {/* Fade edges */}
          <div className="absolute left-0 top-0 bottom-0 w-16 bg-gradient-to-r from-emerald-50/90 to-transparent z-10 pointer-events-none" />
          <div className="absolute right-0 top-0 bottom-0 w-16 bg-gradient-to-l from-emerald-50/90 to-transparent z-10 pointer-events-none" />
          
          {/* Loading state */}
          {isLoading && (
            <div className="flex gap-4 justify-center py-4">
              {niches.map((niche, index) => (
                <div
                  key={`loading-${index}`}
                  className="flex-shrink-0 w-28 sm:w-32 aspect-[9/16] rounded-xl bg-gradient-to-br from-gray-200 to-gray-300 animate-pulse"
                />
              ))}
            </div>
          )}
          
          {/* Carousel track - only show when loaded */}
          {!isLoading && (
            <div className="group flex hover:[animation-play-state:paused]">
              <div className="flex gap-4 animate-scroll hover:[animation-play-state:paused]">
                {/* First set of cards */}
                {niches.map((niche, index) => (
                  <VideoCard 
                    key={`first-${index}`} 
                    niche={niche} 
                    index={index} 
                    setKey="first" 
                    cachedVideoUrl={videoCache.get(niche.video)}
                  />
                ))}
                {/* Duplicate set for seamless loop */}
                {niches.map((niche, index) => (
                  <VideoCard 
                    key={`second-${index}`} 
                    niche={niche} 
                    index={index} 
                    setKey="second" 
                    cachedVideoUrl={videoCache.get(niche.video)}
                  />
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Trust indicators */}
        <div className="flex flex-wrap items-center justify-center gap-3 sm:gap-6 text-[10px] sm:text-xs text-gray-600">
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>No filming required</span>
          </div>
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>No editing needed</span>
          </div>
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>100% automated</span>
          </div>
        </div>
      </div>

      {/* CSS for infinite scroll animation */}
      <style jsx>{`
        @keyframes scroll {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .animate-scroll {
          animation: scroll 40s linear infinite;
        }
        .animate-scroll:hover {
          animation-play-state: paused;
        }
      `}</style>
    </section>
  )
}
