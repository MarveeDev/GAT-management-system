import type { User } from '../../types'
import { formatRole } from '../../utils/format'

interface StaffDetailsProps {
  user: User
  shopName: string | null
}

export default function StaffDetails({ user, shopName }: StaffDetailsProps) {
  const rows: [string, string][] = [
    ['Name', user.name],
    ['Email', user.email],
    ['Phone', user.phone || '—'],
    ['Role', formatRole(user.role)],
    ['Shop', shopName || '—'],
    ['Status', user.status === 'ACTIVE' ? 'Active' : 'Inactive'],
  ]

  return (
    <dl className="space-y-3">
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2 text-sm last:border-0 last:pb-0"
        >
          <dt className="text-slate-500">{label}</dt>
          <dd className="text-right font-medium text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}
