'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Calendar, Play, Clock, Check, Loader2, Plus, Youtube, Instagram, Sparkles, AlertCircle } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Video {
  id: string
  title: string
  thumbnail: string
  duration: number
  created_at: string
  status: 'generating' | 'ready' | 'published' | 'failed' | 'pending'
  progress: number
  currentStage: string
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
  isActive: boolean
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
  const [generating, setGenerating] = useState(false)
  const [seriesName, setSeriesName] = useState('')
  const [seriesStatus, setSeriesStatus] = useState('active')
  const [videos, setVideos] = useState<Video[]>([])
  const [connectedAccounts, setConnectedAccounts] = useState<ConnectedAccount[]>([])
  const [thumbnailUrls, setThumbnailUrls] = useState<Record<string, string>>({})

  const getToken = () => typeof window !== 'undefined' ? localStorage.getItem('reelflow_access_token') : null

  // Fetch thumbnail blob URLs for ready videos
  const fetchThumbnails = async (videoList: Video[]) => {
    const token = getToken()
    if (!token) return
    const readyVideos = videoList.filter(v => v.status === 'ready' || v.status === 'published')
    const newUrls: Record<string, string> = { ...thumbnailUrls }
    await Promise.all(readyVideos.map(async (v) => {
      if (newUrls[v.id]) return // already fetched
      try {
        const res = await fetch(`${API_URL}/api/videos/${v.id}/thumbnail`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
        if (res.ok) {
          const blob = await res.blob()
          newUrls[v.id] = URL.createObjectURL(blob)
        }
      } catch { /* ignore */ }
    }))
    setThumbnailUrls(newUrls)
  }

  useEffect(() => {
    fetchSeriesData()
  }, [params.id])

  // Poll for generating videos
  useEffect(() => {
    const hasGenerating = videos.some(v => v.status === 'generating' || v.status === 'pending')
    if (!hasGenerating) return

    const interval = setInterval(() => {
      fetchSeriesData()
    }, 8000)

    return () => clearInterval(interval)
  }, [videos])

  const fetchSeriesData = async () => {
    try {
      const token = getToken()
      if (!token) { router.push('/login'); return }

      const response = await fetch(`${API_URL}/api/series/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })

      if (response.ok) {
        const data = await response.json()
        setSeriesName(data.name)
        setSeriesStatus(data.status)

        if (data.videos) {
          const videoList = data.videos.map((v: any) => ({
            id: v.id,
            title: v.title || 'Untitled Video',
            thumbnail: v.thumbnailPath || '',
            duration: Math.floor(v.durationSeconds || 0),
            created_at: v.createdAt,
            status: v.status as Video['status'],
            progress: v.progress || 0,
            currentStage: v.currentStage || '',
            platforms: {
              ...(v.youtubeUrl ? { youtube: 'published' as const } : {}),
              ...(v.tiktokUrl ? { tiktok: 'published' as const } : {}),
              ...(v.instagramUrl ? { instagram: 'published' as const } : {})
            }
          }))
          setVideos(videoList)
          fetchThumbnails(videoList)
        }

        // Fetch real connected accounts
        fetchConnectedAccounts(token)
      }

      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch series:', error)
      setLoading(false)
    }
  }

  const fetchConnectedAccounts = async (token: string) => {
    try {
      const response = await fetch(`${API_URL}/api/platforms/connections`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        const data = await response.json()
        const accounts: ConnectedAccount[] = []

        if (data.youtube?.length > 0) {
          data.youtube.forEach((c: any) => accounts.push({
            id: c.id, platform: 'youtube', username: c.username || c.platform_username || 'YouTube Channel', isActive: c.status === 'active'
          }))
        }
        if (data.tiktok?.length > 0) {
          data.tiktok.forEach((c: any) => accounts.push({
            id: c.id, platform: 'tiktok', username: c.username || c.platform_username || '@TikTok', isActive: c.status === 'active'
          }))
        }
        if (data.instagram?.length > 0) {
          data.instagram.forEach((c: any) => accounts.push({
            id: c.id, platform: 'instagram', username: c.username || c.platform_username || 'Instagram', isActive: c.status === 'active'
          }))
        }

        setConnectedAccounts(accounts)
      }
    } catch (e) {
      console.error('Failed to fetch connected accounts:', e)
    }
  }

  const handleGenerateVideo = async () => {
    const token = getToken()
    if (!token) return
    setGenerating(true)
    try {
      const response = await fetch(`${API_URL}/api/series/${params.id}/generate`, {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (response.ok) {
        await fetchSeriesData()
      } else {
        const err = await response.json()
        alert(err.detail || 'Failed to start generation')
      }
    } catch (e) {
      console.error('Failed to generate:', e)
    } finally {
      setGenerating(false)
    }
  }

  const breadcrumbItems = [
    { label: 'Series', href: '/dashboard' },
    { label: seriesName || 'Loading...' }
  ]

  const getPlatformIcon = (platform: string) => {
    switch (platform) {
      case 'youtube': return <Youtube className="w-5 h-5" />
      case 'tiktok': return <TikTokIcon className="w-5 h-5" />
      case 'instagram': return <Instagram className="w-5 h-5" />
      default: return null
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, string> = {
      generating: 'bg-yellow-100 text-yellow-700',
      pending: 'bg-yellow-100 text-yellow-700',
      ready: 'bg-green-100 text-green-700',
      published: 'bg-blue-100 text-blue-700',
      failed: 'bg-red-100 text-red-700'
    }
    return (
      <span className={`px-2 py-1 text-xs font-semibold rounded-full ${styles[status] || 'bg-gray-100 text-gray-700'}`}>
        {status === 'generating' || status === 'pending' ? 'Generating...' : status.charAt(0).toUpperCase() + status.slice(1)}
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
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                <MobileMenuButton onClick={() => setSidebarOpen(true)} />
                <Breadcrumb items={breadcrumbItems} />
              </div>
              <button
                onClick={handleGenerateVideo}
                disabled={generating || seriesStatus !== 'active'}
                className="flex items-center space-x-2 px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all disabled:opacity-50 disabled:cursor-not-allowed text-sm"
              >
                {generating ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                <span>{generating ? 'Starting...' : 'Generate Video'}</span>
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="px-4 sm:px-6 lg:px-8">
            <div className="flex space-x-6 border-b border-gray-200">
              <button
                onClick={() => setActiveTab('videos')}
                className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                  activeTab === 'videos' ? 'text-emerald-600' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Videos
                {activeTab === 'videos' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600" />}
              </button>
              <button
                onClick={() => setActiveTab('calendar')}
                className={`pb-3 px-1 font-medium text-sm transition-colors relative ${
                  activeTab === 'calendar' ? 'text-emerald-600' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                Calendar
                {activeTab === 'calendar' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-emerald-600" />}
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
              {/* Generated Shorts */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Generated Shorts</h2>
                    <p className="text-sm text-gray-500 mt-1">
                      {videos.length} video{videos.length !== 1 ? 's' : ''} generated
                    </p>
                  </div>
                </div>

                <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 2xl:grid-cols-6 gap-3">
                  {videos.map((video) => (
                    <div key={video.id} className="group relative bg-gray-100 rounded-lg overflow-hidden hover:shadow-lg transition-all border border-gray-200 hover:border-emerald-500 max-w-[200px]">
                      {video.status === 'generating' || video.status === 'pending' ? (
                        <div className="aspect-[9/16] bg-gradient-to-br from-gray-800 to-gray-900 flex flex-col items-center justify-center">
                          <Loader2 className="w-6 h-6 text-emerald-400 animate-spin mb-2" />
                          <p className="text-white text-xs font-medium">Generating...</p>
                          <p className="text-gray-400 text-[10px] mt-0.5 capitalize">{video.currentStage || 'Initializing'}</p>
                          {video.progress > 0 && (
                            <div className="mt-2 w-3/4 h-1 bg-gray-700 rounded-full overflow-hidden">
                              <div className="h-full bg-emerald-500 rounded-full transition-all" style={{ width: `${video.progress}%` }} />
                            </div>
                          )}
                        </div>
                      ) : video.status === 'failed' ? (
                        <div className="aspect-[9/16] bg-gradient-to-br from-red-900 to-red-950 flex flex-col items-center justify-center">
                          <AlertCircle className="w-6 h-6 text-red-400 mb-2" />
                          <p className="text-white text-xs font-medium">Failed</p>
                        </div>
                      ) : (
                        <button
                          onClick={() => router.push(`/dashboard/series/${params.id}/video/${video.id}`)}
                          className="w-full text-left"
                        >
                          <div className="aspect-[9/16] bg-gradient-to-br from-gray-200 to-gray-300 relative overflow-hidden">
                            {thumbnailUrls[video.id] && (
                              /* eslint-disable-next-line @next/next/no-img-element */
                              <img
                                src={thumbnailUrls[video.id]}
                                alt={video.title}
                                className="absolute inset-0 w-full h-full object-cover"
                              />
                            )}
                            <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/30 transition-colors">
                              <Play className="w-8 h-8 text-white opacity-0 group-hover:opacity-100 transition-opacity drop-shadow-lg" />
                            </div>
                            {video.duration > 0 && (
                              <div className="absolute top-1.5 right-1.5 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded">
                                {video.duration}s
                              </div>
                            )}
                          </div>
                        </button>
                      )}

                      <div className="p-2">
                        <h3 className="font-semibold text-xs text-gray-900 line-clamp-2 text-left mb-1">
                          {video.title}
                        </h3>
                        <div className="flex items-center justify-between">
                          <div className="flex items-center space-x-0.5">
                            {Object.entries(video.platforms).map(([platform, status]) => (
                              <div key={platform} className={`text-[10px] px-1.5 py-0.5 rounded ${
                                status === 'published' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'
                              }`}>{platform}</div>
                            ))}
                          </div>
                          {getStatusBadge(video.status)}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {videos.length === 0 && (
                  <div className="text-center py-12">
                    <Clock className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                    <p className="text-gray-500">No videos generated yet</p>
                    <p className="text-sm text-gray-400 mt-1">Click &quot;Generate Video&quot; above to create your first video</p>
                  </div>
                )}
              </div>

              {/* Connected Accounts */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <div className="flex items-center justify-between mb-4">
                  <div>
                    <h2 className="text-lg font-bold text-gray-900">Connected Accounts</h2>
                    <p className="text-sm text-gray-500 mt-1">Accounts linked for auto-posting.</p>
                  </div>
                  <Link href="/dashboard/settings" className="flex items-center space-x-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold rounded-lg transition-colors">
                    <Plus className="w-4 h-4" />
                    <span>Manage</span>
                  </Link>
                </div>

                {connectedAccounts.length === 0 ? (
                  <div className="text-center py-8">
                    <p className="text-gray-500 text-sm">No accounts connected yet.</p>
                    <Link href="/dashboard/settings" className="text-emerald-600 text-sm font-medium hover:underline mt-1 inline-block">
                      Connect your first account →
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-3">
                    {connectedAccounts.map((account) => (
                      <div key={account.id} className="flex items-center justify-between p-4 border border-gray-200 rounded-lg">
                        <div className="flex items-center space-x-3">
                          <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                            account.platform === 'youtube' ? 'bg-red-100 text-red-600'
                            : account.platform === 'tiktok' ? 'bg-gray-900 text-white'
                            : 'bg-pink-100 text-pink-600'
                          }`}>{getPlatformIcon(account.platform)}</div>
                          <div>
                            <p className="font-semibold text-sm text-gray-900">{account.username}</p>
                            <p className="text-xs text-gray-500 capitalize">{account.platform}</p>
                          </div>
                        </div>
                        <span className={`px-2.5 py-1 text-xs font-medium rounded-full ${account.isActive ? 'bg-green-100 text-green-700' : 'bg-gray-100 text-gray-500'}`}>
                          {account.isActive ? 'Active' : 'Inactive'}
                        </span>
                      </div>
                    ))}
                  </div>
                )}
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
