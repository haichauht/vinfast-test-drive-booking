import { useCallback, useEffect, useState } from 'react'

export function useRemote(loader, deps = []) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const reload = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true)
    if (!silent) setError('')
    try {
      setData(await loader())
    } catch (caught) {
      if (!silent) setError(caught.message)
    } finally {
      if (!silent) setLoading(false)
    }
  }, deps)

  useEffect(() => {
    reload()
  }, [reload])

  return { data, loading, error, reload, setData }
}
