import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { CheckCircle2, FileUp, Loader2, UploadCloud, X } from 'lucide-react'

import { SectionHeader } from '@/components/common/SectionHeader'
import { MetricCard } from '@/components/common/MetricCard'
import { Button } from '@/components/ui/button'
import { Card } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { api, type ExtractionResult } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

type PendingFile = { file: File; accountHint: string; bankHint: string }

export function Extraction() {
  const navigate = useNavigate()
  const setActiveCase = useAppStore((s) => s.setActiveCase)
  const setFlash = useAppStore((s) => s.setFlash)

  const [files, setFiles] = useState<PendingFile[]>([])
  const [caseName, setCaseName] = useState('')
  const [investigator, setInvestigator] = useState('')
  const [maxOcrPages, setMaxOcrPages] = useState(3)
  const [running, setRunning] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [result, setResult] = useState<ExtractionResult | null>(null)
  const [justCompleted, setJustCompleted] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  // Case id is formatted as "<case name> <year> - <investigator>" (item 8),
  // e.g. "Kumar_Fraud 2026 - J. Rao". Parts are dropped when left blank.
  const caseYear = new Date().getFullYear()
  const caseBase = caseName.trim()
  const investigatorName = investigator.trim()
  const formattedCaseName = caseBase
    ? `${caseBase} ${caseYear}${investigatorName ? ` - ${investigatorName}` : ''}`
    : ''

  function addFiles(fileList: FileList | null) {
    if (!fileList) return
    const additions: PendingFile[] = Array.from(fileList).map((file) => ({
      file,
      accountHint: file.name.replace(/\.[^/.]+$/, ''),
      bankHint: '',
    }))
    setFiles((prev) => [...prev, ...additions])
  }

  function updateHint(index: number, field: 'accountHint' | 'bankHint', value: string) {
    setFiles((prev) => prev.map((f, i) => (i === index ? { ...f, [field]: value } : f)))
  }

  function removeFile(index: number) {
    setFiles((prev) => prev.filter((_, i) => i !== index))
  }

  async function runExtraction() {
    setRunning(true)
    setError(null)
    try {
      const form = new FormData()
      files.forEach((f) => form.append('files', f.file))
      form.append('account_hints', JSON.stringify(files.map((f) => f.accountHint)))
      form.append('bank_hints', JSON.stringify(files.map((f) => f.bankHint)))
      form.append('case_name', formattedCaseName)
      form.append('max_ocr_pages', String(maxOcrPages))

      const res = await api.runExtraction(form)
      setResult(res)
      setActiveCase(res.session_id)
      setFlash(`Case '${res.session_id}' extracted and indexed — ${res.indexed_chunks} chunks ready.`)
      // Confirm completion, then move to Analysis automatically (item 6).
      setRunning(false)
      setJustCompleted(true)
      setTimeout(() => navigate('/analysis'), 1700)
      return
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Extraction failed.')
    } finally {
      setRunning(false)
    }
  }

  return (
    <div>
      <AnimatePresence>
        {justCompleted && (
          <motion.div
            className="fixed inset-0 z-[60] flex items-center justify-center bg-black/70 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          >
            <motion.div
              className="flex flex-col items-center gap-4 rounded-2xl border border-green/40 bg-paper px-10 py-9 text-center shadow-[0_24px_60px_rgba(0,0,0,0.5)]"
              initial={{ opacity: 0, scale: 0.9, y: 10 }}
              animate={{ opacity: 1, scale: 1, y: 0 }}
              transition={{ type: 'spring', stiffness: 260, damping: 22 }}
            >
              <motion.span
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ delay: 0.1, type: 'spring', stiffness: 300, damping: 16 }}
                className="grid size-16 place-items-center rounded-full bg-green/15 text-green"
              >
                <CheckCircle2 className="size-9" />
              </motion.span>
              <div>
                <div className="font-display text-xl font-extrabold text-ink">Extraction is complete</div>
                <div className="mt-1.5 flex items-center justify-center gap-2 text-sm text-muted-foreground">
                  <Loader2 className="size-3.5 animate-spin" /> Taking you to Analysis…
                </div>
              </div>
            </motion.div>
          </motion.div>
        )}
      </AnimatePresence>

      <SectionHeader
        eyebrow="Ingest"
        title="Extraction"
        sub="Upload bank statements and run the pipeline. On completion the case is indexed and you move to Analysis automatically."
      />

      <div className="grid gap-5 lg:grid-cols-[2fr_1fr]">
        <Card className="p-5">
          <div
            className="flex cursor-pointer flex-col items-center justify-center rounded-xl border-1.5 border-dashed border-line bg-line-soft/40 px-6 py-10 text-center transition-colors hover:border-teal/50 hover:bg-teal-pale/40"
            onClick={() => inputRef.current?.click()}
            onDragOver={(e) => e.preventDefault()}
            onDrop={(e) => {
              e.preventDefault()
              addFiles(e.dataTransfer.files)
            }}
          >
            <UploadCloud className="size-7 text-teal" />
            <div className="mt-3 text-sm font-semibold text-ink">Drop bank statement files, or click to browse</div>
            <div className="mt-1 text-xs text-muted-foreground">PDF, CSV, XLSX, DOCX, PNG/JPG supported</div>
            <input
              ref={inputRef}
              type="file"
              multiple
              className="hidden"
              onChange={(e) => addFiles(e.target.files)}
            />
          </div>

          {files.length > 0 && (
            <div className="mt-5 space-y-2">
              <p className="text-xs text-muted-foreground">
                Account and bank fields are hints only; the parser reads the statement content.
              </p>
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
                  <Input
                    value={f.accountHint}
                    placeholder="Account hint"
                    onChange={(e) => updateHint(i, 'accountHint', e.target.value)}
                    className="h-8 text-xs"
                  />
                  <Input
                    value={f.bankHint}
                    placeholder="Bank hint"
                    onChange={(e) => updateHint(i, 'bankHint', e.target.value)}
                    className="h-8 text-xs"
                  />
                  <Button variant="ghost" size="icon" className="size-8" onClick={() => removeFile(i)}>
                    <X className="size-3.5" />
                  </Button>
                </motion.div>
              ))}
            </div>
          )}

          {error && (
            <div className="mt-4 rounded-lg border border-red/30 bg-red/5 px-3 py-2 text-sm text-red">{error}</div>
          )}

          <Button
            className="mt-5 w-full"
            size="lg"
            disabled={files.length === 0 || running}
            onClick={runExtraction}
          >
            {running ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Extracting {files.length} file(s)…
              </>
            ) : (
              'Run extraction and index'
            )}
          </Button>
        </Card>

        <Card className="space-y-4 p-5">
          <div>
            <Label htmlFor="case-name">Case name (optional)</Label>
            <Input
              id="case-name"
              value={caseName}
              onChange={(e) => setCaseName(e.target.value)}
              placeholder="e.g. Kumar_Fraud"
              className="mt-1.5"
            />
          </div>
          <div>
            <Label htmlFor="investigator">Investigating inspector</Label>
            <Input
              id="investigator"
              value={investigator}
              onChange={(e) => setInvestigator(e.target.value)}
              placeholder="e.g. J. Rao"
              className="mt-1.5"
            />
          </div>
          <div className="rounded-lg border border-line bg-line-soft/50 px-3 py-2">
            <div className="text-[0.62rem] font-bold uppercase tracking-widest text-faint">Case ID preview</div>
            <div className="mt-1 truncate font-mono text-sm text-ink">
              {formattedCaseName || <span className="text-faint">Enter a case name…</span>}
            </div>
            <p className="mt-1 text-[0.72rem] text-muted-foreground">
              Formatted as “name {caseYear} - inspector”. A timestamp is always appended to keep runs unique.
            </p>
          </div>
          <div>
            <Label htmlFor="ocr-pages">Max OCR pages per scanned PDF</Label>
            <Input
              id="ocr-pages"
              type="number"
              min={1}
              max={100}
              value={maxOcrPages}
              onChange={(e) => setMaxOcrPages(Number(e.target.value))}
              className="mt-1.5"
            />
            <p className="mt-1 text-[0.72rem] text-muted-foreground">
              Caps OCR work so the machine stays responsive.
            </p>
          </div>
        </Card>
      </div>

      {result && (
        <div className="mt-8">
          <div className="mb-3 rounded-lg border border-teal-bright/30 bg-teal-pale px-4 py-2 text-sm font-medium text-teal">
            Last run: {result.session_id}
          </div>
          <div className="grid grid-cols-2 gap-3 sm:grid-cols-5">
            <MetricCard label="Clean rows" value={result.clean_rows} />
            <MetricCard label="Flagged rows" value={result.flagged_rows} />
            <MetricCard label="Files processed" value={result.files_processed} />
            <MetricCard label="Failed files" value={result.files_failed.length} />
            <Card className="flex flex-col justify-center px-4 py-3.5">
              <div className="text-[0.68rem] font-bold uppercase tracking-widest text-faint">Time</div>
              <div className="mt-1 font-display text-2xl font-extrabold text-ink">{result.elapsed_label}</div>
            </Card>
          </div>

          <Tabs defaultValue="clean" className="mt-6">
            <TabsList>
              <TabsTrigger value="clean">Clean</TabsTrigger>
              <TabsTrigger value="flagged">Flagged</TabsTrigger>
              <TabsTrigger value="receipt">Receipt</TabsTrigger>
              <TabsTrigger value="downloads">Downloads</TabsTrigger>
            </TabsList>
            <TabsContent value="clean">
              <PreviewTable rows={result.clean_preview} empty="No clean rows." />
            </TabsContent>
            <TabsContent value="flagged">
              <PreviewTable rows={result.flagged_preview} empty="No flagged rows." />
            </TabsContent>
            <TabsContent value="receipt" className="space-y-2">
              {result.per_file.map((record, i) => (
                <details key={i} className="rounded-lg border border-line bg-paper p-3">
                  <summary className="cursor-pointer text-sm font-medium text-ink">
                    {(record.file as string) || `file ${i + 1}`}
                  </summary>
                  <pre className="mt-2 overflow-x-auto text-xs text-muted-foreground">
                    {JSON.stringify(record, null, 2)}
                  </pre>
                </details>
              ))}
            </TabsContent>
            <TabsContent value="downloads" className="flex flex-wrap gap-2">
              {result.downloads_available.map((key) => (
                <Button key={key} variant="outline" size="sm" asChild>
                  <a href={api.downloadUrl(result.session_id, key)}>{key}</a>
                </Button>
              ))}
              {result.downloads_available.length === 0 && (
                <p className="text-sm text-muted-foreground">No files available for download.</p>
              )}
            </TabsContent>
          </Tabs>
        </div>
      )}
    </div>
  )
}

function PreviewTable({ rows, empty }: { rows: Record<string, unknown>[]; empty: string }) {
  if (rows.length === 0) return <p className="py-4 text-sm text-muted-foreground">{empty}</p>
  const columns = Object.keys(rows[0])
  return (
    <div className="overflow-x-auto rounded-lg border border-line">
      <table className="w-full min-w-[720px] border-collapse text-left text-xs">
        <thead className="bg-line-soft text-[0.65rem] uppercase tracking-wide text-muted-foreground">
          <tr>
            {columns.map((col) => (
              <th key={col} className="whitespace-nowrap px-3 py-2 font-bold">
                {col}
              </th>
            ))}
          </tr>
        </thead>
        <tbody className="font-mono">
          {rows.slice(0, 50).map((row, i) => (
            <tr key={i} className="border-t border-line-soft">
              {columns.map((col) => (
                <td key={col} className="whitespace-nowrap px-3 py-1.5 text-ink">
                  {String(row[col] ?? '')}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
