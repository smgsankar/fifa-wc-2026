import { useEffect, useMemo, useState } from 'react'

export interface Countdown {
  days: number
  hours: number
  minutes: number
  seconds: number
  isPast: boolean
}

function toCountdown(targetMs: number): Countdown {
  const ms = targetMs - Date.now()
  if (ms <= 0) return { days: 0, hours: 0, minutes: 0, seconds: 0, isPast: true }
  const total = Math.floor(ms / 1000)
  return {
    days: Math.floor(total / 86400),
    hours: Math.floor(total / 3600) % 24,
    minutes: Math.floor(total / 60) % 60,
    seconds: total % 60,
    isPast: false,
  }
}

export function useCountdown(targetIso: string): Countdown {
  const targetMs = useMemo(() => new Date(targetIso).getTime(), [targetIso])
  const [state, setState] = useState(() => ({ targetMs, countdown: toCountdown(targetMs) }))

  /* Render-time reset when the target changes — avoids a stale first tick. */
  if (state.targetMs !== targetMs) {
    setState({ targetMs, countdown: toCountdown(targetMs) })
  }

  useEffect(() => {
    const id = setInterval(() => setState({ targetMs, countdown: toCountdown(targetMs) }), 1000)
    return () => clearInterval(id)
  }, [targetMs])

  return state.countdown
}
