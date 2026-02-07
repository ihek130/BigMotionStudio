'use client'

import { useState, useEffect } from 'react'
import { useWizard } from '@/context/WizardContext'
import { useAuth } from '@/context/AuthContext'
import { useRouter } from 'next/navigation'
import { ArrowRight } from 'lucide-react'
import PaywallModal from '@/components/PaywallModal'

const niches = [
  {
    id: 'scary-stories',
    name: 'Scary Stories',
    description: 'Scary stories that give you goosebumps',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    gradient: 'from-red-500 to-orange-600',
  },
  {
    id: 'history',
    name: 'History',
    description: 'Viral videos about history',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
      </svg>
    ),
    gradient: 'from-blue-500 to-indigo-600',
  },
  {
    id: 'true-crime',
    name: 'True Crime',
    description: 'True crime stories',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
      </svg>
    ),
    gradient: 'from-gray-700 to-gray-900',
  },
  {
    id: 'stoic-motivation',
    name: 'Stoic Motivation',
    description: 'Stoic philosophy & life lessons',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    gradient: 'from-emerald-500 to-green-600',
  },
  {
    id: 'random-fact',
    name: 'Random Facts',
    description: 'Interesting facts',
    format: '5 Things You Didn\'t Know',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    gradient: 'from-yellow-500 to-amber-600',
  },
  {
    id: 'good-morals',
    name: 'Good Morals',
    description: 'Good morals & life lessons',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
      </svg>
    ),
    gradient: 'from-pink-500 to-rose-600',
  },
  {
    id: 'psychology',
    name: 'Psychology',
    description: 'Human behavior & mind facts',
    format: 'Storytelling',
    icon: (
      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z" />
      </svg>
    ),
    gradient: 'from-teal-500 to-cyan-600',
  },
]

export default function NicheSelectionPage() {
  const [selectedNiche, setSelectedNiche] = useState<string>('')
  const [showPaywall, setShowPaywall] = useState(false)
  const { updateData } = useWizard()
  const { user } = useAuth()
  const router = useRouter()

  // Show paywall if user is on free plan
  useEffect(() => {
    if (user && user.plan === 'free') {
      setShowPaywall(true)
    }
  }, [user])

  const handleContinue = () => {
    if (user && user.plan === 'free') {
      setShowPaywall(true)
      return
    }
    if (selectedNiche) {
      updateData({ niche: selectedNiche })
      router.push('/create/style')
    }
  }

  return (
    <div className="max-w-6xl mx-auto">
      {/* Header */}
      <div className="text-center mb-5">
        <h1 className="text-xl sm:text-2xl font-bold mb-2">
          Choose Your{' '}
          <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
            Content Niche
          </span>
        </h1>
        <p className="text-sm text-gray-600 max-w-xl mx-auto">
          Select the topic that resonates with you. Our AI will create engaging content tailored to this niche.
        </p>
      </div>

      {/* Niche Grid - 4 columns for better fit */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3 mb-6">
        {niches.map((niche) => (
          <button
            key={niche.id}
            onClick={() => setSelectedNiche(niche.id)}
            className={`group relative p-3 rounded-xl border-2 transition-all duration-300 text-left ${
              selectedNiche === niche.id
                ? 'border-emerald-500 bg-gradient-to-br from-emerald-50 to-teal-50 shadow-lg shadow-emerald-100/50'
                : 'border-gray-200 bg-white hover:border-emerald-300 hover:shadow-md'
            }`}
          >
            {/* Selected indicator */}
            {selectedNiche === niche.id && (
              <div className="absolute top-2 right-2 w-5 h-5 bg-emerald-500 rounded-full flex items-center justify-center shadow-md">
                <svg className="w-3 h-3 text-white" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
              </div>
            )}

            {/* Icon */}
            <div className={`w-10 h-10 bg-gradient-to-br ${niche.gradient} rounded-lg flex items-center justify-center mb-2 text-white shadow-md group-hover:scale-105 transition-transform`}>
              {niche.icon}
            </div>

            {/* Content */}
            <h3 className="text-sm font-bold text-gray-900 mb-0.5">{niche.name}</h3>
            <p className="text-xs text-gray-600 mb-1.5 line-clamp-1">{niche.description}</p>
            <div className="inline-block px-1.5 py-0.5 bg-emerald-100 text-emerald-700 rounded text-[10px] font-medium">
              {niche.format}
            </div>
          </button>
        ))}
      </div>

      {/* Navigation */}
      <div className="flex justify-end">
        <button
          onClick={handleContinue}
          disabled={!selectedNiche}
          className={`group px-5 py-2.5 rounded-xl font-semibold transition-all flex items-center space-x-2 text-sm ${
            selectedNiche
              ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/40 hover:shadow-xl hover:-translate-y-0.5'
              : 'bg-gray-200 text-gray-400 cursor-not-allowed'
          }`}
        >
          <span>Continue to Style</span>
          <ArrowRight className={`w-4 h-4 ${selectedNiche ? 'group-hover:translate-x-1' : ''} transition-transform`} />
        </button>
      </div>

      {/* Paywall Modal for free users */}
      <PaywallModal
        isOpen={showPaywall}
        onClose={() => setShowPaywall(false)}
        title="Subscribe to Create Series"
        message="You need a paid plan to create video series. Choose a plan to start generating content!"
      />
    </div>
  )
}
