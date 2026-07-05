import { create } from 'zustand'

import type { ChatMessage } from '@/lib/api'

type AppState = {
  entered: boolean
  activeCaseId: string | null
  // When set to a case id, that case should auto-cascade through the pipeline
  // (Analysis runs automatically, then Reports generates automatically). Cleared
  // once the report has been generated, so revisiting an old case never re-runs.
  autoRunCaseId: string | null
  messagesByCase: Record<string, ChatMessage[]>
  flashMessage: string | null

  enter: () => void
  setActiveCase: (caseId: string | null) => void
  setAutoRun: (caseId: string | null) => void
  setMessages: (caseId: string, messages: ChatMessage[]) => void
  appendMessage: (caseId: string, message: ChatMessage) => void
  setFlash: (message: string | null) => void
}

export const useAppStore = create<AppState>((set, get) => ({
  entered: false,
  activeCaseId: null,
  autoRunCaseId: null,
  messagesByCase: {},
  flashMessage: null,

  enter: () => set({ entered: true }),
  setActiveCase: (caseId) => set({ activeCaseId: caseId }),
  setAutoRun: (caseId) => set({ autoRunCaseId: caseId }),
  setMessages: (caseId, messages) =>
    set({ messagesByCase: { ...get().messagesByCase, [caseId]: messages } }),
  appendMessage: (caseId, message) => {
    const existing = get().messagesByCase[caseId] || []
    set({ messagesByCase: { ...get().messagesByCase, [caseId]: [...existing, message] } })
  },
  setFlash: (message) => set({ flashMessage: message }),
}))
