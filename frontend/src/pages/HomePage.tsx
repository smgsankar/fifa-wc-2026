import { getModelStats, getNext4 } from '../lib/api'
import { useFetch } from '../hooks/useFetch'
import HeroMatchCard from '../components/match/HeroMatchCard'
import MatchCard from '../components/match/MatchCard'
import ModelStatsSection from '../components/stats/ModelStatsSection'
import SectionHeading from '../components/ui/SectionHeading'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import { CardSkeleton, HeroSkeleton, StatsSkeleton } from '../components/ui/Skeleton'

export default function HomePage() {
  const matches = useFetch(getNext4)
  const stats = useFetch(getModelStats)

  return (
    <div className="space-y-14">
      <section>
        {matches.loading ? (
          <>
            <HeroSkeleton />
            <div className="mt-8 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <CardSkeleton />
              <CardSkeleton />
              <CardSkeleton />
            </div>
          </>
        ) : matches.error ? (
          <ErrorState error={matches.error} onRetry={matches.retry} />
        ) : !matches.data || matches.data.length === 0 ? (
          <EmptyState
            title="No upcoming matches"
            message="The tournament schedule is empty — check back once fixtures are announced."
          />
        ) : (
          <>
            <HeroMatchCard match={matches.data[0]} />
            {matches.data.length > 1 && (
              <div className="mt-10">
                <SectionHeading kicker="On the horizon" title="Up Next" />
                <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
                  {matches.data.slice(1, 4).map((m) => (
                    <MatchCard key={m.match_id} match={m} />
                  ))}
                </div>
              </div>
            )}
          </>
        )}
      </section>

      <section>
        <SectionHeading kicker="How we're doing" title="Model Performance" />
        {stats.loading ? (
          <StatsSkeleton />
        ) : stats.error ? (
          <ErrorState error={stats.error} onRetry={stats.retry} title="Stats unavailable" />
        ) : stats.data ? (
          <ModelStatsSection stats={stats.data} />
        ) : null}
      </section>
    </div>
  )
}
