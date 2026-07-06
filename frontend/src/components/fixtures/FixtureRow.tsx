import { Link } from 'react-router-dom'
import type { MatchListItem, Team } from '../../lib/types'
import { formatPercent, formatTime, formatVenue, resultAnnotation, stageLabel } from '../../lib/format'
import TeamLogo from '../ui/TeamLogo'
import StatusBadge from '../ui/StatusBadge'
import CorrectBadge from '../ui/CorrectBadge'

function predictedFavorite(match: MatchListItem): { team: Team | null; prob: number } | null {
  const p = match.prediction
  if (!p) return null
  const top = Math.max(p.team_a_win_prob, p.team_b_win_prob, p.draw_prob)
  if (top === p.draw_prob) return { team: null, prob: p.draw_prob }
  return { team: top === p.team_a_win_prob ? match.team_a : match.team_b, prob: top }
}

/* Undecided knockout slots ("Winner SF 1") render dimmed until resolved. */
const placeholderClass = (team: Team) =>
  team.is_placeholder ? 'text-ink/45 dark:text-stone-100/45' : ''

function TeamSide({ team, align }: { team: Team; align: 'left' | 'right' }) {
  return (
    <div
      className={`flex min-w-0 flex-1 items-center gap-2.5 ${align === 'right' ? 'flex-row-reverse' : ''}`}
    >
      <TeamLogo team={team} className="size-8 shrink-0" fallbackTextClass="text-[0.55rem]" />
      <span
        className={`truncate font-display text-base font-bold tracking-tight uppercase ${placeholderClass(team)}`}
      >
        {team.name}
      </span>
    </div>
  )
}

function TeamRow({ team, score }: { team: Team; score: number | null }) {
  return (
    <div className="flex items-center gap-3">
      <TeamLogo team={team} className="size-9 shrink-0" fallbackTextClass="text-[0.6rem]" />
      <span
        className={`min-w-0 flex-1 truncate font-display text-base font-bold tracking-tight uppercase ${placeholderClass(team)}`}
      >
        {team.name}
      </span>
      {score !== null && (
        <span className="shrink-0 font-mono text-base font-bold tabular-nums">{score}</span>
      )}
    </div>
  )
}

export default function FixtureRow({ match }: { match: MatchListItem }) {
  const completed = match.status === 'completed'
  const hasScore = match.actual_score_a !== null && match.actual_score_b !== null
  const annotation = completed ? resultAnnotation(match) : null
  const favorite = predictedFavorite(match)
  const venue = formatVenue(match.stadium, match.city)

  return (
    <Link
      id={`match-${match.match_id}`}
      to={`/matches/${match.match_id}`}
      className="flex flex-wrap items-center gap-x-4 gap-y-2 border border-ink/15 bg-white px-4 py-3 transition-all hover:border-ink hover:shadow-[3px_3px_0_0_var(--color-pitch-600)] sm:flex-nowrap dark:border-stone-100/15 dark:bg-night-soft dark:hover:border-stone-100/60 dark:hover:shadow-[3px_3px_0_0_var(--color-pitch-400)]"
    >
      <div className="w-16 shrink-0">
        <p className="font-mono text-xs font-semibold tabular-nums">{formatTime(match.match_date)}</p>
        <p className="mt-0.5 text-[0.6rem] tracking-wide text-ink/40 uppercase dark:text-stone-100/40">
          {stageLabel(match.stage)}
        </p>
      </div>

      <div className="min-w-0 flex-1">
        <div className="space-y-3 sm:hidden">
          <TeamRow team={match.team_a} score={completed && hasScore ? match.actual_score_a : null} />
          <TeamRow team={match.team_b} score={completed && hasScore ? match.actual_score_b : null} />
          {annotation && (
            <p className="text-[0.65rem] tracking-wide text-ink/50 dark:text-stone-100/50">
              {annotation}
            </p>
          )}
        </div>
        <div className="hidden items-center gap-3 sm:flex">
          <TeamSide team={match.team_a} align="right" />
          {completed && hasScore ? (
            <span className="flex shrink-0 flex-col items-center">
              <span className="font-mono text-base font-bold tabular-nums">
                {match.actual_score_a}–{match.actual_score_b}
              </span>
              {annotation && (
                <span className="text-[0.6rem] whitespace-nowrap text-ink/50 dark:text-stone-100/50">
                  {annotation}
                </span>
              )}
            </span>
          ) : (
            <span className="shrink-0 text-xs text-ink/30 dark:text-stone-100/30">v</span>
          )}
          <TeamSide team={match.team_b} align="left" />
        </div>
        {venue && (
          <p className="mt-2 truncate text-[0.65rem] tracking-wide text-ink/40 sm:mt-1 sm:text-center dark:text-stone-100/40">
            {venue}
          </p>
        )}
      </div>

      <div className="flex w-full shrink-0 items-center justify-between gap-3 sm:w-auto sm:justify-end">
        {favorite && (
          <span className="text-xs text-ink/60 dark:text-stone-100/60">
            <span className="font-display text-[0.6rem] font-bold tracking-[0.15em] uppercase text-ink/40 dark:text-stone-100/40">
              Pick{' '}
            </span>
            <span className="font-mono font-semibold">
              {favorite.team ? favorite.team.country_code : 'Draw'} {formatPercent(favorite.prob)}
            </span>
          </span>
        )}
        {completed ? <CorrectBadge correct={match.prediction_correct} /> : <StatusBadge status={match.status} />}
      </div>
    </Link>
  )
}
