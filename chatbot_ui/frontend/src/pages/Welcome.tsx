import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { FileSearch, MessageSquareText, ScanSearch, ShieldCheck } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { useAppStore } from '@/store/useAppStore'

const CAPABILITIES = [
  {
    n: '01 / EXTRACT',
    t: 'Read every statement',
    d: 'Tiered parser pulls each field A-to-Z. Nothing summarized away.',
    icon: ScanSearch,
  },
  {
    n: '02 / ANALYSE',
    t: 'See the case',
    d: 'Per-account ledgers, flags, duplicates, counterparty graph.',
    icon: FileSearch,
  },
  {
    n: '03 / INTERROGATE',
    t: 'Question the evidence',
    d: 'Bilingual chatbot, deterministic lookups, verbatim citations.',
    icon: MessageSquareText,
  },
  {
    n: '04 / REPORT',
    t: 'Put it on record',
    d: 'Generate a print-ready, court-ready case report.',
    icon: ShieldCheck,
  },
]

export function Welcome() {
  const navigate = useNavigate()
  const enter = useAppStore((s) => s.enter)

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas px-6 py-16">
      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
        className="relative w-full max-w-4xl overflow-hidden rounded-2xl border border-line bg-paper px-10 py-12 shadow-[0_12px_32px_rgba(22,51,46,0.07)] sm:px-14 sm:py-16"
      >
        <div className="absolute inset-x-0 top-0 h-[3px] bg-gradient-to-r from-teal to-teal-bright" />

        <div className="text-[0.68rem] font-extrabold uppercase tracking-[0.28em] text-teal">
          Case File // Confidential — Clearance Required
        </div>
        <h1 className="mt-2 font-display text-4xl font-extrabold tracking-tight text-ink sm:text-5xl">
          SURVEY&nbsp;CORPS
        </h1>
        <div className="my-4 h-[3px] w-20 bg-teal" />
        <div className="font-display text-base uppercase tracking-[0.14em] text-muted-foreground">
          Financial Forensics Engine
        </div>
        <p className="mt-4 max-w-2xl text-[1.02rem] leading-relaxed text-muted-foreground">
          A forensic workspace for financial-crime investigators. Feed it inconsistent bank statements across
          banks, formats and languages — it reconstructs a single, reconciled ledger, flags what doesn't add up,
          traces money between parties, and lets you interrogate the whole case in plain language with citations
          you can trust.
        </p>

        <div className="mt-8 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {CAPABILITIES.map((cap, i) => (
            <motion.div
              key={cap.n}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.3, delay: 0.08 * i, ease: [0.16, 1, 0.3, 1] }}
              className="rounded-xl border border-line bg-teal-pale p-4"
            >
              <cap.icon className="size-4 text-teal" />
              <div className="mt-2 text-[0.66rem] font-bold tracking-widest text-teal">{cap.n}</div>
              <div className="mt-1 font-display text-base font-bold tracking-tight text-ink">{cap.t}</div>
              <div className="mt-1 text-[0.82rem] leading-relaxed text-muted-foreground">{cap.d}</div>
            </motion.div>
          ))}
        </div>

        <div className="mt-10 flex justify-center">
          <Button
            size="lg"
            className="px-10"
            onClick={() => {
              enter()
              navigate('/extraction')
            }}
          >
            ▶&nbsp;&nbsp;ENTER THE CASE FILE
          </Button>
        </div>

        <div className="mt-6 text-center text-[0.72rem] tracking-wide text-muted-foreground">
          <span className="animate-pulse text-teal-bright">●</span>&nbsp; SYSTEM READY &nbsp;·&nbsp; ENGINE{' '}
          <b className="text-teal">CIDECODE</b> &nbsp;·&nbsp; OPEN A CASE TO BEGIN
        </div>
      </motion.div>
    </div>
  )
}
