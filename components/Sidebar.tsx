'use client'

import Link from 'next/link'
import { usePathname, useRouter } from 'next/navigation'
import { Film, Video, BookOpen, Settings, CreditCard, Plus, X, Zap, LogOut, ChevronUp } from 'lucide-react'
import { useState, useEffect, useRef } from 'react'
import { useAuth } from '@/context/AuthContext'

interface SidebarProps {
  mobileOpen?: boolean
  onClose?: () => void
}

type PlanType = 'launch' | 'grow' | 'scale'

export default function Sidebar({ mobileOpen = false, onClose }: SidebarProps = {}) {
  const pathname = usePathname()
  const router = useRouter()
  const [isOpen, setIsOpen] = useState(false)
  const [userMenuOpen, setUserMenuOpen] = useState(false)
  const userMenuRef = useRef<HTMLDivElement>(null)
  
  // Get user from auth context
  const { user, logout, isAuthenticated } = useAuth()

  // User data from context or defaults
  const userPlan = (user?.plan || 'launch') as PlanType
  const maxVideos = user?.plan_limits?.videos_per_month ?? 0
  const used = user?.videos_generated_this_month ?? 0
  const credits = Math.max(0, maxVideos - used)
  const userEmail = user?.email || ''
  const userName = user?.name || userEmail.split('@')[0] || 'User'

  useEffect(() => {
    setIsOpen(mobileOpen)
  }, [mobileOpen])

  // Close user menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(event.target as Node)) {
        setUserMenuOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleClose = () => {
    setIsOpen(false)
    onClose?.()
  }

  const handleSignOut = () => {
    logout()
    router.push('/login')
  }

  const isActive = (path: string) => {
    if (path === '/dashboard') return pathname === '/dashboard'
    return pathname.startsWith(path)
  }

  return (
    <>
      {/* Mobile Overlay */}
      {isOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-40 lg:hidden" 
          onClick={handleClose}
        />
      )}

      {/* Sidebar */}
      <aside className={`
        w-64 bg-white border-r border-gray-200 flex flex-col fixed h-full z-50 transition-transform duration-300
        lg:translate-x-0
        ${isOpen ? 'translate-x-0' : '-translate-x-full'}
      `}>
      {/* Logo */}
      <div className="p-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <Link href="/" className="flex items-center space-x-2" onClick={handleClose}>
          <img src="/Pictures/Pi7_cropper.png" alt="Big Motion Studio" className="w-8 h-8 rounded-xl" />
          <span className="text-lg font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
            Big Motion Studio
          </span>
          </Link>
          <button 
            onClick={handleClose}
            className="lg:hidden p-1.5 hover:bg-gray-100 rounded-lg transition-colors"
          >
            <X className="w-4 h-4 text-gray-600" />
          </button>
        </div>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-3 space-y-1">
        <Link
          href="/dashboard"
          onClick={handleClose}
          className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive('/dashboard') && !pathname.startsWith('/create')
              ? 'bg-emerald-50 text-emerald-700'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Film className="w-4 h-4" />
          <span>Series</span>
        </Link>
        <Link
          href="/dashboard/videos"
          onClick={handleClose}
          className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive('/dashboard/videos')
              ? 'bg-emerald-50 text-emerald-700'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Video className="w-4 h-4" />
          <span>Videos</span>
        </Link>
        <Link
          href="/dashboard/guides"
          onClick={handleClose}
          className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive('/dashboard/guides')
              ? 'bg-emerald-50 text-emerald-700'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <BookOpen className="w-4 h-4" />
          <span>Guides</span>
        </Link>
        <Link
          href="/dashboard/settings"
          onClick={handleClose}
          className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive('/dashboard/settings')
              ? 'bg-emerald-50 text-emerald-700'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <Settings className="w-4 h-4" />
          <span>Settings</span>
        </Link>
        <Link
          href="/dashboard/billing"
          onClick={handleClose}
          className={`w-full flex items-center space-x-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors ${
            isActive('/dashboard/billing')
              ? 'bg-emerald-50 text-emerald-700'
              : 'text-gray-700 hover:bg-gray-100'
          }`}
        >
          <CreditCard className="w-4 h-4" />
          <span>Billing</span>
        </Link>
      </nav>

      {/* Bottom Section */}
      <div className="p-3 border-t border-gray-200 space-y-3">
        {/* Upgrade Button - Only show if not on highest plan and not admin */}
        {userPlan !== 'scale' && !user?.is_admin && (
          <Link
            href="/dashboard/billing"
            onClick={handleClose}
            className="w-full flex items-center justify-center space-x-2 px-3 py-2.5 bg-gradient-to-r from-amber-500 to-orange-500 text-white rounded-lg text-sm font-semibold hover:from-amber-600 hover:to-orange-600 transition-all shadow-md shadow-orange-500/30"
          >
            <Zap className="w-4 h-4" />
            <span>Upgrade</span>
          </Link>
        )}
        
        {/* Credits Display */}
        <div className={`rounded-lg p-3 bg-emerald-50`}>
          <div className="flex items-center justify-between mb-1">
            <span className="text-xs font-medium text-emerald-900">
              Credits
            </span>
            <span className={`text-[10px] px-1.5 py-0.5 rounded-full font-medium ${
              user?.is_admin ? 'bg-purple-100 text-purple-600' :
              userPlan === 'launch' ? 'bg-blue-100 text-blue-600' :
              userPlan === 'grow' ? 'bg-emerald-100 text-emerald-600' :
              'bg-purple-100 text-purple-600'
            }`}>
              {user?.is_admin ? 'Admin' : userPlan === 'launch' ? 'Launch' : userPlan === 'grow' ? 'Grow' : 'Scale'}
            </span>
          </div>
          <div className="text-xl font-bold text-emerald-700">
            {user?.is_admin ? '∞' : credits}
          </div>
          <p className="text-[10px] text-emerald-600">
            {user?.is_admin ? 'Unlimited videos' : `videos remaining`}
          </p>
        </div>

        {/* New Series Button */}
        <Link
          href="/create"
          onClick={handleClose}
          className="w-full flex items-center justify-center space-x-2 px-3 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-lg text-sm font-semibold hover:from-emerald-600 hover:to-teal-600 transition-all shadow-md shadow-emerald-500/30"
        >
          <Plus className="w-4 h-4" />
          <span>New Series</span>
        </Link>

        {/* User Account Section - Always show */}
        <div ref={userMenuRef} className="relative">
          <button
            onClick={() => setUserMenuOpen(!userMenuOpen)}
            className="w-full flex items-center justify-between px-3 py-2.5 bg-gray-50 hover:bg-gray-100 rounded-lg transition-colors border border-gray-200"
          >
            <div className="flex items-center space-x-3">
              {/* Avatar */}
              <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-full flex items-center justify-center text-white font-semibold text-sm">
                {userName.charAt(0).toUpperCase()}
              </div>
              <div className="text-left">
                <p className="text-sm font-medium text-gray-900 truncate max-w-[120px]">
                  {userName}
                </p>
                <p className="text-[10px] text-gray-500 truncate max-w-[120px]">
                  {userEmail || 'Not signed in'}
                </p>
              </div>
            </div>
            <ChevronUp className={`w-4 h-4 text-gray-400 transition-transform ${userMenuOpen ? '' : 'rotate-180'}`} />
          </button>

          {/* Dropdown Menu */}
          {userMenuOpen && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-white rounded-lg shadow-lg border border-gray-200 py-1 z-50">
              <button
                onClick={handleSignOut}
                className="w-full flex items-center space-x-3 px-4 py-2.5 text-sm text-red-600 hover:bg-red-50 transition-colors"
              >
                <LogOut className="w-4 h-4" />
                <span>Sign out</span>
              </button>
            </div>
          )}
        </div>
      </div>
      </aside>
    </>
  )
}
