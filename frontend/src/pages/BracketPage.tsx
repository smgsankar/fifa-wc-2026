import { Link } from 'react-router-dom'
import { getAllMatches } from '../lib/api'
import { useFetch } from '../hooks/useFetch'
import type { MatchListItem, Team } from '../lib/types'
import { formatDate, formatPercent, matchWinner, stageLabel } from '../lib/format'
import SectionHeading from '../components/ui/SectionHeading'
import ErrorState from '../components/ui/ErrorState'
import { RowsSkeleton } from '../components/ui/Skeleton'

const FINAL_ID = 104
const THIRD_PLACE_ID = 103

/* Which two matches feed each knockout fixture (team_a's source first).
   Static for this tournament — mirrors seed_data/knockout_schedule.csv. */
const FEEDS: Record<number, [number, number]> = {
  89: [73, 76],
  90: [75, 78],
  91: [74, 77],
  92: [79, 80],
  93: [84, 83],
  94: [82, 81],
  95: [87, 86],
  96: [85, 88],
  97: [90, 89],
  98: [93, 94],
  99: [91, 92],
  100: [95, 96],
  101: [97, 98],
  102: [99, 100],
  [THIRD_PLACE_ID]: [101, 102],
  [FINAL_ID]: [101, 102],
}

/* Columns from the round of 32 up to the final, ordered so each match sits
   between the two matches that feed it. */
const COLUMNS: number[][] = (() => {
  let columns: number[][] = [[FINAL_ID]]
  for (;;) {
    const previous = columns[0].flatMap((id) => FEEDS[id] ?? [])
    if (previous.length === 0) break
    columns = [previous, ...columns]
  }
  return columns
})()

function predictedFavorite(match: MatchListItem): { team: Team | null; prob: number } | null {
  const p = match.prediction
  if (!p) return null
  const top = Math.max(p.team_a_win_prob, p.team_b_win_prob, p.draw_prob)
  if (top === p.draw_prob) return { team: null, prob: top }
  return { team: top === p.team_a_win_prob ? match.team_a : match.team_b, prob: top }
}

function TeamLine({
  team,
  score,
  pens,
  emphasized,
  dimmed,
}: {
  team: Team
  score: number | null
  pens: number | null
  emphasized: boolean
  dimmed: boolean
}) {
  return (
    <div className={`flex items-center gap-1.5 ${dimmed ? 'opacity-40' : ''}`}>
      <span className="w-10 shrink-0 font-mono text-[0.6rem] font-semibold text-ink/60 dark:text-stone-100/60">
        {team.country_code}
      </span>
      <span
        className={`min-w-0 flex-1 truncate font-display text-xs tracking-tight uppercase ${
          emphasized ? 'font-black text-pitch-700 dark:text-pitch-300' : 'font-semibold'
        } ${team.is_placeholder ? 'text-ink/45 dark:text-stone-100/45' : ''}`}
      >
        {team.name}
      </span>
      {score !== null && (
        <span className="shrink-0 font-mono text-xs font-bold tabular-nums">
          {score}
          {pens !== null && (
            <span className="font-normal text-ink/50 dark:text-stone-100/50"> ({pens})</span>
          )}
        </span>
      )}
    </div>
  )
}

function BracketMatch({ match }: { match: MatchListItem }) {
  const completed = match.status === 'completed'
  const hasScore = completed && match.actual_score_a !== null && match.actual_score_b !== null
  const winner = matchWinner(match)
  const favorite = !completed ? predictedFavorite(match) : null

  return (
    <Link
      to={`/matches/${match.match_id}`}
      className="block w-48 border border-ink/20 bg-white px-3 py-2 transition-all hover:border-ink hover:shadow-[3px_3px_0_0_var(--color-pitch-600)] dark:border-stone-100/20 dark:bg-night-soft dark:hover:border-stone-100/60 dark:hover:shadow-[3px_3px_0_0_var(--color-pitch-400)]"
    >
      <div className="space-y-1">
        <TeamLine
          team={match.team_a}
          score={hasScore ? match.actual_score_a : null}
          pens={match.penalty_score_a}
          emphasized={winner?.id === match.team_a.id}
          dimmed={winner !== null && winner.id !== match.team_a.id}
        />
        <TeamLine
          team={match.team_b}
          score={hasScore ? match.actual_score_b : null}
          pens={match.penalty_score_b}
          emphasized={winner?.id === match.team_b.id}
          dimmed={winner !== null && winner.id !== match.team_b.id}
        />
      </div>
      <p className="mt-1.5 flex items-center justify-between text-[0.6rem] tracking-wide text-ink/40 dark:text-stone-100/40">
        <span>{completed ? 'FT' : formatDate(match.match_date)}</span>
        {favorite?.team && (
          <span className="font-mono font-semibold text-ink/60 dark:text-stone-100/60">
            {favorite.team.country_code} {formatPercent(favorite.prob)}
          </span>
        )}
        {match.status === 'live' && (
          <span className="font-display font-bold text-loss uppercase">Live</span>
        )}
      </p>
    </Link>
  )
}

export default function BracketPage() {
  const { data, loading, error, retry } = useFetch(getAllMatches)

  if (loading) return <RowsSkeleton count={10} />
  if (error) return <ErrorState error={error} onRetry={retry} />

  const byId = new Map<number, MatchListItem>()
  for (const m of data ?? []) byId.set(m.match_id, m)
  const thirdPlace = byId.get(THIRD_PLACE_ID)

  return (
    <div>
      <SectionHeading kicker="Road to the final" title="Knockout Bracket" />

      <div className="overflow-x-auto pb-4">
        <div className="flex min-w-[64rem] gap-4">
          {COLUMNS.map((ids) => {
            const first = byId.get(ids[0])
            return (
              <div key={ids[0]} className="flex w-48 shrink-0 flex-col">
                <h3 className="mb-3 font-display text-[0.65rem] font-bold tracking-[0.2em] uppercase text-ink/50 dark:text-stone-100/50">
                  {first ? stageLabel(first.stage) : ''}
                </h3>
                <div className="flex min-h-[68rem] flex-1 flex-col">
                  {ids.map((id) => {
                    const match = byId.get(id)
                    return (
                      <div key={id} className="flex flex-1 items-center">
                        {match ? <BracketMatch match={match} /> : null}
                      </div>
                    )
                  })}
                </div>
              </div>
            )
          })}
        </div>
      </div>

      {thirdPlace && (
        <div className="mt-8">
          <h3 className="mb-3 font-display text-[0.65rem] font-bold tracking-[0.2em] uppercase text-ink/50 dark:text-stone-100/50">
            {stageLabel(thirdPlace.stage)}
          </h3>
          <BracketMatch match={thirdPlace} />
        </div>
      )}
    </div>
  )
}
