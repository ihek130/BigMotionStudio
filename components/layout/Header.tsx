'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import Image from 'next/image'
import { Menu, X, Sparkles } from 'lucide-react'
import { cn } from '@/lib/utils'

export default function Header() {
  const [isScrolled, setIsScrolled] = useState(false)
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false)

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 10)
    }
    window.addEventListener('scroll', handleScroll)
    return () => window.removeEventListener('scroll', handleScroll)
  }, [])

  return (
    <header
      className={cn(
        'fixed top-0 left-0 right-0 z-50 transition-all duration-300',
        isScrolled
          ? 'bg-white/80 backdrop-blur-md shadow-sm'
          : 'bg-transparent'
      )}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16 sm:h-20">
          {/* Logo */}
          <Link href="/" className="flex items-center space-x-2 group">
            <Image 
              src="/Pictures/Pi7_cropper.png" 
              alt="Big Motion Studio" 
              width={40} 
              height={40} 
              className="w-8 h-8 sm:w-10 sm:h-10 rounded-2xl transform group-hover:scale-110 transition-transform"
              priority
            />
            <span className="text-lg sm:text-xl font-bold bg-gradient-to-r from-emerald-600 via-teal-600 to-green-600 bg-clip-text text-transparent">
              Big Motion Studio
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center space-x-8">
            <Link
              href="#how-it-works"
              className="text-gray-700 hover:text-emerald-600 transition-colors text-sm font-medium"
            >
              How it works
            </Link>
            <Link
              href="#pricing"
              className="text-gray-700 hover:text-emerald-600 transition-colors text-sm font-medium"
            >
              Pricing
            </Link>
            <Link
              href="#faq"
              className="text-gray-700 hover:text-emerald-600 transition-colors text-sm font-medium"
            >
              FAQ
            </Link>
          </nav>

          {/* CTA Buttons */}
          <div className="hidden md:flex items-center space-x-4">
            <Link
              href="/login"
              className="text-gray-700 hover:text-emerald-600 transition-colors text-sm font-medium"
            >
              Log in
            </Link>
            <Link
              href="/login"
              className="px-5 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-sm font-medium rounded-xl transition-all hover:shadow-xl hover:shadow-emerald-500/30 transform hover:-translate-y-0.5"
            >
              Start Creating
            </Link>
          </div>

          {/* Mobile Menu Button */}
          <button
            onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
            className="md:hidden p-2 rounded-lg hover:bg-gray-100 transition-colors"
          >
            {isMobileMenuOpen ? (
              <X className="w-6 h-6 text-gray-700" />
            ) : (
              <Menu className="w-6 h-6 text-gray-700" />
            )}
          </button>
        </div>
      </div>

      {/* Mobile Menu */}
      {isMobileMenuOpen && (
        <div className="md:hidden bg-white border-t border-gray-100 shadow-lg">
          <div className="px-4 py-6 space-y-4">
            <Link
              href="#how-it-works"
              className="block text-gray-700 hover:text-emerald-600 transition-colors font-medium"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              How it works
            </Link>
            <Link
              href="#pricing"
              className="block text-gray-700 hover:text-emerald-600 transition-colors font-medium"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              Pricing
            </Link>
            <Link
              href="#faq"
              className="block text-gray-700 hover:text-emerald-600 transition-colors font-medium"
              onClick={() => setIsMobileMenuOpen(false)}
            >
              FAQ
            </Link>
            <div className="pt-4 space-y-3 border-t border-gray-100">
              <Link
                href="/login"
                className="block w-full px-4 py-2.5 text-center text-gray-700 hover:bg-gray-50 rounded-lg transition-colors font-medium"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Log in
              </Link>
              <Link
                href="/login"
                className="block w-full px-4 py-2.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white text-center rounded-xl transition-all font-medium shadow-lg"
                onClick={() => setIsMobileMenuOpen(false)}
              >
                Start Creating
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  )
}
