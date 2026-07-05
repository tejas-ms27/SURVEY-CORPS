import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react'
import { Maximize2, Minimize2, RotateCcw, ZoomIn, ZoomOut } from 'lucide-react'

/**
 * Shared chrome for every graph/chart surface (round 5, item 3): a bordered
 * canvas with zoom-in / zoom-out / fullscreen controls pinned to the top-right
 * corner, plus a reset. Zoom is a CSS transform on the content, so it works
 * uniformly for Plotly charts, pyvis iframes and the force-graph canvas without
 * each needing its own zoom API. The inner area scrolls, so a zoomed-in graph
 * can be panned. Fullscreen uses the native Fullscreen API on the frame.
 */
const MIN_SCALE = 0.6
const MAX_SCALE = 3
const STEP = 0.25

export function GraphFrame({
  children,
  className = '',
  minHeight = 420,
}: {
  children: ReactNode
  className?: string
  minHeight?: number
}) {
  const frameRef = useRef<HTMLDivElement>(null)
  const [scale, setScale] = useState(1)
  const [isFullscreen, setIsFullscreen] = useState(false)

  const zoomIn = useCallback(() => setScale((s) => Math.min(MAX_SCALE, +(s + STEP).toFixed(2))), [])
  const zoomOut = useCallback(() => setScale((s) => Math.max(MIN_SCALE, +(s - STEP).toFixed(2))), [])
  const reset = useCallback(() => setScale(1), [])

  const toggleFullscreen = useCallback(() => {
    const el = frameRef.current
    if (!el) return
    if (document.fullscreenElement) {
      document.exitFullscreen().catch(() => {})
    } else {
      el.requestFullscreen().catch(() => {})
    }
  }, [])

  useEffect(() => {
    const onChange = () => setIsFullscreen(document.fullscreenElement === frameRef.current)
    document.addEventListener('fullscreenchange', onChange)
    return () => document.removeEventListener('fullscreenchange', onChange)
  }, [])

  const btn =
    'grid size-7 place-items-center rounded-md border border-line bg-paper/90 text-muted-foreground shadow-sm backdrop-blur transition-colors hover:border-teal/50 hover:text-ink disabled:opacity-40'

  return (
    <div
      ref={frameRef}
      className={`relative overflow-hidden rounded-xl border border-line bg-paper ${
        isFullscreen ? 'flex flex-col' : ''
      } ${className}`}
    >
      {/* Controls — top-right corner, above the canvas. */}
      <div className="absolute right-2.5 top-2.5 z-20 flex items-center gap-1.5">
        <button type="button" aria-label="Zoom out" className={btn} onClick={zoomOut} disabled={scale <= MIN_SCALE}>
          <ZoomOut className="size-3.5" />
        </button>
        <button type="button" aria-label="Zoom in" className={btn} onClick={zoomIn} disabled={scale >= MAX_SCALE}>
          <ZoomIn className="size-3.5" />
        </button>
        <button type="button" aria-label="Reset zoom" className={btn} onClick={reset} disabled={scale === 1}>
          <RotateCcw className="size-3.5" />
        </button>
        <button
          type="button"
          aria-label={isFullscreen ? 'Exit full screen' : 'Full screen'}
          className={btn}
          onClick={toggleFullscreen}
        >
          {isFullscreen ? <Minimize2 className="size-3.5" /> : <Maximize2 className="size-3.5" />}
        </button>
      </div>

      <div className={`h-full w-full overflow-auto ${isFullscreen ? 'flex-1' : ''}`}>
        <div
          className="origin-top-left transition-transform duration-150"
          style={{
            transform: `scale(${scale})`,
            width: `${100 / scale}%`,
            minHeight: isFullscreen ? '100%' : minHeight,
          }}
        >
          {children}
        </div>
      </div>
    </div>
  )
}
