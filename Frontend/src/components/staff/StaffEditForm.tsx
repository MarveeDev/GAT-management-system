import { useState, type FormEvent } from 'react'

import type { Shop, User, UserStatus } from '../../types'
import ErrorMessage from '../ErrorMessage'

export interface StaffEditValues {
  name: string
  phone: string
  status: UserStatus
  role?: 'SHOP_MANAGER' | 'STAFF'
  shop_id?: string
}

interface StaffEditFormProps {
  target: User
  isSuperAdmin: boolean
  isSelf: boolean
  activeShops: Shop[]
  onSubmit: (values: StaffEditValues) => Promise<void>
  onCancel: () => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function StaffEditForm({
  target,
  isSuperAdmin,
  isSelf,
  activeShops,
  onSubmit,
  onCancel,
}: StaffEditFormProps) {
  const [name, setName] = useState(target.name)
  const [phone, setPhone] = useState(target.phone ?? '')
  const [role, setRole] = useState<'SHOP_MANAGER' | 'STAFF'>(
    target.role === 'SHOP_MANAGER' ? 'SHOP_MANAGER' : 'STAFF',
  )
  const [shopId, setShopId] = useState(target.shop_id ?? '')
  const [status, setStatus] = useState<UserStatus>(target.status)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const canEditRole = isSuperAdmin && !isSelf && target.role !== 'SUPER_ADMIN'
  const canEditShop = canEditRole && (role === 'SHOP_MANAGER' || role === 'STAFF')
  const canEditStatus = !isSelf

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Full name is required.')
      return
    }
    if (canEditShop && !shopId) {
      setError('A shop assignment is required.')
      return
    }

    const values: StaffEditValues = { name: trimmedName, phone, status }
    if (canEditRole) {
      values.role = role
      if (canEditShop) {
        values.shop_id = shopId
      }
    }

    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(values)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update staff.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      {isSelf && (
        <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
          You cannot change your own role, status, or shop assignment.
        </p>
      )}

      <div>
        <label htmlFor="edit-name" className="block text-sm font-medium text-slate-700">
          Full Name <span className="text-danger-600">*</span>
        </label>
        <input
          id="edit-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          className={inputClass}
        />
      </div>

      <div>
        <label htmlFor="edit-phone" className="block text-sm font-medium text-slate-700">
          Phone
        </label>
        <input
          id="edit-phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          className={inputClass}
        />
      </div>

      {canEditRole && (
        <div>
          <label htmlFor="edit-role" className="block text-sm font-medium text-slate-700">
            Role
          </label>
          <select
            id="edit-role"
            value={role}
            onChange={(event) => setRole(event.target.value as 'SHOP_MANAGER' | 'STAFF')}
            className={inputClass}
          >
            <option value="STAFF">Staff</option>
            <option value="SHOP_MANAGER">Shop Manager</option>
          </select>
        </div>
      )}

      {canEditShop && (
        <div>
          <label htmlFor="edit-shop" className="block text-sm font-medium text-slate-700">
            Shop <span className="text-danger-600">*</span>
          </label>
          <select
            id="edit-shop"
            value={shopId}
            onChange={(event) => setShopId(event.target.value)}
            className={inputClass}
          >
            <option value="">Select a shop…</option>
            {activeShops.map((shop) => (
              <option key={shop.id} value={shop.id}>
                {shop.name}
              </option>
            ))}
          </select>
        </div>
      )}

      {canEditStatus && (
        <div>
          <label htmlFor="edit-status" className="block text-sm font-medium text-slate-700">
            Status
          </label>
          <select
            id="edit-status"
            value={status}
            onChange={(event) => setStatus(event.target.value as UserStatus)}
            className={inputClass}
          >
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>
      )}

      <ErrorMessage message={error ?? undefined} title="Unable to update staff" />

      <div className="flex justify-end gap-2 pt-1">
        <button
          type="button"
          onClick={onCancel}
          className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
        >
          Cancel
        </button>
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting && (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          )}
          {submitting ? 'Saving…' : 'Save Changes'}
        </button>
      </div>
    </form>
  )
}
