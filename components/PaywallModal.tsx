'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '@/context/AuthContext';

interface PaywallModalProps {
  isOpen: boolean;
  onClose: () => void;
  title?: string;
  message?: string;
}

const PLANS = [
  {
    id: 'launch',
    name: 'Launch',
    price: 19,
    videos: 12,
    series: 1,
    features: [
      '12 videos per month',
      '1 video series',
      'All caption styles',
      'Custom AI voiceover',
      'YouTube, TikTok, Instagram',
    ]
  },
  {
    id: 'grow',
    name: 'Grow',
    price: 39,
    videos: 30,
    series: '1+',
    popular: true,
    features: [
      '30 videos per month',
      'Add extra series',
      'All caption styles',
      'Custom AI voiceover',
      'YouTube, TikTok, Instagram',
    ]
  },
  {
    id: 'scale',
    name: 'Scale',
    price: 69,
    videos: 60,
    series: '1+',
    features: [
      '60 videos per month',
      'Add extra series',
      'All caption styles',
      'Custom AI voiceover',
      'YouTube, TikTok, Instagram',
    ]
  }
];

export default function PaywallModal({ isOpen, onClose, title, message }: PaywallModalProps) {
  const { user } = useAuth();
  const router = useRouter();

  if (!isOpen) return null;

  const handleSelectPlan = () => {
    onClose();
    router.push('/dashboard/billing');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop — non-dismissible */}
      <div 
        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
      />
      
      {/* Modal */}
      <div className="relative bg-white rounded-2xl shadow-2xl max-w-4xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="text-center pt-10 pb-6 px-8 bg-gradient-to-br from-emerald-50 to-teal-50 rounded-t-2xl">
          <div className="w-16 h-16 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-2xl flex items-center justify-center mx-auto mb-4 shadow-lg shadow-emerald-500/30">
            <svg className="w-8 h-8 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
          </div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">
            {title || 'Upgrade to Continue'}
          </h2>
          <p className="text-gray-600 max-w-md mx-auto">
            {message || "You need a paid plan to create series and generate videos. Choose a plan to get started!"}
          </p>
        </div>

        {/* Plans */}
        <div className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {PLANS.map((plan) => (
              <div
                key={plan.id}
                className={`relative rounded-2xl border-2 p-6 transition-all ${
                  plan.popular
                    ? 'border-emerald-500 shadow-xl shadow-emerald-500/10 scale-105'
                    : 'border-gray-200 hover:border-gray-300'
                }`}
              >
                {plan.popular && (
                  <div className="absolute -top-3 left-1/2 -translate-x-1/2 bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-xs font-bold px-3 py-1 rounded-full">
                    MOST POPULAR
                  </div>
                )}

                <div className="text-center mb-6">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{plan.name}</h3>
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-gray-900">${plan.price}</span>
                    <span className="text-gray-500 ml-1">/mo</span>
                  </div>
                  <p className="text-sm text-gray-500 mt-2">
                    {plan.videos} videos/month
                  </p>
                </div>

                <ul className="space-y-3 mb-6">
                  {plan.features.map((feature, i) => (
                    <li key={i} className="flex items-center text-sm text-gray-600">
                      <svg className="w-4 h-4 text-emerald-500 mr-2 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      {feature}
                    </li>
                  ))}
                </ul>

                <button
                  className={`w-full py-3 rounded-xl font-semibold transition-all ${
                    plan.popular
                      ? 'bg-gradient-to-r from-emerald-500 to-teal-500 text-white shadow-lg shadow-emerald-500/30 hover:shadow-xl'
                      : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                  }`}
                  onClick={handleSelectPlan}
                >
                  Get {plan.name}
                </button>
              </div>
            ))}
          </div>

          {/* Current Plan Info */}
          {user && user.plan !== 'free' && (
            <div className="mt-8 p-4 bg-gray-50 rounded-xl text-center">
              <p className="text-sm text-gray-600">
                You&apos;ve used <strong>{user.videos_generated_this_month}</strong> of <strong>{user.plan_limits?.videos_per_month}</strong> videos this month.
                Upgrade now to keep creating!
              </p>
            </div>
          )}

          {/* Trust signals */}
          <div className="mt-8 pt-6 border-t border-gray-100">
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <p className="text-xs text-gray-600">Cancel anytime</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                  </svg>
                </div>
                <p className="text-xs text-gray-600">Secure payment</p>
              </div>
              <div>
                <div className="w-10 h-10 bg-emerald-100 rounded-xl flex items-center justify-center mx-auto mb-2">
                  <svg className="w-5 h-5 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 5.636l-3.536 3.536m0 5.656l3.536 3.536M9.172 9.172L5.636 5.636m3.536 9.192l-3.536 3.536M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-5 0a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                </div>
                <p className="text-xs text-gray-600">24/7 support</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
