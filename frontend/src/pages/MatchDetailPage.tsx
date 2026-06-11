import { useCallback } from 'react'
import { Link, useParams } from 'react-router-dom'
import { ApiError, getMatch } from '../lib/api'
import { useFetch } from '../hooks/useFetch'
import MatchHeader from '../components/detail/MatchHeader'
import PredictionPanel from '../components/detail/PredictionPanel'
import RecentFormList from '../components/detail/RecentFormList'
import H2HPanel from '../components/detail/H2HPanel'
import SquadTable from '../components/detail/SquadTable'
import SectionHeading from '../components/ui/SectionHeading'
import ErrorState from '../components/ui/ErrorState'
import EmptyState from '../components/ui/EmptyState'
import { HeroSkeleton, RowsSkeleton } from '../components/ui/Skeleton'

export default function MatchDetailPage() {
  const { matchId } = useParams()
  const fetcher = useCallback(() => getMatch(matchId!), [matchId])
  const { data: match, loading, error, retry } = useFetch(fetcher)

  if (loading) {
    return (
      <div className="space-y-8">
        <HeroSkeleton />
        <RowsSkeleton count={6} />
      </div>
    )
  }

  if (error) {
    if (error instanceof ApiError && error.status === 404) {
      return (
        <EmptyState
          title="Match not found"
          message="This match isn't on the tournament schedule."
          action={
            <Link
              to="/fixtures"
              className="border-2 border-ink px-5 py-2 font-display text-xs font-bold tracking-[0.2em] uppercase transition-colors hover:bg-ink hover:text-paper dark:border-stone-100 dark:hover:bg-stone-100 dark:hover:text-night"
            >
              Browse all fixtures
            </Link>
          }
        />
      )
    }
    return <ErrorState error={error} onRetry={retry} />
  }

  if (!match) return null

  return (
    <div className="space-y-12">
      <MatchHeader match={match} />

      <section>
        <SectionHeading kicker="The model's call" title="Prediction" />
        <PredictionPanel match={match} />
      </section>

      <section>
        <SectionHeading kicker="History" title="Head to Head" />
        <H2HPanel h2h={match.h2h} teamA={match.team_a} teamB={match.team_b} />
      </section>

      <section>
        <SectionHeading kicker="Last five matches" title="Recent Form" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <RecentFormList team={match.team_a} />
          <RecentFormList team={match.team_b} />
        </div>
      </section>

      <section>
        <SectionHeading kicker="The rosters" title="Squads" />
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <SquadTable team={match.team_a} />
          <SquadTable team={match.team_b} />
        </div>
      </section>
    </div>
  )
}
