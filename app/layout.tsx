import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { AuthProvider } from '@/context/AuthContext'
import { PlatformProvider } from '@/context/PlatformContext'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Big Motion Studio - Create Viral Videos on Autopilot',
  description: 'Generate and post viral short-form videos to Instagram Reels, TikTok, and YouTube Shorts automatically with AI',
  icons: {
    icon: '/Pictures/Pi7_cropper.png',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="scroll-smooth">
      <head>
        {/* Preload critical assets for faster LCP */}
        <link rel="preload" href="/Pictures/Pi7_cropper.png" as="image" />
        <link rel="preload" href="/landing-samples/posters/scary-stories.jpg" as="image" />
        <link rel="preload" href="/landing-samples/posters/true-crime.jpg" as="image" />
        <link rel="preload" href="/landing-samples/posters/history.jpg" as="image" />
        <link rel="preload" href="/landing-samples/posters/psychology.jpg" as="image" />
      </head>
      <body className={inter.className}>
        <AuthProvider>
          <PlatformProvider>
            {children}
          </PlatformProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
