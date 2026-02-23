import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import Script from 'next/script'
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
        {/* Meta Pixel */}
        <Script id="meta-pixel" strategy="afterInteractive">
          {`
            !function(f,b,e,v,n,t,s)
            {if(f.fbq)return;n=f.fbq=function(){n.callMethod?
            n.callMethod.apply(n,arguments):n.queue.push(arguments)};
            if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
            n.queue=[];t=b.createElement(e);t.async=!0;
            t.src=v;s=b.getElementsByTagName(e)[0];
            s.parentNode.insertBefore(t,s)}(window, document,'script',
            'https://connect.facebook.net/en_US/fbevents.js');
            fbq('init', '789505827533924');
            fbq('track', 'PageView');
          `}
        </Script>
        <noscript>
          <img height="1" width="1" style={{display:'none'}}
            src="https://www.facebook.com/tr?id=789505827533924&ev=PageView&noscript=1"
          />
        </noscript>
        <AuthProvider>
          <PlatformProvider>
            {children}
          </PlatformProvider>
        </AuthProvider>
      </body>
    </html>
  )
}
