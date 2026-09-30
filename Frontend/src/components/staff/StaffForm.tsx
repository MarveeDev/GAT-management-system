import { useState, type FormEvent } from 'react'

import type { Shop } from '../../types'
import ErrorMessage from '../ErrorMessage'

export interface StaffCreateValues {
  name: string
  email: string
  phone: string
  password: string
  role: 'SHOP_MANAGER' | 'STAFF'
  shop_id: string
}

interface StaffFormProps {
  isSuperAdmin: boolean
  ownShop: Shop | null
  activeShops: Shop[]
  onSubmit: (values: StaffCreateValues) => Promise<void>
  onCancel: () => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function StaffForm({
  isSuperAdmin,
  ownShop,
  activeShops,
  onSubmit,
  onCancel,
}: StaffFormProps) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [role, setRole] = useState<'SHOP_MANAGER' | 'STAFF'>('STAFF')
  const [shopId, setShopId] = useState(isSuperAdmin ? '' : ownShop?.id ?? '')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Full name is required.')
      return
    }
    if (!email.trim()) {
      setError('Email is required.')
      return
    }
    if (password.length < 8) {
      setError('Password must be at least 8 characters.')
      return
    }
    const resolvedShopId = isSuperAdmin ? shopId : ownShop?.id
    if (!resolvedShopId) {
      setError('A shop assignment is required.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await onSubmit({
        name: trimmedName,
        email: email.trim(),
        phone,
        password,
        role,
        shop_id: resolvedShopId,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to create staff.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="staff-name" className="block text-sm font-medium text-slate-700">
          Full Name <span className="text-danger-600">*</span>
        </label>
        <input
          id="staff-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          className={inputClass}
          placeholder="e.g. John Mensah"
        />
      </div>

      <div>
        <label htmlFor="staff-email" className="block text-sm font-medium text-slate-700">
          Email <span className="text-danger-600">*</span>
        </label>
        <input
          id="staff-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
          className={inputClass}
          placeholder="e.g. john@example.com"
        />
      </div>

      <div>
        <label htmlFor="staff-phone" className="block text-sm font-medium text-slate-700">
          Phone
        </label>
        <input
          id="staff-phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          className={inputClass}
          placeholder="e.g. 0240000000"
        />
      </div>

      <div>
        <label htmlFor="staff-password" className="block text-sm font-medium text-slate-700">
          Password <span className="text-danger-600">*</span>
        </label>
        <div className="relative">
          <input
            id="staff-password"
            type={showPassword ? 'text' : 'password'}
            autoComplete="new-password"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
            className={`${inputClass} pr-16`}
            placeholder="At least 8 characters"
          />
          <button
            type="button"
            onClick={() => setShowPassword((v) => !v)}
            aria-label={showPassword ? 'Hide password' : 'Show password'}
            className="absolute inset-y-0 right-0 flex items-center px-3 text-sm font-medium text-slate-500 hover:text-slate-700"
          >
            {showPassword ? 'Hide' : 'Show'}
          </button>
        </div>
      </div>

      <div>
        <label htmlFor="staff-role" className="block text-sm font-medium text-slate-700">
          Role
        </label>
        {isSuperAdmin ? (
          <select
            id="staff-role"
            value={role}
            onChange={(event) => setRole(event.target.value as 'SHOP_MANAGER' | 'STAFF')}
            className={inputClass}
          >
            <option value="STAFF">Staff</option>
            <option value="SHOP_MANAGER">Shop Manager</option>
          </select>
        ) : (
          <p className="mt-1 text-sm text-slate-600">Staff</p>
        )}
      </div>

      <div>
        <label htmlFor="staff-shop" className="block text-sm font-medium text-slate-700">
          Shop <span className="text-danger-600">*</span>
        </label>
        {isSuperAdmin ? (
          <select
            id="staff-shop"
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
        ) : (
          <p className="mt-1 text-sm text-slate-600">{ownShop?.name ?? '—'}</p>
        )}
      </div>

      <ErrorMessage message={error ?? undefined} title="Unable to create staff" />

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
          {submitting ? 'Creating…' : 'Create Staff'}
        </button>
      </div>
    </form>
  )
}
