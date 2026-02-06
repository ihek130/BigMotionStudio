'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Download, Play, Calendar, Clock, Loader2 } from 'lucide-react'

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

interface Video {
  id: string
  title: string
  thumbnail: string
  seriesName: string
  seriesId: string
  durationSeconds: number
  createdAt: string
  status: 'ready' | 'generating' | 'pending' | 'failed' | 'published'
  videoPath: string | null
}

export default function VideosPage() {
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [loading, setLoading] = useState(true)
  const [videos, setVideos] = useState<Video[]>([])

  useEffect(() => {
    fetchVideos()
  }, [])

  const fetchVideos = async () => {
    try {
      const token = localStorage.getItem('reelflow_access_token')
      if (!token) { router.push('/login'); return }

      const res = await fetch(`${API_URL}/api/videos`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (res.ok) {
        const data = await res.json()
        setVideos(data.videos || [])
      }
    } catch (err) {
      console.error('Failed to fetch videos:', err)
    } finally {
      setLoading(false)
    }
  }

  const handleDownload = async (video: Video) => {
    if (video.status !== 'ready' && video.status !== 'published') return
    try {
      const token = localStorage.getItem('reelflow_access_token')
      const res = await fetch(`${API_URL}/api/videos/${video.id}/download`, {
        headers: { 'Authorization': `Bearer ${token}` }
      })
      if (!res.ok) throw new Error('Download failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${video.title || 'video'}.mp4`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    } catch (err) {
      console.error('Download failed:', err)
    }
  }

  const formatDuration = (seconds: number) => {
    if (!seconds) return '--:--'
    const m = Math.floor(seconds / 60)
    const s = seconds % 60
    return `${m}:${s.toString().padStart(2, '0')}`
  }

  const formatDate = (iso: string) => {
    if (!iso) return ''
    return new Date(iso).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })
  }

  const getStatusBadge = (status: string) => {
    const map: Record<string, { bg: string; text: string; label: string }> = {
      ready: { bg: 'bg-green-100', text: 'text-green-700', label: 'Ready' },
      published: { bg: 'bg-blue-100', text: 'text-blue-700', label: 'Published' },
      generating: { bg: 'bg-yellow-100', text: 'text-yellow-700', label: 'Generating' },
      pending: { bg: 'bg-gray-100', text: 'text-gray-600', label: 'Pending' },
      failed: { bg: 'bg-red-100', text: 'text-red-700', label: 'Failed' },
    }
    const s = map[status] || map.pending
    return (
      <span className={`px-1.5 py-0.5 text-[10px] font-semibold rounded-full ${s.bg} ${s.text}`}>
        {s.label}
      </span>
    )
  }

  const breadcrumbItems = [{ label: 'Videos' }]

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

        {/* Page Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="mb-4">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Your Videos</h1>
            <p className="text-sm text-gray-600 mt-1">All your generated videos in one place</p>
          </div>

          {loading ? (
            <div className="flex items-center justify-center py-20">
              <Loader2 className="w-8 h-8 animate-spin text-emerald-500" />
            </div>
          ) : videos.length === 0 ? (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-3">
                <Play className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-base font-semibold text-gray-900 mb-1">No videos yet</h3>
              <p className="text-sm text-gray-600 mb-4">Create your first series to start generating videos</p>
              <Link
                href="/create"
                className="inline-flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-sm font-semibold rounded-lg hover:from-emerald-600 hover:to-teal-600 transition-all"
              >
                <span>Create Series</span>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
              {videos.map((video) => (
                <div
                  key={video.id}
                  className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
                >
                  {/* Thumbnail */}
                  <Link href={`/dashboard/series/${video.seriesId}/video/${video.id}`}>
                    <div className="relative aspect-[9/16] bg-gray-900 cursor-pointer">
                      {video.status === 'generating' || video.status === 'pending' ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-800">
                          <div className="w-10 h-10 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin mb-2" />
                          <span className="text-white text-xs">
                            {video.status === 'generating' ? 'Generating...' : 'Pending...'}
                          </span>
                        </div>
                      ) : video.status === 'failed' ? (
                        <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-800">
                          <span className="text-red-400 text-xs">Failed</span>
                        </div>
                      ) : (
                        <>
                          <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                          <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                            <span className="text-white text-xs font-medium bg-black/50 px-1.5 py-0.5 rounded">
                              {formatDuration(video.durationSeconds)}
                            </span>
                            <div className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center">
                              <Play className="w-4 h-4 text-white fill-white" />
                            </div>
                          </div>
                        </>
                      )}
                    </div>
                  </Link>

                  {/* Video Info */}
                  <div className="p-3">
                    <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5">
                      {video.title || 'Untitled Video'}
                    </h3>
                    
                    <div className="flex items-center gap-2 text-xs text-gray-500 mb-2">
                      <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-[10px] font-medium truncate max-w-[120px]">
                        {video.seriesName}
                      </span>
                      {getStatusBadge(video.status)}
                    </div>

                    <div className="flex items-center text-xs text-gray-500 mb-3">
                      <Calendar className="w-3 h-3 mr-1" />
                      <span>{formatDate(video.createdAt)}</span>
                    </div>

                    {/* Actions */}
                    <div className="flex items-center space-x-2">
                      <button
                        onClick={() => handleDownload(video)}
                        disabled={video.status !== 'ready' && video.status !== 'published'}
                        className={`flex-1 flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                          video.status === 'ready' || video.status === 'published'
                            ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                            : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                        }`}
                      >
                        <Download className="w-3.5 h-3.5" />
                        <span>Download</span>
                      </button>
                      <Link
                        href={`/dashboard/series/${video.seriesId}/video/${video.id}`}
                        className="px-3 py-1.5 border border-gray-200 hover:border-gray-300 rounded-md text-sm font-medium text-gray-700 transition-colors"
                      >
                        View
                      </Link>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
