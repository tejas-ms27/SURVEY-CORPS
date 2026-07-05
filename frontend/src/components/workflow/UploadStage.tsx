import { useRef, useState } from 'react'
import { motion } from 'framer-motion'
import { FileUp, Play, UploadCloud, X } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'

type PendingFile = { file: File; accountHint: string; bankHint: string }

type Props = {
  onStart: (form: FormData) => void
}

/** The initial case screen: drop statements, name the case, start the pipeline.
 *  No OCR/config knobs — the pipeline picks a safe default internally. */
export function UploadStage({ onStart }: Props) {
  const [files, setFiles] = useState<PendingFile[]>([])
  const [caseName, setCaseName] = useState('')
  const [investigator, setInvestigator] = useState('')
  const inputRef = useRef<HTMLInputElement>(null)

  const caseYear = new Date().getFullYear()
  const formattedCaseName = caseName.trim()
    ? `${caseName.trim()} ${caseYear}${investigator.trim() ? ` - ${investigator.trim()}` : ''}`
    : ''

  function addFiles(list: FileList | null) {
    if (!list) return
    setFiles((prev) => [
      ...prev,
      ...Array.from(list).map((file) => ({ file, accountHint: file.name.replace(/\.[^/.]+$/, ''), bankHint: '' })),
    ])
  }
  function updateHint(i: number, field: 'accountHint' | 'bankHint', value: string) {
    setFiles((prev) => prev.map((f, idx) => (idx === i ? { ...f, [field]: value } : f)))
  }

  function start() {
    const form = new FormData()
    files.forEach((f) => form.append('files', f.file))
    form.append('account_hints', JSON.stringify(files.map((f) => f.accountHint)))
    form.append('bank_hints', JSON.stringify(files.map((f) => f.bankHint)))
    form.append('case_name', formattedCaseName)
    // max_ocr_pages intentionally omitted — the backend applies a safe default.
    onStart(form)
  }

  return (
    <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
      <Card className="p-5">
        <div
          className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-1.5 border-dashed border-line bg-line-soft/40 px-6 py-12 text-center transition-colors hover:border-teal/50 hover:bg-teal-pale/40"
          onClick={() => inputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault()
            addFiles(e.dataTransfer.files)
          }}
        >
          <UploadCloud className="size-7 text-teal" />
          <div className="mt-3 text-sm font-semibold text-ink">Drop the case's bank statements, or click to browse</div>
          <div className="mt-1 text-xs text-muted-foreground">PDF, CSV, XLSX, DOCX, PNG/JPG — multiple files, multiple accounts</div>
          <input ref={inputRef} type="file" multiple className="hidden" onChange={(e) => addFiles(e.target.files)} />
        </div>

        {files.length > 0 && (
          <div className="mt-5 space-y-2">
            <p className="text-xs text-muted-foreground">Account and bank fields are hints only — the parser reads each statement's content.</p>
            {files.map((f, i) => (
              <motion.div
                key={`${f.file.name}-${i}`}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                className="grid grid-cols-[1fr_1fr_1fr_auto] items-center gap-2 rounded-lg border border-line bg-paper p-2.5"
              >
                <div className="flex items-center gap-2 truncate text-sm text-ink">
                  <FileUp className="size-3.5 flex-none text-faint" />
                  <span className="truncate">{f.file.name}</span>
                </div>
                <Input value={f.accountHint} placeholder="Account hint" onChange={(e) => updateHint(i, 'accountHint', e.target.value)} className="h-8 text-xs" />
                <Input value={f.bankHint} placeholder="Bank hint" onChange={(e) => updateHint(i, 'bankHint', e.target.value)} className="h-8 text-xs" />
                <Button variant="ghost" size="icon" className="size-8" onClick={() => setFiles((prev) => prev.filter((_, idx) => idx !== i))}>
                  <X className="size-3.5" />
                </Button>
              </motion.div>
            ))}
          </div>
        )}

        <Button className="mt-5 w-full" size="lg" disabled={files.length === 0} onClick={start}>
          <Play className="size-4" /> Start case processing
        </Button>
        <p className="mt-2 text-center text-xs text-muted-foreground">
          Runs the full pipeline — extraction, fraud analysis and the investigation report — automatically.
        </p>
      </Card>

      <Card className="space-y-4 p-5">
        <div>
          <Label htmlFor="case-name">Case name (optional)</Label>
          <Input id="case-name" value={caseName} onChange={(e) => setCaseName(e.target.value)} placeholder="e.g. Kumar_Fraud" className="mt-1.5" />
        </div>
        <div>
          <Label htmlFor="investigator">Investigating inspector</Label>
          <Input id="investigator" value={investigator} onChange={(e) => setInvestigator(e.target.value)} placeholder="e.g. J. Rao" className="mt-1.5" />
        </div>
        <div className="rounded-lg border border-line bg-line-soft/50 px-3 py-2">
          <div className="text-[0.62rem] font-bold uppercase tracking-widest text-faint">Case ID preview</div>
          <div className="mt-1 truncate font-mono text-sm text-ink">
            {formattedCaseName || <span className="text-faint">Enter a case name…</span>}
          </div>
          <p className="mt-1 text-[0.72rem] text-muted-foreground">A timestamp is always appended to keep runs unique.</p>
        </div>
      </Card>
    </div>
  )
}
