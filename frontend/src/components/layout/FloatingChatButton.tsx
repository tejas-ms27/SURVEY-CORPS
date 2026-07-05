import { useEffect, useRef, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { Loader2, Maximize2, Minimize2, MoreHorizontal, Send, X } from 'lucide-react'

import logoUrl from '@/assets/logo.png'
import { ChatBubble } from '@/components/chat/ChatBubble'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

/**
 * Floating chat widget — bottom-right on every app screen.
 *
 * Clicking the trigger opens a chat panel *docked to the right edge* of the
 * screen (not a centered modal). The panel has two states:
 *   - collapsed: a narrow docked column, with an expand (diagonal-arrows)
 *     control top-left;
 *   - expanded: grows to ~72% of the viewport width, with a "Collapse"
 *     control top-left.
 * A "…" menu and an "X" close sit top-right in both states.
 *
 * The content itself is kept intentionally minimal (no suggested-question
 * chips / consent banner / third-party branding) — it's wired to the real
 * chat backend and shares message state with the full /chatbot page.
 */
export function FloatingChatButton() {
  const navigate = useNavigate()
  const location = useLocation()

  const activeCaseId = useAppStore((s) => s.activeCaseId)
  const messagesByCase = useAppStore((s) => s.messagesByCase)
  const setMessages = useAppStore((s) => s.setMessages)
  const appendMessage = useAppStore((s) => s.appendMessage)

  const [open, setOpen] = useState(false)
  const [expanded, setExpanded] = useState(false)
  const [menuOpen, setMenuOpen] = useState(false)
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const messages = activeCaseId ? messagesByCase[activeCaseId] || [] : []

  // Lazily pull history the first time the panel is opened for a case.
  useEffect(() => {
    if (!open || !activeCaseId || messagesByCase[activeCaseId]) return
    api.chatHistory(activeCaseId).then((r) => setMessages(activeCaseId, r.messages))
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [open, activeCaseId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages, open, asking])

  async function ask() {
    if (!activeCaseId || !question.trim() || asking) return
    const q = question.trim()
    setQuestion('')
    appendMessage(activeCaseId, { role: 'user', content: q, ts: Date.now() })
    setAsking(true)
    try {
      const res = await api.askQuestion(activeCaseId, q)
      appendMessage(activeCaseId, {
        role: 'assistant',
        content: res.answer,
        ts: Date.now(),
        meta: `language: ${res.detected_language} · route: ${res.matched_pattern}`,
        citations: res.citations,
        structuring_alerts: res.structuring_alerts,
        graph_html: res.graph_html,
        disclaimer: res.disclaimer,
        chart: res.chart,
      })
    } catch (err) {
      appendMessage(activeCaseId, {
        role: 'assistant',
        content: `Chatbot error: ${err instanceof Error ? err.message : 'unknown error'}`,
        ts: Date.now(),
      })
    } finally {
      setAsking(false)
    }
  }

  // The full /chatbot page keeps its own richer view; hide the widget there.
  if (location.pathname === '/chatbot') return null

  const widthPx = expanded
    ? Math.round(window.innerWidth * 0.72)
    : Math.min(384, Math.round(window.innerWidth * 0.92))

  return (
    <>
      <AnimatePresence>
        {!open && (
          <motion.button
            key="trigger"
            type="button"
            aria-label="Open chatbot"
            onClick={() => setOpen(true)}
            className="fixed bottom-6 right-6 z-50 flex items-center gap-2 rounded-full border border-white/15 bg-navy-2 py-2.5 pl-2.5 pr-4 text-ink shadow-[0_10px_30px_rgba(0,0,0,0.55)]"
            initial={{ opacity: 0, scale: 0.8, y: 12 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.8, y: 12 }}
            transition={{ duration: 0.3, ease: [0.16, 1, 0.3, 1] }}
            whileHover={{ scale: 1.06 }}
            whileTap={{ scale: 0.95 }}
          >
            <img src={logoUrl} alt="" className="size-8 flex-none rounded-full object-cover ring-1 ring-white/15" />
            <span className="text-sm font-semibold tracking-wide">Ask the case</span>
          </motion.button>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {open && (
          <>
            {/* Transparent click-away catcher — no dimming, keeps the docked feel. */}
            <motion.div
              key="catcher"
              className="fixed inset-0 z-40"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => {
                setMenuOpen(false)
                setOpen(false)
              }}
            />

            <motion.aside
              key="panel"
              className="fixed inset-y-0 right-0 z-50 flex h-screen max-w-[92vw] flex-col border-l border-line bg-card shadow-[-16px_0_48px_rgba(15,23,42,0.22)]"
              initial={{ x: '100%' }}
              animate={{ x: 0, width: widthPx }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', stiffness: 320, damping: 34 }}
            >
              {/* Header — expand/collapse top-left, "…" + close top-right */}
              <div className="flex flex-none items-center gap-2 border-b border-line px-3 py-2.5">
                <button
                  type="button"
                  onClick={() => setExpanded((v) => !v)}
                  className="flex items-center gap-1.5 rounded-md px-2 py-1.5 text-xs font-medium text-muted-foreground transition-colors hover:bg-line-soft hover:text-ink"
                  aria-label={expanded ? 'Collapse panel' : 'Expand panel'}
                >
                  {expanded ? (
                    <>
                      <Minimize2 className="size-4" /> Collapse
                    </>
                  ) : (
                    <Maximize2 className="size-4" />
                  )}
                </button>

                <span className="text-sm font-semibold text-ink">Assistant</span>

                <div className="relative ml-auto flex items-center gap-1">
                  <button
                    type="button"
                    onClick={() => setMenuOpen((v) => !v)}
                    className="grid size-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-line-soft hover:text-ink"
                    aria-label="More options"
                  >
                    <MoreHorizontal className="size-4" />
                  </button>

                  <AnimatePresence>
                    {menuOpen && (
                      <motion.div
                        initial={{ opacity: 0, y: -4 }}
                        animate={{ opacity: 1, y: 0 }}
                        exit={{ opacity: 0, y: -4 }}
                        transition={{ duration: 0.14 }}
                        className="absolute right-0 top-9 z-10 w-40 overflow-hidden rounded-lg border border-line bg-card py-1 text-sm shadow-lg"
                      >
                        <button
                          type="button"
                          onClick={() => {
                            setMenuOpen(false)
                            setOpen(false)
                            navigate('/chatbot')
                          }}
                          className="block w-full px-3 py-2 text-left text-ink transition-colors hover:bg-line-soft"
                        >
                          Open full page
                        </button>
                        <button
                          type="button"
                          disabled={!activeCaseId}
                          onClick={() => {
                            if (activeCaseId) setMessages(activeCaseId, [])
                            setMenuOpen(false)
                          }}
                          className="block w-full px-3 py-2 text-left text-ink transition-colors hover:bg-line-soft disabled:cursor-not-allowed disabled:opacity-40"
                        >
                          Clear chat
                        </button>
                      </motion.div>
                    )}
                  </AnimatePresence>

                  <button
                    type="button"
                    onClick={() => {
                      setMenuOpen(false)
                      setOpen(false)
                    }}
                    className="grid size-8 place-items-center rounded-md text-muted-foreground transition-colors hover:bg-line-soft hover:text-ink"
                    aria-label="Close chatbot"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              </div>

              {/* Messages */}
              <div ref={scrollRef} className="flex-1 space-y-3 overflow-y-auto px-3 py-4">
                {!activeCaseId ? (
                  <p className="mt-6 text-center text-sm text-muted-foreground">
                    Open a case first, then ask away.
                  </p>
                ) : messages.length === 0 ? (
                  <div className="mt-10 flex flex-col items-center gap-3 text-center">
                    <img
                      src={logoUrl}
                      alt="Assistant"
                      className="size-12 rounded-full object-cover ring-1 ring-white/15"
                    />
                    <p className="text-sm text-muted-foreground">I'm ur assistant, ask ur questions</p>
                  </div>
                ) : (
                  messages.map((m, i) => <ChatBubble key={i} message={m} />)
                )}
                {asking && (
                  <div className="flex items-center gap-2 text-sm text-muted-foreground">
                    <Loader2 className="size-3.5 animate-spin" /> Answering…
                  </div>
                )}
              </div>

              {/* Composer */}
              <div className="flex flex-none gap-2 border-t border-line p-3">
                <Input
                  value={question}
                  onChange={(e) => setQuestion(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && ask()}
                  placeholder="Ask about accounts, transactions, flags…"
                  className="flex-1"
                  disabled={!activeCaseId}
                />
                <Button
                  onClick={ask}
                  disabled={asking || !activeCaseId || !question.trim()}
                  className="border border-white/15 bg-white/10 text-ink shadow-none hover:bg-white/20"
                >
                  <Send className="size-4" />
                </Button>
              </div>
            </motion.aside>
          </>
        )}
      </AnimatePresence>
    </>
  )
}
