export function Skeleton({ className = '' }: { className?: string }) {
  return <div className={`animate-pulse rounded bg-ink/10 dark:bg-stone-100/10 ${className}`} />
}

export function HeroSkeleton() {
  return (
    <div className="border-2 border-ink/10 p-6 sm:p-10 dark:border-stone-100/10">
      <Skeleton className="mx-auto h-3 w-40" />
      <div className="mt-8 flex items-center justify-between gap-6">
        <div className="flex flex-1 flex-col items-center gap-3">
          <Skeleton className="size-20 rounded-full" />
          <Skeleton className="h-6 w-28" />
        </div>
        <Skeleton className="h-10 w-12" />
        <div className="flex flex-1 flex-col items-center gap-3">
          <Skeleton className="size-20 rounded-full" />
          <Skeleton className="h-6 w-28" />
        </div>
      </div>
      <Skeleton className="mx-auto mt-10 h-4 w-64" />
      <Skeleton className="mt-6 h-8 w-full" />
    </div>
  )
}

export function CardSkeleton() {
  return (
    <div className="border border-ink/10 p-5 dark:border-stone-100/10">
      <Skeleton className="h-3 w-24" />
      <div className="mt-4 flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-4 w-24" />
      </div>
      <div className="mt-3 flex items-center gap-3">
        <Skeleton className="size-9 rounded-full" />
        <Skeleton className="h-4 w-24" />
      </div>
      <Skeleton className="mt-5 h-5 w-full" />
    </div>
  )
}

export function StatsSkeleton() {
  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
      {[0, 1, 2].map((i) => (
        <div key={i} className="border border-ink/10 p-5 dark:border-stone-100/10">
          <Skeleton className="h-3 w-20" />
          <Skeleton className="mt-4 h-10 w-24" />
        </div>
      ))}
    </div>
  )
}

export function RowsSkeleton({ count = 8 }: { count?: number }) {
  return (
    <div className="space-y-px">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="flex items-center gap-4 border border-ink/10 p-4 dark:border-stone-100/10">
          <Skeleton className="size-8 rounded-full" />
          <Skeleton className="h-4 flex-1" />
          <Skeleton className="size-8 rounded-full" />
          <Skeleton className="h-4 w-20" />
        </div>
      ))}
    </div>
  )
}
