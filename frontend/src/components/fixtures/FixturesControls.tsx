import type { Team } from '../../lib/types'
import { stageLabel } from '../../lib/format'

export interface FixtureFilters {
  status: string
  team: string
  stage: string
  date: string
  sort: string
}

interface FixturesControlsProps {
  filters: FixtureFilters
  onChange: (key: keyof FixtureFilters, value: string) => void
  teams: Team[]
  stages: string[]
}

const fieldClass =
  'w-full border border-ink/25 bg-white px-3 py-2 text-sm text-ink focus:border-pitch-600 focus:outline-none dark:border-stone-100/25 dark:bg-night-soft dark:text-stone-100 dark:focus:border-pitch-300'

function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1 block font-display text-[0.6rem] font-bold tracking-[0.25em] uppercase text-ink/50 dark:text-stone-100/50">
        {label}
      </span>
      {children}
    </label>
  )
}

export default function FixturesControls({ filters, onChange, teams, stages }: FixturesControlsProps) {
  return (
    <div className="grid grid-cols-2 gap-3 border border-ink/20 bg-white p-4 sm:grid-cols-3 lg:grid-cols-5 dark:border-stone-100/20 dark:bg-night-soft">
      <Field label="Status">
        <select
          className={fieldClass}
          value={filters.status}
          onChange={(e) => onChange('status', e.target.value)}
        >
          <option value="all">All</option>
          <option value="pending">Upcoming</option>
          <option value="live">Live</option>
          <option value="completed">Completed</option>
        </select>
      </Field>

      <Field label="Team">
        <select
          className={fieldClass}
          value={filters.team}
          onChange={(e) => onChange('team', e.target.value)}
        >
          <option value="all">All teams</option>
          {teams.map((t) => (
            <option key={t.id} value={String(t.id)}>
              {t.name}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Stage">
        <select
          className={fieldClass}
          value={filters.stage}
          onChange={(e) => onChange('stage', e.target.value)}
        >
          <option value="all">All stages</option>
          {stages.map((s) => (
            <option key={s} value={s}>
              {stageLabel(s)}
            </option>
          ))}
        </select>
      </Field>

      <Field label="Date">
        <input
          type="date"
          className={fieldClass}
          value={filters.date}
          onChange={(e) => onChange('date', e.target.value)}
        />
      </Field>

      <Field label="Sort by">
        <select
          className={fieldClass}
          value={filters.sort}
          onChange={(e) => onChange('sort', e.target.value)}
        >
          <option value="date-asc">Date · earliest first</option>
          <option value="date-desc">Date · latest first</option>
          <option value="team">Team · A to Z</option>
          <option value="accuracy">Prediction accuracy</option>
        </select>
      </Field>
    </div>
  )
}
