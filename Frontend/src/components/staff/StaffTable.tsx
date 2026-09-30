import { Eye, KeyRound, Pencil } from 'lucide-react'

import type { User } from '../../types'
import { formatRole } from '../../utils/format'

interface StaffTableProps {
  users: User[]
  shopNames: Map<string, string>
  currentUserId: string | null
  canManage: (user: User) => boolean
  onEdit: (user: User) => void
  onPassword: (user: User) => void
  onDetails: (user: User) => void
}

function StatusBadge({ status }: { status: User['status'] }) {
  if (status === 'ACTIVE') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-medium text-success-700">
        <span className="h-1.5 w-1.5 rounded-full bg-success-600" aria-hidden="true" />
        Active
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400" aria-hidden="true" />
      Inactive
    </span>
  )
}

export default function StaffTable({
  users,
  shopNames,
  currentUserId,
  canManage,
  onEdit,
  onPassword,
  onDetails,
}: StaffTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[760px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Name</th>
            <th className="px-5 py-3 font-semibold">Role</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Status</th>
            <th className="px-5 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users.map((user) => {
            const manageable = canManage(user)
            return (
              <tr key={user.id} className="border-b border-slate-100 last:border-0">
                <td className="px-5 py-3">
                  <div className="flex items-center gap-2">
                    <span className="font-medium text-slate-900">{user.name}</span>
                    {user.id === currentUserId && (
                      <span className="rounded-full bg-brand-50 px-2 py-0.5 text-xs font-medium text-brand-700">
                        You
                      </span>
                    )}
                  </div>
                  <p className="text-xs text-slate-500">{user.email}</p>
                </td>
                <td className="px-5 py-3 text-slate-600">{formatRole(user.role)}</td>
                <td className="px-5 py-3 text-slate-600">
                  {user.shop_id ? (shopNames.get(user.shop_id) ?? '—') : '—'}
                </td>
                <td className="px-5 py-3 text-slate-600">{user.phone || '—'}</td>
                <td className="px-5 py-3">
                  <StatusBadge status={user.status} />
                </td>
                <td className="px-5 py-3">
                  <div className="flex items-center justify-end gap-1">
                    <button
                      type="button"
                      onClick={() => onDetails(user)}
                      aria-label={`View details for ${user.name}`}
                      title="Details"
                      className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                    >
                      <Eye className="h-4 w-4" aria-hidden="true" />
                    </button>
                    {manageable && (
                      <>
                        <button
                          type="button"
                          onClick={() => onPassword(user)}
                          aria-label={`Change password for ${user.name}`}
                          title="Change Password"
                          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                        >
                          <KeyRound className="h-4 w-4" aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          onClick={() => onEdit(user)}
                          aria-label={`Edit ${user.name}`}
                          title="Edit"
                          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Pencil className="h-4 w-4" aria-hidden="true" />
                        </button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
