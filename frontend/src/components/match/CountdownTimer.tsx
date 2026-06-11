import { useCountdown } from '../../hooks/useCountdown'

const pad = (n: number) => String(n).padStart(2, '0')

export default function CountdownTimer({ targetIso }: { targetIso: string }) {
  const { days, hours, minutes, seconds, isPast } = useCountdown(targetIso)

  if (isPast) {
    return (
      <p className="font-display text-lg font-black tracking-[0.2em] uppercase text-pitch-600 dark:text-pitch-300">
        Kicking off
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
