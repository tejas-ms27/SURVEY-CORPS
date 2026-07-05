import { motion } from 'framer-motion'
import { AlertTriangle, Check } from 'lucide-react'

export type StageKey = 'upload' | 'extraction' | 'analysis' | 'graph' | 'report' | 'done'

export type StageDef = { key: StageKey; label: string }

export const STAGES: StageDef[] = [
  { key: 'upload', label: 'Open case' },
  { key: 'extraction', label: 'Extraction' },
  { key: 'analysis', label: 'Analysis' },
  { key: 'graph', label: 'Relationships' },
  { key: 'report', label: 'Report' },
  { key: 'done', label: 'Done' },
]

type Props = {
  /** index of the stage the pipeline has reached (the live position) */
  currentIndex: number
  /** index of the stage whose content is being viewed (may be a completed one) */
  viewIndex: number
  /** true while the current stage is actively processing (drives the pulse) */
  working: boolean
  error?: boolean
  /** click a reached stage to review its content */
  onSelect: (index: number) => void
}

/** Persistent case-processing pipeline. Stays fixed while the content below changes;
 *  the rail fills as stages complete and the live stage pulses. */
export function ProgressTimeline({ currentIndex, viewIndex, working, error, onSelect }: Props) {
  const last = STAGES.length - 1
  const fill = Math.min(currentIndex / last, 1)

  return (
    <div className="rounded-xl border border-line bg-paper/60 px-5 py-4 backdrop-blur">
      <div className="mb-3 flex items-center gap-2">
        <span className="inline-block size-1.5 rounded-full bg-teal" />
        <span className="text-[0.6rem] font-bold uppercase tracking-[0.22em] text-faint">
          Case processing pipeline
        </span>
      </div>

      <div className="relative">
        {/* rail */}
        <div className="absolute left-0 right-0 top-[11px] h-[2px] rounded bg-line" aria-hidden="true" />
        <motion.div
          className={`absolute left-0 top-[11px] h-[2px] rounded ${error ? 'bg-red' : 'bg-teal'}`}
          initial={false}
          animate={{ width: `${fill * 100}%` }}
          transition={{ duration: 0.5, ease: [0.16, 1, 0.3, 1] }}
          aria-hidden="true"
        />

        <ol className="relative flex items-start justify-between">
          {STAGES.map((stage, i) => {
            const status =
              error && i === currentIndex
                ? 'error'
                : i < currentIndex
                  ? 'done'
                  : i === currentIndex
                    ? 'active'
                    : 'pending'
            const reached = i <= currentIndex
            const viewing = i === viewIndex
            return (
              <li key={stage.key} className="flex min-w-0 flex-1 flex-col items-center">
                <button
                  type="button"
                  disabled={!reached}
                  onClick={() => reached && onSelect(i)}
                  aria-current={viewing ? 'step' : undefined}
                  className="group flex flex-col items-center gap-2 disabled:cursor-default"
                >
                  <span className="relative grid size-6 place-items-center">
                    {status === 'active' && working && !error && (
                      <motion.span
                        className="absolute inset-0 rounded-full bg-teal/40"
                        animate={{ scale: [1, 1.9, 1], opacity: [0.6, 0, 0.6] }}
                        transition={{ duration: 1.6, repeat: Infinity, ease: 'easeInOut' }}
                      />
                    )}
                    <span
                      className={[
                        'relative grid size-[22px] place-items-center rounded-full border text-[0.62rem] font-bold transition-colors',
                        status === 'done'
                          ? 'border-teal bg-teal text-white'
                          : status === 'active'
                            ? 'border-teal bg-canvas text-teal'
                            : status === 'error'
                              ? 'border-red bg-red text-white'
                              : 'border-line bg-canvas text-faint',
                        viewing ? 'ring-2 ring-teal/40 ring-offset-2 ring-offset-paper' : '',
                      ].join(' ')}
                    >
                      {status === 'done' ? (
                        <Check className="size-3" />
                      ) : status === 'error' ? (
                        <AlertTriangle className="size-3" />
                      ) : (
                        i + 1
                      )}
                    </span>
                  </span>
                  <span
                    className={[
                      'text-center text-[0.62rem] font-semibold uppercase tracking-wider transition-colors',
                      status === 'pending' ? 'text-faint' : 'text-ink',
                      viewing ? 'text-teal' : 'group-hover:text-ink',
                    ].join(' ')}
                  >
                    {stage.label}
                  </span>
                </button>
              </li>
            )
          })}
        </ol>
      </div>
    </div>
  )
}
