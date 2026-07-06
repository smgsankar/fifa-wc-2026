import { useEffect, useMemo, useRef } from 'react'
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

const STAGE_ORDER = [
  'group',
  'round32',
  'round16',
  'quarterfinal',
  'semifinal',
  'third_place',
  'final',
]

function applyFilters(matches: MatchListItem[], f: FixtureFilters): MatchListItem[] {
  const result = matches.filter((m) => {
    if (f.status !== 'all' && m.status !== f.status) return false
    if (f.team !== 'all' && String(m.team_a.id) !== f.team && String(m.team_b.id) !== f.team)
      return false
    if (f.stage !== 'all' && m.stage !== f.stage) return false
    const day = dayKey(m.match_date)
    if (f.from && day < f.from) return false
    if (f.to && day > f.to) return false
    return true
  })

  const byDate = (a: MatchListItem, b: MatchListItem) =>
    new Date(a.match_date).getTime() - new Date(b.match_date).getTime()

  return f.sort === 'date-desc' ? result.sort((a, b) => byDate(b, a)) : result.sort(byDate)
}

export default function FixturesPage() {
  const { data, loading, error, retry } = useFetch(getAllMatches)
  const [searchParams, setSearchParams] = useSearchParams()

  const filters: FixtureFilters = useMemo(
    () => ({
      status: searchParams.get('status') ?? 'all',
      team: searchParams.get('team') ?? 'all',
      stage: searchParams.get('stage') ?? 'all',
      from: searchParams.get('from') ?? '',
      to: searchParams.get('to') ?? '',
      sort: searchParams.get('sort') ?? 'date-asc',
    }),
    [searchParams],
  )

  const hasActiveFilters =
    filters.status !== 'all' ||
    filters.team !== 'all' ||
    filters.stage !== 'all' ||
    !!filters.from ||
    !!filters.to

  /* Apply all entries in one update — consecutive setSearchParams calls in the
     same tick would each start from the pre-navigation params and clobber
     each other (the range picker sets `from` and `to` together). */
  const setFilters = (updates: Partial<FixtureFilters>) => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        for (const [key, value] of Object.entries(updates)) {
          const isDefault =
            value === 'all' || value === '' || (key === 'sort' && value === 'date-asc')
          if (isDefault) next.delete(key)
          else next.set(key, value)
        }
        return next
      },
      { replace: true },
    )
  }

  const clearFilters = () => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        for (const key of ['status', 'team', 'stage', 'from', 'to']) next.delete(key)
        return next
      },
      { replace: true },
    )
  }

  const teams = useMemo(() => {
    const byId = new Map<number, Team>()
    for (const m of data ?? []) {
      // Undecided knockout slots ("Winner SF 1") are not filterable teams.
      if (!m.team_a.is_placeholder) byId.set(m.team_a.id, m.team_a)
      if (!m.team_b.is_placeholder) byId.set(m.team_b.id, m.team_b)
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

  /* On first render with data, jump to "now" in the schedule: the most recent
     match rather than the top of the list. Centering it keeps the boundary
     visible — last result just played on one side, next kickoff on the other.
     Runs once; later filter/sort changes don't yank the scroll position. */
  const autoScrolled = useRef(false)
  useEffect(() => {
    if (autoScrolled.current || filtered.length === 0) return
    autoScrolled.current = true
    const completed = filtered.filter((m) => m.status === 'completed')
    if (completed.length === 0) return // nothing played yet — stay at the top
    const mostRecent = completed.reduce((latest, m) =>
      new Date(m.match_date) > new Date(latest.match_date) ? m : latest,
    )
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    document
      .getElementById(`match-${mostRecent.match_id}`)
      ?.scrollIntoView({ block: 'center', behavior: reducedMotion ? 'auto' : 'smooth' })
  }, [filtered])

  /* Group under date headings — both sorts are chronological. */
  const groups = useMemo(() => {
    const map = new Map<string, MatchListItem[]>()
    for (const m of filtered) {
      const key = dayKey(m.match_date)
      const list = map.get(key)
      if (list) list.push(m)
      else map.set(key, [m])
    }
    return [...map.entries()]
  }, [filtered])

  return (
    <div>
      <SectionHeading kicker="All matches" title="Fixtures & Results" />

      {loading ? (
        <RowsSkeleton count={10} />
      ) : error ? (
        <ErrorState error={error} onRetry={retry} />
      ) : (
        <>
          <FixturesControls filters={filters} onChange={setFilters} teams={teams} stages={stages} />

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
          ) : (
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
          )}
        </>
      )}
    </div>
  )
}
