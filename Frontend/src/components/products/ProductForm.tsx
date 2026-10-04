import { useState, type FormEvent } from 'react'

import type { Product, ProductStatus, Shop } from '../../types'
import ErrorMessage from '../ErrorMessage'

export interface ProductInitialStock {
  shop_id: string
  quantity: number
}

export interface ProductFormValues {
  name: string
  category: string
  minimum_price: string
  maximum_price: string
  status: ProductStatus
  initial_stock?: ProductInitialStock[]
}

interface ProductFormProps {
  initial?: Product
  shops?: Shop[]
  onSubmit: (values: ProductFormValues) => Promise<void>
  onCancel: () => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

function validatePrice(value: string, label: string): string | null {
  const trimmed = value.trim()
  if (!trimmed) return `${label} is required.`
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) return `Enter a valid ${label.toLowerCase()}.`
  const amount = Number(trimmed)
  if (!Number.isFinite(amount)) return `Enter a valid ${label.toLowerCase()}.`
  if (amount < 0) return `${label} must not be negative.`
  return null
}

export default function ProductForm({ initial, shops, onSubmit, onCancel }: ProductFormProps) {
  const isEdit = initial !== undefined

  const [name, setName] = useState(initial?.name ?? '')
  const [category, setCategory] = useState(initial?.category ?? '')
  const [minimumPrice, setMinimumPrice] = useState(initial?.minimum_price ?? '')
  const [maximumPrice, setMaximumPrice] = useState(initial?.maximum_price ?? '')
  const [status, setStatus] = useState<ProductStatus>(initial?.status ?? 'ACTIVE')
  const [stockValues, setStockValues] = useState<Record<string, string>>(() => {
    const values: Record<string, string> = {}
    for (const shop of shops ?? []) values[shop.id] = '0'
    return values
  })

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  function updateStock(shopId: string, value: string) {
    setStockValues((prev) => ({ ...prev, [shopId]: value }))
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()

    const trimmedName = name.trim()
    if (!trimmedName) {
      setError('Product name is required.')
      return
    }

    const minError = validatePrice(minimumPrice, 'Minimum price')
    if (minError) {
      setError(minError)
      return
    }
    const maxError = validatePrice(maximumPrice, 'Maximum price')
    if (maxError) {
      setError(maxError)
      return
    }

    if (Number(minimumPrice.trim()) > Number(maximumPrice.trim())) {
      setError('Minimum price must not exceed maximum price.')
      return
    }

    const values: ProductFormValues = {
      name: trimmedName,
      category: category.trim(),
      minimum_price: minimumPrice.trim(),
      maximum_price: maximumPrice.trim(),
      status,
    }

    if (!isEdit) {
      const initialStock: ProductInitialStock[] = []
      for (const shop of shops ?? []) {
        const raw = (stockValues[shop.id] ?? '0').trim()
        if (raw === '') {
          initialStock.push({ shop_id: shop.id, quantity: 0 })
        } else if (/^\d+$/.test(raw)) {
          initialStock.push({ shop_id: shop.id, quantity: Number(raw) })
        } else {
          setError(`Enter a valid whole-number quantity for ${shop.name}.`)
          return
        }
      }
      values.initial_stock = initialStock
    }

    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(values)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to save product.')
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <div>
        <label htmlFor="product-name" className="block text-sm font-medium text-slate-700">
          Product Name <span className="text-danger-600">*</span>
        </label>
        <input
          id="product-name"
          value={name}
          onChange={(event) => setName(event.target.value)}
          required
          className={inputClass}
          placeholder="e.g. Bluetooth Speaker"
        />
      </div>

      <div>
        <label htmlFor="product-category" className="block text-sm font-medium text-slate-700">
          Category
        </label>
        <input
          id="product-category"
          value={category}
          onChange={(event) => setCategory(event.target.value)}
          className={inputClass}
          placeholder="e.g. Audio & Accessories"
        />
      </div>

      <div className="grid grid-cols-2 gap-3">
        <div>
          <label htmlFor="product-min-price" className="block text-sm font-medium text-slate-700">
            Minimum Price <span className="text-danger-600">*</span>
          </label>
          <input
            id="product-min-price"
            value={minimumPrice}
            onChange={(event) => setMinimumPrice(event.target.value)}
            inputMode="decimal"
            className={inputClass}
            placeholder="e.g. 100.00"
          />
        </div>
        <div>
          <label htmlFor="product-max-price" className="block text-sm font-medium text-slate-700">
            Maximum Price <span className="text-danger-600">*</span>
          </label>
          <input
            id="product-max-price"
            value={maximumPrice}
            onChange={(event) => setMaximumPrice(event.target.value)}
            inputMode="decimal"
            className={inputClass}
            placeholder="e.g. 150.00"
          />
        </div>
      </div>

      <div>
        <label htmlFor="product-status" className="block text-sm font-medium text-slate-700">
          Status
        </label>
        <select
          id="product-status"
          value={status}
          onChange={(event) => setStatus(event.target.value as ProductStatus)}
          className={inputClass}
        >
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
        </select>
      </div>

      {!isEdit && (shops?.length ?? 0) > 0 && (
        <div className="space-y-3 border-t border-slate-200 pt-4">
          <div>
            <p className="text-sm font-semibold text-slate-900">Initial Stock</p>
            <p className="mt-0.5 text-xs text-slate-500">
              Set the starting quantity for each shop. Initial stock is set separately for each shop.
            </p>
          </div>
          <div className="grid grid-cols-1 gap-3 sm:grid-cols-2">
            {shops?.map((shop) => (
              <div key={shop.id} className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-3">
                <label
                  htmlFor={`stock-${shop.id}`}
                  className="block text-sm font-medium text-slate-700"
                >
                  {shop.name}
                </label>
                <div className="mt-1 flex items-center gap-2">
                  <input
                    id={`stock-${shop.id}`}
                    value={stockValues[shop.id] ?? '0'}
                    onChange={(event) => updateStock(shop.id, event.target.value.replace(/\D/g, ''))}
                    inputMode="numeric"
                    className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
                  />
                  <span className="whitespace-nowrap text-xs text-slate-500">items</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <ErrorMessage message={error ?? undefined} title="Unable to save product" />

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
          {submitting ? 'Saving…' : initial ? 'Save Changes' : 'Create Product'}
        </button>
      </div>
    </form>
  )
}
