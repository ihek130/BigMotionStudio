'use client'

import Link from 'next/link'
import { Plus, Calendar, Trash2, Pause, Play } from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { useState, useEffect } from 'react'

interface Series {
  id: string
  name: string
  type: string
  created: string
  videos: number
  status: 'active' | 'paused' | 'generating'
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

export default function DashboardPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [series, setSeries] = useState<Series[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchSeries()
  }, [])

  const fetchSeries = async () => {
    setLoading(true)
    try {
      const token = typeof window !== 'undefined' ? localStorage.getItem('reelflow_access_token') : null
      
      if (!token) {
        setLoading(false)
        return
      }
      
      const response = await fetch(`${API_BASE_URL}/api/series`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        setSeries(data.map((s: any) => ({
          id: s.id,
          name: s.name,
          type: s.niche,
          created: new Date(s.createdAt).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' }),
          videos: s.videosGenerated || 0,
          status: s.status as 'active' | 'paused' | 'generating'
        })))
      }
      
      setLoading(false)
    } catch (error) {
      console.error('Failed to fetch series:', error)
      setLoading(false)
    }
  }

  const breadcrumbItems = [
    { label: 'Series' }
  ]

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex">
        <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />
        <div className="flex-1 lg:ml-64 flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 border-4 border-emerald-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Loading your series...</p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* Sidebar */}
      <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      {/* Main Content */}
      <div className="flex-1 lg:ml-64">
        {/* Header with Breadcrumb */}
        <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
          <div className="px-4 sm:px-6 lg:px-8 py-4">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div className="flex items-center space-x-3">
                <MobileMenuButton onClick={() => setSidebarOpen(true)} />
                <Breadcrumb items={breadcrumbItems} />
              </div>
              <Link
                href="/create"
                className="flex items-center justify-center space-x-2 px-4 sm:px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all whitespace-nowrap"
              >
                <Plus className="w-5 h-5" />
                <span>Create Series</span>
              </Link>
            </div>
          </div>
        </div>

        {/* Page Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="mb-6">
            <h1 className="text-2xl sm:text-3xl font-bold text-gray-900">Your Series</h1>
            <p className="text-gray-600 mt-1">Manage your automated video series</p>
          </div>

          {series.length === 0 ? (
            <div className="bg-white rounded-xl border-2 border-dashed border-gray-300 p-12 text-center">
              <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <Plus className="w-8 h-8 text-gray-400" />
              </div>
              <h3 className="text-lg font-semibold text-gray-900 mb-2">No series yet</h3>
              <p className="text-gray-600 mb-6">Create your first automated video series to get started</p>
              <Link
                href="/create"
                className="inline-flex items-center space-x-2 px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/30 transition-all"
              >
                <Plus className="w-5 h-5" />
                <span>Create Series</span>
              </Link>
            </div>
          ) : (
            <div className="bg-white rounded-xl border border-gray-200 overflow-hidden shadow-sm">
              {/* Desktop Table */}
              <div className="hidden sm:block overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-gray-50 border-b border-gray-200">
                    <tr>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Name</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Type</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Created</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Published</th>
                      <th className="px-6 py-4 text-left text-xs font-semibold text-gray-600 uppercase tracking-wider">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-gray-200">
                    {series.map((item) => (
                      <tr key={item.id} className="hover:bg-gray-50 transition-colors">
                        <td className="px-6 py-4">
                          <Link href={`/dashboard/series/${item.id}`} className="text-sm font-medium text-gray-900 hover:text-emerald-600">
                            {item.name}
                          </Link>
                        </td>
                        <td className="px-6 py-4">
                          <span className="inline-flex px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                            {item.type}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-2 text-sm text-gray-600">
                            <Calendar className="w-4 h-4" />
                            <span>{item.created}</span>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className="text-sm text-gray-900">{item.videos} video(s)</span>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center space-x-2">
                            <button className="px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium rounded-lg transition-colors flex items-center space-x-1">
                              {item.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                              <span>{item.status === 'active' ? 'Pause' : 'Resume'}</span>
                          </button>
                          <button className="p-2 text-gray-400 hover:text-red-600 transition-colors">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Mobile Cards */}
            <div className="sm:hidden divide-y divide-gray-200">
              {series.map((item) => (
                <div key={item.id} className="p-4 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                      <Link href={`/dashboard/series/${item.id}`} className="text-base font-medium text-gray-900 hover:text-emerald-600 block mb-2">
                        {item.name}
                      </Link>
                      <span className="inline-flex px-3 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-medium">
                        {item.type}
                      </span>
                    </div>
                  </div>
                  <div className="space-y-2 mb-3">
                    <div className="flex items-center space-x-2 text-sm text-gray-600">
                      <Calendar className="w-4 h-4" />
                      <span>{item.created}</span>
                    </div>
                    <div className="text-sm text-gray-900">{item.videos} video(s) published</div>
                  </div>
                  <div className="flex items-center space-x-2">
                    <button className="flex-1 px-4 py-2 bg-gray-900 hover:bg-gray-800 text-white text-sm font-medium rounded-lg transition-colors flex items-center justify-center space-x-1">
                      {item.status === 'active' ? <Pause className="w-4 h-4" /> : <Play className="w-4 h-4" />}
                      <span>{item.status === 'active' ? 'Pause' : 'Resume'}</span>
                    </button>
                    <button className="p-2 text-gray-400 hover:text-red-600 transition-colors border border-gray-300 rounded-lg">
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
          )}
        </div>
      </div>
    </div>
  )
}
