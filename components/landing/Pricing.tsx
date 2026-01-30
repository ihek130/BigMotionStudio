'use client'

import { useState } from 'react'
import { Check, TrendingUp, Plus, Minus } from 'lucide-react'
import Link from 'next/link'

interface Plan {
  name: string
  price: number
  income: string
  videos: number
  series: number
  features: string[]
  popular: boolean
  canAddSeries: boolean
}

export default function Pricing() {
  const [seriesCount, setSeriesCount] = useState<Record<string, number>>({
    Launch: 1,
    Grow: 1,
    Scale: 1,
  })

  const handleSeriesChange = (planName: string, baseSeries: number, increment: number) => {
    setSeriesCount(prev => ({
      ...prev,
      [planName]: Math.max(baseSeries, (prev[planName] || baseSeries) + increment)
    }))
  }

  const calculatePrice = (basePrice: number, baseSeries: number, currentSeries: number) => {
    const extraSeries = currentSeries - baseSeries
    return basePrice + (extraSeries * basePrice)
  }

  const plans: Plan[] = [
    {
      name: 'Launch',
      price: 19,
      income: '$50-200',
      videos: 12,
      series: 1,
      features: [
        'Posts 3 times per week',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark',
      ],
      popular: false,
      canAddSeries: false,
    },
    {
      name: 'Grow',
      price: 39,
      income: '$200-500',
      videos: 30,
      series: 1,
      features: [
        'Posts every day',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark',
      ],
      popular: true,
      canAddSeries: true,
    },
    {
      name: 'Scale',
      price: 69,
      income: '$500-2.3K',
      videos: 60,
      series: 1,
      features: [
        'Posts 2 times per day',
        '1 Series',
        'Automated posting',
        'Background music',
        '6+ video art styles',
        'Custom AI voiceover',
        'No watermark',
      ],
      popular: false,
      canAddSeries: true,
    },
  ]

  return (
    <section id="pricing" className="py-8 sm:py-10 bg-white">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-6">
          <h2 className="text-xl sm:text-2xl font-bold mb-1">
            Start Earning{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Passive Income
            </span>
          </h2>
          <p className="text-xs text-gray-600 max-w-2xl mx-auto mb-4">
            Choose the plan that fits your content goals
          </p>

          {/* Toggle */}
          <div className="inline-flex items-center space-x-2 p-0.5 bg-gray-100 rounded-lg text-xs">
            <button className="px-4 py-1.5 bg-white text-gray-900 font-medium rounded-md shadow-sm">
              Monthly
            </button>
            <button className="px-4 py-1.5 text-gray-600 hover:text-gray-900 font-medium">
              Yearly
              <span className="ml-1.5 px-1.5 py-0.5 bg-green-100 text-green-700 text-[10px] rounded-full">
                Save 10%
              </span>
            </button>
          </div>
        </div>

        <div className="grid md:grid-cols-3 gap-4">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-white rounded-xl p-4 border transition-all duration-300 ${
                plan.popular
                  ? 'border-emerald-500 shadow-xl shadow-emerald-100/50 scale-[1.02] md:scale-105'
                  : 'border-gray-200 hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-50'
              }`}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2 px-3 py-0.5 bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-[10px] font-semibold rounded-full shadow-md shadow-emerald-500/40">
                  Most Popular
                </div>
              )}

              {/* Header */}
              <div className="text-center mb-4">
                <h3 className="text-lg font-bold text-gray-900 mb-1">{plan.name}</h3>
                <div className="flex items-baseline justify-center space-x-1 mb-2">
                  <span className="text-3xl font-bold text-gray-900">
                    ${calculatePrice(plan.price, plan.series, seriesCount[plan.name] || plan.series)}
                  </span>
                  <span className="text-xs text-gray-600">/month</span>
                </div>
                {seriesCount[plan.name] > plan.series && (
                  <div className="text-[10px] text-emerald-600 mb-1">
                    +${(seriesCount[plan.name] - plan.series) * plan.price}/mo for {seriesCount[plan.name] - plan.series} extra series
                  </div>
                )}
                <div className="flex items-center justify-center space-x-1 text-emerald-600 font-medium">
                  <TrendingUp className="w-3 h-3" />
                  <span className="text-[11px]">Potential: {plan.income}/mo</span>
                </div>
              </div>

              {/* Features */}
              <ul className="space-y-2 mb-4">
                {plan.features.map((feature, fIndex) => (
                  <li key={fIndex} className="flex items-start space-x-2">
                    <div className="flex-shrink-0 w-4 h-4 bg-emerald-100 rounded-full flex items-center justify-center mt-0.5">
                      <Check className="w-2.5 h-2.5 text-emerald-600" />
                    </div>
                    {feature === '1 Series' && plan.canAddSeries ? (
                      <div className="flex items-center space-x-1.5">
                        <span className="text-xs text-gray-700 font-medium">
                          {seriesCount[plan.name] || plan.series} Series
                        </span>
                        <button
                          onClick={() => handleSeriesChange(plan.name, plan.series, -1)}
                          className="w-4 h-4 rounded-full bg-gray-100 hover:bg-gray-200 flex items-center justify-center transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                          disabled={seriesCount[plan.name] <= plan.series}
                        >
                          <Minus className="w-2.5 h-2.5 text-gray-600" />
                        </button>
                        <button
                          onClick={() => handleSeriesChange(plan.name, plan.series, 1)}
                          className="w-4 h-4 rounded-full bg-emerald-100 hover:bg-emerald-200 flex items-center justify-center transition-colors"
                        >
                          <Plus className="w-2.5 h-2.5 text-emerald-600" />
                        </button>
                      </div>
                    ) : (
                      <span className="text-xs text-gray-700">{feature}</span>
                    )}
                  </li>
                ))}
              </ul>

              {/* CTA Button */}
              <Link
                href="/login"
                className={`block w-full py-2 text-center text-sm font-semibold rounded-lg transition-all ${
                  plan.popular
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-md shadow-emerald-500/40 hover:shadow-lg hover:shadow-emerald-500/50'
                    : 'bg-gradient-to-br from-gray-50 to-gray-100 hover:from-emerald-50 hover:to-teal-50 text-gray-900 hover:text-emerald-700 border border-gray-200 hover:border-emerald-300'
                }`}
              >
                Get Started
              </Link>
            </div>
          ))}
        </div>

        {/* Guarantee */}
        <div className="mt-6 text-center">
          <div className="inline-flex items-center space-x-1.5 text-gray-600">
            <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span className="text-xs font-medium">7-day money-back guarantee • Cancel anytime</span>
          </div>
        </div>
      </div>
    </section>
  )
}
