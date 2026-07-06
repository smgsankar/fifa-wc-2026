import type { MatchDetail } from '../../lib/types'
import { formatKickoff, formatVenue, stageLabel } from '../../lib/format'
import TeamLogo from '../ui/TeamLogo'
import StatusBadge from '../ui/StatusBadge'
import CountdownTimer from '../match/CountdownTimer'

export default function MatchHeader({ match }: { match: MatchDetail }) {
  const completed = match.status === 'completed'
  const hasScore = match.actual_score_a !== null && match.actual_score_b !== null
  const venue = formatVenue(match.stadium, match.city)

  return (
    <div className="border-2 border-ink bg-white dark:border-stone-100/80 dark:bg-night-soft">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-ink/15 px-5 py-3 sm:px-8 dark:border-stone-100/15">
        <p className="font-display text-[0.65rem] font-bold tracking-[0.3em] uppercase text-pitch-600 dark:text-pitch-300">
          {stageLabel(match.stage)} · Match {match.match_id}
        </p>
        {match.status !== 'live' && <StatusBadge status={match.status} />}
      </div>

      <div className="px-5 py-8 sm:px-8 sm:py-10">
        <div className="flex items-start justify-between gap-4 sm:gap-8">
          <div className="flex flex-1 flex-col items-center gap-3 text-center">
            <TeamLogo team={match.team_a} className="size-16 sm:size-20" fallbackTextClass="text-lg sm:text-xl" />
            <p className="font-display text-lg leading-tight font-black tracking-tight uppercase font-stretch-110% sm:text-2xl">
              {match.team_a.name}
            </p>
          </div>

          {completed && hasScore ? (
            <div className="flex h-16 flex-col items-center justify-center sm:h-20">
              <p className="flex items-center font-mono text-5xl font-bold tabular-nums sm:text-6xl">
                {match.actual_score_a}
                <span className="mx-1 text-ink/30 sm:mx-2 dark:text-stone-100/30">–</span>
                {match.actual_score_b}
              </p>
              {match.decided_by === 'penalties' && (
                <p className="mt-1 text-[0.65rem] tracking-wide whitespace-nowrap text-ink/50 dark:text-stone-100/50">
                  {match.penalty_score_a !== null
                    ? `Penalties ${match.penalty_score_a}–${match.penalty_score_b}`
                    : 'Decided on penalties'}
                </p>
              )}
              {match.decided_by === 'extra_time' && (
                <p className="mt-1 text-[0.65rem] tracking-wide whitespace-nowrap text-ink/50 dark:text-stone-100/50">
                  After extra time
                </p>
              )}
            </div>
          ) : (
            <p className="flex h-16 items-center font-display text-sm font-black tracking-[0.3em] uppercase text-ink/30 sm:h-20 dark:text-stone-100/30">
              VS
            </p>
          )}

          <div className="flex flex-1 flex-col items-center gap-3 text-center">
            <TeamLogo team={match.team_b} className="size-16 sm:size-20" fallbackTextClass="text-lg sm:text-xl" />
            <p className="font-display text-lg leading-tight font-black tracking-tight uppercase font-stretch-110% sm:text-2xl">
              {match.team_b.name}
            </p>
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

        {!completed && (
          <div className="mt-5">
            <CountdownTimer targetIso={match.match_date} status={match.status} />
          </div>
        )}
      </div>
    </div>
  )
}
