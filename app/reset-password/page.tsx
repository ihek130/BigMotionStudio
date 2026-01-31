'use client'

import { useState, useEffect, Suspense } from 'react'
import Link from 'next/link'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/context/AuthContext'

function ResetPasswordContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { resetPassword, isLoading } = useAuth()
  
  const [token, setToken] = useState<string | null>(null)
  const [formData, setFormData] = useState({
    password: '',
    confirmPassword: '',
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSuccess, setIsSuccess] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const tokenParam = searchParams.get('token')
    if (!tokenParam) {
      setError('Invalid or missing reset token')
    } else {
      setToken(tokenParam)
    }
  }, [searchParams])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return
    }
    
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters')
      return
    }
    
    if (!token) {
      setError('Invalid reset token')
      return
    }
    
    setIsSubmitting(true)
    
    try {
      await resetPassword(token, formData.password)
      setIsSuccess(true)
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/login')
      }, 3000)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to reset password')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({ ...prev, [e.target.name]: e.target.value }))
    setError(null)
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50 flex items-center justify-center p-4">
      <div className="absolute inset-0" style={{
        backgroundImage: `radial-gradient(circle at 25% 25%, rgba(52, 211, 153, 0.08) 0%, transparent 50%),
                         radial-gradient(circle at 75% 75%, rgba(16, 185, 129, 0.08) 0%, transparent 50%)`
      }} />

      <div className="relative w-full max-w-md">
        {/* Logo */}
        <Link href="/" className="flex items-center justify-center space-x-2 mb-8">
          <div className="w-12 h-12 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center shadow-lg shadow-emerald-500/30">
            <svg className="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 10l4.553-2.276A1 1 0 0121 8.618v6.764a1 1 0 01-1.447.894L15 14M5 18h8a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="text-2xl font-bold bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
            Big Motion Studio
          </span>
        </Link>

        {/* Card */}
        <div className="bg-white rounded-2xl shadow-2xl border-2 border-gray-100 p-8">
          {!isSuccess ? (
            <>
              {/* Header */}
              <div className="text-center mb-8">
                <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                  </svg>
                </div>
                <h1 className="text-2xl font-bold text-gray-900 mb-2">Reset Your Password</h1>
                <p className="text-gray-600">
                  Enter your new password below
                </p>
              </div>

              {/* Error Display */}
              {error && (
                <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded-xl">
                  <p className="text-red-600 text-sm font-medium">{error}</p>
                </div>
              )}

              {/* Form */}
              <form onSubmit={handleSubmit} className="space-y-5">
                <div>
                  <label htmlFor="password" className="block text-sm font-semibold text-gray-700 mb-2">
                    New Password
                  </label>
                  <input
                    type="password"
                    id="password"
                    name="password"
                    value={formData.password}
                    onChange={handleInputChange}
                    required
                    minLength={8}
                    disabled={isSubmitting || !token}
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-emerald-500 focus:outline-none transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="••••••••"
                  />
                  <p className="mt-1 text-xs text-gray-500">Must be at least 8 characters</p>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-semibold text-gray-700 mb-2">
                    Confirm New Password
                  </label>
                  <input
                    type="password"
                    id="confirmPassword"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleInputChange}
                    required
                    minLength={8}
                    disabled={isSubmitting || !token}
                    className="w-full px-4 py-3 rounded-xl border-2 border-gray-200 focus:border-emerald-500 focus:outline-none transition-colors disabled:bg-gray-100 disabled:cursor-not-allowed"
                    placeholder="••••••••"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isSubmitting || isLoading || !token}
                  className="w-full py-3.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5 transition-all disabled:opacity-70 disabled:cursor-not-allowed disabled:hover:translate-y-0"
                >
                  {isSubmitting ? (
                    <span className="flex items-center justify-center">
                      <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                      </svg>
                      Resetting...
                    </span>
                  ) : (
                    'Reset Password'
                  )}
                </button>
              </form>
            </>
          ) : (
            /* Success State */
            <div className="text-center">
              <div className="w-16 h-16 bg-emerald-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <h1 className="text-2xl font-bold text-gray-900 mb-2">Password Reset!</h1>
              <p className="text-gray-600 mb-6">
                Your password has been successfully reset. Redirecting you to login...
              </p>
              <Link
                href="/login"
                className="inline-flex items-center justify-center px-6 py-3 bg-gradient-to-r from-emerald-500 to-teal-500 text-white font-semibold rounded-xl shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5 transition-all"
              >
                Go to Login
              </Link>
            </div>
          )}

          {/* Back to Login */}
          {!isSuccess && (
            <Link 
              href="/login" 
              className="flex items-center justify-center space-x-2 mt-6 text-gray-600 hover:text-gray-900 font-medium"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              <span>Back to login</span>
            </Link>
          )}
        </div>
      </div>
    </div>
  )
}

export default function ResetPasswordPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600"></div>
      </div>
    }>
      <ResetPasswordContent />
    </Suspense>
  )
}
