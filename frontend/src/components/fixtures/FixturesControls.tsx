import type { Team } from '../../lib/types'
import { stageLabel } from '../../lib/format'
import Select, { type SelectOption } from '../ui/Select'
import DateRangePicker from '../ui/DateRangePicker'

export interface FixtureFilters {
  status: string
  team: string
  stage: string
  from: string
  to: string
  sort: string
}

interface FixturesControlsProps {
  filters: FixtureFilters
  onChange: (updates: Partial<FixtureFilters>) => void
  teams: Team[]
  stages: string[]
}

const STATUS_OPTIONS: SelectOption[] = [
  { value: 'all', label: 'All' },
  { value: 'pending', label: 'Upcoming' },
  { value: 'live', label: 'Live' },
  { value: 'awaiting_results', label: 'Waiting for results' },
  { value: 'completed', label: 'Completed' },
]

const SORT_OPTIONS: SelectOption[] = [
  { value: 'date-asc', label: 'Earliest first' },
  { value: 'date-desc', label: 'Latest first' },
]

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div>
      <span className="mb-1 block font-display text-[0.6rem] font-bold tracking-[0.25em] uppercase text-ink/50 dark:text-stone-100/50">
        {label}
      </span>
      {children}
    </div>
  )
}

export default function FixturesControls({ filters, onChange, teams, stages }: FixturesControlsProps) {
  const teamOptions: SelectOption[] = [
    { value: 'all', label: 'All teams' },
    ...teams.map((t) => ({ value: String(t.id), label: t.name })),
  ]

  const stageOptions: SelectOption[] = [
    { value: 'all', label: 'All stages' },
    ...stages.map((s) => ({ value: s, label: stageLabel(s) })),
  ]

  return (
    <div className="grid grid-cols-2 gap-3 border border-ink/20 bg-white p-4 sm:grid-cols-3 lg:grid-cols-5 dark:border-stone-100/20 dark:bg-night-soft">
      <Field label="Status">
        <Select
          ariaLabel="Filter by status"
          value={filters.status}
          options={STATUS_OPTIONS}
          onChange={(v) => onChange({ status: v })}
        />
      </Field>

      <Field label="Team">
        <Select
          ariaLabel="Filter by team"
          value={filters.team}
          options={teamOptions}
          onChange={(v) => onChange({ team: v })}
        />
      </Field>

      <Field label="Stage">
        <Select
          ariaLabel="Filter by stage"
          value={filters.stage}
          options={stageOptions}
          onChange={(v) => onChange({ stage: v })}
        />
      </Field>

      <Field label="Dates">
        <DateRangePicker
          ariaLabel="Filter by date range"
          from={filters.from}
          to={filters.to}
          onChange={(from, to) => onChange({ from, to })}
        />
      </Field>

      <Field label="Sort">
        <Select
          ariaLabel="Sort fixtures"
          value={filters.sort}
          options={SORT_OPTIONS}
          onChange={(v) => onChange({ sort: v })}
        />
      </Field>
    </div>
  )
}
