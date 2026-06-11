interface ErrorStateProps {
  error: Error
  onRetry: () => void
  title?: string
}

export default function ErrorState({ error, onRetry, title = 'VAR check failed' }: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center border-2 border-dashed border-ink/20 px-6 py-14 text-center dark:border-stone-100/20">
      <svg
        viewBox="0 0 24 24"
        className="size-8 text-loss"
        fill="none"
        stroke="currentColor"
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden
      >
        <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0Z" />
        <line x1="12" y1="9" x2="12" y2="13" />
        <line x1="12" y1="17" x2="12.01" y2="17" />
      </svg>
      <p className="mt-4 font-display text-lg font-bold tracking-wide uppercase">{title}</p>
      <p className="mt-2 max-w-sm text-sm text-ink/60 dark:text-stone-100/60">{error.message}</p>
      <button
        type="button"
        onClick={onRetry}
        className="mt-6 border-2 border-ink px-5 py-2 font-display text-xs font-bold tracking-[0.2em] uppercase transition-colors hover:bg-ink hover:text-paper dark:border-stone-100 dark:hover:bg-stone-100 dark:hover:text-night"
      >
        Retry
      </button>
    </div>
  )
}
