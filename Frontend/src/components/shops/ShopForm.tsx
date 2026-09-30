import { useState, type FormEvent } from 'react'

import type { Shop, ShopStatus } from '../../types'
import ErrorMessage from '../ErrorMessage'

export interface ShopFormValues {
  name: string
  location: string
  phone: string
  sender_id: string
  status: ShopStatus
}

interface ShopFormProps {
  initial?: Shop
  onSubmit: (values: ShopFormValues) => Promise<void>
  onCancel: () => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function ShopForm({ initial, onSubmit, onCancel }: ShopFormProps) {
  const [name, setName] = useState(initial?.name ?? '')
  const [location, setLocation] = useState(initial?.location ?? '')
  const [phone, setPhone] = useState(initial?.phone ?? '')
  const [senderId, setSenderId] = useState(initial?.sender_id ?? '')
  const [status, setStatus] = useState<ShopStatus>(initial?.status ?? 'ACTIVE')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Shop name is required.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await onSubmit({
        name: trimmedName,
        location,
        phone,
        sender_id: senderId,
        status,
      })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save shop.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="shop-name" className="block text-sm font-medium text-slate-700">
          Shop Name <span className="text-danger-600">*</span>
        </label>
        <input
          id="shop-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          className={inputClass}
          placeholder="e.g. Main Branch"
        />
      </div>

      <div>
        <label htmlFor="shop-location" className="block text-sm font-medium text-slate-700">
          Location
        </label>
        <input
          id="shop-location"
          value={location}
          onChange={(event) => setLocation(event.target.value)}
          className={inputClass}
          placeholder="e.g. Accra"
        />
      </div>

      <div>
        <label htmlFor="shop-phone" className="block text-sm font-medium text-slate-700">
          Phone
        </label>
        <input
          id="shop-phone"
          type="tel"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
          className={inputClass}
          placeholder="e.g. 0240000000"
        />
      </div>

      <div>
        <label htmlFor="shop-sender-id" className="block text-sm font-medium text-slate-700">
          Sender ID
        </label>
        <input
          id="shop-sender-id"
          value={senderId}
          onChange={(event) => setSenderId(event.target.value)}
          className={inputClass}
          placeholder="e.g. GREAT-ALEX"
        />
      </div>

      <div>
        <label htmlFor="shop-status" className="block text-sm font-medium text-slate-700">
          Status
        </label>
        <select
          id="shop-status"
          value={status}
          onChange={(event) => setStatus(event.target.value as ShopStatus)}
          className={inputClass}
        >
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>

      <ErrorMessage message={error ?? undefined} title="Unable to save shop" />

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
          {submitting ? 'Saving…' : initial ? 'Save Changes' : 'Create Shop'}
        </button>
      </div>
    </form>
  )
}
