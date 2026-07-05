import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Download, RotateCcw } from 'lucide-react'

import { SectionHeader } from '@/components/common/SectionHeader'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

const RAW_LABELS: Record<string, string> = {
  clean: 'Clean transactions',
  flagged: 'Flagged transactions',
  duplicates: 'Duplicates',
  metadata: 'Metadata',
}

export function Reports() {
  const navigate = useNavigate()
  const activeCaseId = useAppStore((s) => s.activeCaseId)
  const [reportHtml, setReportHtml] = useState('')
  const [available, setAvailable] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!activeCaseId) return
    api.reportHtml(activeCaseId).then(setReportHtml)
    api.reportDownloads(activeCaseId).then((r) => setAvailable(r.available))
  }, [activeCaseId])

  function downloadReport() {
    if (!activeCaseId || !reportHtml) return
    const blob = new Blob([reportHtml], { type: 'text/html' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `survey_corps_report_${activeCaseId}.html`
    link.click()
    URL.revokeObjectURL(url)
  }

  if (!activeCaseId) {
    return (
      <div>
        <SectionHeader eyebrow="Put it on record" title="Reports" />
        <Card className="px-4 py-6 text-sm text-muted-foreground">
          Run extraction first, or pick an existing case from the sidebar.
        </Card>
      </div>
    )
  }

  return (
    <div>
      <SectionHeader
        eyebrow="Put it on record"
        title="Reports"
        sub="Generate a print-ready case report, or export the raw extraction data."
      />

      <div className="grid gap-3 sm:grid-cols-2">
        <Button size="lg" disabled={!reportHtml} onClick={downloadReport}>
          <Download className="size-4" /> Download case report (HTML)
        </Button>
        <Button size="lg" variant="outline" onClick={() => navigate('/extraction')}>
          <RotateCcw className="size-4" /> Start a new case
        </Button>
      </div>
      <p className="mt-2 text-xs text-muted-foreground">
        Open the downloaded file in a browser and Print → Save as PDF for a court-ready document.
      </p>

      <h2 className="mt-8 mb-2 text-sm font-bold text-ink">Raw data downloads</h2>
      <div className="grid grid-cols-2 gap-2 sm:grid-cols-4">
        {Object.keys(RAW_LABELS).map((key) => (
          <Button key={key} variant="outline" size="sm" disabled={!available[key]} asChild={!!available[key]}>
            {available[key] ? (
              <a href={api.downloadUrl(activeCaseId, key)}>{RAW_LABELS[key]}</a>
            ) : (
              <span>{RAW_LABELS[key]}: n/a</span>
            )}
          </Button>
        ))}
      </div>

      <h2 className="mt-8 mb-2 text-sm font-bold text-ink">Report preview</h2>
      <Card className="overflow-hidden p-0">
        <iframe title="case-report-preview" srcDoc={reportHtml} className="h-[640px] w-full" />
      </Card>
    </div>
  )
}
