import { useCallback, useEffect, useState } from 'react'

import { api } from '@/lib/api'
import { useAppStore } from '@/store/useAppStore'

export function useCases() {
  const [cases, setCases] = useState<string[]>([])
  const [loading, setLoading] = useState(true)
  const activeCaseId = useAppStore((s) => s.activeCaseId)
  const setActiveCase = useAppStore((s) => s.setActiveCase)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const res = await api.listCases()
      setCases(res.cases)
      if (!res.cases.includes(activeCaseId || '')) {
        setActiveCase(res.latest)
      }
    } finally {
      setLoading(false)
    }
  }, [activeCaseId, setActiveCase])

  useEffect(() => {
    refresh()
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { cases, loading, refresh, activeCaseId, setActiveCase }
}
