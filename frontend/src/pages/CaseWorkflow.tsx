import { useRef, useState } from 'react'
import { AnimatePresence, motion } from 'framer-motion'
import { Loader2, RotateCcw } from 'lucide-react'

import { ProgressTimeline, STAGES } from '@/components/workflow/ProgressTimeline'
import { UploadStage } from '@/components/workflow/UploadStage'
import { ExtractionResults } from '@/components/workflow/ExtractionResults'
import { AnalysisResults } from '@/components/workflow/AnalysisResults'
import { GraphPreview } from '@/components/workflow/GraphPreview'
import { ReportDone } from '@/components/workflow/ReportDone'
import { SectionHeader } from '@/components/common/SectionHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { api, type ExtractionResult, type FraudAnalysis } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

const pause = (ms: number) => new Promise((r) => setTimeout(r, ms))

// Stage indices (must match STAGES order): 0 upload, 1 extraction, 2 analysis, 3 graph, 4 report, 5 done
const S = { UPLOAD: 0, EXTRACTION: 1, ANALYSIS: 2, GRAPH: 3, REPORT: 4, DONE: 5 }

function Processing({ label }: { label: string }) {
  return (
    <div className="flex flex-col items-center justify-center gap-3 py-20 text-center">
      <Loader2 className="size-7 animate-spin text-teal" />
      <p className="text-sm font-semibold text-ink">{label}</p>
      <p className="text-xs text-muted-foreground">Working on it — you can watch the pipeline advance above.</p>
    </div>
  )
}

export function CaseWorkflow() {
  const setActiveCase = useAppStore((s) => s.setActiveCase)
  const activeCaseId = useAppStore((s) => s.activeCaseId)

  const [reached, setReached] = useState(S.UPLOAD)
  const [view, setView] = useState(S.UPLOAD)
  const [working, setWorking] = useState(false)
  const [error, setError] = useState<{ index: number; message: string } | null>(null)
  const [extraction, setExtraction] = useState<ExtractionResult | null>(null)
  const [fraud, setFraud] = useState<FraudAnalysis | null>(null)
  const [caseId, setCaseId] = useState('')

  const formRef = useRef<FormData | null>(null)

  function goto(index: number) {
    setReached((r) => Math.max(r, index))
    setView(index)
  }

  async function pollUntilDone(getStatus: () => Promise<{ status: string; error?: string }>) {
    for (;;) {
      await pause(3000)
      let s
      try {
        s = await getStatus()
      } catch {
        continue
      }
      if (s.status === 'done') return
      if (s.status === 'error') throw new Error(s.error || 'Stage failed.')
    }
  }

  async function runAnalysisReport(cid: string) {
    // Analysis
    goto(S.ANALYSIS)
    setWorking(true)
    await api.runFraud(cid)
    await pollUntilDone(() => api.fraudStatus(cid))
    setFraud(await api.getFraud(cid))
    setWorking(false)
    await pause(4200) // let the investigator glance at the findings

    // Graph (static preview — no backend call)
    goto(S.GRAPH)
    setWorking(false)
    await pause(3200)

    // Report
    goto(S.REPORT)
    setWorking(true)
    await api.runReportPdf(cid, 'en')
    await pollUntilDone(() => api.reportPdfStatus(cid, 'en'))
    setWorking(false)

    // Done
    goto(S.DONE)
  }

  async function run(form: FormData) {
    formRef.current = form
    setError(null)
    setExtraction(null)
    setFraud(null)
    try {
      // Extraction
      goto(S.EXTRACTION)
      setWorking(true)
      const ext = await api.runExtraction(form)
      setExtraction(ext)
      setActiveCase(ext.session_id)
      setCaseId(ext.session_id)
      setWorking(false)
      if (ext.files_failed.length >= ext.files_processed && ext.clean_rows === 0) {
        throw new Error('No transactions could be extracted from the uploaded files.')
      }
      await pause(3800)
      await runAnalysisReport(ext.session_id)
    } catch (e) {
      setWorking(false)
      setError({ index: reached, message: e instanceof Error ? e.message : String(e) })
    }
  }

  async function retry() {
    setError(null)
    try {
      if (caseId && reached >= S.ANALYSIS) {
        await runAnalysisReport(caseId)
      } else if (formRef.current) {
        await run(formRef.current)
      }
    } catch (e) {
      setError({ index: reached, message: e instanceof Error ? e.message : String(e) })
    }
  }

  function reset() {
    setReached(S.UPLOAD)
    setView(S.UPLOAD)
    setWorking(false)
    setError(null)
    setExtraction(null)
    setFraud(null)
    setCaseId('')
    formRef.current = null
    setActiveCase(null)
  }

  const started = reached > S.UPLOAD

  function content() {
    if (error && view === error.index) {
      return (
        <Card className="border-l-2 border-l-red border-line p-6">
          <h3 className="text-sm font-bold text-red">{STAGES[error.index]?.label} failed</h3>
          <p className="mt-1 text-sm text-muted-foreground">{error.message}</p>
          <div className="mt-4 flex gap-2">
            <Button onClick={retry}>Retry</Button>
            <Button variant="outline" onClick={reset}>
              <RotateCcw className="size-4" /> Start over
            </Button>
          </div>
        </Card>
      )
    }
    switch (view) {
      case S.UPLOAD:
        return <UploadStage onStart={run} />
      case S.EXTRACTION:
        return working || !extraction ? (
          <Processing label="Extracting transactions from the statements…" />
        ) : (
          <ExtractionResults result={extraction} caseId={caseId} />
        )
      case S.ANALYSIS:
        return working || !fraud ? (
          <Processing label="Running the fraud-detection engine…" />
        ) : (
          <AnalysisResults fraud={fraud} />
        )
      case S.GRAPH:
        return <GraphPreview caseId={caseId || activeCaseId || ''} />
      case S.REPORT:
        return working ? <Processing label="Generating the investigation report…" /> : <ReportDone caseId={caseId} onReset={reset} />
      case S.DONE:
        return <ReportDone caseId={caseId} onReset={reset} />
      default:
        return null
    }
  }

  return (
    <div>
      <SectionHeader
        eyebrow="Investigation"
        title="Open case file"
        sub="Upload the statements once — extraction, fraud analysis and the report run as one guided flow."
      />

      {started && (
        <div className="mb-6">
          <ProgressTimeline
            currentIndex={reached}
            viewIndex={view}
            working={working}
            error={!!error}
            onSelect={(i) => setView(i)}
          />
        </div>
      )}

      <AnimatePresence mode="wait">
        <motion.div
          key={`${view}-${working}-${!!error}`}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -8 }}
          transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
        >
          {content()}
        </motion.div>
      </AnimatePresence>
    </div>
  )
}
