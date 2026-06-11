/** Prediction verdict for completed matches; renders nothing while the result is pending. */
export default function CorrectBadge({ correct }: { correct: boolean | null }) {
  if (correct === null) return null

  return correct ? (
    <span className="inline-flex items-center gap-1 font-display text-[0.65rem] font-bold tracking-[0.15em] uppercase text-win dark:text-pitch-300">
      <span aria-hidden>✓</span> Correct
    </span>
  ) : (
    <span className="inline-flex items-center gap-1 font-display text-[0.65rem] font-bold tracking-[0.15em] uppercase text-loss">
      <span aria-hidden>✗</span> Incorrect
    </span>
  )
}
