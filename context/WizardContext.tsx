'use client'

import { createContext, useContext, useState, ReactNode } from 'react'

export interface WizardData {
  // Step 1: Niche
  niche?: string
  nicheFormat?: string  // 'storytelling' or '5-things'
  
  // Step 2: Visual Style
  style?: string
  
  // Step 3: Voice & Music
  voiceId?: string
  musicId?: string
  
  // Step 4: Captions
  captionStyle?: string
  
  // Step 5: Series Details
  seriesName?: string
  description?: string
  videoDuration?: number  // 30, 45, 60 seconds
  postingTimes?: string[] // Array of posting times based on plan
  
  // Step 6: Platforms
  platforms?: string[]
}

interface WizardContextType {
  data: WizardData
  updateData: (updates: Partial<WizardData>) => void
  currentStep: number
  setCurrentStep: (step: number) => void
}

const WizardContext = createContext<WizardContextType | undefined>(undefined)

export function WizardProvider({ children }: { children: ReactNode }) {
  const [data, setData] = useState<WizardData>({})
  const [currentStep, setCurrentStep] = useState(1)

  const updateData = (updates: Partial<WizardData>) => {
    setData(prev => ({ ...prev, ...updates }))
  }

  return (
    <WizardContext.Provider value={{ data, updateData, currentStep, setCurrentStep }}>
      {children}
    </WizardContext.Provider>
  )
}

export function useWizard() {
  const context = useContext(WizardContext)
  if (context === undefined) {
    throw new Error('useWizard must be used within a WizardProvider')
  }
  return context
}
