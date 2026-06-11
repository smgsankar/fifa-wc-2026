import { Link, NavLink } from 'react-router-dom'
import ThemeToggle from './ThemeToggle'

const linkClass = ({ isActive }: { isActive: boolean }) =>
  `font-display text-xs font-semibold tracking-[0.15em] uppercase transition-colors sm:text-sm ${
    isActive
      ? 'text-pitch-600 dark:text-pitch-300'
      : 'text-ink/60 hover:text-ink dark:text-stone-100/60 dark:hover:text-stone-100'
  }`

export default function Navbar() {
  return (
    <header className="sticky top-0 z-40 border-b-2 border-ink bg-paper/95 backdrop-blur dark:border-stone-100/80 dark:bg-night/95">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between gap-4 px-4 py-3 sm:px-6">
        <Link to="/" className="group flex items-baseline gap-2">
          <span className="font-display text-2xl leading-none font-black tracking-tight uppercase font-stretch-125%">
            WC26
          </span>
          <span className="hidden font-display text-xs font-semibold tracking-[0.3em] uppercase text-pitch-600 sm:inline dark:text-pitch-300">
            Predictor
          </span>
        </Link>
        <nav className="flex items-center gap-4 sm:gap-7">
          <NavLink to="/" end className={linkClass}>
            Home
          </NavLink>
          <NavLink to="/fixtures" className={linkClass}>
            Schedule
          </NavLink>
          <ThemeToggle />
        </nav>
      </div>
    </header>
  )
}
