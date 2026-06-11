import { useEffect, useRef, useState } from 'react'

interface DateRangePickerProps {
  /** Range bounds as local YYYY-MM-DD, '' for unset. */
  from: string
  to: string
  onChange: (from: string, to: string) => void
  ariaLabel: string
  placeholder?: string
}

const triggerBase =
  'flex w-full items-center justify-between gap-2 border bg-white px-3 py-2 text-left text-sm text-ink transition-[border-color,box-shadow] focus:outline-none focus-visible:border-pitch-600 dark:bg-night-soft dark:text-stone-100 dark:focus-visible:border-pitch-300'
const triggerOpen =
  'border-ink shadow-[3px_3px_0_0_var(--color-pitch-600)] dark:border-stone-100/60 dark:shadow-[3px_3px_0_0_var(--color-pitch-400)]'
const triggerClosed =
  'border-ink/25 hover:border-ink/60 dark:border-stone-100/25 dark:hover:border-stone-100/60'
const footerButton =
  'font-display text-[0.6rem] font-bold tracking-[0.2em] uppercase text-ink/60 transition-colors hover:text-pitch-700 dark:text-stone-100/60 dark:hover:text-pitch-300'
const navButton =
  'flex size-7 items-center justify-center text-ink/60 transition-colors hover:bg-ink/10 hover:text-ink dark:text-stone-100/60 dark:hover:bg-stone-100/10 dark:hover:text-stone-100'

const WEEKDAYS = ['Su', 'Mo', 'Tu', 'We', 'Th', 'Fr', 'Sa']

const dayFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short', year: 'numeric' })
const shortFmt = new Intl.DateTimeFormat(undefined, { day: 'numeric', month: 'short' })
const monthFmt = new Intl.DateTimeFormat(undefined, { month: 'long', year: 'numeric' })

function toISO(d: Date): string {
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  return `${d.getFullYear()}-${month}-${day}`
}

/** Parse YYYY-MM-DD as a local date (new Date(string) would read it as UTC). */
function fromISO(value: string): Date | null {
  const m = /^(\d{4})-(\d{2})-(\d{2})$/.exec(value)
  if (!m) return null
  return new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]))
}

function addMonths(d: Date, delta: number): Date {
  const day = d.getDate()
  const target = new Date(d.getFullYear(), d.getMonth() + delta, 1)
  const clamp = Math.min(day, new Date(target.getFullYear(), target.getMonth() + 1, 0).getDate())
  target.setDate(clamp)
  return target
}

/** Custom range calendar in the editorial theme: first click sets the start,
 *  second sets the end (a click before the start restarts the range). Days in
 *  between get a green wash; hovering previews the range before the end is
 *  fixed. Arrow keys move the focused day, PageUp/Down change month. */
export default function DateRangePicker({
  from,
  to,
  onChange,
  ariaLabel,
  placeholder = 'Any date',
}: DateRangePickerProps) {
  const [open, setOpen] = useState(false)
  const [hovered, setHovered] = useState('')
  const [focused, setFocused] = useState<Date>(() => fromISO(from) ?? new Date())
  const rootRef = useRef<HTMLDivElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)

  const fromDate = fromISO(from)
  const toDate = fromISO(to)
  const today = new Date()

  const openCalendar = () => {
    setFocused(fromDate ?? new Date())
    setHovered('')
    setOpen(true)
  }

  const close = (refocus: boolean) => {
    setOpen(false)
    if (refocus) triggerRef.current?.focus()
  }

  const pick = (d: Date) => {
    const iso = toISO(d)
    if (!from || to || iso < from) {
      onChange(iso, '') // start (or restart) the range; stay open for the end
    } else {
      onChange(from, iso)
      close(true)
    }
  }

  useEffect(() => {
    if (!open) return
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    const onKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setOpen(false)
        triggerRef.current?.focus()
      }
    }
    document.addEventListener('pointerdown', onPointerDown)
    document.addEventListener('keydown', onKeyDown)
    return () => {
      document.removeEventListener('pointerdown', onPointerDown)
      document.removeEventListener('keydown', onKeyDown)
    }
  }, [open])

  /* Keep keyboard focus on the focused day cell as it moves. */
  useEffect(() => {
    if (!open) return
    rootRef.current
      ?.querySelector<HTMLButtonElement>(`[data-date="${toISO(focused)}"]`)
      ?.focus()
  }, [open, focused])

  const onGridKeyDown = (e: React.KeyboardEvent) => {
    const moves: Record<string, () => Date> = {
      ArrowLeft: () => new Date(focused.getFullYear(), focused.getMonth(), focused.getDate() - 1),
      ArrowRight: () => new Date(focused.getFullYear(), focused.getMonth(), focused.getDate() + 1),
      ArrowUp: () => new Date(focused.getFullYear(), focused.getMonth(), focused.getDate() - 7),
      ArrowDown: () => new Date(focused.getFullYear(), focused.getMonth(), focused.getDate() + 7),
      PageUp: () => addMonths(focused, -1),
      PageDown: () => addMonths(focused, 1),
    }
    const move = moves[e.key]
    if (move) {
      e.preventDefault()
      setFocused(move())
    }
  }

  const monthStart = new Date(focused.getFullYear(), focused.getMonth(), 1)
  const daysInMonth = new Date(focused.getFullYear(), focused.getMonth() + 1, 0).getDate()
  const cells: (Date | null)[] = [
    ...Array.from({ length: monthStart.getDay() }, () => null),
    ...Array.from(
      { length: daysInMonth },
      (_, i) => new Date(focused.getFullYear(), focused.getMonth(), i + 1),
    ),
  ]

  /* While only the start is set, a hover past it previews the range end. */
  const rangeEnd = to || (from && hovered >= from ? hovered : '')

  const label =
    fromDate && toDate
      ? `${shortFmt.format(fromDate)} – ${shortFmt.format(toDate)}`
      : fromDate
        ? `From ${shortFmt.format(fromDate)}`
        : ''

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        ref={triggerRef}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => (open ? close(false) : openCalendar())}
        className={`${triggerBase} ${open ? triggerOpen : triggerClosed}`}
      >
        {label ? (
          <span className="truncate font-mono text-xs leading-5 font-semibold tabular-nums">{label}</span>
        ) : (
          <span className="truncate text-ink/40 dark:text-stone-100/40">{placeholder}</span>
        )}
        <svg
          viewBox="0 0 14 14"
          aria-hidden="true"
          className={`size-3.5 shrink-0 ${
            open ? 'text-pitch-600 dark:text-pitch-300' : 'text-ink/40 dark:text-stone-100/40'
          }`}
        >
          <rect x="1" y="2.5" width="12" height="10.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
          <path d="M1 6h12M4.5 0.5v3.5M9.5 0.5v3.5" fill="none" stroke="currentColor" strokeWidth="1.5" />
        </svg>
      </button>

      {open && (
        <div
          role="dialog"
          aria-label={ariaLabel}
          className="absolute right-0 z-30 mt-1.5 w-max border border-ink bg-white p-3 shadow-[4px_4px_0_0_var(--color-pitch-600)] sm:right-auto sm:left-0 dark:border-stone-100/60 dark:bg-night-soft dark:shadow-[4px_4px_0_0_var(--color-pitch-400)]"
        >
          <div className="mb-2 flex items-center justify-between">
            <button
              type="button"
              aria-label="Previous month"
              onClick={() => setFocused(addMonths(focused, -1))}
              className={navButton}
            >
              <svg viewBox="0 0 12 12" aria-hidden="true" className="size-3">
                <path d="M8 2L4 6l4 4" fill="none" stroke="currentColor" strokeWidth="1.75" />
              </svg>
            </button>
            <p className="font-display text-xs font-bold tracking-[0.2em] uppercase">
              {monthFmt.format(focused)}
            </p>
            <button
              type="button"
              aria-label="Next month"
              onClick={() => setFocused(addMonths(focused, 1))}
              className={navButton}
            >
              <svg viewBox="0 0 12 12" aria-hidden="true" className="size-3">
                <path d="M4 2l4 4-4 4" fill="none" stroke="currentColor" strokeWidth="1.75" />
              </svg>
            </button>
          </div>

          <div className="grid grid-cols-7 gap-y-0.5" onKeyDown={onGridKeyDown} onPointerLeave={() => setHovered('')}>
            {WEEKDAYS.map((day) => (
              <span
                key={day}
                className="flex h-8 w-9 items-center justify-center font-display text-[0.55rem] font-bold tracking-widest uppercase text-ink/40 dark:text-stone-100/40"
              >
                {day}
              </span>
            ))}
            {cells.map((d, i) => {
              if (!d) return <span key={`pad-${i}`} />
              const iso = toISO(d)
              const isEdge = iso === from || iso === to
              const inRange = !!from && !!rangeEnd && iso > from && iso < rangeEnd
              const isToday = toISO(today) === iso
              const isFocused = toISO(focused) === iso
              return (
                <button
                  key={iso}
                  type="button"
                  data-date={iso}
                  tabIndex={isFocused ? 0 : -1}
                  aria-label={dayFmt.format(d)}
                  aria-pressed={isEdge}
                  onClick={() => pick(d)}
                  onPointerEnter={() => setHovered(iso)}
                  className={`flex h-8 w-9 items-center justify-center font-mono text-xs tabular-nums transition-colors focus:outline-none focus-visible:ring-1 focus-visible:ring-pitch-600 dark:focus-visible:ring-pitch-300 ${
                    isEdge
                      ? 'bg-pitch-600 font-bold text-white dark:bg-pitch-400 dark:text-night'
                      : inRange
                        ? 'bg-pitch-600/15 text-pitch-800 hover:bg-pitch-600/25 dark:bg-pitch-400/20 dark:text-pitch-200 dark:hover:bg-pitch-400/30'
                        : isToday
                          ? 'border border-pitch-600/60 text-pitch-700 hover:bg-pitch-600/10 dark:border-pitch-300/60 dark:text-pitch-300 dark:hover:bg-pitch-400/15'
                          : 'hover:bg-ink/10 dark:hover:bg-stone-100/10'
                  }`}
                >
                  {d.getDate()}
                </button>
              )
            })}
          </div>

          <div className="mt-2 flex items-center justify-between border-t border-ink/15 pt-2 dark:border-stone-100/15">
            <p className="font-display text-[0.55rem] font-bold tracking-[0.15em] uppercase text-ink/40 dark:text-stone-100/40">
              {from && !to ? 'Pick end date' : 'Pick start date'}
            </p>
            {(from || to) && (
              <button
                type="button"
                onClick={() => {
                  onChange('', '')
                  close(true)
                }}
                className={footerButton}
              >
                Clear
              </button>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
