import { useMemo } from 'react'
import { useSearchParams } from 'react-router-dom'
import { getAllMatches } from '../lib/api'
import { useFetch } from '../hooks/useFetch'
import type { MatchListItem, Team } from '../lib/types'
import { dayKey, formatDayHeading } from '../lib/format'
import FixturesControls, { type FixtureFilters } from '../components/fixtures/FixturesControls'
import FixtureRow from '../components/fixtures/FixtureRow'
import SectionHeading from '../components/ui/SectionHeading'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import { RowsSkeleton } from '../components/ui/Skeleton'

const STAGE_ORDER = ['group', 'round16', 'quarterfinal', 'semifinal', 'final']

/** Accuracy sort: correct picks first, then misses, then unplayed matches. */
function accuracyRank(m: MatchListItem): number {
  if (m.prediction_correct === true) return 0
  if (m.prediction_correct === false) return 1
  return 2
}

function applyFilters(matches: MatchListItem[], f: FixtureFilters): MatchListItem[] {
  const result = matches.filter((m) => {
    if (f.status !== 'all' && m.status !== f.status) return false
    if (f.team !== 'all' && String(m.team_a.id) !== f.team && String(m.team_b.id) !== f.team)
      return false
    if (f.stage !== 'all' && m.stage !== f.stage) return false
    if (f.date && dayKey(m.match_date) !== f.date) return false
    return true
  })

  const byDate = (a: MatchListItem, b: MatchListItem) =>
    new Date(a.match_date).getTime() - new Date(b.match_date).getTime()

  switch (f.sort) {
    case 'date-desc':
      return result.sort((a, b) => byDate(b, a))
    case 'team':
      return result.sort((a, b) => a.team_a.name.localeCompare(b.team_a.name) || byDate(a, b))
    case 'accuracy':
      return result.sort((a, b) => accuracyRank(a) - accuracyRank(b) || byDate(a, b))
    default:
      return result.sort(byDate)
  }
}

export default function FixturesPage() {
  const { data, loading, error, retry } = useFetch(getAllMatches)
  const [searchParams, setSearchParams] = useSearchParams()

  const filters: FixtureFilters = useMemo(
    () => ({
      status: searchParams.get('status') ?? 'all',
      team: searchParams.get('team') ?? 'all',
      stage: searchParams.get('stage') ?? 'all',
      date: searchParams.get('date') ?? '',
      sort: searchParams.get('sort') ?? 'date-asc',
    }),
    [searchParams],
  )

  const hasActiveFilters =
    filters.status !== 'all' || filters.team !== 'all' || filters.stage !== 'all' || !!filters.date

  const setFilter = (key: keyof FixtureFilters, value: string) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        const isDefault = value === 'all' || value === '' || (key === 'sort' && value === 'date-asc')
        if (isDefault) next.delete(key)
        else next.set(key, value)
        return next
      },
      { replace: true },
    )
  }

  const clearFilters = () => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        for (const key of ['status', 'team', 'stage', 'date']) next.delete(key)
        return next
      },
      { replace: true },
    )
  }

  const teams = useMemo(() => {
    const byId = new Map<number, Team>()
    for (const m of data ?? []) {
      byId.set(m.team_a.id, m.team_a)
      byId.set(m.team_b.id, m.team_b)
    }
    return [...byId.values()].sort((a, b) => a.name.localeCompare(b.name))
  }, [data])

  const stages = useMemo(() => {
    const present = new Set((data ?? []).map((m) => m.stage))
    const ordered = STAGE_ORDER.filter((s) => present.has(s))
    for (const s of present) if (!STAGE_ORDER.includes(s)) ordered.push(s)
    return ordered
  }, [data])

  const filtered = useMemo(() => (data ? applyFilters([...data], filters) : []), [data, filters])

  /* Group under date headings only for chronological sorts. */
  const groups = useMemo(() => {
    if (filters.sort === 'team' || filters.sort === 'accuracy') return null
    const map = new Map<string, MatchListItem[]>()
    for (const m of filtered) {
      const key = dayKey(m.match_date)
      const list = map.get(key)
      if (list) list.push(m)
      else map.set(key, [m])
    }
    return [...map.entries()]
  }, [filtered, filters.sort])

  return (
    <div>
      <SectionHeading kicker="All 64 matches" title="Fixtures & Results" />

      {loading ? (
        <RowsSkeleton count={10} />
      ) : error ? (
        <ErrorState error={error} onRetry={retry} />
      ) : (
        <>
          <FixturesControls filters={filters} onChange={setFilter} teams={teams} stages={stages} />

          <p className="mt-4 mb-3 text-xs text-ink/50 dark:text-stone-100/50">
            Showing {filtered.length} of {data?.length ?? 0} matches
          </p>

          {filtered.length === 0 ? (
            <EmptyState
              title="No matches found"
              message="No fixtures match the current filters."
              action={
                hasActiveFilters ? (
                  <button
                    type="button"
                    onClick={clearFilters}
                    className="border-2 border-ink px-5 py-2 font-display text-xs font-bold tracking-[0.2em] uppercase transition-colors hover:bg-ink hover:text-paper dark:border-stone-100 dark:hover:bg-stone-100 dark:hover:text-night"
                  >
                    Clear filters
                  </button>
                ) : undefined
              }
            />
          ) : groups ? (
            <div className="space-y-8">
              {groups.map(([key, matches]) => (
                <div key={key}>
                  <h3 className="mb-2 font-display text-sm font-bold tracking-[0.15em] uppercase text-ink/60 dark:text-stone-100/60">
                    {formatDayHeading(matches[0].match_date)}
                  </h3>
                  <div className="space-y-2">
                    {matches.map((m) => (
                      <FixtureRow key={m.match_id} match={m} />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-2">
              {filtered.map((m) => (
                <FixtureRow key={m.match_id} match={m} />
              ))}
            </div>
          )}
        </>
      )}
    </div>
  )
}
