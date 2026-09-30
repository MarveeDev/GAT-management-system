import { NavLink, useNavigate } from 'react-router-dom'

import { NAV_GROUPS } from '../../config/navigation'
import { useAuth } from '../../contexts/authContext'
import { formatRole, shopScopeLabel } from '../../utils/format'

interface SidebarContentProps {
  onNavigate?: () => void
}

export default function SidebarContent({ onNavigate }: SidebarContentProps) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const role = user?.role

  function handleLogout() {
    logout()
    navigate('/login', { replace: true })
  }

  return (
    <div className="flex h-full flex-col">
      <div className="flex items-center gap-3 border-b border-white/10 px-5 py-5">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold text-white">
          GAE
        </div>
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold leading-tight text-white">
            Great Alexender Enterprise
          </p>
          <p className="text-xs text-white/60">Management System</p>
        </div>
      </div>

      <nav className="flex-1 overflow-y-auto px-3 py-2" aria-label="Main navigation">
        {NAV_GROUPS.map((group) => {
          const items = group.items.filter(
            (item) => !item.roles || (role !== undefined && item.roles.includes(role)),
          )
          if (items.length === 0) return null
          return (
            <div key={group.title} className="mb-4">
              <p className="px-3 pb-1 text-[11px] font-semibold uppercase tracking-wider text-white/40">
                {group.title}
              </p>
              <ul className="space-y-1">
                {items.map((item) => {
                  const Icon = item.icon
                  return (
                    <li key={item.path}>
                      <NavLink
                        to={item.path}
                        end
                        onClick={onNavigate}
                        className={({ isActive }) =>
                          `flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
                            isActive
                              ? 'bg-brand-600 text-white'
                              : 'text-white/70 hover:bg-white/10 hover:text-white'
                          }`
                        }
                      >
                        <Icon className="h-4 w-4 shrink-0" aria-hidden="true" />
                        <span className="truncate">{item.label}</span>
                      </NavLink>
                    </li>
                  )
                })}
              </ul>
            </div>
          )
        })}
      </nav>

      <div className="border-t border-white/10 px-5 py-4">
        {user && (
          <div className="mb-3">
            <p className="truncate text-sm font-medium text-white">{user.name}</p>
            <p className="text-xs text-white/50">{formatRole(user.role)}</p>
            <p className="mt-1 text-xs text-white/40">{shopScopeLabel(user.shop_id)}</p>
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
    </div>
  )
}
