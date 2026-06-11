import { useCallback, useEffect, useState } from 'react'

interface FetchState<T> {
  data: T | null
  loading: boolean
  error: Error | null
}

/**
 * Runs an async fetcher and exposes {data, loading, error, retry}.
 * The fetcher must be referentially stable (wrap in useCallback) —
 * a new fetcher identity triggers a refetch.
 */
export function useFetch<T>(fetcher: () => Promise<T>) {
  const [state, setState] = useState<FetchState<T>>({ data: null, loading: true, error: null })
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    let cancelled = false
    setState({ data: null, loading: true, error: null })
    fetcher().then(
      (data) => {
        if (!cancelled) setState({ data, loading: false, error: null })
      },
      (error: Error) => {
        if (!cancelled) setState({ data: null, loading: false, error })
      },
    )
    return () => {
      cancelled = true
    }
  }, [fetcher, attempt])

  const retry = useCallback(() => setAttempt((a) => a + 1), [])

  return { ...state, retry }
}
