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
  const [countdown, setCountdown] = useState(() => toCountdown(targetMs))

  useEffect(() => {
    setCountdown(toCountdown(targetMs))
    const id = setInterval(() => setCountdown(toCountdown(targetMs)), 1000)
    return () => clearInterval(id)
  }, [targetMs])

  return countdown
}
