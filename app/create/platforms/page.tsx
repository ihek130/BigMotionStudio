'use client'

import { useState, useEffect } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Check, Instagram, Youtube, Loader2 } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

interface PlatformConnection {
  id: string
  platform: string
  platform_username: string
  is_active: boolean
}

const platforms = [
  {
    id: 'instagram',
    name: 'Instagram Reels',
    icon: Instagram,
    color: 'from-pink-500 to-purple-600',
    description: 'Post to Instagram Reels automatically',
    requirements: ['Business/Creator account', 'Public profile'],
  },
  {
    id: 'tiktok',
    name: 'TikTok',
    icon: () => (
      <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
        <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
      </svg>
    ),
    color: 'from-gray-900 to-gray-700',
    description: 'Publish videos to TikTok',
    requirements: ['TikTok account', 'API access approved'],
  },
  {
    id: 'youtube',
    name: 'YouTube Shorts',
    icon: Youtube,
    color: 'from-red-600 to-red-700',
    description: 'Upload to YouTube Shorts',
    requirements: ['YouTube channel', 'Channel verification'],
  },
]

export default function PlatformsPage() {
  const [connectedPlatforms, setConnectedPlatforms] = useState<Record<string, PlatformConnection>>({})
  const [selectedPlatforms, setSelectedPlatforms] = useState<string[]>([])
  const [loading, setLoading] = useState<string>('')
  const [initialLoading, setInitialLoading] = useState(true)
  const { updateData, data } = useWizard()
  const { user } = useAuth()
  const router = useRouter()

  // Get token from localStorage
  const getToken = () => {
    if (typeof window !== 'undefined') {
      return localStorage.getItem('reelflow_access_token')
    }
    return null
  }

  // Fetch connected platforms on mount
  useEffect(() => {
    fetchConnectedPlatforms()
    
    // Check if returning from OAuth (URL params indicate success)
    const urlParams = new URLSearchParams(window.location.search)
    const justConnected = urlParams.get('connected')
    
    if (justConnected) {
      // Remove the query param and refresh platforms
      window.history.replaceState({}, '', window.location.pathname)
      // Fetch will happen above anyway
    }
  }, [])

  const fetchConnectedPlatforms = async () => {
    try {
      const token = getToken()
      if (!token) {
        router.push('/login')
        return
      }
      
      const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'
      let response = await fetch(`${API_URL}/api/platforms/connections`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      // Handle 401 - try to refresh token
      if (response.status === 401) {
        const refreshToken = localStorage.getItem('reelflow_refresh_token')
        
        if (refreshToken) {
          try {
            const refreshResponse = await fetch(`${API_URL}/api/auth/refresh`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ refresh_token: refreshToken }),
            })
            
            if (refreshResponse.ok) {
              const tokens = await refreshResponse.json()
              localStorage.setItem('reelflow_access_token', tokens.access_token)
              localStorage.setItem('reelflow_refresh_token', tokens.refresh_token)
              
              // Retry with new token
              response = await fetch(`${API_URL}/api/platforms/connections`, {
                headers: {
                  'Authorization': `Bearer ${tokens.access_token}`,
                },
              })
            } else {
              // Refresh failed
              localStorage.removeItem('reelflow_access_token')
              localStorage.removeItem('reelflow_refresh_token')
              router.push('/login?expired=true')
              return
            }
          } catch {
            localStorage.removeItem('reelflow_access_token')
            localStorage.removeItem('reelflow_refresh_token')
            router.push('/login?expired=true')
            return
          }
        } else {
          router.push('/login')
          return
        }
      }
      
      if (response.ok) {
        const data = await response.json()
        const platformsMap: Record<string, PlatformConnection> = {}
        
        // Flatten the response structure
        if (data.youtube?.length > 0) {
          platformsMap['youtube'] = data.youtube[0]
        }
        if (data.tiktok?.length > 0) {
          platformsMap['tiktok'] = data.tiktok[0]
        }
        if (data.instagram?.length > 0) {
          platformsMap['instagram'] = data.instagram[0]
        }
        
        setConnectedPlatforms(platformsMap)
        
        // Auto-select all connected platforms by default
        setSelectedPlatforms(Object.keys(platformsMap))
      }
    } catch (error) {
      console.error('Error fetching connected platforms:', error)
    } finally {
      setInitialLoading(false)
    }
  }

  const [showInstagramNote, setShowInstagramNote] = useState(false)

  const handleConnectPlatform = async (platformId: string) => {
    // Show info note for Instagram before redirecting
    if (platformId === 'instagram' && !showInstagramNote) {
      setShowInstagramNote(true)
      return
    }
    setShowInstagramNote(false)
    setLoading(platformId)
    
    try {
      // Get OAuth URL from backend
      const token = getToken()
      const response = await fetch(`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')}/api/oauth/${platformId}/connect`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        // Redirect to OAuth URL
        window.location.href = data.auth_url
      }
    } catch (error) {
      console.error(`Error connecting to ${platformId}:`, error)
      setLoading('')
    }
  }

  const handleTogglePlatform = (platformId: string) => {
    setSelectedPlatforms(prev => 
      prev.includes(platformId)
        ? prev.filter(p => p !== platformId)
        : [...prev, platformId]
    )
  }

  const handleFinish = async () => {
    if (selectedPlatforms.length === 0) return
    
    setLoading('creating')
    
    try {
      // Update wizard context with selected platforms
      updateData({ platforms: selectedPlatforms })
      
      // Get token
      const token = getToken()
      if (!token) {
        router.push('/login')
        return
      }
      
      // Prepare series creation data
      const seriesData = {
        user_id: user?.id || 'guest',
        niche: data.niche || 'scary-stories',
        nicheFormat: data.nicheFormat || 'storytelling',
        style: data.style || 'dark-comic',
        voiceId: data.voiceId || 'male-deep',
        musicId: data.musicId || 'ambient',
        captionStyle: data.captionStyle || 'modern-bold',
        videoDuration: data.videoDuration || 60,
        seriesName: data.seriesName || 'My Series',
        description: data.description || '',
        postingTimes: data.postingTimes || ['09:00'],
        platforms: selectedPlatforms
      }
      
      // Call backend to create series
      const response = await fetch(`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')}/api/series/create`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(seriesData)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.detail || 'Failed to create series')
      }
      
      const result = await response.json()
      console.log('Series created:', result)
      
      // Redirect to dashboard
      router.push('/dashboard')
      
    } catch (error) {
      console.error('Failed to create series:', error)
      alert(error instanceof Error ? error.message : 'Failed to create series. Please try again.')
      setLoading('')
    }
  }

  const handleBack = () => {
    router.push('/create/details')
  }

  if (initialLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="flex flex-col items-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
          <p className="text-sm text-gray-600">Loading platforms...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-4">
        <h1 className="text-xl sm:text-2xl font-bold mb-1">
          Connect Your{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Social Platforms
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Link your social accounts to start posting automatically.
        </p>
      </div>

      {/* Platform Cards - Horizontal layout */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mb-5">
        {platforms.map((platform) => {
          const Icon = platform.icon
          const connection = connectedPlatforms[platform.id]
          const isConnected = !!connection
          const isSelected = selectedPlatforms.includes(platform.id)
          const isLoading = loading === platform.id

          return (
            <div
              key={platform.id}
              className={`relative bg-white rounded-xl border-2 p-4 transition-all duration-300 ${
                isConnected && isSelected
                  ? 'border-emerald-500 shadow-md shadow-emerald-100/50'
                  : isConnected
                  ? 'border-gray-300'
                  : 'border-gray-200 hover:border-gray-300 hover:shadow-md'
              }`}
            >
              <div className="flex items-center space-x-3 mb-3">
                {/* Icon */}
                <div className={`w-10 h-10 bg-gradient-to-br ${platform.color} rounded-lg flex items-center justify-center text-white shadow-md flex-shrink-0`}>
                  <Icon className="w-5 h-5" />
                </div>

                {/* Info */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-sm font-bold text-gray-900">{platform.name}</h3>
                  {isConnected ? (
                    <p className="text-xs text-emerald-600 font-medium">@{connection.platform_username}</p>
                  ) : (
                    <p className="text-xs text-gray-500 truncate">{platform.description}</p>
                  )}
                </div>
              </div>

              {/* Toggle for connected platforms, Connect button for non-connected */}
              {isConnected ? (
                <div className="flex items-center justify-between">
                  <span className="text-xs text-gray-600">Include in series</span>
                  <button
                    onClick={() => handleTogglePlatform(platform.id)}
                    className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                      isSelected ? 'bg-emerald-500' : 'bg-gray-300'
                    }`}
                  >
                    <span
                      className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                        isSelected ? 'translate-x-6' : 'translate-x-1'
                      }`}
                    />
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => handleConnectPlatform(platform.id)}
                  disabled={isLoading}
                  className={`w-full py-2 rounded-lg font-semibold transition-all flex items-center justify-center space-x-1.5 text-xs bg-gray-100 hover:bg-gray-200 text-gray-700 ${
                    isLoading ? 'opacity-50 cursor-not-allowed' : ''
                  }`}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="w-4 h-4 animate-spin" />
                      <span>Connecting...</span>
                    </>
                  ) : (
                    <span>Connect</span>
                  )}
                </button>
              )}
            </div>
          )
        })}
      </div>

      {/* Instagram Info Note Modal */}
      {showInstagramNote && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-sm w-full p-5 shadow-xl">
            <div className="flex items-center space-x-2 mb-3">
              <div className="w-8 h-8 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 rounded-lg flex items-center justify-center text-white">
                <Instagram className="w-4 h-4" />
              </div>
              <h3 className="text-base font-bold text-gray-900">Before you continue</h3>
            </div>
            <div className="bg-amber-50 border border-amber-200 rounded-lg p-3 mb-4">
              <p className="text-sm text-amber-800 leading-relaxed">
                You&apos;ll be redirected to <span className="font-semibold">Facebook</span> first &mdash; this is completely normal. Instagram uses Meta&apos;s login system.
              </p>
              <ul className="mt-2 space-y-1.5 text-sm text-amber-800">
                <li className="flex items-start space-x-2">
                  <span className="text-amber-500 mt-0.5">1.</span>
                  <span>Select the <span className="font-semibold">Facebook Page</span> linked to your Instagram account</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-amber-500 mt-0.5">2.</span>
                  <span>Grant the requested permissions</span>
                </li>
                <li className="flex items-start space-x-2">
                  <span className="text-amber-500 mt-0.5">3.</span>
                  <span>Your Instagram account will be connected automatically</span>
                </li>
              </ul>
            </div>
            <p className="text-xs text-gray-500 mb-4">
              <span className="font-semibold">Requirements:</span> Your Instagram must be a Business or Creator account linked to a Facebook Page.
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowInstagramNote(false)}
                className="flex-1 py-2.5 text-sm text-gray-600 font-medium hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
              >
                Cancel
              </button>
              <button
                onClick={() => handleConnectPlatform('instagram')}
                className="flex-1 py-2.5 text-sm text-white font-semibold bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 rounded-lg transition-all shadow-md"
              >
                Continue to Facebook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Info Box - Compact */}
      <div className="bg-gradient-to-br from-blue-50 to-indigo-50 border border-blue-200 rounded-lg p-3 mb-5">
        <div className="flex items-start space-x-2">
          <svg className="w-4 h-4 text-blue-600 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7-4a1 1 0 11-2 0 1 1 0 012 0zM9 9a1 1 0 000 2v3a1 1 0 001 1h1a1 1 0 100-2v-3a1 1 0 00-1-1H9z" clipRule="evenodd" />
          </svg>
          <p className="text-xs text-blue-800">
            <span className="font-semibold">Privacy:</span> We use secure OAuth. We never store your passwords.
          </p>
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
          onClick={handleFinish}
          disabled={selectedPlatforms.length === 0}
          className={`group px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2 text-sm ${
            selectedPlatforms.length > 0
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <span>Create Series</span>
        </button>
      </div>
    </div>
  )
}
