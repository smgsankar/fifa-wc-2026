import { useCallback, useEffect, useState } from 'react'

interface Request<T> {
  fetcher: () => Promise<T>
  attempt: number
}

interface Settled<T> {
  request: Request<T>
  data: T | null
  error: Error | null
}

/**
 * Runs an async fetcher and exposes {data, loading, error, retry}.
 * The fetcher must be referentially stable (wrap in useCallback) —
 * a new fetcher identity triggers a refetch.
 */
export function useFetch<T>(fetcher: () => Promise<T>) {
  const [attempt, setAttempt] = useState(0)
  const [request, setRequest] = useState<Request<T>>({ fetcher, attempt })
  const [settled, setSettled] = useState<Settled<T> | null>(null)

  /* Render-time reset: a new fetcher or retry starts a new request identity. */
  if (request.fetcher !== fetcher || request.attempt !== attempt) {
    setRequest({ fetcher, attempt })
  }

  useEffect(() => {
    let cancelled = false
    request.fetcher().then(
      (data) => {
        if (!cancelled) setSettled({ request, data, error: null })
      },
      (error: Error) => {
        if (!cancelled) setSettled({ request, data: null, error })
      },
    )
    return () => {
      cancelled = true
    }
  }, [request])

  const retry = useCallback(() => setAttempt((a) => a + 1), [])

  /* Loading is derived: nothing settled yet for the current request. */
  const current = settled && settled.request === request ? settled : null
  return {
    data: current?.data ?? null,
    loading: current === null,
    error: current?.error ?? null,
    retry,
  }
}
