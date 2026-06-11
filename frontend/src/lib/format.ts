import type { FormResult } from './types'

const kickoffFmt = new Intl.DateTimeFormat(undefined, {
  weekday: 'short',
  month: 'short',
  day: 'numeric',
  hour: 'numeric',
  minute: '2-digit',
  timeZoneName: 'short',
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

export function formatPercent(p: number): string {
  return `${Math.round(p * 100)}%`
}

const STAGE_LABELS: Record<string, string> = {
  group: 'Group Stage',
  round16: 'Round of 16',
  quarterfinal: 'Quarter-final',
  semifinal: 'Semi-final',
  final: 'Final',
}

export function stageLabel(stage: string): string {
  return STAGE_LABELS[stage] ?? stage
}

const RESULT_LABELS: Record<FormResult, string> = {
  W: 'Win',
  D: 'Draw',
  L: 'Loss',
}

export function resultLabel(result: FormResult): string {
  return RESULT_LABELS[result] ?? result
}
