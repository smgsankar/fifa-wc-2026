import type { FormResult, MatchListItem, Team } from './types'

const kickoffFmt = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
})

const dateFmt = new Intl.DateTimeFormat(undefined, {
  day: 'numeric',
  month: 'short',
  year: 'numeric',
})

const dayHeadingFmt = new Intl.DateTimeFormat(undefined, {
  weekday: 'long',
  month: 'long',
  day: 'numeric',
})

const timeFmt = new Intl.DateTimeFormat(undefined, {
  hour: 'numeric',
  minute: '2-digit',
  hour12: true,
})

export function formatKickoff(iso: string): string {
  return kickoffFmt.format(new Date(iso))
}

export function formatDate(iso: string): string {
  return dateFmt.format(new Date(iso))
}

export function formatDayHeading(iso: string): string {
  return dayHeadingFmt.format(new Date(iso))
}

export function formatTime(iso: string): string {
  return timeFmt.format(new Date(iso))
}

/** Local calendar day (YYYY-MM-DD) — used to group and filter fixtures by date. */
export function dayKey(iso: string): string {
  const d = new Date(iso)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

export function formatVenue(stadium: string | null, city: string | null): string | null {
  if (!stadium && !city) return null
  if (stadium && city) return `${stadium}, ${city}`
  return stadium ?? city
}

export function formatPercent(p: number): string {
  return `${Math.round(p * 100)}%`
}

const STAGE_LABELS: Record<string, string> = {
  group: 'Group Stage',
  round32: 'Round of 32',
  round16: 'Round of 16',
  quarterfinal: 'Quarter-final',
  semifinal: 'Semi-final',
  third_place: 'Third Place',
  final: 'Final',
}

export function stageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage
}

/** Short marker for results that went beyond regular time, e.g. "a.e.t." or "3–4 pens". */
export function resultAnnotation(
  match: Pick<MatchListItem, 'decided_by' | 'penalty_score_a' | 'penalty_score_b'>,
): string | null {
  if (match.decided_by === 'penalties') {
    return match.penalty_score_a !== null && match.penalty_score_b !== null
      ? `${match.penalty_score_a}–${match.penalty_score_b} pens`
      : 'pens'
  }
  if (match.decided_by === 'extra_time') return 'a.e.t.'
  return null
}

/** The team that advanced from a completed match: score first, shootout as tiebreak. */
export function matchWinner(match: MatchListItem): Team | null {
  if (match.status !== 'completed' || match.actual_score_a === null || match.actual_score_b === null)
    return null
  if (match.actual_score_a > match.actual_score_b) return match.team_a
  if (match.actual_score_b > match.actual_score_a) return match.team_b
  if (match.penalty_score_a !== null && match.penalty_score_b !== null) {
    if (match.penalty_score_a > match.penalty_score_b) return match.team_a
    if (match.penalty_score_b > match.penalty_score_a) return match.team_b
  }
  return null
}

const RESULT_LABELS: Record<FormResult, string> = {
  W: 'Win',
  D: 'Draw',
  L: 'Loss',
}

export function resultLabel(result: FormResult): string {
  return RESULT_LABELS[result] ?? result
}
