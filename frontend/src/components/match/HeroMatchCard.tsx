import { Link } from 'react-router-dom'
import type { MatchSummary } from '../../lib/types'
import { formatKickoff, formatVenue, stageLabel } from '../../lib/format'
import TeamLogo from '../ui/TeamLogo'
import StatusBadge from '../ui/StatusBadge'
import ProbabilityBar from './ProbabilityBar'
import CountdownTimer from './CountdownTimer'

export default function HeroMatchCard({ match }: { match: MatchSummary }) {
  const venue = formatVenue(match.stadium, match.city)
  return (
    <Link
      to={`/matches/${match.match_id}`}
      className="group block border-2 border-ink bg-white transition-shadow hover:shadow-[6px_6px_0_0_var(--color-pitch-600)] dark:border-stone-100/80 dark:bg-night-soft dark:hover:shadow-[6px_6px_0_0_var(--color-pitch-400)]"
    >
      <div className="flex items-center justify-between gap-3 border-b border-ink/15 px-5 py-3 sm:px-8 dark:border-stone-100/15">
        <p className="font-display text-[0.65rem] font-bold tracking-[0.3em] uppercase text-pitch-600 dark:text-pitch-300">
          {match.status === 'live' ? 'Live Now' : 'Next Match'} · {stageLabel(match.stage)}
        </p>
        {match.status !== 'live' && <StatusBadge status={match.status} />}
      </div>

      <div className="px-5 py-8 sm:px-8 sm:py-10">
        <div className="flex items-start justify-between gap-4 sm:gap-8">
          <div className="flex flex-1 flex-col items-center gap-3 text-center">
            <TeamLogo team={match.team_a} className="size-16 sm:size-24" fallbackTextClass="text-lg sm:text-2xl" />
            <div>
              <p className="font-display text-xl leading-tight font-black tracking-tight uppercase font-stretch-110% sm:text-3xl">
                {match.team_a.name}
              </p>
              <p className="mt-1 font-mono text-xs text-ink/50 dark:text-stone-100/50">
                {match.team_a.country_code}
              </p>
            </div>
          </div>

          <p className="flex h-16 items-center font-display text-sm font-black tracking-[0.3em] uppercase text-ink/30 sm:h-24 dark:text-stone-100/30">
            VS
          </p>

          <div className="flex flex-1 flex-col items-center gap-3 text-center">
            <TeamLogo team={match.team_b} className="size-16 sm:size-24" fallbackTextClass="text-lg sm:text-2xl" />
            <div>
              <p className="font-display text-xl leading-tight font-black tracking-tight uppercase font-stretch-110% sm:text-3xl">
                {match.team_b.name}
              </p>
              <p className="mt-1 font-mono text-xs text-ink/50 dark:text-stone-100/50">
                {match.team_b.country_code}
              </p>
            </div>
          </div>
        </div>

        <p className="mt-8 text-center text-sm font-medium text-ink/60 dark:text-stone-100/60">
          {formatKickoff(match.match_date)}
        </p>
        {venue && (
          <p className="mt-1 text-center text-xs tracking-wide text-ink/40 dark:text-stone-100/40">
            {venue}
          </p>
        )}

        <div className="mt-5">
          <CountdownTimer targetIso={match.match_date} status={match.status} />
        </div>

        {match.prediction && (
          <div className="mx-auto mt-8 max-w-xl">
            <ProbabilityBar
              prediction={match.prediction}
              teamA={match.team_a}
              teamB={match.team_b}
              showConfidence
            />
          </div>
        )}
      </div>
    </Link>
  )
}
