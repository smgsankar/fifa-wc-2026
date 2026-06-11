interface SectionHeadingProps {
  kicker?: string
  title: string
}

/** Editorial section head: small green kicker, bold expanded title, hairline rule. */
export default function SectionHeading({ kicker, title }: SectionHeadingProps) {
  return (
    <div className="mb-6">
      {kicker && (
        <p className="font-display text-[0.65rem] font-bold tracking-[0.3em] uppercase text-pitch-600 dark:text-pitch-300">
          {kicker}
        </p>
      )}
      <div className="mt-1 flex items-center gap-4">
        <h2 className="font-display text-2xl font-black tracking-tight uppercase font-stretch-110% sm:text-3xl">
          {title}
        </h2>
        <div className="h-px flex-1 bg-ink/20 dark:bg-stone-100/20" />
      </div>
    </div>
  )
}
