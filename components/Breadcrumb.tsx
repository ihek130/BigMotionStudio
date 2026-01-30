'use client'

import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'

interface BreadcrumbItem {
  label: string
  href?: string
}

interface BreadcrumbProps {
  items: BreadcrumbItem[]
}

export default function Breadcrumb({ items }: BreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-1 text-sm overflow-x-auto py-2" aria-label="Breadcrumb">
      <Link 
        href="/dashboard" 
        className="flex items-center text-gray-500 hover:text-emerald-600 transition-colors whitespace-nowrap"
      >
        <Home className="w-4 h-4" />
      </Link>
      
      {items.map((item, index) => (
        <div key={index} className="flex items-center space-x-1">
          <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
          {item.href ? (
            <Link 
              href={item.href}
              className="text-gray-500 hover:text-emerald-600 transition-colors whitespace-nowrap"
            >
              {item.label}
            </Link>
          ) : (
            <span className="text-gray-900 font-medium whitespace-nowrap">{item.label}</span>
          )}
        </div>
      ))}
    </nav>
  )
}
