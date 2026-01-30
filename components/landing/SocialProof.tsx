'use client'

export default function SocialProof() {
  return (
    <section className="py-8 sm:py-10 bg-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-6">
          <h2 className="text-xl sm:text-2xl font-bold mb-1">
            Real Creators,{' '}
            <span className="bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Real Results
            </span>
          </h2>
          <p className="text-xs text-gray-600">
            See what our users are achieving with AI-generated shorts
          </p>
        </div>

        <div className="flex flex-wrap justify-center gap-4">
          {[
            {
              platform: 'TikTok',
              username: '@mysterystories',
              views: '2.3M',
              income: '$850/mo',
              growth: '+120K',
            },
            {
              platform: 'Instagram',
              username: '@historyfacts',
              views: '1.8M',
              income: '$1,200/mo',
              growth: '+95K',
            },
            {
              platform: 'YouTube',
              username: '@crimestories',
              views: '4.1M',
              income: '$2,300/mo',
              growth: '+180K',
            },
          ].map((creator, index) => (
            <div
              key={index}
              className="group relative bg-gradient-to-br from-emerald-50/30 to-white px-4 py-3 rounded-xl border border-gray-100 hover:border-emerald-300 hover:shadow-lg hover:shadow-emerald-100/50 transition-all duration-300 flex items-center gap-4 min-w-[280px] sm:min-w-[300px]"
            >
              {/* Platform badge */}
              <div className="flex flex-col items-center">
                <div className="inline-flex items-center space-x-1.5 px-2 py-1 bg-gradient-to-r from-emerald-100 to-teal-100 text-emerald-700 rounded-full text-xs font-medium shadow-sm mb-1">
                  <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                  <span>{creator.platform}</span>
                </div>
                <div className="text-[10px] text-gray-400">{creator.username}</div>
              </div>

              {/* Stats - horizontal */}
              <div className="flex items-center gap-4 flex-1">
                <div className="text-center">
                  <div className="text-lg font-bold text-gray-900">{creator.views}</div>
                  <div className="text-[10px] text-gray-500">Views/mo</div>
                </div>
                <div className="text-center">
                  <div className="text-lg font-bold bg-gradient-to-r from-green-600 to-emerald-600 bg-clip-text text-transparent">
                    {creator.income}
                  </div>
                  <div className="text-[10px] text-gray-500">Revenue</div>
                </div>
                <div className="text-center">
                  <div className="text-sm font-semibold text-gray-700">{creator.growth}</div>
                  <div className="text-[10px] text-gray-500">in 90d</div>
                </div>
              </div>

              {/* Verified badge */}
              <div className="flex-shrink-0">
                <svg className="w-4 h-4 text-emerald-500" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                </svg>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
