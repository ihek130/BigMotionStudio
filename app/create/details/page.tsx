'use client'

import { useState, useEffect } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useRouter } from 'next/navigation'
import { ArrowRight, ArrowLeft, Clock, Globe } from 'lucide-react'
import { useAuth } from '@/context/AuthContext'

// TikTok Icon Component
const TikTokIcon = ({ className }: { className?: string }) => (
  <svg className={className} viewBox="0 0 24 24" fill="currentColor">
    <path d="M19.59 6.69a4.83 4.83 0 01-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 01-5.2 1.74 2.89 2.89 0 012.31-4.64 2.93 2.93 0 01.88.13V9.4a6.84 6.84 0 00-1-.05A6.33 6.33 0 005 20.1a6.34 6.34 0 0010.86-4.43v-7a8.16 8.16 0 004.77 1.52v-3.4a4.85 4.85 0 01-1-.1z"/>
  </svg>
)

// Plan type for posting times
type PlanType = 'launch' | 'grow' | 'scale'

export default function DetailsPage() {
  const { updateData, data } = useWizard()
  const router = useRouter()
  const { user } = useAuth()
  
  // Get user plan from auth context
  const userPlan = (user?.plan || 'launch') as PlanType
  
  // Determine videos per day based on plan
  const videosPerDay = userPlan === 'scale' ? 2 : 1
  
  const [formData, setFormData] = useState({
    seriesName: '',
    description: '',
    videoDuration: '60',
    postingTime1: '09:00',
    postingTime2: '18:00', // Second time for Scale plan
    timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
  })

  const [errors, setErrors] = useState<Record<string, string>>({})

  // Common timezone options
  const timezoneOptions = [
    { value: 'Pacific/Honolulu', label: 'Hawaii (HST, UTC-10)' },
    { value: 'America/Anchorage', label: 'Alaska (AKST, UTC-9)' },
    { value: 'America/Los_Angeles', label: 'Pacific Time (PST, UTC-8)' },
    { value: 'America/Denver', label: 'Mountain Time (MST, UTC-7)' },
    { value: 'America/Chicago', label: 'Central Time (CST, UTC-6)' },
    { value: 'America/New_York', label: 'Eastern Time (EST, UTC-5)' },
    { value: 'America/Sao_Paulo', label: 'Brasília (BRT, UTC-3)' },
    { value: 'UTC', label: 'UTC (UTC+0)' },
    { value: 'Europe/London', label: 'London (GMT, UTC+0)' },
    { value: 'Europe/Paris', label: 'Central Europe (CET, UTC+1)' },
    { value: 'Europe/Istanbul', label: 'Istanbul (TRT, UTC+3)' },
    { value: 'Asia/Dubai', label: 'Dubai (GST, UTC+4)' },
    { value: 'Asia/Karachi', label: 'Pakistan (PKT, UTC+5)' },
    { value: 'Asia/Kolkata', label: 'India (IST, UTC+5:30)' },
    { value: 'Asia/Dhaka', label: 'Bangladesh (BST, UTC+6)' },
    { value: 'Asia/Bangkok', label: 'Bangkok (ICT, UTC+7)' },
    { value: 'Asia/Shanghai', label: 'China (CST, UTC+8)' },
    { value: 'Asia/Tokyo', label: 'Japan (JST, UTC+9)' },
    { value: 'Australia/Sydney', label: 'Sydney (AEST, UTC+10)' },
    { value: 'Pacific/Auckland', label: 'New Zealand (NZST, UTC+12)' },
  ]

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
    // Clear error when user types
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }))
    }
  }

  const validateForm = () => {
    const newErrors: Record<string, string> = {}
    
    if (!formData.seriesName.trim()) {
      newErrors.seriesName = 'Series name is required'
    }
    
    if (!formData.description.trim()) {
      newErrors.description = 'Description is required'
    } else if (formData.description.length < 20) {
      newErrors.description = 'Description should be at least 20 characters'
    }

    setErrors(newErrors)
    return Object.keys(newErrors).length === 0
  }

  const handleContinue = () => {
    if (validateForm()) {
      updateData({
        seriesName: formData.seriesName,
        description: formData.description,
        videoDuration: parseInt(formData.videoDuration),
        postingTimes: videosPerDay === 2 
          ? [formData.postingTime1, formData.postingTime2]
          : [formData.postingTime1],
        timezone: formData.timezone,
      })
      router.push('/create/platforms')
    }
  }

  const handleBack = () => {
    router.push('/create/captions')
  }

  return (
    <div className="max-w-4xl mx-auto">
      {/* Header */}
      <div className="text-center mb-4">
        <h1 className="text-xl sm:text-2xl font-bold mb-1">
          Configure{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Series Details
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Set up your video series name, description, and posting schedule
        </p>
      </div>

      {/* Form */}
      <div className="bg-white rounded-xl shadow-md border border-gray-200 p-5 mb-6">
        <div className="space-y-4">
          {/* Series Name and Description in a row on larger screens */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
            {/* Series Name */}
            <div>
              <label htmlFor="seriesName" className="block text-xs font-semibold text-gray-700 mb-1">
                Series Name *
              </label>
              <input
                type="text"
                id="seriesName"
                name="seriesName"
                value={formData.seriesName}
                onChange={handleInputChange}
                placeholder="e.g., Dark Mysteries Uncovered"
                className={`w-full px-3 py-2 rounded-lg border-2 transition-colors text-sm ${
                  errors.seriesName
                    ? 'border-red-300 focus:border-red-500'
                    : 'border-gray-200 focus:border-emerald-500'
                } focus:outline-none`}
              />
              {errors.seriesName && (
                <p className="mt-1 text-xs text-red-600">{errors.seriesName}</p>
              )}
            </div>

            {/* Description */}
            <div>
              <label htmlFor="description" className="block text-xs font-semibold text-gray-700 mb-1">
                Series Description *
              </label>
              <input
                type="text"
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                placeholder="Describe what your series is about..."
                className={`w-full px-3 py-2 rounded-lg border-2 transition-colors text-sm ${
                  errors.description
                    ? 'border-red-300 focus:border-red-500'
                    : 'border-gray-200 focus:border-emerald-500'
                } focus:outline-none`}
              />
              {errors.description && (
                <p className="mt-1 text-xs text-red-600">{errors.description}</p>
              )}
            </div>
          </div>

          {/* Video Duration - 30s, 45s, 60s with TikTok badge */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              Video Duration
            </label>
            <div className="grid grid-cols-3 gap-2">
              {[
                { value: '30', label: '30s', desc: 'Quick' },
                { value: '45', label: '45s', desc: 'Standard' },
                { value: '60', label: '60s', desc: 'Monetizable', tiktok: true },
              ].map((option) => (
                <button
                  key={option.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, videoDuration: option.value }))}
                  className={`relative py-2.5 px-3 rounded-lg border-2 transition-all text-center ${
                    formData.videoDuration === option.value
                      ? option.tiktok 
                        ? 'border-pink-500 bg-gradient-to-br from-pink-50 to-purple-50 font-semibold'
                        : 'border-emerald-500 bg-emerald-50 font-semibold text-emerald-700'
                      : 'border-gray-200 bg-white hover:border-emerald-300 text-gray-700'
                  }`}
                >
                  {option.tiktok && (
                    <div className="absolute -top-2 left-1/2 -translate-x-1/2 flex items-center space-x-1 bg-gradient-to-r from-pink-500 to-purple-500 text-white text-[8px] px-1.5 py-0.5 rounded-full font-bold">
                      <TikTokIcon className="w-2 h-2" />
                      <span>MONETIZABLE</span>
                    </div>
                  )}
                  <div className={`text-sm font-bold ${option.tiktok && formData.videoDuration === option.value ? 'text-pink-600' : ''}`}>
                    {option.label}
                  </div>
                  <div className={`text-[10px] ${option.tiktok && formData.videoDuration === option.value ? 'text-purple-500' : 'text-gray-400'}`}>
                    {option.desc}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {/* Posting Times - Dynamic based on plan */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              <span className="flex items-center space-x-1">
                <Clock className="w-3 h-3" />
                <span>Posting Time{videosPerDay > 1 ? 's' : ''}</span>
                <span className="text-[10px] text-gray-400 font-normal ml-1">
                  — Your plan posts {videosPerDay === 2 ? '2x daily' : userPlan === 'launch' ? '3x weekly' : 'daily'}
                </span>
              </span>
            </label>
            <div className={`grid ${videosPerDay === 2 ? 'grid-cols-2' : 'grid-cols-1'} gap-3`}>
              <div>
                <label className="text-[10px] text-gray-500 mb-1 block">
                  {videosPerDay === 2 ? 'First Video' : 'Video Time'}
                </label>
                <input
                  type="time"
                  name="postingTime1"
                  value={formData.postingTime1}
                  onChange={handleInputChange}
                  className="w-full px-3 py-2 rounded-lg border-2 border-gray-200 focus:border-emerald-500 focus:outline-none transition-colors text-sm"
                />
              </div>
              {videosPerDay === 2 && (
                <div>
                  <label className="text-[10px] text-gray-500 mb-1 block">Second Video</label>
                  <input
                    type="time"
                    name="postingTime2"
                    value={formData.postingTime2}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 rounded-lg border-2 border-gray-200 focus:border-emerald-500 focus:outline-none transition-colors text-sm"
                  />
                </div>
              )}
            </div>
          </div>

          {/* Timezone */}
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-2">
              <span className="flex items-center space-x-1">
                <Globe className="w-3 h-3" />
                <span>Your Timezone</span>
                <span className="text-[10px] text-gray-400 font-normal ml-1">
                  — Auto-detected from your browser
                </span>
              </span>
            </label>
            <select
              name="timezone"
              value={formData.timezone}
              onChange={handleInputChange}
              className="w-full px-3 py-2 rounded-lg border-2 border-gray-200 focus:border-emerald-500 focus:outline-none transition-colors text-sm"
            >
              {timezoneOptions.map((tz) => (
                <option key={tz.value} value={tz.value}>
                  {tz.label}
                </option>
              ))}
              {/* If user's detected timezone isn't in our list, add it */}
              {!timezoneOptions.find(tz => tz.value === formData.timezone) && (
                <option value={formData.timezone}>
                  {formData.timezone}
                </option>
              )}
            </select>
          </div>

          {/* Compact Summary */}
          <div className="p-3 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-lg border border-emerald-200">
            <h3 className="font-semibold text-xs mb-2 text-gray-900">Series Summary</h3>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 text-xs">
              <div className="flex justify-between">
                <span className="text-gray-500">Niche:</span>
                <span className="font-medium text-gray-700">{data.niche || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Style:</span>
                <span className="font-medium text-gray-700">{data.style || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Voice:</span>
                <span className="font-medium text-gray-700">{data.voiceId || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Music:</span>
                <span className="font-medium text-gray-700">{data.musicId || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Captions:</span>
                <span className="font-medium text-gray-700">{data.captionStyle || '-'}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-gray-500">Duration:</span>
                <span className="font-medium text-gray-700">{formData.videoDuration}s</span>
              </div>
              <div className="flex justify-between col-span-2 sm:col-span-3">
                <span className="text-gray-500">Posting:</span>
                <span className="font-medium text-gray-700">
                  {videosPerDay === 2 
                    ? `${formData.postingTime1} & ${formData.postingTime2}` 
                    : formData.postingTime1}
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={handleBack}
          className="group px-5 py-2.5 bg-white border-2 border-gray-200 hover:border-gray-300 text-gray-700 rounded-xl font-semibold transition-all flex items-center space-x-2 hover:shadow-md text-sm"
        >
          <ArrowLeft className="w-4 h-4 group-hover:-translate-x-1 transition-transform" />
          <span>Back</span>
        </button>
        <button
          onClick={handleContinue}
          className="group px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white rounded-xl font-semibold transition-all flex items-center space-x-2 shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5 text-sm"
        >
          <span>Continue to Platforms</span>
          <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
        </button>
      </div>
    </div>
  )
}
