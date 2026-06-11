import { useState } from 'react'
import type { Team } from '../../lib/types'

interface TeamLogoProps {
  team: Team
  className?: string
  fallbackTextClass?: string
}

/** Team crest with a country-code fallback for null or broken logo URLs. */
export default function TeamLogo({
  team,
  className = 'size-12',
  fallbackTextClass = 'text-sm',
}: TeamLogoProps) {
  const [failed, setFailed] = useState(false)

  if (!team.logo_url || failed) {
    return (
      <div
        role="img"
        aria-label={team.name}
        className={`${className} flex items-center justify-center rounded-full border-2 border-pitch-600/30 bg-pitch-50 dark:border-pitch-300/30 dark:bg-pitch-950`}
      >
        <span
          className={`${fallbackTextClass} font-display font-black tracking-wide text-pitch-700 dark:text-pitch-300`}
        >
          {team.country_code}
        </span>
      </div>
    )
  }

  return (
    <img
      src={team.logo_url}
      alt={`${team.name} crest`}
      onError={() => setFailed(true)}
      className={`${className} object-contain`}
    />
  )
}
