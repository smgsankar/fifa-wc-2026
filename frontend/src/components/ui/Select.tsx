import { useEffect, useId, useRef, useState } from 'react'

export interface SelectOption {
  value: string
  label: string
}

interface SelectProps {
  value: string
  options: SelectOption[]
  onChange: (value: string) => void
  ariaLabel: string
}

const triggerBase =
  'flex w-full items-center justify-between gap-2 border bg-white px-3 py-2 text-left text-sm text-ink transition-[border-color,box-shadow] focus:outline-none focus-visible:border-pitch-600 dark:bg-night-soft dark:text-stone-100 dark:focus-visible:border-pitch-300'
const triggerOpen =
  'border-ink shadow-[3px_3px_0_0_var(--color-pitch-600)] dark:border-stone-100/60 dark:shadow-[3px_3px_0_0_var(--color-pitch-400)]'
const triggerClosed =
  'border-ink/25 hover:border-ink/60 dark:border-stone-100/25 dark:hover:border-stone-100/60'

/** Custom listbox in the editorial theme: sharp corners, ink hairlines, hard
 *  pitch-green offset shadow when open. Arrow keys, Home/End and typeahead. */
export default function Select({ value, options, onChange, ariaLabel }: SelectProps) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const rootRef = useRef<HTMLDivElement>(null)
  const listRef = useRef<HTMLUListElement>(null)
  const triggerRef = useRef<HTMLButtonElement>(null)
  const typeahead = useRef({ buffer: '', last: 0 })
  const id = useId()

  const selectedIndex = options.findIndex((o) => o.value === value)
  const selected = options[selectedIndex]

  const openList = () => {
    setActive(selectedIndex >= 0 ? selectedIndex : 0)
    setOpen(true)
  }

  const close = (refocus: boolean) => {
    setOpen(false)
    if (refocus) triggerRef.current?.focus()
  }

  const choose = (index: number) => {
    onChange(options[index].value)
    close(true)
  }

  useEffect(() => {
    if (!open) return
    listRef.current?.focus()
    const onPointerDown = (e: PointerEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', onPointerDown)
    return () => document.removeEventListener('pointerdown', onPointerDown)
  }, [open])

  useEffect(() => {
    if (!open) return
    listRef.current?.children[active]?.scrollIntoView({ block: 'nearest' })
  }, [open, active])

  const onTriggerKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      openList()
    }
  }

  const findByTypeahead = (key: string, now: number) => {
    const t = typeahead.current
    t.buffer = now - t.last > 500 ? key : t.buffer + key
    t.last = now
    const query = t.buffer.toLowerCase()
    const start = t.buffer.length === 1 ? active + 1 : active
    for (let i = 0; i < options.length; i++) {
      const idx = (start + i) % options.length
      if (options[idx].label.toLowerCase().startsWith(query)) {
        setActive(idx)
        return
      }
    }
  }

  const onListKeyDown = (e: React.KeyboardEvent) => {
    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setActive((i) => Math.min(i + 1, options.length - 1))
        break
      case 'ArrowUp':
        e.preventDefault()
        setActive((i) => Math.max(i - 1, 0))
        break
      case 'Home':
        e.preventDefault()
        setActive(0)
        break
      case 'End':
        e.preventDefault()
        setActive(options.length - 1)
        break
      case 'Enter':
      case ' ':
        e.preventDefault()
        choose(active)
        break
      case 'Escape':
        e.preventDefault()
        close(true)
        break
      case 'Tab':
        setOpen(false)
        break
      default:
        if (e.key.length === 1 && !e.metaKey && !e.ctrlKey && !e.altKey)
          findByTypeahead(e.key, e.timeStamp)
    }
  }

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        ref={triggerRef}
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={ariaLabel}
        onClick={() => (open ? close(false) : openList())}
        onKeyDown={onTriggerKeyDown}
        className={`${triggerBase} ${open ? triggerOpen : triggerClosed}`}
      >
        <span className="truncate">{selected?.label ?? ''}</span>
        <svg
          viewBox="0 0 12 12"
          aria-hidden="true"
          className={`size-3 shrink-0 transition-transform ${
            open
              ? 'rotate-180 text-pitch-600 dark:text-pitch-300'
              : 'text-ink/40 dark:text-stone-100/40'
          }`}
        >
          <path d="M2 4l4 4 4-4" fill="none" stroke="currentColor" strokeWidth="1.75" />
        </svg>
      </button>

      {open && (
        <ul
          ref={listRef}
          role="listbox"
          tabIndex={-1}
          aria-label={ariaLabel}
          aria-activedescendant={`${id}-opt-${active}`}
          onKeyDown={onListKeyDown}
          className="absolute right-0 left-0 z-30 mt-1.5 max-h-64 overflow-auto border border-ink bg-white py-1 shadow-[4px_4px_0_0_var(--color-pitch-600)] focus:outline-none dark:border-stone-100/60 dark:bg-night-soft dark:shadow-[4px_4px_0_0_var(--color-pitch-400)]"
        >
          {options.map((option, i) => {
            const isSelected = option.value === value
            return (
              <li
                key={option.value}
                id={`${id}-opt-${i}`}
                role="option"
                aria-selected={isSelected}
                onPointerEnter={() => setActive(i)}
                onClick={() => choose(i)}
                className={`flex cursor-pointer items-center gap-2 px-3 py-1.5 text-sm ${
                  i === active ? 'bg-pitch-600/10 dark:bg-pitch-400/15' : ''
                } ${isSelected ? 'font-semibold text-pitch-700 dark:text-pitch-300' : ''}`}
              >
                <span
                  aria-hidden="true"
                  className={`size-1.5 shrink-0 ${isSelected ? 'bg-pitch-600 dark:bg-pitch-300' : ''}`}
                />
                <span className="truncate">{option.label}</span>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
