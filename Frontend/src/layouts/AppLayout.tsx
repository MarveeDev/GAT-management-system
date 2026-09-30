import { NavLink, Outlet, useNavigate } from 'react-router-dom'

import { useAuth } from '../contexts/authContext'

const NAV_ITEMS = [
  { to: '/', label: 'Overview', end: true },
  { to: '/dashboard', label: 'Dashboard' },
  { to: '/shops', label: 'Shops' },
  { to: '/staff', label: 'Staff' },
  { to: '/purchases', label: 'Purchases' },
  { to: '/customers', label: 'Customers' },
  { to: '/sms', label: 'SMS' },
  { to: '/reports', label: 'Reports' },
]

export default function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-64 shrink-0 flex-col bg-navy-900 text-white md:flex">
        <div className="flex items-center gap-3 px-5 py-5">
          <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold">
            GAE
          </div>
          <div>
            <p className="text-sm font-semibold leading-tight">Great Alexender</p>
            <p className="text-xs text-white/60">Enterprise</p>
          </div>
        </div>

        <nav className="flex-1 space-y-1 px-3 py-3">
          {NAV_ITEMS.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={item.end}
              className={({ isActive }) =>
                `block rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                  isActive
                    ? 'bg-brand-600 text-white'
                    : 'text-white/70 hover:bg-white/10 hover:text-white'
                }`
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="border-t border-white/10 px-5 py-4">
          {user && (
            <div className="mb-3">
              <p className="truncate text-sm font-medium text-white">{user.name}</p>
              <p className="text-xs text-white/50">{user.role}</p>
            </div>
          )}
          <button
            type="button"
            onClick={handleLogout}
            className="w-full rounded-lg bg-white/10 px-3 py-2 text-sm font-medium text-white/80 transition-colors hover:bg-white/20 hover:text-white"
          >
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col bg-slate-50">
        <header className="flex items-center justify-between border-b border-slate-200 bg-white px-4 py-3 md:hidden">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-xs font-bold text-white">
              GAE
            </div>
            <span className="text-sm font-semibold text-slate-900">Great Alexender Enterprise</span>
          </div>
          <button
            type="button"
            onClick={handleLogout}
            className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-600 hover:bg-slate-50"
          >
            Sign out
          </button>
        </header>

        <main className="flex-1 px-4 py-6 md:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
