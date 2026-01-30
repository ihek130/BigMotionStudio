'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { Check, Zap, Rocket, Crown, Clock, Video, Headphones, TrendingUp, Plus, Minus } from 'lucide-react'

interface Plan {
  id: string
  name: string
  price: number
  originalPrice: number
  priceYearly: number
  description: string
  income: string
  features: string[]
  highlighted?: boolean
  icon: React.ReactNode
  color: string
  videos: number
  baseSeries: number
  canAddSeries: boolean
}

export default function BillingPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [billingPeriod, setBillingPeriod] = useState<'monthly' | 'yearly'>('monthly')
  const [selectedPlan, setSelectedPlan] = useState<string | null>(null)
  
  // Series count state for each plan that supports it
  const [seriesCount, setSeriesCount] = useState<Record<string, number>>({
    launch: 1,
    grow: 1,
    scale: 1
  })

  // Mock current plan - replace with actual user data
  const currentPlan = 'free'
  const currentCredits = 2
  const maxCredits = 3

  const plans: Plan[] = [
    {
      id: 'launch',
      name: 'Launch',
      price: 19,
      originalPrice: 29,
      priceYearly: 17,
      description: 'Best for creators starting with faceless content',
      income: '$50-200',
      videos: 12,
      baseSeries: 1,
      canAddSeries: false,
      icon: <Rocket className="w-6 h-6" />,
      color: 'gray',
      features: [
        'Posts 3 times per week',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark'
      ]
    },
    {
      id: 'grow',
      name: 'Grow',
      price: 39,
      originalPrice: 59,
      priceYearly: 35,
      description: 'Best for creators who want to grow fast',
      income: '$200-500',
      videos: 30,
      baseSeries: 1,
      canAddSeries: true,
      highlighted: true,
      icon: <TrendingUp className="w-6 h-6" />,
      color: 'emerald',
      features: [
        'Posts every day',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark'
      ]
    },
    {
      id: 'scale',
      name: 'Scale',
      price: 69,
      originalPrice: 89,
      priceYearly: 62,
      description: 'Best for creators who want to grow super fast',
      income: '$500-2.3K',
      videos: 60,
      baseSeries: 1,
      canAddSeries: true,
      icon: <Crown className="w-6 h-6" />,
      color: 'gray',
      features: [
        'Posts 2 times per day',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark'
      ]
    }
  ]

  // Calculate price based on series count
  const calculatePrice = (plan: Plan, isYearly: boolean) => {
    const basePrice = isYearly ? plan.priceYearly : plan.price
    if (!plan.canAddSeries || plan.price === 0) return basePrice
    
    const currentSeries = seriesCount[plan.id] || plan.baseSeries
    const extraSeries = currentSeries - plan.baseSeries
    
    // Each extra series adds 100% of the base price
    return basePrice + (extraSeries * basePrice)
  }

  const handleSeriesChange = (planId: string, delta: number, baseSeries: number) => {
    setSeriesCount(prev => {
      const current = prev[planId] || baseSeries
      const newCount = Math.max(baseSeries, current + delta) // Can't go below base
      return { ...prev, [planId]: newCount }
    })
  }

  const handleUpgrade = (planId: string) => {
    setSelectedPlan(planId)
    // In production, redirect to Stripe checkout
    console.log(`Upgrading to ${planId}`)
  }

  const breadcrumbItems = [
    { label: 'Billing' }
  ]

  const planColorClasses = {
    gray: {
      bg: 'bg-gray-100',
      text: 'text-gray-600',
      border: 'border-gray-200',
      button: 'bg-gray-200 text-gray-700 hover:bg-gray-300'
    },
    blue: {
      bg: 'bg-blue-100',
      text: 'text-blue-600',
      border: 'border-blue-200',
      button: 'bg-blue-500 text-white hover:bg-blue-600'
    },
    purple: {
      bg: 'bg-purple-100',
      text: 'text-purple-600',
      border: 'border-purple-300',
      button: 'bg-purple-500 text-white hover:bg-purple-600'
    },
    emerald: {
      bg: 'bg-emerald-100',
      text: 'text-emerald-600',
      border: 'border-emerald-200',
      button: 'bg-emerald-500 text-white hover:bg-emerald-600'
    }
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

        {/* Page Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="mb-6 text-center">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">Choose Your Plan</h1>
            <p className="text-sm text-gray-600 mt-1">Scale your content creation with the right plan for you</p>
          </div>

          {/* Current Plan Status */}
          <div className="max-w-sm mx-auto mb-6">
            <div className="bg-white rounded-xl border border-gray-200 p-4">
              <div className="flex items-center justify-between mb-3">
                <div>
                  <span className="text-xs text-gray-500">Current Plan</span>
                  <h3 className="text-lg font-bold text-gray-900 capitalize">{currentPlan}</h3>
                </div>
                <div className={`w-10 h-10 rounded-lg flex items-center justify-center ${
                  currentPlan === 'free' ? 'bg-gray-100 text-gray-600' :
                  currentPlan === 'launch' ? 'bg-blue-100 text-blue-600' :
                  currentPlan === 'grow' ? 'bg-emerald-100 text-emerald-600' :
                  'bg-purple-100 text-purple-600'
                }`}>
                  {currentPlan === 'free' ? <Zap className="w-5 h-5" /> :
                   currentPlan === 'launch' ? <Rocket className="w-5 h-5" /> :
                   currentPlan === 'grow' ? <TrendingUp className="w-5 h-5" /> :
                   <Crown className="w-5 h-5" />}
                </div>
              </div>
              <div className="flex items-center space-x-3">
                <div className="flex-1">
                  <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-emerald-500 rounded-full transition-all"
                      style={{ width: `${(currentCredits / maxCredits) * 100}%` }}
                    />
                  </div>
                </div>
                <span className="text-sm font-medium text-gray-600">
                  {currentCredits}/{maxCredits} videos
                </span>
              </div>
            </div>
          </div>

          {/* Billing Toggle */}
          <div className="flex items-center justify-center mb-6">
            <div className="bg-white rounded-lg p-1 border border-gray-200 inline-flex">
              <button
                onClick={() => setBillingPeriod('monthly')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors ${
                  billingPeriod === 'monthly'
                    ? 'bg-emerald-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                Monthly
              </button>
              <button
                onClick={() => setBillingPeriod('yearly')}
                className={`px-4 py-1.5 rounded-md text-sm font-medium transition-colors flex items-center space-x-1.5 ${
                  billingPeriod === 'yearly'
                    ? 'bg-emerald-500 text-white'
                    : 'text-gray-600 hover:text-gray-900'
                }`}
              >
                <span>Yearly</span>
                <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                  billingPeriod === 'yearly' ? 'bg-emerald-400' : 'bg-green-100 text-green-700'
                }`}>
                  Save 10%
                </span>
              </button>
            </div>
          </div>

          {/* Pricing Cards */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-4xl mx-auto pt-4">
            {plans.map((plan) => {
              const colors = planColorClasses[plan.color as keyof typeof planColorClasses]
              const dynamicPrice = calculatePrice(plan, billingPeriod === 'yearly')
              const currentSeriesCount = seriesCount[plan.id] || plan.baseSeries
              const isCurrentPlan = plan.id === currentPlan

              return (
                <div
                  key={plan.id}
                  className={`relative bg-white rounded-xl border-2 transition-all hover:shadow-lg ${
                    plan.highlighted 
                      ? 'border-emerald-500 shadow-md shadow-emerald-100 mt-2' 
                      : colors.border
                  }`}
                >
                  {plan.highlighted && (
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 px-3 py-0.5 bg-emerald-500 text-white text-[10px] font-semibold rounded-full uppercase tracking-wide whitespace-nowrap">
                      Most Popular
                    </div>
                  )}

                  <div className="p-4">
                    <div className="flex items-center space-x-2 mb-3">
                      <div className={`w-9 h-9 rounded-lg flex items-center justify-center ${colors.bg} ${colors.text}`}>
                        {plan.icon}
                      </div>
                      <div>
                        <h3 className="text-base font-bold text-gray-900">{plan.name}</h3>
                        <p className="text-xs text-gray-500 leading-tight">{plan.description}</p>
                      </div>
                    </div>

                    <div className="mb-4">
                      <div className="flex items-baseline space-x-1">
                        <span className="text-3xl font-bold text-gray-900">${dynamicPrice}</span>
                        <span className="text-sm text-gray-500">/mo</span>
                      </div>
                      <div className="text-xs text-gray-400 line-through">
                        ${plan.originalPrice}/mo
                      </div>
                      {billingPeriod === 'yearly' && (
                        <p className="text-xs text-gray-500">
                          Billed ${dynamicPrice * 12}/year
                        </p>
                      )}
                    </div>

                    {/* Series Selector */}
                    {plan.canAddSeries && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700">Active Series</span>
                          <div className="flex items-center space-x-2">
                            <button
                              onClick={() => handleSeriesChange(plan.id, -1, plan.baseSeries)}
                              disabled={currentSeriesCount <= plan.baseSeries}
                              className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors ${
                                currentSeriesCount <= plan.baseSeries
                                  ? 'bg-gray-200 text-gray-400 cursor-not-allowed'
                                  : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                              }`}
                            >
                              <Minus className="w-3 h-3" />
                            </button>
                            <span className="text-base font-bold text-gray-900 w-6 text-center">
                              {currentSeriesCount}
                            </span>
                            <button
                              onClick={() => handleSeriesChange(plan.id, 1, plan.baseSeries)}
                              className={`w-7 h-7 rounded-md flex items-center justify-center transition-colors ${colors.bg} ${colors.text} hover:opacity-80`}
                            >
                              <Plus className="w-3 h-3" />
                            </button>
                          </div>
                        </div>
                        {currentSeriesCount > plan.baseSeries && (
                          <p className="text-[10px] text-gray-500 mt-1">
                            +{currentSeriesCount - plan.baseSeries} extra (+${(currentSeriesCount - plan.baseSeries) * (billingPeriod === 'yearly' ? plan.priceYearly : plan.price)}/mo)
                          </p>
                        )}
                      </div>
                    )}

                    {/* Fixed series for Launch plan */}
                    {!plan.canAddSeries && plan.baseSeries > 0 && (
                      <div className="mb-4 p-3 bg-gray-50 rounded-lg">
                        <div className="flex items-center justify-between">
                          <span className="text-xs font-medium text-gray-700">Active Series</span>
                          <span className="text-base font-bold text-gray-900">{plan.baseSeries}</span>
                        </div>
                      </div>
                    )}

                    <div className="space-y-2 mb-4">
                      {plan.features.map((feature, index) => (
                        <div key={index} className="flex items-center space-x-2">
                          <div className={`w-4 h-4 rounded-full flex items-center justify-center flex-shrink-0 ${colors.bg}`}>
                            <Check className={`w-2.5 h-2.5 ${colors.text}`} />
                          </div>
                          <span className="text-xs text-gray-600">{feature}</span>
                        </div>
                      ))}
                    </div>

                    <button
                      onClick={() => handleUpgrade(plan.id)}
                      disabled={isCurrentPlan}
                      className={`w-full py-2.5 rounded-lg text-sm font-semibold transition-colors ${
                        isCurrentPlan
                          ? 'bg-gray-100 text-gray-400 cursor-not-allowed'
                          : plan.highlighted
                            ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200 border border-gray-200'
                      }`}
                    >
                      {isCurrentPlan ? 'Current Plan' : `Choose ${plan.name}`}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>

          {/* Features Comparison */}
          <div className="mt-10 max-w-3xl mx-auto">
            <h2 className="text-lg font-bold text-gray-900 text-center mb-4">Why Upgrade?</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <div className="bg-white rounded-lg p-4 border border-gray-200 text-center">
                <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Video className="w-5 h-5 text-emerald-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">More Videos</h3>
                <p className="text-xs text-gray-600">
                  Generate more videos per month to grow faster.
                </p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200 text-center">
                <div className="w-10 h-10 bg-purple-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Clock className="w-5 h-5 text-purple-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Auto-Posting</h3>
                <p className="text-xs text-gray-600">
                  Post automatically to multiple platforms.
                </p>
              </div>

              <div className="bg-white rounded-lg p-4 border border-gray-200 text-center">
                <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Headphones className="w-5 h-5 text-blue-600" />
                </div>
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Priority Support</h3>
                <p className="text-xs text-gray-600">
                  Get faster responses and assistance.
                </p>
              </div>
            </div>
          </div>

          {/* FAQ */}
          <div className="mt-10 max-w-2xl mx-auto pb-8">
            <h2 className="text-lg font-bold text-gray-900 text-center mb-4">Frequently Asked Questions</h2>
            <div className="space-y-3">
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Can I cancel anytime?</h3>
                <p className="text-xs text-gray-600">
                  Yes! Cancel anytime. Your plan stays active until the billing period ends.
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-1">What happens if I downgrade?</h3>
                <p className="text-xs text-gray-600">
                  Existing videos remain downloadable. New generation follows your new plan's limits.
                </p>
              </div>
              <div className="bg-white rounded-lg p-4 border border-gray-200">
                <h3 className="text-sm font-semibold text-gray-900 mb-1">Do unused credits roll over?</h3>
                <p className="text-xs text-gray-600">
                  Credits reset each billing period and don't roll over.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
