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
