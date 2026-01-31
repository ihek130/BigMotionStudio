import Link from 'next/link'
import { Sparkles, Youtube, Instagram, Twitter } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-gray-50 border-t border-gray-100">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div className="col-span-1 md:col-span-2">
            <Link href="/" className="flex items-center space-x-2 mb-4">
              <img src="/Pictures/Pi7_cropper.png" alt="Big Motion Studio" className="w-10 h-10 rounded-2xl" />
              <span className="text-xl font-bold bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
                Big Motion Studio
              </span>
            </Link>
            <p className="text-gray-600 text-sm max-w-md mb-6">
              Create viral short-form videos automatically. Post to Instagram Reels, TikTok, and YouTube Shorts while you sleep.
            </p>
            <div className="flex items-center space-x-4">
              <a
                href="https://youtube.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center hover:border-emerald-500 hover:text-emerald-500 transition-colors"
              >
                <Youtube className="w-5 h-5" />
              </a>
              <a
                href="https://instagram.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center hover:border-emerald-500 hover:text-emerald-500 transition-colors"
              >
                <Instagram className="w-5 h-5" />
              </a>
              <a
                href="https://twitter.com"
                target="_blank"
                rel="noopener noreferrer"
                className="w-10 h-10 bg-white border border-gray-200 rounded-lg flex items-center justify-center hover:border-emerald-500 hover:text-emerald-500 transition-colors"
              >
                <Twitter className="w-5 h-5" />
              </a>
            </div>
          </div>

          {/* Product */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Product</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="#how-it-works" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  How it works
                </Link>
              </li>
              <li>
                <Link href="#pricing" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  Pricing
                </Link>
              </li>
              <li>
                <Link href="#faq" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  FAQ
                </Link>
              </li>
            </ul>
          </div>

          {/* Legal */}
          <div>
            <h3 className="font-semibold text-gray-900 mb-4">Legal</h3>
            <ul className="space-y-3 text-sm">
              <li>
                <Link href="/privacy" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  Privacy Policy
                </Link>
              </li>
              <li>
                <Link href="/terms" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  Terms of Service
                </Link>
              </li>
              <li>
                <Link href="/contact" className="text-gray-600 hover:text-emerald-600 transition-colors">
                  Contact
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-12 pt-8 border-t border-gray-200">
          <p className="text-center text-sm text-gray-600">
            © {new Date().getFullYear()} ShortsAI. All rights reserved. Made with ❤️ for creators.
          </p>
        </div>
      </div>
    </footer>
  )
}
