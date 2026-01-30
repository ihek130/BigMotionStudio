'use client'

import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useState, useTransition } from 'react'

interface TransitionLinkProps {
  href: string
  children: React.ReactNode
  className?: string
  onClick?: () => void
}

export default function TransitionLink({ href, children, className, onClick }: TransitionLinkProps) {
  const router = useRouter()
  const [isPending, startTransition] = useTransition()
  const [isNavigating, setIsNavigating] = useState(false)

  const handleClick = (e: React.MouseEvent<HTMLAnchorElement>) => {
    e.preventDefault()
    
    if (onClick) {
      onClick()
    }

    setIsNavigating(true)

    // Add a small delay for the transition effect
    setTimeout(() => {
      startTransition(() => {
        router.push(href)
        // Reset after navigation
        setTimeout(() => setIsNavigating(false), 300)
      })
    }, 150)
  }

  return (
    <Link
      href={href}
      className={`${className} ${isNavigating ? 'opacity-70 pointer-events-none' : ''}`}
      onClick={handleClick}
    >
      {children}
    </Link>
  )
}
