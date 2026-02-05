'use client'

import { useState, useEffect } from 'react'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Settings, Trash2, Plus, AlertTriangle, Youtube, Music2, Instagram, Loader2 } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'
import { usePlatforms } from '@/context/PlatformContext'

export default function SettingsPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [showDeleteModal, setShowDeleteModal] = useState(false)
  const [showConnectModal, setShowConnectModal] = useState(false)
  const [showInstagramNote, setShowInstagramNote] = useState(false)
  
  const { user, logout } = useAuth()
  const { 
    youtube, 
    tiktok, 
    instagram, 
    status, 
    isLoading, 
    error,
    fetchConnections, 
    connectPlatform, 
    disconnectPlatform 
  } = usePlatforms()

  useEffect(() => {
    fetchConnections()
  }, [fetchConnections])

  // Combine all accounts for display
  const accounts = [
    ...youtube.map(c => ({ ...c, platform: 'youtube' as const })),
    ...tiktok.map(c => ({ ...c, platform: 'tiktok' as const })),
    ...instagram.map(c => ({ ...c, platform: 'instagram' as const }))
  ]

  const platformIcons = {
    youtube: <Youtube className="w-5 h-5" />,
    tiktok: <Music2 className="w-5 h-5" />,
    instagram: <Instagram className="w-5 h-5" />,
  }

  const platformColors = {
    youtube: 'bg-red-500 text-white',
    tiktok: 'bg-black text-white',
    instagram: 'bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 text-white',
  }

  const handleDisconnect = async (platform: string, connectionId: string) => {
    try {
      await disconnectPlatform(platform, connectionId)
    } catch (e) {
      console.error('Failed to disconnect:', e)
    }
  }

  const handleConnect = async (platform: 'youtube' | 'tiktok' | 'instagram') => {
    // Show info note for Instagram before redirecting
    if (platform === 'instagram' && !showInstagramNote) {
      setShowConnectModal(false)
      setShowInstagramNote(true)
      return
    }
    try {
      setShowConnectModal(false)
      setShowInstagramNote(false)
      await connectPlatform(platform)
    } catch (e) {
      console.error('Failed to connect:', e)
    }
  }

  const breadcrumbItems = [
    { label: 'Settings' }
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
        <div className="p-4 sm:p-6 lg:p-8 max-w-4xl mx-auto">
          <div className="mb-6">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Settings</h1>
            <p className="text-sm text-gray-600 mt-1">Manage your account settings and connected platforms</p>
          </div>

          {/* Connected Accounts Section */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-4">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-base font-semibold text-gray-900">Connected accounts</h2>
              <p className="text-gray-600 text-xs mt-0.5">
                Connect your social media accounts for automatic content distribution.
              </p>
            </div>

            {error && (
              <div className="mx-4 mt-4 p-3 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{error}</p>
              </div>
            )}

            <div className="p-4 space-y-3">
              {isLoading && accounts.length === 0 ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="w-6 h-6 text-gray-400 animate-spin" />
                </div>
              ) : (
                <>
                  {accounts.map((account) => (
                    <div
                      key={account.id}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:border-gray-300 transition-colors"
                    >
                      <div className="flex items-center space-x-3">
                        {account.profile_image_url ? (
                          <img 
                            src={account.profile_image_url} 
                            alt={account.username}
                            className="w-8 h-8 rounded-lg object-cover"
                          />
                        ) : (
                          <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${platformColors[account.platform]}`}>
                            {platformIcons[account.platform]}
                          </div>
                        )}
                        <div>
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-semibold text-gray-900">{account.channel_name || account.username}</span>
                            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
                              account.status === 'active' 
                                ? 'bg-green-100 text-green-700' 
                                : account.status === 'expired'
                                ? 'bg-red-100 text-red-700'
                                : 'bg-yellow-100 text-yellow-700'
                            }`}>
                              {account.status === 'active' ? 'Active ✓' : account.status === 'expired' ? 'Expired' : 'Error'}
                            </span>
                          </div>
                          <span className="text-xs text-gray-500">
                            {account.platform === 'youtube' ? 'YouTube' : 
                             account.platform === 'tiktok' ? 'TikTok' : 'Instagram'}
                          </span>
                        </div>
                      </div>
                      <button
                        onClick={() => handleDisconnect(account.platform, account.id)}
                        disabled={isLoading}
                        className="p-1.5 text-gray-400 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </>
              )}

              {/* Connect New Account Button */}
              <button
                onClick={() => setShowConnectModal(true)}
                disabled={isLoading}
                className="w-full flex items-center justify-center space-x-2 p-3 border-2 border-dashed border-gray-300 rounded-lg text-sm text-gray-600 hover:border-emerald-500 hover:text-emerald-600 transition-colors disabled:opacity-50"
              >
                <Plus className="w-4 h-4" />
                <span className="font-medium">Connect new account</span>
              </button>
            </div>
          </div>

          {/* Notification Settings */}
          <div className="bg-white rounded-lg border border-gray-200 overflow-hidden mb-4">
            <div className="p-4 border-b border-gray-200">
              <h2 className="text-base font-semibold text-gray-900">Notifications</h2>
              <p className="text-gray-600 text-xs mt-0.5">
                Configure how you receive updates about your videos.
              </p>
            </div>

            <div className="p-4 space-y-3">
              <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                <div>
                  <span className="text-sm font-medium text-gray-900">Email notifications</span>
                  <p className="text-xs text-gray-500">Receive updates when videos are generated</p>
                </div>
                <input type="checkbox" defaultChecked className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500" />
              </label>

              <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                <div>
                  <span className="text-sm font-medium text-gray-900">Upload confirmations</span>
                  <p className="text-xs text-gray-500">Get notified when videos are posted</p>
                </div>
                <input type="checkbox" defaultChecked className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500" />
              </label>

              <label className="flex items-center justify-between p-3 border border-gray-200 rounded-lg cursor-pointer hover:bg-gray-50">
                <div>
                  <span className="text-sm font-medium text-gray-900">Weekly analytics</span>
                  <p className="text-xs text-gray-500">Receive weekly performance reports</p>
                </div>
                <input type="checkbox" className="w-4 h-4 text-emerald-500 rounded focus:ring-emerald-500" />
              </label>
            </div>
          </div>

          {/* Danger Zone */}
          <div className="bg-white rounded-lg border border-red-200 overflow-hidden">
            <div className="p-4 border-b border-red-100 bg-red-50">
              <h2 className="text-base font-semibold text-red-700">Danger zone</h2>
              <p className="text-red-600 text-xs mt-0.5">
                Irreversible actions that affect your account.
              </p>
            </div>

            <div className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <span className="text-sm font-medium text-gray-900">Delete account</span>
                  <p className="text-xs text-gray-500">Permanently delete your account and all data</p>
                </div>
                <button
                  onClick={() => setShowDeleteModal(true)}
                  className="flex items-center space-x-1.5 px-3 py-2 bg-red-500 hover:bg-red-600 text-white text-sm font-medium rounded-lg transition-colors"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>Delete</span>
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Connect Account Modal */}
      {showConnectModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-sm w-full p-5">
            <h3 className="text-base font-bold text-gray-900 mb-2">Connect Account</h3>
            <p className="text-sm text-gray-600 mb-4">Choose a platform to connect:</p>
            
            <div className="space-y-2">
              <button
                onClick={() => handleConnect('youtube')}
                className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-red-500 hover:bg-red-50 transition-colors"
              >
                <div className="w-10 h-10 bg-red-500 rounded-lg flex items-center justify-center text-white">
                  <Youtube className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <span className="text-sm font-semibold text-gray-900">YouTube</span>
                  <p className="text-xs text-gray-500">Connect your channel</p>
                </div>
              </button>

              <button
                onClick={() => handleConnect('tiktok')}
                className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-black hover:bg-gray-50 transition-colors"
              >
                <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center text-white">
                  <Music2 className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <span className="text-sm font-semibold text-gray-900">TikTok</span>
                  <p className="text-xs text-gray-500">Connect your account</p>
                </div>
              </button>

              <button
                onClick={() => handleConnect('instagram')}
                className="w-full flex items-center space-x-3 p-3 border border-gray-200 rounded-lg hover:border-pink-500 hover:bg-pink-50 transition-colors"
              >
                <div className="w-10 h-10 bg-gradient-to-br from-purple-500 via-pink-500 to-orange-500 rounded-lg flex items-center justify-center text-white">
                  <Instagram className="w-5 h-5" />
                </div>
                <div className="text-left">
                  <span className="text-sm font-semibold text-gray-900">Instagram</span>
                  <p className="text-xs text-gray-500">Connect your account</p>
                </div>
              </button>

            </div>

            <button
              onClick={() => setShowConnectModal(false)}
              className="w-full mt-4 py-2 text-sm text-gray-600 font-medium hover:bg-gray-100 rounded-lg transition-colors"
            >
              Cancel
            </button>
          </div>
        </div>
      )}

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
                onClick={() => handleConnect('instagram')}
                className="flex-1 py-2.5 text-sm text-white font-semibold bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 hover:from-purple-600 hover:via-pink-600 hover:to-orange-600 rounded-lg transition-all shadow-md"
              >
                Continue to Facebook
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Delete Account Modal */}
      {showDeleteModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl max-w-sm w-full p-5">
            <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-3">
              <AlertTriangle className="w-6 h-6 text-red-500" />
            </div>
            <h3 className="text-base font-bold text-gray-900 text-center mb-1">Delete Account?</h3>
            <p className="text-sm text-gray-600 text-center mb-4">
              This action cannot be undone. All your data will be permanently deleted.
            </p>
            <div className="flex space-x-2">
              <button
                onClick={() => setShowDeleteModal(false)}
                className="flex-1 py-2 text-sm border border-gray-200 text-gray-700 font-medium rounded-lg hover:bg-gray-50 transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => {
                  // Handle delete
                  setShowDeleteModal(false)
                }}
                className="flex-1 py-2 text-sm bg-red-500 text-white font-medium rounded-lg hover:bg-red-600 transition-colors"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
