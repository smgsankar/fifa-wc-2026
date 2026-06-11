import type { H2H, Team } from '../../lib/types'
import { formatDate } from '../../lib/format'

interface H2HPanelProps {
  h2h: H2H | null
  teamA: Team
  teamB: Team
}

export default function H2HPanel({ h2h, teamA, teamB }: H2HPanelProps) {
  const total = h2h ? h2h.team_a_wins + h2h.team_b_wins + h2h.draws : 0

  if (!h2h || total === 0) {
    return (
      <p className="border border-dashed border-ink/20 p-6 text-sm text-ink/50 dark:border-stone-100/20 dark:text-stone-100/50">
        No previous meetings between {teamA.name} and {teamB.name}.
      </p>
    )
  }

  return (
    <div className="border border-ink/20 bg-white p-5 sm:p-8 dark:border-stone-100/20 dark:bg-night-soft">
      <div className="flex items-baseline justify-between gap-2 font-mono text-sm font-semibold">
        <span className="text-pitch-700 dark:text-pitch-300">
          {teamA.country_code} {h2h.team_a_wins}
        </span>
        <span className="text-ink/50 dark:text-stone-100/50">Draws {h2h.draws}</span>
        <span>
          {teamB.country_code} {h2h.team_b_wins}
        </span>
      </div>

      <div className="mt-2 flex h-2.5 w-full overflow-hidden rounded-full">
        <div className="bg-pitch-600" style={{ width: `${(h2h.team_a_wins / total) * 100}%` }} />
        <div className="bg-stone-300 dark:bg-stone-700" style={{ width: `${(h2h.draws / total) * 100}%` }} />
        <div className="bg-ink dark:bg-stone-100" style={{ width: `${(h2h.team_b_wins / total) * 100}%` }} />
      </div>

      <p className="mt-4 text-xs text-ink/50 dark:text-stone-100/50">
        {total} previous {total === 1 ? 'meeting' : 'meetings'}
        {h2h.last_match && (
          <>
            {' '}
            · Last met {formatDate(h2h.last_match.date)}
            {h2h.last_match.score && ` (${h2h.last_match.score})`}
          </>
        )}
      </p>
    </div>
  )
}
