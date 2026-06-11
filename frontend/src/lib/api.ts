import type { MatchDetail, MatchListItem, MatchSummary, ModelStats } from './types'

const BASE_URL = (import.meta.env.VITE_API_BASE_URL as string | undefined)?.replace(/\/$/, '')

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function apiFetch<T>(path: string): Promise<T> {
  if (!BASE_URL) {
    throw new ApiError(0, 'VITE_API_BASE_URL is not configured — see .env.example')
  }

  let res: Response
  try {
    res = await fetch(`${BASE_URL}${path}`)
  } catch {
    throw new ApiError(0, 'Cannot reach the prediction server')
  }

  if (!res.ok) {
    let message = res.statusText || `Request failed (${res.status})`
    try {
      const body = (await res.json()) as { error?: unknown }
      if (typeof body.error === 'string') message = body.error
    } catch {
      /* non-JSON error body — keep default message */
    }
    throw new ApiError(res.status, message)
  }

  return res.json() as Promise<T>
}

export function getNext4(): Promise<MatchSummary[]> {
  return apiFetch<{ upcoming_matches: MatchSummary[] }>('/api/matches/next-4').then(
    (r) => r.upcoming_matches,
  )
}

export function getMatch(matchId: string | number): Promise<MatchDetail> {
  return apiFetch<{ match: MatchDetail }>(`/api/matches/${matchId}`).then((r) => r.match)
}

export function getAllMatches(): Promise<MatchListItem[]> {
  return apiFetch<{ all_matches: MatchListItem[] }>('/api/matches/all').then((r) => r.all_matches)
}

export function getModelStats(): Promise<ModelStats> {
  return apiFetch<{ stats: ModelStats }>('/api/model/stats').then((r) => r.stats)
}
