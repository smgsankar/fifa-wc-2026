import type { MatchStatus } from '../../lib/types'

const STYLES: Record<string, string> = {
  pending: 'border-ink/25 text-ink/70 dark:border-stone-100/25 dark:text-stone-100/70',
  live: 'border-loss/40 bg-loss/10 text-loss',
  awaiting_results: 'border-draw/40 bg-draw/10 text-draw',
  completed: 'border-pitch-600/40 bg-pitch-600/10 text-pitch-700 dark:text-pitch-300',
}

const LABELS: Record<string, string> = {
  pending: 'Upcoming',
  live: 'Live',
  awaiting_results: 'Waiting for results',
  completed: 'Full-time',
}

export default function StatusBadge({ status }: { status: MatchStatus }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 font-display text-[0.65rem] font-bold tracking-[0.15em] uppercase ${STYLES[status] ?? STYLES.pending}`}
    >
      {status === 'live' && (
        <span className="relative flex size-1.5">
          <span className="absolute inline-flex size-full animate-ping rounded-full bg-loss opacity-75" />
          <span className="relative inline-flex size-1.5 rounded-full bg-loss" />
        </span>
      )}
      {LABELS[status] ?? status}
    </span>
  )
}
