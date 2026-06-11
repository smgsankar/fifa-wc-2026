import type { ModelStats } from '../../lib/types'
import { formatDate, formatPercent } from '../../lib/format'

function BigStat({ label, value }: { label: string; value: number }) {
  return (
    <div className="border border-ink/20 bg-white p-5 dark:border-stone-100/20 dark:bg-night-soft">
      <p className="font-display text-[0.65rem] font-bold tracking-[0.25em] uppercase text-ink/50 dark:text-stone-100/50">
        {label}
      </p>
      <p className="mt-2 font-mono text-4xl font-bold tabular-nums sm:text-5xl">
        {formatPercent(value)}
      </p>
      <div className="mt-3 h-1.5 w-full overflow-hidden rounded-full bg-ink/10 dark:bg-stone-100/10">
        <div className="h-full bg-pitch-600 dark:bg-pitch-400" style={{ width: `${value * 100}%` }} />
      </div>
    </div>
  )
}

export default function ModelStatsSection({ stats }: { stats: ModelStats }) {
  return (
    <div>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
        <BigStat label="Accuracy" value={stats.accuracy} />
        <BigStat label="Precision" value={stats.precision} />
        <BigStat label="Recall" value={stats.recall} />
      </div>

      <div className="mt-4 grid grid-cols-3 divide-x divide-ink/15 border border-ink/20 bg-white dark:divide-stone-100/15 dark:border-stone-100/20 dark:bg-night-soft">
        <div className="p-4 text-center sm:p-5">
          <p className="font-mono text-2xl font-bold tabular-nums sm:text-3xl">{stats.total_predictions}</p>
          <p className="mt-1 font-display text-[0.6rem] font-bold tracking-[0.2em] uppercase text-ink/50 dark:text-stone-100/50">
            Predictions
          </p>
        </div>
        <div className="p-4 text-center sm:p-5">
          <p className="font-mono text-2xl font-bold tabular-nums text-win sm:text-3xl dark:text-pitch-300">
            {stats.correct_predictions}
          </p>
          <p className="mt-1 font-display text-[0.6rem] font-bold tracking-[0.2em] uppercase text-ink/50 dark:text-stone-100/50">
            Correct
          </p>
        </div>
        <div className="p-4 text-center sm:p-5">
          <p className="font-mono text-2xl font-bold tabular-nums text-loss sm:text-3xl">
            {stats.incorrect_predictions}
          </p>
          <p className="mt-1 font-display text-[0.6rem] font-bold tracking-[0.2em] uppercase text-ink/50 dark:text-stone-100/50">
            Incorrect
          </p>
        </div>
      </div>

      <p className="mt-3 text-right text-xs text-ink/40 dark:text-stone-100/40">
        Last updated {formatDate(stats.last_updated)}
      </p>
    </div>
  )
}
