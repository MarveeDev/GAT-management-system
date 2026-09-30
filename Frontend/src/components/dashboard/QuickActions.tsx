import { Link } from 'react-router-dom'
import { MessageSquare, ShoppingCart, Store, UserPlus } from 'lucide-react'

const ACTIONS = [
  { label: 'Add Shop', path: '/shops', icon: Store },
  { label: 'Add Staff', path: '/staff', icon: UserPlus },
  { label: 'Record Purchase', path: '/purchases', icon: ShoppingCart },
  { label: 'View SMS', path: '/sms', icon: MessageSquare },
]

export default function QuickActions() {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-900">Quick Actions</h2>
      </div>

      <div className="grid grid-cols-1 gap-2 p-5 sm:grid-cols-2 lg:grid-cols-4">
        {ACTIONS.map((action) => {
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
