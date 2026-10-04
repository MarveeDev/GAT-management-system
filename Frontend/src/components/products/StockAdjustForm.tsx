import { useState, type FormEvent } from 'react'

import type { Product } from '../../types'
import ErrorMessage from '../ErrorMessage'

interface StockAdjustFormProps {
  product: Product
  shopName: string
  currentQuantity: number
  onSubmit: (quantity: number) => Promise<void>
  onCancel: () => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function StockAdjustForm({
  product,
  shopName,
  currentQuantity,
  onSubmit,
  onCancel,
}: StockAdjustFormProps) {
  const [addValue, setAddValue] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const addNumber = /^\d+$/.test(addValue.trim()) ? parseInt(addValue.trim(), 10) : 0
  const totalStock = currentQuantity + addNumber

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmed = addValue.trim()
    if (!/^\d+$/.test(trimmed)) {
      setError('Enter a valid whole-number quantity to add.')
      return
    }
    const add = Number(trimmed)
    if (!Number.isFinite(add) || add < 0) {
      setError('Stock to add must be zero or greater.')
      return
    }

    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(currentQuantity + add)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to update stock.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div className="rounded-lg bg-slate-50 px-4 py-3 text-sm">
        <p className="font-medium text-slate-900">{product.name}</p>
        <p className="mt-0.5 text-slate-500">{shopName}</p>
        <p className="mt-2 text-slate-600">
          Previous Stock:{' '}
          <span className="font-semibold text-slate-900">{currentQuantity} units</span>
        </p>
      </div>

      <div>
        <label htmlFor="stock-to-add" className="block text-sm font-medium text-slate-700">
          Stock to Add <span className="text-danger-600">*</span>
        </label>
        <input
          id="stock-to-add"
          value={addValue}
          onChange={(event) => setAddValue(event.target.value.replace(/\D/g, ''))}
          inputMode="numeric"
          className={inputClass}
          placeholder="e.g. 10"
        />
      </div>

      <div className="flex items-center justify-between border-t border-slate-200 pt-3 text-sm">
        <span className="text-slate-600">Total Stock</span>
        <span className="font-semibold text-slate-900">{totalStock} units</span>
      </div>

      <ErrorMessage message={error ?? undefined} title="Unable to update stock" />

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
          {submitting ? 'Saving…' : 'Update Stock'}
        </button>
      </div>
    </form>
  )
}
