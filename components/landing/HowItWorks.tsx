'use client'

import { Sparkles, Palette, Rocket } from 'lucide-react'

export default function HowItWorks() {
  const steps = [
    {
      number: '01',
      icon: Sparkles,
      title: 'Create Your Series',
      description: 'Choose your niche and content format.',
      features: ['20+ niches', 'Multiple formats', 'AI scripts'],
    },
    {
      number: '02',
      icon: Palette,
      title: 'Customize Style',
      description: 'Select visual styles, voices, and music.',
      features: ['10+ art styles', 'AI voices', 'Music library'],
    },
    {
      number: '03',
      icon: Rocket,
      title: 'Auto-Publish',
      description: 'Auto-post across all platforms.',
      features: ['Auto-posting', 'Multi-platform', 'Analytics'],
    },
  ]

  return (
    <section id="how-it-works" className="py-8 sm:py-10 bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-6">
          <h2 className="text-2xl sm:text-[1.7rem] font-bold mb-1">
            From Idea to Published{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              in 5 Minutes
            </span>
          </h2>
          <p className="text-[13px] text-gray-600 max-w-2xl mx-auto">
            Our streamlined process makes creating professional videos effortless
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-4">
          {steps.map((step, index) => {
            const Icon = step.icon
            return (
              <div
                key={index}
                className="relative bg-white rounded-xl px-4 py-3 border border-gray-100 hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-100/40 transition-all duration-300 group flex items-start gap-3 min-w-[280px] sm:min-w-[300px] max-w-[320px]"
              >
                {/* Step number */}
                <div className="absolute -top-2 -right-2 w-7 h-7 bg-gradient-to-br from-emerald-500 to-teal-500 rounded-lg flex items-center justify-center text-white text-xs font-bold shadow-md shadow-emerald-500/40">
                  {step.number}
                </div>

                {/* Icon */}
                <div className="w-10 h-10 bg-gradient-to-br from-emerald-100 to-teal-100 rounded-lg flex items-center justify-center flex-shrink-0 group-hover:scale-110 transition-transform">
                  <Icon className="w-5 h-5 text-emerald-600" />
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <h3 className="text-[15px] font-bold text-gray-900 mb-0.5">
                    {step.title}
                  </h3>
                  <p className="text-[11px] text-gray-600 mb-2 leading-tight">
                    {step.description}
                  </p>

                  {/* Features - inline */}
                  <div className="flex flex-wrap gap-1">
                    {step.features.map((feature, fIndex) => (
                      <span key={fIndex} className="inline-flex items-center gap-0.5 text-[10px] text-gray-600 bg-gray-50 px-1.5 py-0.5 rounded">
                        <svg className="w-2.5 h-2.5 text-emerald-500 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                          <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
                        </svg>
                        {feature}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            )
          })}
        </div>
      </div>
    </section>
  )
}
