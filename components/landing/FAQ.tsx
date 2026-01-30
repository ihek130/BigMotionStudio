'use client'

import { useState } from 'react'
import { ChevronDown } from 'lucide-react'

export default function FAQ() {
  const [openIndex, setOpenIndex] = useState<number | null>(0)

  const faqs = [
    {
      question: 'What is a series?',
      answer: 'A series is a collection of related videos centered around a specific topic. For example, you could create a "Dark Mysteries" series where our AI automatically creates and posts new videos 3x per week or daily, depending on your plan.',
    },
    {
      question: 'How do I make money with this?',
      answer: 'You earn passive income through platform monetization (YouTube Partner Program, TikTok Creator Fund, Instagram bonuses), sponsored content, affiliate marketing, and selling products/services to your growing audience.',
    },
    {
      question: 'Do I own the videos?',
      answer: 'Yes! You own 100% of the videos created. Download them, use them on other platforms, or even sell them to clients. There are no restrictions on commercial use.',
    },
    {
      question: 'What platforms are supported?',
      answer: 'We support Instagram Reels, TikTok, and YouTube Shorts. Videos are automatically formatted and posted to all connected platforms based on your schedule.',
    },
    {
      question: 'Can I customize the videos?',
      answer: 'Absolutely! Choose from 10+ visual styles (Dark Comic, Anime, LEGO, etc.), select voice styles, add background music, customize caption styles, and set your niche and content format.',
    },
    {
      question: 'What if I don\'t get views?',
      answer: 'Our AI is trained on viral content patterns and optimizes for each platform\'s algorithm. We also provide best practices and analytics to help you understand what works. Most creators see growth within 30-60 days of consistent posting.',
    },
    {
      question: 'Do I need video editing skills?',
      answer: 'Not at all! Our AI handles everything from scriptwriting to video editing. Just choose your preferences, and we\'ll create professional videos ready to post.',
    },
  ]

  return (
    <section id="faq" className="py-8 sm:py-10 bg-gray-50">
      <div className="max-w-2xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-6">
          <h2 className="text-xl sm:text-2xl font-bold mb-1">
            Frequently Asked{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Questions
            </span>
          </h2>
          <p className="text-xs text-gray-600">
            Everything you need to know about creating viral shorts with AI
          </p>
        </div>

        <div className="space-y-2">
          {faqs.map((faq, index) => (
            <div
              key={index}
              className="bg-white rounded-lg border border-gray-100 overflow-hidden transition-all duration-300 hover:border-emerald-300 hover:shadow-sm hover:shadow-emerald-100/30"
            >
              <button
                onClick={() => setOpenIndex(openIndex === index ? null : index)}
                className="w-full px-4 py-3 flex items-center justify-between text-left"
              >
                <span className="text-sm font-semibold text-gray-900 pr-3">
                  {faq.question}
                </span>
                <ChevronDown
                  className={`w-4 h-4 text-emerald-600 flex-shrink-0 transition-transform duration-300 ${
                    openIndex === index ? 'transform rotate-180' : ''
                  }`}
                />
              </button>
              <div
                className={`overflow-hidden transition-all duration-300 ${
                  openIndex === index ? 'max-h-96' : 'max-h-0'
                }`}
              >
                <div className="px-4 pb-3 text-xs text-gray-600 leading-relaxed">
                  {faq.answer}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Contact support */}
        <div className="mt-6 text-center">
          <p className="text-xs text-gray-600 mb-2">Can't find the answer you're looking for?</p>
          <a
            href="mailto:support@shortsai.com"
            className="inline-flex items-center space-x-1.5 text-emerald-600 hover:text-emerald-700 text-sm font-medium transition-colors"
          >
            <span>Contact our support team</span>
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
            </svg>
          </a>
        </div>
      </div>
    </section>
  )
}
