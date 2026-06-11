import { useCountdown } from '../../hooks/useCountdown'
import type { MatchStatus } from '../../lib/types'

const pad = (n: number) => String(n).padStart(2, '0')

export default function CountdownTimer({
  targetIso,
  status,
}: {
  targetIso: string
  status?: MatchStatus
}) {
  const { days, hours, minutes, seconds, isPast } = useCountdown(targetIso)

  if (isPast) {
    if (status === 'live') {
      return (
        <p className="flex items-center justify-center gap-2.5 font-display text-lg font-black tracking-[0.2em] uppercase text-loss">
          <span className="relative flex size-2.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-loss opacity-75" />
            <span className="relative inline-flex size-2.5 rounded-full bg-loss" />
          </span>
          Live
        </p>
      )
    }
    if (status === 'awaiting_results') {
      return (
        <p className="flex items-center justify-center gap-2.5 font-display text-lg font-black tracking-[0.2em] uppercase text-draw">
          <span className="relative flex size-2.5">
            <span className="absolute inline-flex size-full animate-ping rounded-full bg-draw opacity-75" />
            <span className="relative inline-flex size-2.5 rounded-full bg-draw" />
          </span>
          Waiting for results
        </p>
      )
    }
    return (
      <p className="text-center font-display text-lg font-black tracking-[0.2em] uppercase text-pitch-600 dark:text-pitch-300">
        Completed
      </p>
    )
  }

  const units = [
    { value: days, label: 'Days' },
    { value: hours, label: 'Hrs' },
    { value: minutes, label: 'Min' },
    { value: seconds, label: 'Sec' },
  ]

  return (
    <div className="flex items-start justify-center gap-3 sm:gap-5">
      {units.map((u) => (
        <div key={u.label} className="flex flex-col items-center">
          <span className="font-mono text-3xl font-bold tabular-nums sm:text-4xl">
            {pad(u.value)}
          </span>
          <span className="mt-1 font-display text-[0.6rem] font-semibold tracking-[0.25em] uppercase text-ink/50 dark:text-stone-100/50">
            {u.label}
          </span>
        </div>
      ))}
    </div>
  )
}
