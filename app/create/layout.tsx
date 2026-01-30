'use client'

import { WizardProvider } from '@/context/WizardContext'
import { usePathname, useRouter } from 'next/navigation'
import { Check } from 'lucide-react'
import Sidebar from '@/components/Sidebar'
import Breadcrumb from '@/components/Breadcrumb'
import MobileMenuButton from '@/components/MobileMenuButton'
import { useState, useEffect } from 'react'
import { useAuth } from '@/context/AuthContext'

const steps = [
  { id: 1, name: 'Niche', path: '/create' },
  { id: 2, name: 'Style', path: '/create/style' },
  { id: 3, name: 'Voice & Music', path: '/create/voice' },
  { id: 4, name: 'Captions', path: '/create/captions' },
  { id: 5, name: 'Details', path: '/create/details' },
  { id: 6, name: 'Platforms', path: '/create/platforms' },
]

export default function CreateLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false)
  const { isAuthenticated, isLoading } = useAuth()

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace('/login')
    }
  }, [isAuthenticated, isLoading, router])

  // Show nothing while checking auth or redirecting
  if (isLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-emerald-500"></div>
      </div>
    )
  }
  
  const getCurrentStep = () => {
    const step = steps.find(s => s.path === pathname)
    return step ? step.id : 1
  }

  const currentStep = getCurrentStep()
  const currentStepData = steps.find(s => s.id === currentStep)

  const breadcrumbItems = [
    { label: 'New Series', href: '/create' },
    ...(currentStepData ? [{ label: currentStepData.name }] : [])
  ]

  return (
    <WizardProvider>
      <div className="min-h-screen bg-gray-50 flex">
        {/* Sidebar */}
        <Sidebar mobileOpen={sidebarOpen} onClose={() => setSidebarOpen(false)} />

        {/* Main Content */}
        <div className="flex-1 lg:ml-64">
          {/* Header with Breadcrumb */}
          <div className="bg-white border-b border-gray-200 shadow-sm sticky top-0 z-30">
            <div className="px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <MobileMenuButton onClick={() => setSidebarOpen(true)} />
                  <Breadcrumb items={breadcrumbItems} />
                </div>
                <div className="text-sm text-gray-500">
                  Step {currentStep} of {steps.length}
                </div>
              </div>
            </div>
          </div>

          {/* Progress Steps */}
          <div className="bg-white border-b border-gray-200">
            <div className="px-4 sm:px-6 lg:px-8 py-3 overflow-x-auto">
              <nav aria-label="Progress">
                <ol className="flex items-center justify-between min-w-max">
                  {steps.map((step, stepIdx) => (
                    <li key={step.name} className={`relative ${stepIdx !== steps.length - 1 ? 'pr-4 sm:pr-16 flex-1' : ''}`}>
                      {step.id < currentStep ? (
                        <>
                          {stepIdx !== steps.length - 1 && (
                            <div className="absolute inset-0 flex items-center" aria-hidden="true">
                              <div className="h-0.5 w-full bg-emerald-500" />
                            </div>
                          )}
                          <div className="relative flex flex-col items-center">
                            <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full bg-emerald-500 flex items-center justify-center shadow-md shadow-emerald-500/30">
                              <Check className="w-3.5 h-3.5 sm:w-4 sm:h-4 text-white" />
                            </div>
                            <span className="mt-1 text-[10px] font-medium text-emerald-600 text-center">
                              {step.name}
                            </span>
                          </div>
                        </>
                      ) : step.id === currentStep ? (
                        <>
                          {stepIdx !== steps.length - 1 && (
                            <div className="absolute inset-0 flex items-center" aria-hidden="true">
                              <div className="h-0.5 w-full bg-gray-200" />
                            </div>
                          )}
                          <div className="relative flex flex-col items-center">
                            <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full border-2 border-emerald-500 bg-white flex items-center justify-center shadow-md">
                              <span className="text-emerald-600 font-semibold text-xs sm:text-sm">{step.id}</span>
                            </div>
                            <span className="mt-1 text-[10px] font-semibold text-emerald-600 text-center">
                              {step.name}
                            </span>
                          </div>
                        </>
                      ) : (
                        <>
                          {stepIdx !== steps.length - 1 && (
                            <div className="absolute inset-0 flex items-center" aria-hidden="true">
                              <div className="h-0.5 w-full bg-gray-200" />
                            </div>
                          )}
                          <div className="relative flex flex-col items-center">
                            <div className="h-7 w-7 sm:h-8 sm:w-8 rounded-full border-2 border-gray-300 bg-white flex items-center justify-center">
                              <span className="text-gray-500 font-medium text-xs sm:text-sm">{step.id}</span>
                            </div>
                            <span className="mt-1 text-[10px] font-medium text-gray-500 text-center">
                              {step.name}
                            </span>
                          </div>
                        </>
                      )}
                    </li>
                  ))}
                </ol>
              </nav>
            </div>
          </div>

          {/* Page Content */}
          <div className="bg-gradient-to-br from-emerald-50 via-teal-50 to-green-50 min-h-[calc(100vh-10rem)]">
            <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              {children}
            </main>
          </div>
        </div>
      </div>
    </WizardProvider>
  )
}
