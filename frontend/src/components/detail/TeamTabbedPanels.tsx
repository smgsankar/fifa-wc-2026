import { useState, type ReactNode } from 'react'
import type { TeamDetail } from '../../lib/types'
import TeamLogo from '../ui/TeamLogo'

/** Two team panels side by side on large screens; below that, a tab
 * switcher showing one team at a time instead of a long stacked scroll. */
export default function TeamTabbedPanels({
  teamA,
  teamB,
  children,
}: {
  teamA: TeamDetail
  teamB: TeamDetail
  children: (team: TeamDetail) => ReactNode
}) {
  const [selectedId, setSelectedId] = useState(teamA.id)
  const selected = selectedId === teamB.id ? teamB : teamA

  return (
    <>
      <div className="lg:hidden">
        <div className="mb-4 grid grid-cols-2 border border-ink/20 dark:border-stone-100/20">
          {[teamA, teamB].map((team) => {
            const active = team.id === selected.id
            return (
              <button
                key={team.id}
                type="button"
                aria-pressed={active}
                onClick={() => setSelectedId(team.id)}
                className={`flex min-w-0 items-center justify-center gap-2 px-3 py-2.5 font-display text-xs font-bold tracking-[0.15em] uppercase transition-colors ${
                  active
                    ? 'bg-ink text-paper dark:bg-stone-100 dark:text-night'
                    : 'text-ink/60 hover:text-ink dark:text-stone-100/60 dark:hover:text-stone-100'
                }`}
              >
                <TeamLogo team={team} className="size-5 shrink-0" fallbackTextClass="text-[0.5rem]" />
                <span className="truncate">{team.name}</span>
              </button>
            )
          })}
        </div>
        {children(selected)}
      </div>

      <div className="hidden gap-4 lg:grid lg:grid-cols-2">
        {children(teamA)}
        {children(teamB)}
      </div>
    </>
  )
}
