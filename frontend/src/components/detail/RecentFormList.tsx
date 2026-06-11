import type { FormResult, TeamDetail } from '../../lib/types'
import { formatDate, resultLabel } from '../../lib/format'

const CHIP_STYLES: Record<FormResult, string> = {
  W: 'bg-win text-white',
  D: 'bg-draw text-white',
  L: 'bg-loss text-white',
}

export default function RecentFormList({ team }: { team: TeamDetail }) {
  return (
    <div className="border border-ink/20 bg-white dark:border-stone-100/20 dark:bg-night-soft">
      <p className="border-b border-ink/15 px-4 py-3 font-display text-sm font-bold tracking-wide uppercase dark:border-stone-100/15">
        {team.name}
      </p>
      {team.recent_form.length === 0 ? (
        <p className="px-4 py-6 text-sm text-ink/50 dark:text-stone-100/50">
          No recent matches on record.
        </p>
      ) : (
        <ul className="divide-y divide-ink/10 dark:divide-stone-100/10">
          {team.recent_form.map((entry, i) => (
            <li key={i} className="flex items-center gap-3 px-4 py-2.5">
              <span
                title={resultLabel(entry.result)}
                className={`flex size-6 shrink-0 items-center justify-center rounded font-display text-xs font-black ${CHIP_STYLES[entry.result] ?? 'bg-stone-400 text-white'}`}
              >
                {entry.result}
              </span>
              <span className="flex-1 truncate text-sm font-medium">vs {entry.opponent}</span>
              <span className="font-mono text-sm font-semibold tabular-nums">{entry.score}</span>
              <span className="w-24 text-right text-xs text-ink/40 dark:text-stone-100/40">
                {formatDate(entry.match_date)}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
