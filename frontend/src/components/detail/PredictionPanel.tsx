import type { MatchDetail } from '../../lib/types'
import { formatPercent } from '../../lib/format'
import ProbabilityBar from '../match/ProbabilityBar'
import CorrectBadge from '../ui/CorrectBadge'

function favoriteLine(match: MatchDetail): string {
  const p = match.prediction!
  const top = Math.max(p.team_a_win_prob, p.team_b_win_prob, p.draw_prob)
  if (top === p.draw_prob) return `The model leans toward a draw (${formatPercent(p.draw_prob)})`
  const team = top === p.team_a_win_prob ? match.team_a : match.team_b
  return `The model favors ${team.name} (${formatPercent(top)})`
}

export default function PredictionPanel({ match }: { match: MatchDetail }) {
  if (!match.prediction) {
    return (
      <p className="border border-dashed border-ink/20 p-6 text-sm text-ink/50 dark:border-stone-100/20 dark:text-stone-100/50">
        No prediction available for this match.
      </p>
    )
  }

  return (
    <div className="border border-ink/20 bg-white p-5 sm:p-8 dark:border-stone-100/20 dark:bg-night-soft">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-medium">{favoriteLine(match)}</p>
        <CorrectBadge correct={match.prediction_correct} />
      </div>
      <div className="mt-5">
        <ProbabilityBar
          prediction={match.prediction}
          teamA={match.team_a}
          teamB={match.team_b}
          showConfidence
        />
      </div>
    </div>
  )
}
