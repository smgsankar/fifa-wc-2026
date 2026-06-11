import type { Prediction, Team } from '../../lib/types'
import { formatPercent } from '../../lib/format'

interface ProbabilityBarProps {
  prediction: Prediction
  teamA: Team
  teamB: Team
  size?: 'sm' | 'md'
  showConfidence?: boolean
}

/** Three-segment win/draw/win probability bar: team A in pitch green, draw neutral, team B in ink. */
export default function ProbabilityBar({
  prediction,
  teamA,
  teamB,
  size = 'md',
  showConfidence = false,
}: ProbabilityBarProps) {
  const { team_a_win_prob: a, draw_prob: draw, team_b_win_prob: b } = prediction
  const labelClass =
    size === 'sm'
      ? 'font-mono text-[0.65rem] font-semibold'
      : 'font-mono text-xs font-semibold sm:text-sm'

  return (
    <div>
      <div className={`flex items-baseline justify-between gap-2 ${labelClass}`}>
        <span className="text-pitch-700 dark:text-pitch-300">
          {teamA.country_code} {formatPercent(a)}
        </span>
        <span className="text-ink/50 dark:text-stone-100/50">Draw {formatPercent(draw)}</span>
        <span>
          {teamB.country_code} {formatPercent(b)}
        </span>
      </div>
      <div
        className={`mt-1.5 flex w-full overflow-hidden rounded-full ${size === 'sm' ? 'h-1.5' : 'h-2.5'}`}
        role="img"
        aria-label={`${teamA.name} ${formatPercent(a)}, draw ${formatPercent(draw)}, ${teamB.name} ${formatPercent(b)}`}
      >
        <div className="bg-pitch-600" style={{ width: `${a * 100}%` }} />
        <div className="bg-stone-300 dark:bg-stone-700" style={{ width: `${draw * 100}%` }} />
        <div className="bg-ink dark:bg-stone-100" style={{ width: `${b * 100}%` }} />
      </div>
      {showConfidence && (
        <p className="mt-2 text-right font-display text-[0.65rem] font-semibold tracking-[0.15em] uppercase text-ink/50 dark:text-stone-100/50">
          Model confidence {formatPercent(prediction.confidence)}
        </p>
      )}
    </div>
  )
}
