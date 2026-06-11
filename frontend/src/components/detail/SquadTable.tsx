import type { SquadPlayer, TeamDetail } from '../../lib/types'

const POSITION_GROUPS: { keys: string[]; label: string }[] = [
  { keys: ['G', 'GK'], label: 'Goalkeepers' },
  { keys: ['D', 'DF'], label: 'Defenders' },
  { keys: ['M', 'MF'], label: 'Midfielders' },
  { keys: ['F', 'FW'], label: 'Forwards' },
]

function groupSquad(squad: SquadPlayer[]) {
  const grouped = POSITION_GROUPS.map((g) => ({
    label: g.label,
    players: squad
      .filter((p) => g.keys.includes(p.position.toUpperCase()))
      .sort((a, b) => a.number - b.number),
  }))
  const known = new Set(POSITION_GROUPS.flatMap((g) => g.keys))
  const other = squad
    .filter((p) => !known.has(p.position.toUpperCase()))
    .sort((a, b) => a.number - b.number)
  if (other.length > 0) grouped.push({ label: 'Other', players: other })
  return grouped.filter((g) => g.players.length > 0)
}

export default function SquadTable({ team }: { team: TeamDetail }) {
  const groups = groupSquad(team.squad)

  return (
    <div className="border border-ink/20 bg-white dark:border-stone-100/20 dark:bg-night-soft">
      <p className="border-b border-ink/15 px-4 py-3 font-display text-sm font-bold tracking-wide uppercase dark:border-stone-100/15">
        {team.name}
      </p>
      {groups.length === 0 ? (
        <p className="px-4 py-6 text-sm text-ink/50 dark:text-stone-100/50">Squad unavailable.</p>
      ) : (
        groups.map((group) => (
          <div key={group.label}>
            <p className="bg-ink/5 px-4 py-1.5 font-display text-[0.6rem] font-bold tracking-[0.25em] uppercase text-ink/50 dark:bg-stone-100/5 dark:text-stone-100/50">
              {group.label}
            </p>
            <ul className="divide-y divide-ink/10 dark:divide-stone-100/10">
              {group.players.map((player) => (
                <li key={player.player_id} className="flex items-center gap-3 px-4 py-2">
                  <span className="w-7 text-right font-mono text-sm font-semibold tabular-nums text-pitch-700 dark:text-pitch-300">
                    {player.number}
                  </span>
                  <span className="text-sm font-medium">{player.name}</span>
                </li>
              ))}
            </ul>
          </div>
        ))
      )}
    </div>
  )
}
