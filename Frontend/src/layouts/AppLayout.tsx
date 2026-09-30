import { useEffect, useState } from 'react'
import { Outlet } from 'react-router-dom'
import { Menu, X } from 'lucide-react'

import SidebarContent from '../components/navigation/SidebarContent'

export default function AppLayout() {
  const [mobileOpen, setMobileOpen] = useState(false)

  useEffect(() => {
    if (!mobileOpen) return
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') setMobileOpen(false)
    }
    document.addEventListener('keydown', onKeyDown)
    return () => document.removeEventListener('keydown', onKeyDown)
  }, [mobileOpen])

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 bg-navy-900 md:block">
        <SidebarContent />
      </aside>

      {mobileOpen && (
        <div className="fixed inset-0 z-40 md:hidden">
          <div
            className="absolute inset-0 bg-black/50"
            aria-hidden="true"
            onClick={() => setMobileOpen(false)}
          />
          <div
            className="absolute inset-y-0 left-0 w-72 max-w-[85%] bg-navy-900 text-white shadow-xl"
            role="dialog"
            aria-modal="true"
            aria-label="Navigation"
          >
            <button
              type="button"
              onClick={() => setMobileOpen(false)}
              aria-label="Close menu"
              className="absolute right-3 top-4 z-10 rounded-lg p-1.5 text-white/70 transition-colors hover:bg-white/10 hover:text-white"
            >
              <X className="h-5 w-5" aria-hidden="true" />
            </button>
            <SidebarContent onNavigate={() => setMobileOpen(false)} />
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col bg-slate-50">
        <header className="flex h-14 items-center justify-between border-b border-slate-200 bg-white px-4 md:hidden">
          <button
            type="button"
            onClick={() => setMobileOpen(true)}
            aria-label="Open menu"
            className="rounded-lg p-2 text-slate-600 transition-colors hover:bg-slate-100"
          >
            <Menu className="h-5 w-5" aria-hidden="true" />
          </button>
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-xs font-bold text-white">
              GAE
            </div>
            <span className="truncate text-sm font-semibold text-slate-900">
              Great Alexender Enterprise
            </span>
          </div>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
