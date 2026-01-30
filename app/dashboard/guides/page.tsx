'use client'

import { useState } from 'react'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { BookOpen, Play, ChevronRight, Video, Palette, Volume2, Type, Settings, Upload, Zap } from 'lucide-react'

interface GuideSection {
  id: string
  title: string
  icon: React.ReactNode
  description: string
  steps: string[]
}

export default function GuidesPage() {
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const [activeSection, setActiveSection] = useState<string>('getting-started')

  const guides: GuideSection[] = [
    {
      id: 'getting-started',
      title: 'Getting Started',
      icon: <Play className="w-5 h-5" />,
      description: 'Learn the basics of creating your first automated video series.',
      steps: [
        'Sign up for a ReelFlow account and verify your email address.',
        'Navigate to the Dashboard and click "Create Series" or "New Series".',
        'Follow the 6-step wizard to configure your video series.',
        'Once configured, your series will automatically generate videos based on your schedule.',
        'Download your videos or connect social accounts for automatic posting.'
      ]
    },
    {
      id: 'create-series',
      title: 'Creating a Series',
      icon: <Video className="w-5 h-5" />,
      description: 'Step-by-step guide to creating your video series.',
      steps: [
        'Step 1 - Choose Niche: Select your content category (Scary Stories, Motivation, History, etc.)',
        'Step 2 - Select Style: Pick a visual style for your videos (Realistic, Cinematic, Anime, etc.)',
        'Step 3 - Voice & Music: Choose an AI voice narrator and background music.',
        'Step 4 - Captions: Select caption style, position, and animation effects.',
        'Step 5 - Details: Set video duration (30s, 60s, 90s, or 180s), series name, and posting schedule.',
        'Step 6 - Platforms: Connect your YouTube, TikTok, or Instagram accounts for auto-posting.'
      ]
    },
    {
      id: 'visual-styles',
      title: 'Visual Styles Explained',
      icon: <Palette className="w-5 h-5" />,
      description: 'Understanding the different visual styles available.',
      steps: [
        'Realistic: Photorealistic AI-generated images, best for documentary-style content.',
        'Cinematic: Movie-quality visuals with dramatic lighting and composition.',
        'Anime: Japanese animation style, great for storytelling and younger audiences.',
        'Comic Book: Bold colors and dynamic panels, perfect for action content.',
        'Watercolor: Soft, artistic visuals with a painted aesthetic.',
        '3D Render: Modern 3D graphics with clean, polished look.',
        'Vintage: Retro aesthetics with sepia tones and classic styling.',
        'Minimalist: Clean, simple visuals that focus on the narrative.'
      ]
    },
    {
      id: 'voices',
      title: 'AI Voices',
      icon: <Volume2 className="w-5 h-5" />,
      description: 'Choose the perfect voice for your content.',
      steps: [
        'Lewis: Deep & Commanding male voice - ideal for serious/dramatic content.',
        'Harry: Warm & Engaging male voice - great for storytelling.',
        'Eric: Professional & Clear male voice - perfect for educational content.',
        'Ethan: Friendly & Energetic male voice - suits upbeat content.',
        'Oliver: Smooth & Sophisticated male voice - ideal for luxury/lifestyle.',
        'Aria: Calm & Soothing female voice - great for meditation/wellness.',
        'Bella: Bright & Enthusiastic female voice - perfect for entertainment.',
        'Lily: Gentle & Warm female voice - suits emotional storytelling.',
        'Zoey: Energetic & Youthful female voice - ideal for Gen-Z content.',
        'Click "Preview" on any voice to hear a sample before selecting.'
      ]
    },
    {
      id: 'captions',
      title: 'Caption Styles',
      icon: <Type className="w-5 h-5" />,
      description: 'Customize how your captions appear.',
      steps: [
        'Modern Bold: Clean, bold text that pops - most popular choice.',
        'Neon Glow: Glowing effect for eye-catching captions.',
        'Minimal Clean: Subtle, professional captions.',
        'Typewriter: Character-by-character reveal animation.',
        'Karaoke: Words highlight as they are spoken.',
        'Position: Choose top, center, or bottom placement.',
        'Animation: Select bounce, fade, slide, or static effects.',
        'All captions are automatically synced to the AI voiceover.'
      ]
    },
    {
      id: 'connect-accounts',
      title: 'Connecting Social Accounts',
      icon: <Upload className="w-5 h-5" />,
      description: 'Set up automatic posting to your social platforms.',
      steps: [
        'Go to Settings in the sidebar navigation.',
        'Under "Connected Accounts", click "Connect new account".',
        'Select the platform (YouTube, TikTok, or Instagram).',
        'Authorize ReelFlow to post on your behalf.',
        'Once connected, you\'ll see the account with an "Active" badge.',
        'When creating a series, select which connected accounts to post to.',
        'Videos will be automatically uploaded based on your posting schedule.',
        'You can disconnect accounts anytime from the Settings page.'
      ]
    },
    {
      id: 'best-practices',
      title: 'Best Practices',
      icon: <Zap className="w-5 h-5" />,
      description: 'Tips for maximizing your video performance.',
      steps: [
        'Consistency is key: Set a regular posting schedule and stick to it.',
        'Choose the right niche: Pick a topic you\'re passionate about or has high demand.',
        'Optimize video length: 60-second videos typically perform best on most platforms.',
        'Use engaging voices: Match the voice tone to your content style.',
        'Caption placement: Center or bottom captions work best for vertical videos.',
        'Monitor analytics: Check your video performance and adjust accordingly.',
        'A/B test styles: Try different visual styles to see what your audience prefers.',
        'Engage with comments: Build community by responding to your viewers.'
      ]
    }
  ]

  const activeGuide = guides.find(g => g.id === activeSection) || guides[0]

  const breadcrumbItems = [
    { label: 'Guides' }
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

        {/* Page Content */}
        <div className="p-4 sm:p-6 lg:p-8">
          <div className="mb-4">
            <h1 className="text-xl sm:text-2xl font-bold text-gray-900">User Guides</h1>
            <p className="text-sm text-gray-600 mt-1">Everything you need to know about ReelFlow</p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
            {/* Sidebar Navigation */}
            <div className="lg:col-span-1">
              <div className="bg-white rounded-lg border border-gray-200 overflow-hidden sticky top-24">
                <div className="p-3 border-b border-gray-200">
                  <h2 className="text-sm font-semibold text-gray-900 flex items-center space-x-2">
                    <BookOpen className="w-4 h-4 text-emerald-600" />
                    <span>Topics</span>
                  </h2>
                </div>
                <nav className="p-1.5">
                  {guides.map((guide) => (
                    <button
                      key={guide.id}
                      onClick={() => setActiveSection(guide.id)}
                      className={`w-full flex items-center space-x-2 px-3 py-2 rounded-md text-left transition-colors ${
                        activeSection === guide.id
                          ? 'bg-emerald-50 text-emerald-700'
                          : 'text-gray-700 hover:bg-gray-50'
                      }`}
                    >
                      <span className={`${activeSection === guide.id ? 'text-emerald-600' : 'text-gray-400'}`}>
                        {guide.icon}
                      </span>
                      <span className="font-medium text-xs">{guide.title}</span>
                      {activeSection === guide.id && (
                        <ChevronRight className="w-3 h-3 ml-auto text-emerald-500" />
                      )}
                    </button>
                  ))}
                </nav>
              </div>
            </div>

            {/* Guide Content */}
            <div className="lg:col-span-3">
              <div className="bg-white rounded-lg border border-gray-200 p-4 sm:p-6">
                <div className="flex items-center space-x-3 mb-3">
                  <div className="w-10 h-10 bg-emerald-100 rounded-lg flex items-center justify-center text-emerald-600">
                    {activeGuide.icon}
                  </div>
                  <div>
                    <h2 className="text-base font-bold text-gray-900">{activeGuide.title}</h2>
                    <p className="text-gray-600 text-xs">{activeGuide.description}</p>
                  </div>
                </div>

                <div className="mt-4 space-y-3">
                  {activeGuide.steps.map((step, index) => (
                    <div key={index} className="flex items-start space-x-3">
                      <div className="w-6 h-6 bg-emerald-500 text-white rounded-full flex items-center justify-center flex-shrink-0 text-xs font-semibold">
                        {index + 1}
                      </div>
                      <div className="flex-1 pt-0.5">
                        <p className="text-sm text-gray-700">{step}</p>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Quick Links */}
                {activeSection === 'getting-started' && (
                  <div className="mt-6 p-4 bg-gradient-to-r from-emerald-50 to-teal-50 rounded-lg border border-emerald-100">
                    <h3 className="text-sm font-semibold text-emerald-900 mb-2">Quick Links</h3>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      <a href="/create" className="flex items-center space-x-1.5 text-xs text-emerald-700 hover:text-emerald-800">
                        <ChevronRight className="w-3 h-3" />
                        <span>Create your first series</span>
                      </a>
                      <a href="/dashboard/settings" className="flex items-center space-x-1.5 text-xs text-emerald-700 hover:text-emerald-800">
                        <ChevronRight className="w-3 h-3" />
                        <span>Connect social accounts</span>
                      </a>
                      <a href="/dashboard/billing" className="flex items-center space-x-1.5 text-xs text-emerald-700 hover:text-emerald-800">
                        <ChevronRight className="w-3 h-3" />
                        <span>View pricing plans</span>
                      </a>
                      <a href="/dashboard/videos" className="flex items-center space-x-1.5 text-xs text-emerald-700 hover:text-emerald-800">
                        <ChevronRight className="w-3 h-3" />
                        <span>View your videos</span>
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* Need Help Card */}
              <div className="mt-4 bg-gradient-to-r from-purple-500 to-indigo-500 rounded-lg p-4 text-white">
                <h3 className="font-bold text-sm mb-1">Need more help?</h3>
                <p className="text-purple-100 text-xs mb-3">
                  Can't find what you're looking for? Our support team is here to help.
                </p>
                <button className="px-4 py-1.5 bg-white text-purple-600 text-sm font-semibold rounded-md hover:bg-purple-50 transition-colors">
                  Contact Support
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
