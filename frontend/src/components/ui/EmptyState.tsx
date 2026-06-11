import type { ReactNode } from 'react'

interface EmptyStateProps {
  title: string
  message?: string
  action?: ReactNode
}

export default function EmptyState({ title, message, action }: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center border-2 border-dashed border-ink/20 px-6 py-14 text-center dark:border-stone-100/20">
      <p className="font-display text-lg font-bold tracking-wide uppercase">{title}</p>
      {message && <p className="mt-2 max-w-sm text-sm text-ink/60 dark:text-stone-100/60">{message}</p>}
      {action && <div className="mt-6">{action}</div>}
    </div>
  )
}
