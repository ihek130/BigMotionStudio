'use client'

import { ArrowRight, Sparkles } from 'lucide-react'
import Link from 'next/link'

export default function CTA() {
  return (
    <section className="py-8 sm:py-10 bg-gradient-to-br from-emerald-600 via-teal-600 to-green-600 relative overflow-hidden">
      {/* Background pattern */}
      <div className="absolute inset-0 opacity-10">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxwYXRoIGQ9Ik0zNiAxOGMzLjMxNCAwIDYgMi42ODYgNiA2cy0yLjY4NiA2LTYgNi02LTIuNjg2LTYtNiAyLjY4Ni02IDYtNnoiIHN0cm9rZT0iI2ZmZiIgc3Ryb2tlLXdpZHRoPSIyIi8+PC9nPjwvc3ZnPg==')] " />
      </div>

      {/* Decorative floral gradients */}
      <div className="absolute top-0 right-0 w-64 h-64 bg-teal-400/30 rounded-full blur-3xl" />
      <div className="absolute bottom-0 left-0 w-64 h-64 bg-emerald-400/30 rounded-full blur-3xl" />

      <div className="relative max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
        {/* Icon */}
        <div className="inline-flex items-center justify-center w-10 h-10 bg-white/20 backdrop-blur-sm rounded-xl mb-4 shadow-md">
          <svg className="w-5 h-5 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <rect x="2" y="2" width="20" height="20" rx="2" ry="2" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <circle cx="8" cy="8" r="2" fill="currentColor"/>
            <circle cx="16" cy="8" r="2" fill="currentColor"/>
            <circle cx="8" cy="16" r="2" fill="currentColor"/>
            <circle cx="16" cy="16" r="2" fill="currentColor"/>
          </svg>
        </div>

        {/* Heading */}
        <h2 className="text-xl sm:text-2xl font-bold text-white mb-3">
          Start Creating Viral Videos{' '}
          <span className="text-white/90">in 5 Minutes</span>
        </h2>

        {/* Description */}
        <p className="text-xs text-white/90 mb-5 max-w-xl mx-auto">
          Join 307,000+ creators earning passive income with AI-generated shorts
        </p>

        {/* CTA Buttons */}
        <div className="flex flex-col sm:flex-row items-center justify-center space-y-2 sm:space-y-0 sm:space-x-3 mb-5">
          <Link
            href="/login"
            className="w-full sm:w-auto group px-5 py-2.5 bg-white hover:bg-gray-50 text-emerald-600 text-sm font-semibold rounded-xl transition-all hover:shadow-xl shadow-md transform hover:-translate-y-0.5 flex items-center justify-center space-x-1.5"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span>Start Creating Free</span>
            <ArrowRight className="w-4 h-4 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            href="#pricing"
            className="w-full sm:w-auto px-5 py-2.5 bg-white/10 hover:bg-white/20 backdrop-blur-sm text-white text-sm font-semibold rounded-xl border border-white/30 hover:border-white/50 transition-all flex items-center justify-center"
          >
            <span>View Pricing</span>
          </Link>
        </div>

        {/* Trust indicators */}
        <div className="flex flex-wrap items-center justify-center gap-4 text-white/80 text-[11px]">
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>No credit card required</span>
          </div>
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>7-day money-back guarantee</span>
          </div>
          <div className="flex items-center space-x-1">
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            <span>Cancel anytime</span>
          </div>
        </div>
      </div>
    </section>
  )
}
