'use client'

import { useState } from 'react'
import Link from 'next/link'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Download, Play, Calendar, Clock, Eye, MoreVertical, Trash2, Share2 } from 'lucide-react'

interface Video {
  id: string
  title: string
  thumbnail: string
  series: string
  duration: string
  createdAt: string
  views: number
  status: 'ready' | 'processing' | 'failed'
  downloadUrl: string
}

export default function VideosPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeDropdown, setActiveDropdown] = useState<string | null>(null)

  // Mock videos data - replace with actual API call
  const videos: Video[] = [
    {
      id: '1',
      title: 'The Disappearance of Flight 370',
      thumbnail: '/thumbnails/video1.jpg',
      series: 'Last Seen Alive',
      duration: '0:58',
      createdAt: 'Jan 25, 2026',
      views: 1234,
      status: 'ready',
      downloadUrl: '/output/20260125_123456/final_video.mp4'
    },
    {
      id: '2',
      title: 'The Vanishing Hotel Guest',
      thumbnail: '/thumbnails/video2.jpg',
      series: 'Last Seen Alive',
      duration: '1:02',
      createdAt: 'Jan 24, 2026',
      views: 856,
      status: 'ready',
      downloadUrl: '/output/20260124_123456/final_video.mp4'
    },
    {
      id: '3',
      title: 'The Missing Hiker Mystery',
      thumbnail: '/thumbnails/video3.jpg',
      series: 'Last Seen Alive',
      duration: '0:55',
      createdAt: 'Jan 23, 2026',
      views: 2341,
      status: 'ready',
      downloadUrl: '/output/20260123_123456/final_video.mp4'
    },
    {
      id: '4',
      title: 'New Video Processing...',
      thumbnail: '/thumbnails/processing.jpg',
      series: 'Last Seen Alive',
      duration: '--:--',
      createdAt: 'Jan 27, 2026',
      views: 0,
      status: 'processing',
      downloadUrl: ''
    },
  ]

  const handleDownload = async (video: Video) => {
    if (video.status !== 'ready') return
    
    // In production, this would be an actual download
    const link = document.createElement('a')
    link.href = video.downloadUrl
    link.download = `${video.title.replace(/[^a-z0-9]/gi, '_')}.mp4`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  const breadcrumbItems = [
    { label: 'Videos' }
  ]

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

          {/* Videos Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
            {videos.map((video) => (
              <div
                key={video.id}
                className="bg-white rounded-lg border border-gray-200 overflow-hidden shadow-sm hover:shadow-md transition-shadow"
              >
                {/* Thumbnail */}
                <div className="relative aspect-[9/16] bg-gray-900">
                  {video.status === 'processing' ? (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-gray-800">
                      <div className="w-10 h-10 border-3 border-emerald-500 border-t-transparent rounded-full animate-spin mb-2" />
                      <span className="text-white text-xs">Processing...</span>
                    </div>
                  ) : (
                    <>
                      <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent" />
                      <div className="absolute bottom-2 left-2 right-2 flex items-center justify-between">
                        <span className="text-white text-xs font-medium bg-black/50 px-1.5 py-0.5 rounded">
                          {video.duration}
                        </span>
                        <button className="w-8 h-8 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center hover:bg-white/30 transition-colors">
                          <Play className="w-4 h-4 text-white fill-white" />
                        </button>
                      </div>
                    </>
                  )}
                </div>

                {/* Video Info */}
                <div className="p-3">
                  <h3 className="text-sm font-semibold text-gray-900 line-clamp-2 mb-1.5">
                    {video.title}
                  </h3>
                  
                  <div className="flex items-center text-xs text-gray-500 mb-2">
                    <span className="px-1.5 py-0.5 bg-purple-100 text-purple-700 rounded-full text-[10px] font-medium">
                      {video.series}
                    </span>
                  </div>

                  <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                    <div className="flex items-center space-x-1">
                      <Calendar className="w-3 h-3" />
                      <span>{video.createdAt}</span>
                    </div>
                    {video.status === 'ready' && (
                      <div className="flex items-center space-x-1">
                        <Eye className="w-3 h-3" />
                        <span>{video.views.toLocaleString()}</span>
                      </div>
                    )}
                  </div>

                  {/* Actions */}
                  <div className="flex items-center space-x-2">
                    <button
                      onClick={() => handleDownload(video)}
                      disabled={video.status !== 'ready'}
                      className={`flex-1 flex items-center justify-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                        video.status === 'ready'
                          ? 'bg-emerald-500 hover:bg-emerald-600 text-white'
                          : 'bg-gray-100 text-gray-400 cursor-not-allowed'
                      }`}
                    >
                      <Download className="w-3.5 h-3.5" />
                      <span>Download</span>
                    </button>
                    
                    <div className="relative">
                      <button
                        onClick={() => setActiveDropdown(activeDropdown === video.id ? null : video.id)}
                        className="p-1.5 hover:bg-gray-100 rounded-md transition-colors"
                      >
                        <MoreVertical className="w-4 h-4 text-gray-500" />
                      </button>
                      
                      {activeDropdown === video.id && (
                        <div className="absolute right-0 top-full mt-1 w-32 bg-white rounded-md shadow-lg border border-gray-200 py-1 z-10">
                          <button className="w-full flex items-center space-x-2 px-3 py-1.5 text-xs text-gray-700 hover:bg-gray-50">
                            <Share2 className="w-3.5 h-3.5" />
                            <span>Share</span>
                          </button>
                          <button className="w-full flex items-center space-x-2 px-3 py-1.5 text-xs text-red-600 hover:bg-red-50">
                            <Trash2 className="w-3.5 h-3.5" />
                            <span>Delete</span>
                          </button>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Empty State */}
          {videos.length === 0 && (
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
          )}
        </div>
      </div>
    </div>
  )
}
