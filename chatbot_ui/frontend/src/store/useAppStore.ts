import { create } from 'zustand'

import type { ChatMessage } from '@/lib/api'

type AppState = {
  entered: boolean
  activeCaseId: string | null
  messagesByCase: Record<string, ChatMessage[]>
  flashMessage: string | null

  enter: () => void
  setActiveCase: (caseId: string | null) => void
  setMessages: (caseId: string, messages: ChatMessage[]) => void
  appendMessage: (caseId: string, message: ChatMessage) => void
  setFlash: (message: string | null) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  entered: false,
  activeCaseId: null,
  messagesByCase: {},
  flashMessage: null,

  enter: () => set({ entered: true }),
  setActiveCase: (caseId) => set({ activeCaseId: caseId }),
  setMessages: (caseId, messages) =>
    set({ messagesByCase: { ...get().messagesByCase, [caseId]: messages } }),
  appendMessage: (caseId, message) => {
    const existing = get().messagesByCase[caseId] || []
    set({ messagesByCase: { ...get().messagesByCase, [caseId]: [...existing, message] } })
  },
  setFlash: (message) => set({ flashMessage: message }),
}))
