'use client'

import { useState, useEffect } from 'react'
import { useParams, useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Download, Edit, Play, Pause, Volume2, VolumeX, Check, Clock, AlertCircle, Save } from 'lucide-react'

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
    youtube?: { status: 'published' | 'scheduled' | 'failed', scheduled_at?: string }
    tiktok?: { status: 'published' | 'scheduled' | 'failed', scheduled_at?: string }
    instagram?: { status: 'published' | 'scheduled' | 'failed', scheduled_at?: string }
  }
  scheduled_at?: string
}

export default function VideoDetailPage() {
  const params = useParams()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [muted, setMuted] = useState(false)
  
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
      
      const response = await fetch(`http://localhost:8000/api/series/${params.id}/videos/${params.videoId}`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        
        const videoData: VideoData = {
          id: data.id,
          title: data.title || 'Untitled Video',
          description: data.description || '',
          video_url: data.videoPath || '/sample-video.mp4',
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
            ...(data.youtubeUrl ? { youtube: { status: 'published', scheduled_at: data.youtubePublishedAt } } : {}),
            ...(data.tiktokUrl ? { tiktok: { status: 'published', scheduled_at: data.tiktokPublishedAt } } : {}),
            ...(data.instagramUrl ? { instagram: { status: 'published', scheduled_at: data.instagramPublishedAt } } : {})
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
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch video:', error)
      setLoading(false)
    }
  }

  const handleSave = async () => {
    setSaving(true)
    try {
      // TODO: API call to save metadata
      await new Promise(resolve => setTimeout(resolve, 1000))
      console.log('Saved:', formData)
    } finally {
      setSaving(false)
    }
  }

  const handlePublishAgain = async () => {
    // TODO: API call to republish
    console.log('Publishing again...')
  }

  const getStatusBadge = (status: string) => {
    const styles = {
      published: { bg: 'bg-green-100', text: 'text-green-700', icon: Check },
      scheduled: { bg: 'bg-blue-100', text: 'text-blue-700', icon: Clock },
      failed: { bg: 'bg-red-100', text: 'text-red-700', icon: AlertCircle }
    }
    
    const style = styles[status as keyof typeof styles]
    const Icon = style.icon
    
    return (
      <span className={`inline-flex items-center space-x-1 px-2 py-1 text-xs font-semibold rounded-full ${style.bg} ${style.text}`}>
        <Icon className="w-3 h-3" />
        <span>{status.charAt(0).toUpperCase() + status.slice(1)}</span>
      </span>
    )
  }

  const breadcrumbItems = [
    { label: 'Series', href: '/dashboard' },
    { label: 'Dark Mysteries', href: `/dashboard/series/${params.id}` },
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
                  <div className="absolute inset-0 flex items-center justify-center">
                    <Play className="w-16 h-16 text-white opacity-80" />
                  </div>
                  
                  {/* Controls */}
                  <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/80 to-transparent p-3 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex items-center justify-between text-white">
                      <button
                        onClick={() => setPlaying(!playing)}
                        className="p-2 hover:bg-white/20 rounded-full transition-colors"
                      >
                        {playing ? <Pause className="w-5 h-5" /> : <Play className="w-5 h-5" />}
                      </button>
                      <button
                        onClick={() => setMuted(!muted)}
                        className="p-2 hover:bg-white/20 rounded-full transition-colors"
                      >
                        {muted ? <VolumeX className="w-5 h-5" /> : <Volume2 className="w-5 h-5" />}
                      </button>
                    </div>
                    <div className="mt-2 h-1 bg-white/30 rounded-full">
                      <div className="h-full w-1/3 bg-emerald-500 rounded-full" />
                    </div>
                  </div>
                </div>

                {/* Actions */}
                <div className="mt-4 space-y-2">
                  <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 bg-emerald-500 hover:bg-emerald-600 text-white text-sm font-semibold rounded-lg transition-colors">
                    <Download className="w-4 h-4" />
                    <span>Download Video</span>
                  </button>
                  <button className="w-full flex items-center justify-center space-x-2 px-4 py-2 border-2 border-gray-200 hover:border-gray-300 text-gray-700 text-sm font-semibold rounded-lg transition-colors">
                    <Edit className="w-4 h-4" />
                    <span>Edit Video</span>
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
                  {Object.entries(video.publishing).map(([platform, data]) => (
                    <div key={platform} className="flex items-center justify-between p-2 bg-gray-50 rounded">
                      <span className="text-sm font-medium text-gray-700 capitalize">{platform}</span>
                      {getStatusBadge(data.status)}
                    </div>
                  ))}
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
                        className="px-6 py-2 bg-emerald-500 hover:bg-emerald-600 text-white font-semibold rounded-lg transition-colors"
                      >
                        Publish Again
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
