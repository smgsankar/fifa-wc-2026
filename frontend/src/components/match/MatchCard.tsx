import { Link } from 'react-router-dom'
import type { MatchSummary } from '../../lib/types'
import { formatKickoff, stageLabel } from '../../lib/format'
import TeamLogo from '../ui/TeamLogo'
import ProbabilityBar from './ProbabilityBar'

export default function MatchCard({ match }: { match: MatchSummary }) {
  return (
    <Link
      to={`/matches/${match.match_id}`}
      className="block border border-ink/20 bg-white p-5 transition-all hover:border-ink hover:shadow-[4px_4px_0_0_var(--color-pitch-600)] dark:border-stone-100/20 dark:bg-night-soft dark:hover:border-stone-100/60 dark:hover:shadow-[4px_4px_0_0_var(--color-pitch-400)]"
    >
      <p className="font-display text-[0.6rem] font-bold tracking-[0.25em] uppercase text-ink/50 dark:text-stone-100/50">
        {stageLabel(match.stage)} · {formatKickoff(match.match_date)}
      </p>

      <div className="mt-4 space-y-3">
        {[match.team_a, match.team_b].map((team) => (
          <div key={team.id} className="flex items-center gap-3">
            <TeamLogo team={team} className="size-9" fallbackTextClass="text-[0.6rem]" />
            <span className="font-display text-base font-bold tracking-tight uppercase">
              {team.name}
            </span>
          </div>
        ))}
      </div>

      {match.prediction && (
        <div className="mt-5">
          <ProbabilityBar
            prediction={match.prediction}
            teamA={match.team_a}
            teamB={match.team_b}
            size="sm"
          />
        </div>
      )}
    </Link>
  )
}
