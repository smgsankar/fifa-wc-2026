import { Outlet } from 'react-router-dom'
import Navbar from './Navbar'

export default function Layout() {
  return (
    <div className="flex min-h-screen flex-col">
      <Navbar />
      <main className="mx-auto w-full max-w-6xl flex-1 px-4 pt-8 pb-16 sm:px-6">
        <Outlet />
      </main>
      <footer className="border-t border-ink/15 dark:border-stone-100/15">
        <div className="mx-auto flex w-full max-w-6xl items-center justify-between px-4 py-5 text-xs text-ink/50 sm:px-6 dark:text-stone-100/50">
          <p className="font-display font-semibold tracking-widest uppercase">WC26 Predictor</p>
          <p>Predictions are model output, not betting advice.</p>
        </div>
      </footer>
    </div>
  )
}
