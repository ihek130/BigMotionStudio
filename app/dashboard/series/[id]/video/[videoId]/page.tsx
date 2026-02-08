'use client'

import { useState, useEffect, useRef } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Download, Play, Check, Clock, AlertCircle, Save, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface VideoData {
  id: string
  title: string
  description: string
  video_url: string
  thumbnail: string
  duration: number
  rendered: boolean
  metadata: {
    title: string
    description: string
    privacy: 'public' | 'private' | 'unlisted'
    allow_comments: boolean
    allow_duets: boolean
    allow_stitches: boolean
    commercial: boolean
    ai_disclosure: boolean
  }
  publishing: {
    youtube?: { status: 'published' | 'scheduled' | 'failed' | 'pending', scheduled_at?: string }
    tiktok?: { status: 'published' | 'scheduled' | 'failed' | 'pending', scheduled_at?: string }
    instagram?: { status: 'published' | 'scheduled' | 'failed' | 'pending', scheduled_at?: string }
  }
  scheduled_at?: string
}

export default function VideoDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [publishing, setPublishing] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(false)
  const videoRef = useRef<HTMLVideoElement>(null)
  const [seriesName, setSeriesName] = useState('')
  const [videoObjectUrl, setVideoObjectUrl] = useState<string | null>(null)
  const [thumbnailUrl, setThumbnailUrl] = useState<string | null>(null)
  
  const [video, setVideo] = useState<VideoData | null>(null)
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    privacy: 'public' as 'public' | 'private' | 'unlisted',
    scheduled_date: '',
    scheduled_time: '',
    allow_comments: true,
    allow_duets: true,
    allow_stitches: true,
    commercial: false,
    ai_disclosure: true
  })

  useEffect(() => {
    fetchVideoData()
  }, [params.videoId])

  const fetchVideoData = async () => {
    setLoading(true)
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('reelflow_access_token') : null
      
      if (!token) {
        router.push('/login')
        return
      }
      
      const response = await fetch(`${(process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000')}/api/series/${params.id}/videos/${params.videoId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      // Also fetch series info for breadcrumb and platform config
      let seriesData: any = null
      const seriesRes = await fetch(`${API_URL}/api/series/${params.id}`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (seriesRes.ok) {
        seriesData = await seriesRes.json()
        setSeriesName(seriesData.name || seriesData.title || 'Series')
      }

      if (response.ok) {
        const data = await response.json()
        
        const videoData: VideoData = {
          id: data.id,
          title: data.title || 'Untitled Video',
          description: data.description || '',
          video_url: data.videoPath ? `${API_URL}/api/videos/${data.id}/stream` : '',
          thumbnail: data.thumbnailPath || '/placeholder-video.jpg',
          duration: Math.floor(data.durationSeconds || 60),
          rendered: data.status === 'ready' || data.status === 'published',
          metadata: {
            title: data.title || '',
            description: data.description || '',
            privacy: 'public',
            allow_comments: true,
            allow_duets: true,
            allow_stitches: true,
            commercial: false,
            ai_disclosure: true
          },
          publishing: {
            ...(seriesData?.platforms?.includes('youtube') || data.youtubeUrl
              ? { youtube: { status: data.youtubeUrl ? 'published' : (data.scheduledFor ? 'scheduled' : 'pending'), scheduled_at: data.youtubePublishedAt } }
              : {}),
            ...(seriesData?.platforms?.includes('tiktok') || data.tiktokUrl
              ? { tiktok: { status: data.tiktokUrl ? 'published' : (data.scheduledFor ? 'scheduled' : 'pending'), scheduled_at: data.tiktokPublishedAt } }
              : {}),
            ...(seriesData?.platforms?.includes('instagram') || data.instagramUrl
              ? { instagram: { status: data.instagramUrl ? 'published' : (data.scheduledFor ? 'scheduled' : 'pending'), scheduled_at: data.instagramPublishedAt } }
              : {})
          },
          scheduled_at: data.scheduledFor
        }
        
        setVideo(videoData)
        setFormData({
          title: videoData.metadata.title,
          description: videoData.metadata.description,
          privacy: videoData.metadata.privacy,
          scheduled_date: videoData.scheduled_at ? videoData.scheduled_at.split('T')[0] : '',
          scheduled_time: videoData.scheduled_at ? videoData.scheduled_at.split('T')[1]?.substring(0, 5) : '',
          allow_comments: videoData.metadata.allow_comments,
          allow_duets: videoData.metadata.allow_duets,
          allow_stitches: videoData.metadata.allow_stitches,
          commercial: videoData.metadata.commercial,
          ai_disclosure: videoData.metadata.ai_disclosure
        })

        // Fetch thumbnail
        try {
          const thumbRes = await fetch(`${API_URL}/api/videos/${data.id}/thumbnail`, {
            headers: { 'Authorization': `Bearer ${token}` }
          })
          if (thumbRes.ok) {
            const blob = await thumbRes.blob()
            setThumbnailUrl(URL.createObjectURL(blob))
          }
        } catch { /* ignore */ }

        // Fetch video blob for player if video file exists
        if (data.videoPath) {
          try {
            const videoRes = await fetch(`${API_URL}/api/videos/${data.id}/stream`, {
              headers: { 'Authorization': `Bearer ${token}` }
            })
            if (videoRes.ok) {
              const blob = await videoRes.blob()
              const url = URL.createObjectURL(blob)
              setVideoObjectUrl(url)
            }
          } catch (e) {
            console.error('Failed to load video stream:', e)
          }
        }
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch video:', error)
      setLoading(false)
    }
  }

  // Cleanup blob URLs on unmount
  useEffect(() => {
    return () => {
      if (videoObjectUrl) URL.revokeObjectURL(videoObjectUrl)
      if (thumbnailUrl) URL.revokeObjectURL(thumbnailUrl)
    }
  }, [videoObjectUrl, thumbnailUrl])

  const handleSave = async () => {
    setSaving(true)
    try {
      const token = localStorage.getItem('reelflow_access_token')
      const res = await fetch(`${API_URL}/api/series/${params.id}/videos/${params.videoId}/metadata`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          title: formData.title,
          description: formData.description
        })
      })
      if (!res.ok) throw new Error('Failed to save')
    } catch (err) {
      console.error('Save failed:', err)
    } finally {
      setSaving(false)
    }
  }

  const handlePublishAgain = async () => {
    setPublishing(true)
    try {
      const token = localStorage.getItem('reelflow_access_token')
      const res = await fetch(`${API_URL}/api/video/${params.videoId}/upload`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      if (!res.ok) throw new Error('Failed to publish')
    } catch (err) {
      console.error('Publish failed:', err)
    } finally {
      setPublishing(false)
    }
  }

  const handleDownload = async () => {
    try {
      const token = localStorage.getItem('reelflow_access_token')
      const res = await fetch(`${API_URL}/api/videos/${params.videoId}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${video?.title || 'video'}.mp4`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const getStatusBadge = (status: string) => {
    const styles: Record<string, { bg: string, text: string, icon: typeof Check }> = {
      published: { bg: 'bg-green-100', text: 'text-green-700', icon: Check },
      scheduled: { bg: 'bg-blue-100', text: 'text-blue-700', icon: Clock },
      pending: { bg: 'bg-gray-100', text: 'text-gray-500', icon: Clock },
      failed: { bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle }
    }
    
    const style = styles[status] || styles.pending
    const Icon = style.icon
    
    return (
      <span className={`inline-flex items-center space-x-1 px-2 py-1 text-xs font-semibold rounded-full ${style.bg} ${style.text}`}>
        <Icon className="w-3 h-3" />
        <span>{status === 'pending' ? 'Not Published' : status.charAt(0).toUpperCase() + status.slice(1)}</span>
      </span>
    )
  }

  const breadcrumbItems = [
    { label: 'Series', href: '/dashboard' },
    { label: seriesName || 'Series', href: `/dashboard/series/${params.id}` },
    { label: video?.title || 'Video' }
  ]

  if (loading || !video) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
          <p className="text-gray-600">Loading video...</p>
        </div>
      </div>
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
        </div>

        {/* Content */}
        <div className="px-4 sm:px-6 lg:px-8 py-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Left Column - Video Preview */}
            <div className="lg:col-span-1 space-y-4">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="font-bold text-sm text-gray-900 mb-3">Video Preview</h3>
                
                {/* Video Player */}
                <div className="aspect-[9/16] bg-black rounded-lg overflow-hidden relative group">
                  {videoObjectUrl ? (
                    <video
                      ref={videoRef}
                      src={videoObjectUrl}
                      poster={thumbnailUrl || undefined}
                      className="w-full h-full object-contain"
                      controls
                      muted={muted}
                      playsInline
                      onPlay={() => setPlaying(true)}
                      onPause={() => setPlaying(false)}
                    />
                  ) : thumbnailUrl ? (
                    <div className="absolute inset-0">
                      {/* eslint-disable-next-line @next/next/no-img-element */}
                      <img src={thumbnailUrl} alt="Video thumbnail" className="w-full h-full object-cover" />
                      <div className="absolute inset-0 flex items-center justify-center bg-black/20">
                        <Play className="w-16 h-16 text-white/80" />
                      </div>
                    </div>
                  ) : (
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-white/60">
                      <Play className="w-16 h-16 mb-2" />
                      <span className="text-sm">No preview available</span>
                    </div>
                  )}
                </div>

                {/* Actions */}
                <div className="mt-4 space-y-2">
                  <button
                    onClick={handleDownload}
                    disabled={!video.rendered}
                    className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <Download className="w-4 h-4" />
                    <span>Download Video</span>
                  </button>
                </div>

                {video.rendered && (
                  <p className="mt-3 text-xs text-gray-500 text-center">
                    This video has already been rendered.
                  </p>
                )}
              </div>

              {/* Publishing Status */}
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
                <h3 className="font-bold text-sm text-gray-900 mb-3">Publishing Status</h3>
                <div className="space-y-2">
                  {Object.keys(video.publishing).length > 0 ? (
                    Object.entries(video.publishing).map(([platform, data]) => (
                      <div key={platform} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium text-gray-700 capitalize">{platform === 'youtube' ? 'YouTube' : platform === 'tiktok' ? 'TikTok' : 'Instagram'}</span>
                        </div>
                        {getStatusBadge(data.status)}
                      </div>
                    ))
                  ) : (
                    <p className="text-sm text-gray-400 text-center py-2">No platforms configured</p>
                  )}
                </div>
              </div>
            </div>

            {/* Right Column - Metadata Form */}
            <div className="lg:col-span-2">
              <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
                <h3 className="font-bold text-lg text-gray-900 mb-6">Video Settings</h3>
                
                <div className="space-y-6">
                  {/* Title */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Title <span className="text-red-500">*</span>
                    </label>
                    <input
                      type="text"
                      value={formData.title}
                      onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                      maxLength={100}
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:outline-none"
                    />
                    <p className="mt-1 text-xs text-gray-500">{formData.title.length}/100 characters</p>
                  </div>

                  {/* Description */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Description
                    </label>
                    <textarea
                      value={formData.description}
                      onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                      rows={4}
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:outline-none"
                      placeholder="Add hashtags and description..."
                    />
                    <p className="mt-1 text-xs text-gray-500">Supports hashtags for all platforms</p>
                  </div>

                  {/* Scheduling */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Schedule Publishing
                    </label>
                    <div className="grid grid-cols-2 gap-3">
                      <input
                        type="date"
                        value={formData.scheduled_date}
                        onChange={(e) => setFormData({ ...formData, scheduled_date: e.target.value })}
                        className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:outline-none"
                      />
                      <input
                        type="time"
                        value={formData.scheduled_time}
                        onChange={(e) => setFormData({ ...formData, scheduled_time: e.target.value })}
                        className="px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:outline-none"
                      />
                    </div>
                    <p className="mt-1 text-xs text-gray-500">When should this video be published?</p>
                  </div>

                  {/* Privacy */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-2">
                      Privacy Settings
                    </label>
                    <select
                      value={formData.privacy}
                      onChange={(e) => setFormData({ ...formData, privacy: e.target.value as any })}
                      className="w-full px-4 py-2 border-2 border-gray-200 rounded-lg focus:border-emerald-500 focus:outline-none"
                    >
                      <option value="public">Public</option>
                      <option value="private">Private</option>
                      <option value="unlisted">Unlisted</option>
                    </select>
                  </div>

                  {/* Interaction Preferences */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Interaction Preferences
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={formData.allow_comments}
                          onChange={(e) => setFormData({ ...formData, allow_comments: e.target.checked })}
                          className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">Allow comments</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={formData.allow_duets}
                          onChange={(e) => setFormData({ ...formData, allow_duets: e.target.checked })}
                          className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">Allow duets</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={formData.allow_stitches}
                          onChange={(e) => setFormData({ ...formData, allow_stitches: e.target.checked })}
                          className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">Allow stitches</span>
                      </label>
                    </div>
                  </div>

                  {/* Compliance */}
                  <div>
                    <label className="block text-sm font-semibold text-gray-700 mb-3">
                      Compliance & Disclosure
                    </label>
                    <div className="space-y-2">
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={formData.commercial}
                          onChange={(e) => setFormData({ ...formData, commercial: e.target.checked })}
                          className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">This content is for commercial purposes</span>
                      </label>
                      <label className="flex items-center space-x-3">
                        <input
                          type="checkbox"
                          checked={formData.ai_disclosure}
                          onChange={(e) => setFormData({ ...formData, ai_disclosure: e.target.checked })}
                          className="w-4 h-4 text-emerald-500 border-gray-300 rounded focus:ring-emerald-500"
                        />
                        <span className="text-sm text-gray-700">Disclose AI-generated content</span>
                      </label>
                    </div>
                  </div>

                  {/* Actions */}
                  <div className="flex items-center justify-between pt-6 border-t border-gray-200">
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Check className="w-4 h-4 text-green-600" />
                      <span>All changes saved</span>
                    </div>
                    <div className="flex items-center space-x-3">
                      <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center space-x-2 px-6 py-2 border-2 border-emerald-500 text-emerald-600 hover:bg-emerald-50 font-semibold rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Save className="w-4 h-4" />
                        <span>{saving ? 'Saving...' : 'Save'}</span>
                      </button>
                      <button
                        onClick={handlePublishAgain}
                        disabled={publishing || !video.rendered}
                        className="flex items-center space-x-2 px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg transition-colors disabled:opacity-50"
                      >
                        {publishing && <Loader2 className="w-4 h-4 animate-spin" />}
                        <span>{publishing ? 'Publishing...' : 'Publish Again'}</span>
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
