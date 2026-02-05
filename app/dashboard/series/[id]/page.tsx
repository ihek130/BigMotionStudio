'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Calendar, Play, Clock, Check, Loader2, Plus, Youtube, Instagram } from 'lucide-react'

interface Video {
  id: string
  title: string
  thumbnail: string
  duration: number
  created_at: string
  status: 'generating' | 'ready' | 'published' | 'failed'
  platforms: {
    youtube?: 'published' | 'scheduled' | 'failed'
    tiktok?: 'published' | 'scheduled' | 'failed'
    instagram?: 'published' | 'scheduled' | 'failed'
  }
}

interface ConnectedAccount {
  id: string
  platform: 'youtube' | 'tiktok' | 'instagram'
  username: string
  enabled: boolean
}

const TikTokIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
)

export default function SeriesDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeTab, setActiveTab] = useState<'videos' | 'calendar'>('videos')
  const [loading, setLoading] = useState(true)
  const [seriesName, setSeriesName] = useState('Dark Mysteries')
  const [videos, setVideos] = useState<Video[]>([])
  const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([])

  useEffect(() => {
    fetchSeriesData()
  }, [params.id])

  const fetchSeriesData = async () => {
    setLoading(true)
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('reelflow_access_token') : null
      
      if (!token) {
        router.push('/login')
        return
      }
      
      const response = await fetch(`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')}/api/series/${params.id}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        
        setSeriesName(data.name)
        
        // Map videos
        if (data.videos) {
          setVideos(data.videos.map((v: any) => ({
            id: v.id,
            title: v.title || 'Untitled Video',
            thumbnail: v.thumbnailPath || '/placeholder-video.jpg',
            duration: Math.floor(v.durationSeconds || 60),
            created_at: v.createdAt,
            status: v.status as 'generating' | 'ready' | 'published' | 'failed',
            platforms: {
              ...(v.youtubeUrl ? { youtube: 'published' as const } : {}),
              ...(v.tiktokUrl ? { tiktok: 'published' as const } : {}),
              ...(v.instagramUrl ? { instagram: 'published' as const } : {})
            }
          })))
        }
        
        // TODO: Fetch connected accounts from platforms endpoint
        setConnectedAccounts([
          { id: '1', platform: 'youtube', username: 'Channel Name', enabled: true },
          { id: '2', platform: 'tiktok', username: '@username', enabled: true }
        ])
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch series:', error)
      setLoading(false)
    }
  }

  const toggleAccount = (accountId: string) => {
    setConnectedAccounts(prev =>
      prev.map(acc =>
        acc.id === accountId ? { ...acc, enabled: !acc.enabled } : acc
      )
    )
  }

  const removeAccount = (accountId: string) => {
    setConnectedAccounts(prev => prev.filter(acc => acc.id !== accountId))
  }

  const breadcrumbItems = [
    { label: 'Series', href: '/dashboard' },
    { label: seriesName }
  ]

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'youtube':
        return <Youtube className="w-5 h-5" />
      case 'tiktok':
        return <TikTokIcon className="w-5 h-5" />
      case 'instagram':
        return <Instagram className="w-5 h-5" />
      default:
        return null
    }
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      generating: 'bg-yellow-100 text-yellow-700',
      ready: 'bg-green-100 text-green-700',
      published: 'bg-blue-100 text-blue-700',
      failed: 'bg-red-100 text-red-700'
    }
    
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${styles[status as keyof typeof styles]}`}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </span>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="flex-1 lg:ml-64">
        {/* Header */}
        <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex items-center space-x-3">
              <MobileMenuButton onClick={() => setSidebarOpen(true)} />
              <Breadcrumb items={breadcrumbItems} />
            </div>
          </div>

          {/* Tabs */}
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-6 border-b border-gray-200">
              <button
                onClick={() => setActiveTab('videos')}
                className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                  activeTab === 'videos'
                    ? 'text-emerald-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Videos
                {activeTab === 'videos' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600" />
                )}
              </button>
              <button
                onClick={() => setActiveTab('calendar')}
                className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                  activeTab === 'calendar'
                    ? 'text-emerald-600'
                    : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Calendar
                {activeTab === 'calendar' && (
                  <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600" />
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          {loading ? (
            <div className="flex items-center justify-center py-12">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-600" />
            </div>
          ) : activeTab === 'videos' ? (
            <div className="space-y-6">
              {/* Generated Shorts Section */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Generated Shorts</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      Your videos will appear here as they are generated.
                    </p>
                  </div>
                  {getStatusBadge(videos.length > 0 ? 'ready' : 'generating')}
                </div>

                {/* Videos Grid */}
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                  {videos.map((video) => (
                    <button
                      key={video.id}
                      onClick={() => router.push(`/dashboard/series/${params.id}/video/${video.id}`)}
                      className="group relative bg-gray-100 rounded-lg overflow-hidden hover:shadow-lg transition-all border-2 border-transparent hover:border-emerald-500"
                    >
                      {/* Thumbnail */}
                      <div className="aspect-[9/16] bg-gradient-to-br from-gray-200 to-gray-300 flex items-center justify-center relative">
                        <Play className="w-12 h-12 text-white opacity-0 group-hover:opacity-100 transition-opacity" />
                        <div className="absolute top-2 right-2 bg-black/70 text-white text-xs px-2 py-1 rounded">
                          {video.duration}s
                        </div>
                      </div>

                      {/* Info */}
                      <div className="p-3">
                        <h3 className="font-semibold text-sm text-gray-900 line-clamp-2 text-left mb-2">
                          {video.title}
                        </h3>
                        <div className="flex items-center space-x-2">
                          {Object.entries(video.platforms).map(([platform, status]) => (
                            <div
                              key={platform}
                              className={`text-xs px-2 py-1 rounded ${
                                status === 'published'
                                  ? 'bg-green-100 text-green-700'
                                  : status === 'scheduled'
                                  ? 'bg-blue-100 text-blue-700'
                                  : 'bg-red-100 text-red-700'
                              }`}
                            >
                              {platform}
                            </div>
                          ))}
                        </div>
                      </div>
                    </button>
                  ))}
                </div>

                {videos.length === 0 && (
                  <div className="text-center py-12">
                    <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">No videos generated yet</p>
                    <p className="text-sm text-gray-400 mt-1">Videos will appear here soon</p>
                  </div>
                )}
              </div>

              {/* Connected Accounts Section */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Connected Accounts</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      You can connect multiple accounts to the same campaign.
                    </p>
                  </div>
                  <Link
                    href="/dashboard/settings"
                    className="flex items-center space-x-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold rounded-lg transition-colors"
                  >
                    <Plus className="w-4 h-4" />
                    <span>Connect Account</span>
                  </Link>
                </div>

                <div className="space-y-3">
                  {connectedAccounts.map((account) => (
                    <div
                      key={account.id}
                      className="flex items-center justify-between p-4 border border-gray-200 rounded-lg"
                    >
                      <div className="flex items-center space-x-3">
                        <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                          account.platform === 'youtube'
                            ? 'bg-red-100 text-red-600'
                            : account.platform === 'tiktok'
                            ? 'bg-gray-900 text-white'
                            : 'bg-pink-100 text-pink-600'
                        }`}>
                          {getPlatformIcon(account.platform)}
                        </div>
                        <div>
                          <p className="font-semibold text-sm text-gray-900">{account.username}</p>
                          <p className="text-xs text-gray-500 capitalize">{account.platform}</p>
                        </div>
                      </div>

                      <div className="flex items-center space-x-3">
                        {/* Toggle */}
                        <button
                          onClick={() => toggleAccount(account.id)}
                          className={`relative inline-flex h-6 w-11 items-center rounded-full transition-colors ${
                            account.enabled ? 'bg-emerald-500' : 'bg-gray-300'
                          }`}
                        >
                          <span
                            className={`inline-block h-4 w-4 transform rounded-full bg-white transition-transform ${
                              account.enabled ? 'translate-x-6' : 'translate-x-1'
                            }`}
                          />
                        </button>

                        {/* Remove */}
                        <button
                          onClick={() => removeAccount(account.id)}
                          className="p-2 text-gray-400 hover:text-red-600 transition-colors"
                        >
                          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                          </svg>
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-12 text-center">
              <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-semibold text-gray-900 mb-2">Calendar View</h3>
              <p className="text-gray-500">Coming soon</p>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
