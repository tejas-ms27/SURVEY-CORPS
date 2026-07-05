import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Loader2, RefreshCw, Send } from 'lucide-react'

import { SectionHeader } from '@/components/common/SectionHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { ChatBubble } from '@/components/chat/ChatBubble'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { api, type CaseSummary } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export function Chatbot() {
  const navigate = useNavigate()
  const activeCaseId = useAppStore((s) => s.activeCaseId)
  const messagesByCase = useAppStore((s) => s.messagesByCase)
  const setMessages = useAppStore((s) => s.setMessages)
  const appendMessage = useAppStore((s) => s.appendMessage)

  const [summary, setSummary] = useState<CaseSummary | null>(null)
  const [groqConfigured, setGroqConfigured] = useState(true)
  const [question, setQuestion] = useState('')
  const [asking, setAsking] = useState(false)
  const [reindexing, setReindexing] = useState(false)
  const scrollRef = useRef<HTMLDivElement>(null)

  const messages = activeCaseId ? messagesByCase[activeCaseId] || [] : []

  useEffect(() => {
    if (!activeCaseId) return
    api.getCaseSummary(activeCaseId).then(setSummary)
    api.chatStatus(activeCaseId).then((r) => setGroqConfigured(r.groq_configured))
    if (!messagesByCase[activeCaseId]) {
      api.chatHistory(activeCaseId).then((r) => setMessages(activeCaseId, r.messages))
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeCaseId])

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

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

  async function reindex() {
    if (!activeCaseId) return
    setReindexing(true)
    try {
      const res = await api.reindexCase(activeCaseId)
      setSummary((prev) => (prev ? { ...prev, indexed_chunks: res.indexed_chunks } : prev))
    } finally {
      setReindexing(false)
    }
  }

  if (!activeCaseId) {
    return (
      <div>
        <SectionHeader eyebrow="Interrogate" title="Investigator Chatbot" />
        <Card className="px-4 py-6 text-sm text-muted-foreground">
          Run extraction first, or pick an existing case from the sidebar.
        </Card>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader
        eyebrow="Interrogate"
        title="Investigator Chatbot"
        sub="Ask in English or Kannada. Structured lookups and semantic search, with verbatim citations."
      />

      {summary && (
        <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <MetricCard label="Accounts" value={summary.accounts} />
          <MetricCard label="Clean rows" value={summary.clean_rows} />
          <MetricCard label="Flagged rows" value={summary.flagged_rows} />
          <MetricCard label="Indexed chunks" value={summary.indexed_chunks} />
        </div>
      )}

      <div className="mt-4 flex items-center justify-between">
        <p className="text-xs text-muted-foreground">Citations are kept verbatim regardless of the language you ask in.</p>
        <div className="flex gap-2">
          <Button variant="outline" size="sm" onClick={reindex} disabled={reindexing}>
            <RefreshCw className={`size-3.5 ${reindexing ? 'animate-spin' : ''}`} /> Re-index
          </Button>
          <Button variant="outline" size="sm" onClick={() => navigate('/reports')}>
            Reports →
          </Button>
        </div>
      </div>

      {!groqConfigured && (
        <div className="mt-3 rounded-lg border border-amber/30 bg-amber/10 px-3 py-2 text-xs text-amber">
          GROQ_API_KEY is not set — semantic answers are disabled. Structured lookups (IDs, accounts, flags) still
          work.
        </div>
      )}

      <div
        ref={scrollRef}
        className="mt-4 flex h-[520px] flex-col gap-3 overflow-y-auto rounded-xl border border-line bg-card p-4 shadow-[0_4px_16px_rgba(22,51,46,0.035)]"
      >
        {messages.length === 0 && (
          <p className="text-sm text-muted-foreground">
            Try: "show full details for account X", "why were transactions flagged?", or "list all account
            holders".
          </p>
        )}
        {messages.map((m, i) => (
          <ChatBubble key={i} message={m} />
        ))}
        {asking && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-3.5 animate-spin" /> Answering…
          </div>
        )}
      </div>

      <div className="mt-3 flex gap-2">
        <Input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && ask()}
          placeholder="Ask about accounts, transactions, flags, duplicates, or suspicious activity..."
          className="flex-1"
        />
        <Button onClick={ask} disabled={asking || !question.trim()}>
          <Send className="size-4" />
        </Button>
      </div>
    </div>
  )
}
