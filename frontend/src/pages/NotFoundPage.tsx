import { Link } from 'react-router-dom'

export default function NotFoundPage() {
  return (
    <div className="flex flex-col items-center py-20 text-center">
      <p className="font-display text-[7rem] leading-none font-black tracking-tight uppercase font-stretch-125% sm:text-[10rem]">
        404
      </p>
      <p className="mt-2 font-display text-xl font-bold tracking-[0.3em] uppercase text-pitch-600 dark:text-pitch-300">
        Offside
      </p>
      <p className="mt-6 max-w-md text-ink/60 dark:text-stone-100/60">
        The page you're looking for is beyond the last defender. Get back onside.
      </p>
      <Link
        to="/"
        className="mt-8 border-2 border-ink px-6 py-3 font-display text-sm font-bold tracking-[0.2em] uppercase transition-colors hover:bg-ink hover:text-paper dark:border-stone-100 dark:hover:bg-stone-100 dark:hover:text-night"
      >
        Back to kickoff
      </Link>
    </div>
  )
}
