'use client'

export default function VideoShowcase() {
  const niches = [
    { emoji: '🔥', name: 'Horror', color: 'from-red-500 to-orange-600', views: '2.3M' },
    { emoji: '🕵️', name: 'Crime', color: 'from-gray-700 to-gray-900', views: '1.8M' },
    { emoji: '👽', name: 'Conspiracy', color: 'from-green-500 to-emerald-600', views: '1.5M' },
    { emoji: '📚', name: 'History', color: 'from-blue-500 to-indigo-600', views: '3.2M' },
    { emoji: '💰', name: 'Crypto', color: 'from-yellow-500 to-amber-600', views: '890K' },
    { emoji: '🎮', name: 'Gaming', color: 'from-purple-500 to-pink-600', views: '2.7M' },
    { emoji: '🧠', name: 'Psychology', color: 'from-teal-500 to-cyan-600', views: '1.2M' },
    { emoji: '🌌', name: 'Space', color: 'from-indigo-600 to-purple-700', views: '4.1M' },
  ]

  return (
    <section className="py-16 sm:py-24 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-12 sm:mb-16">
          <h2 className="text-3xl sm:text-4xl lg:text-5xl font-bold mb-4">
            Creates Videos for{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Any Niche
            </span>
          </h2>
          <p className="text-lg text-gray-600 max-w-2xl mx-auto">
            From horror to history, gaming to crypto—our AI creates engaging content for every topic
          </p>
        </div>

        {/* Video Grid - Placeholder for actual videos */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 sm:gap-6 mb-12">
          {niches.map((niche, index) => (
            <div
              key={index}
              className="group relative aspect-[9/16] rounded-2xl overflow-hidden bg-gradient-to-br from-gray-100 to-gray-200 hover:shadow-2xl transition-all duration-300 cursor-pointer"
            >
              {/* Gradient overlay */}
              <div className={`absolute inset-0 bg-gradient-to-br ${niche.color} opacity-80 group-hover:opacity-90 transition-opacity`} />
              
              {/* Content */}
              <div className="relative h-full flex flex-col items-center justify-center p-6 text-white">
                <div className="text-4xl sm:text-5xl mb-3">{niche.emoji}</div>
                <h3 className="text-lg sm:text-xl font-bold mb-2">{niche.name}</h3>
                <div className="flex items-center space-x-1 text-xs sm:text-sm opacity-90">
                  <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/>
                    <path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/>
                  </svg>
                  <span>{niche.views} views</span>
                </div>
              </div>

              {/* Play button overlay */}
              <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                <div className="w-16 h-16 bg-white/20 backdrop-blur-sm rounded-full flex items-center justify-center border-2 border-white/50">
                  <svg className="w-8 h-8 text-white ml-1" fill="currentColor" viewBox="0 0 20 20">
                    <path d="M6.3 2.841A1.5 1.5 0 004 4.11V15.89a1.5 1.5 0 002.3 1.269l9.344-5.89a1.5 1.5 0 000-2.538L6.3 2.84z"/>
                  </svg>
                </div>
              </div>

              {/* "Coming soon" badge for demo */}
              <div className="absolute top-3 right-3 px-3 py-1 bg-white/20 backdrop-blur-sm rounded-full text-xs font-medium border border-white/30">
                Sample
              </div>
            </div>
          ))}
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6 sm:gap-8">
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">1.2M+</div>
            <div className="text-sm sm:text-base text-gray-600">Videos Created</div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">307K+</div>
            <div className="text-sm sm:text-base text-gray-600">Active Creators</div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">15M+</div>
            <div className="text-sm sm:text-base text-gray-600">Total Views</div>
          </div>
          <div className="text-center">
            <div className="text-3xl sm:text-4xl font-bold text-gray-900 mb-2">$2.3K</div>
            <div className="text-sm sm:text-base text-gray-600">Avg. Monthly Income</div>
          </div>
        </div>
      </div>
    </section>
  )
}
