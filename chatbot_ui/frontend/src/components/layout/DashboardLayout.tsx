import { Navigate, Outlet } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { useLocation } from 'react-router-dom'

import { TopNav } from '@/components/layout/TopNav'
import { FloatingChatButton } from '@/components/layout/FloatingChatButton'
import { useAppStore } from '@/store/useAppStore'

export function DashboardLayout() {
  const entered = useAppStore((s) => s.entered)
  const flashMessage = useAppStore((s) => s.flashMessage)
  const setFlash = useAppStore((s) => s.setFlash)
  const location = useLocation()

  if (!entered) return <Navigate to="/" replace />

  return (
    <div className="flex h-screen flex-col overflow-hidden bg-canvas">
      <TopNav />
      {/* Ambient line-pattern animation in the side gutters only (item 6) —
          purely decorative, sits behind the centered content column. */}
      <div className="sc-app-side left" aria-hidden="true" />
      <div className="sc-app-side right" aria-hidden="true" />
      <main className="relative z-10 flex-1 overflow-y-auto overflow-x-hidden px-10 py-8">
        <div className="mx-auto w-full max-w-[1200px]">
        <AnimatePresence>
          {flashMessage && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.2 }}
              className="mb-5 rounded-lg border border-green/30 bg-green/10 px-4 py-2.5 text-sm font-medium text-green"
              onAnimationComplete={() => setTimeout(() => setFlash(null), 3500)}
            >
              {flashMessage}
            </motion.div>
          )}
        </AnimatePresence>
        <AnimatePresence mode="wait">
          <motion.div
            key={location.pathname}
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -8 }}
            transition={{ duration: 0.18, ease: [0.16, 1, 0.3, 1] }}
          >
            <Outlet />
          </motion.div>
        </AnimatePresence>
        </div>
      </main>
      <FloatingChatButton />
    </div>
  )
}
