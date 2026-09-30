import { Link } from 'react-router-dom'
import { MessageSquare, ShoppingCart, Store, UserPlus, type LucideIcon } from 'lucide-react'

import { useAuth } from '../../contexts/authContext'
import type { UserRole } from '../../types'

interface QuickAction {
  label: string
  path: string
  icon: LucideIcon
  roles: UserRole[]
}

const ALL_ROLES: UserRole[] = ['SUPER_ADMIN', 'SHOP_MANAGER', 'STAFF']

const ACTIONS: QuickAction[] = [
  { label: 'Add Shop', path: '/shops', icon: Store, roles: ['SUPER_ADMIN'] },
  { label: 'Add Staff', path: '/staff', icon: UserPlus, roles: ['SUPER_ADMIN', 'SHOP_MANAGER'] },
  { label: 'Record Purchase', path: '/purchases', icon: ShoppingCart, roles: ALL_ROLES },
  { label: 'View SMS', path: '/sms', icon: MessageSquare, roles: ALL_ROLES },
]

export default function QuickActions() {
  const { user } = useAuth()
  const role = user?.role
  const actions = ACTIONS.filter((action) => role !== undefined && action.roles.includes(role))

  if (actions.length === 0) return null

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-900">Quick Actions</h2>
      </div>

      <div className="grid grid-cols-1 gap-2 p-5 sm:grid-cols-2 lg:grid-cols-4">
        {actions.map((action) => {
          const Icon = action.icon
          return (
            <Link
              key={action.path}
              to={action.path}
              className="flex items-center gap-3 rounded-lg border border-slate-200 px-3 py-2.5 text-sm font-medium text-slate-700 transition-colors hover:border-brand-500 hover:text-brand-600"
            >
              <Icon className="h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
              <span>{action.label}</span>
            </Link>
          )
        })}
      </div>
    </section>
  )
}
