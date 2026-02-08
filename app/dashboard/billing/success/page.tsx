'use client'

import { useEffect, useState } from 'react'
import { useSearchParams, useRouter } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { CheckCircle, Loader2, AlertCircle, ArrowRight } from 'lucide-react'

const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

type VerifyStatus = 'verifying' | 'success' | 'processing' | 'error'

export default function CheckoutSuccessPage() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const { refreshUser } = useAuth()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [status, setStatus] = useState<VerifyStatus>('verifying')
  const [planName, setPlanName] = useState('')
  const [seriesCount, setSeriesCount] = useState(1)
  const [error, setError] = useState('')
  const [retryCount, setRetryCount] = useState(0)

  const checkoutId = searchParams.get('checkout_id')

  useEffect(() => {
    if (!checkoutId) {
      setStatus('error')
      setError('No checkout ID found. Please try again from the billing page.')
      return
    }

    verifyCheckout()
  }, [checkoutId, retryCount])

  const verifyCheckout = async () => {
    const token = localStorage.getItem('reelflow_access_token')
    if (!token) {
      router.push('/login')
      return
    }

    try {
      const response = await fetch(`${API_BASE}/api/checkout/${checkoutId}/verify`, {
        headers: {
          'Authorization': `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        const err = await response.json().catch(() => ({ detail: 'Verification failed' }))
        throw new Error(err.detail || 'Failed to verify checkout')
      }

      const data = await response.json()

      if (data.status === 'success') {
        setStatus('success')
        setPlanName(data.plan || 'Pro')
        setSeriesCount(data.series_count || 1)
        // Refresh user data to update plan in AuthContext
        await refreshUser()
      } else {
        // Payment still processing — retry a few times
        if (retryCount < 5) {
          setStatus('processing')
          setTimeout(() => setRetryCount(prev => prev + 1), 3000)
        } else {
          // Still not confirmed — show processing state (webhook will handle activation)
          setStatus('processing')
          setPlanName('your selected')
        }
      }
    } catch (err) {
      setStatus('error')
      setError(err instanceof Error ? err.message : 'Verification failed')
    }
  }

  const breadcrumbItems = [
    { label: 'Billing', href: '/dashboard/billing' },
    { label: 'Payment Complete' }
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

        {/* Content */}
        <div className="p-4 sm:p-6 lg:p-8 flex items-center justify-center min-h-[70vh]">
          {status === 'verifying' && (
            <div className="text-center">
              <Loader2 className="w-16 h-16 text-emerald-500 animate-spin mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Verifying Payment...</h1>
              <p className="text-gray-600">Please wait while we confirm your payment.</p>
            </div>
          )}

          {status === 'processing' && (
            <div className="text-center">
              <Loader2 className="w-16 h-16 text-amber-500 animate-spin mx-auto mb-4" />
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Processing Payment...</h1>
              <p className="text-gray-600">Your payment is being processed. This may take a moment.</p>
              {retryCount < 5 ? (
                <p className="text-sm text-gray-400 mt-2">Attempt {retryCount + 1} of 6</p>
              ) : (
                <div className="mt-4 space-y-2">
                  <p className="text-sm text-gray-500">
                    Your payment was received and your plan will activate automatically within a few minutes.
                  </p>
                  <button
                    onClick={() => router.push('/dashboard')}
                    className="mt-3 px-6 py-2 bg-emerald-500 text-white rounded-lg font-semibold hover:bg-emerald-600 transition-colors"
                  >
                    Go to Dashboard
                  </button>
                </div>
              )}
            </div>
          )}

          {status === 'success' && (
            <div className="text-center max-w-md">
              <div className="w-20 h-20 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <CheckCircle className="w-12 h-12 text-emerald-500" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Payment Successful!</h1>
              <p className="text-gray-600 mb-2">
                Welcome to the <span className="font-semibold capitalize">{planName}</span> plan!
              </p>
              {seriesCount > 1 && (
                <p className="text-sm text-gray-500 mb-6">
                  You can now create up to {seriesCount} video series.
                </p>
              )}
              <div className="space-y-3">
                <button
                  onClick={() => router.push('/create')}
                  className="w-full px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white rounded-xl font-semibold hover:from-emerald-600 hover:to-teal-600 transition-all shadow-lg shadow-emerald-500/30 flex items-center justify-center space-x-2"
                >
                  <span>Create Your First Series</span>
                  <ArrowRight className="w-5 h-5" />
                </button>
                <button
                  onClick={() => router.push('/dashboard')}
                  className="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
                >
                  Go to Dashboard
                </button>
              </div>
            </div>
          )}

          {status === 'error' && (
            <div className="text-center max-w-md">
              <div className="w-20 h-20 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-6">
                <AlertCircle className="w-12 h-12 text-red-500" />
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Verification Issue</h1>
              <p className="text-gray-600 mb-6">{error}</p>
              <div className="space-y-3">
                <button
                  onClick={() => {
                    setStatus('verifying')
                    setRetryCount(0)
                  }}
                  className="w-full px-6 py-3 bg-emerald-500 text-white rounded-xl font-semibold hover:bg-emerald-600 transition-colors"
                >
                  Try Again
                </button>
                <button
                  onClick={() => router.push('/dashboard/billing')}
                  className="w-full px-6 py-3 bg-gray-100 text-gray-700 rounded-xl font-semibold hover:bg-gray-200 transition-colors"
                >
                  Back to Billing
                </button>
                <p className="text-xs text-gray-400 mt-4">
                  If you were charged, your plan will be activated automatically within a few minutes.
                  Contact support if the issue persists.
                </p>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
