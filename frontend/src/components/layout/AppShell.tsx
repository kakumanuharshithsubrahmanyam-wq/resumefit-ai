import { Sparkles } from 'lucide-react'
import { Link, NavLink, Outlet } from 'react-router-dom'

import { cn } from '@/lib/utils'

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  cn(
    'rounded-md px-3 py-2 text-sm font-medium transition-colors',
    isActive
      ? 'bg-primary/10 text-primary'
      : 'text-muted-foreground hover:bg-muted hover:text-foreground',
  )

export function AppShell() {
  return (
    <div className="min-h-svh bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.12),transparent_45%),linear-gradient(to_bottom,#fafafa,#f5f3ff)] dark:bg-[radial-gradient(circle_at_top,rgba(99,102,241,0.18),transparent_45%),linear-gradient(to_bottom,#0b0b10,#111827)]">
      <header className="sticky top-0 z-20 border-b border-border/60 bg-background/80 backdrop-blur-md">
        <div className="mx-auto flex max-w-6xl items-center justify-between gap-4 px-4 py-4 sm:px-6">
          <Link to="/" className="flex items-center gap-2 font-semibold tracking-tight">
            <span className="inline-flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-indigo-500 to-violet-600 text-white shadow-sm">
              <Sparkles className="size-4" aria-hidden="true" />
            </span>
            ResumeFit AI
          </Link>
          <nav className="flex items-center gap-1">
            <NavLink to="/" className={navLinkClass} end>
              Home
            </NavLink>
            <NavLink to="/analyze" className={navLinkClass}>
              Analyze
            </NavLink>
            <NavLink to="/history" className={navLinkClass}>
              History
            </NavLink>
          </nav>
        </div>
      </header>
      <Outlet />
    </div>
  )
}
