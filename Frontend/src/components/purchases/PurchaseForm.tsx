import { useEffect, useRef, useState, type FormEvent } from 'react'

import type { PurchaseCreatePayload, Shop } from '../../types'
import ErrorMessage from '../ErrorMessage'

export interface PurchasePreviewValues {
  customerName: string
  product: string
  amount: string
  shopName?: string
}

interface PurchaseFormProps {
  isSuperAdmin: boolean
  activeShops: Shop[]
  assignedShopName: string | null
  onSubmit: (payload: PurchaseCreatePayload) => Promise<void>
  onCancel?: () => void
  onValuesChange?: (values: PurchasePreviewValues) => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

const AMOUNT_RE = /^\d+(\.\d+)?$/

export default function PurchaseForm({
  isSuperAdmin,
  activeShops,
  assignedShopName,
  onSubmit,
  onCancel,
  onValuesChange,
}: PurchaseFormProps) {
  const [customerName, setCustomerName] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [product, setProduct] = useState('')
  const [amount, setAmount] = useState('')
  const [shopId, setShopId] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const submittingRef = useRef(false)

  const selectedShopName = isSuperAdmin
    ? activeShops.find((shop) => shop.id === shopId)?.name
    : assignedShopName ?? undefined

  useEffect(() => {
    onValuesChange?.({
      customerName: customerName.trim(),
      product: product.trim(),
      amount: amount.trim(),
      shopName: selectedShopName,
    })
  }, [customerName, product, amount, selectedShopName, onValuesChange])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (submittingRef.current) return

    const name = customerName.trim()
    if (!name) {
      setError('Customer name is required.')
      return
    }
    if (!customerPhone.trim()) {
      setError('Customer phone is required.')
      return
    }
    if (!product.trim()) {
      setError('Product is required.')
      return
    }
    if (!amount.trim() || !AMOUNT_RE.test(amount.trim())) {
      setError('Enter a valid amount.')
      return
    }
    if (isSuperAdmin && !shopId) {
      setError('Select a shop.')
      return
    }

    const payload: PurchaseCreatePayload = {
      customer: { name, phone: customerPhone.trim() },
      product: product.trim(),
      amount: amount.trim(),
    }
    if (isSuperAdmin) {
      payload.shop_id = shopId
    }

    submittingRef.current = true
    setSubmitting(true)
    setError(null)
    try {
      await onSubmit(payload)
      setCustomerName('')
      setCustomerPhone('')
      setProduct('')
      setAmount('')
      if (isSuperAdmin) setShopId('')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to record purchase.')
    } finally {
      submittingRef.current = false
      setSubmitting(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-4" noValidate>
      <fieldset>
        <legend className="text-sm font-semibold text-slate-900">Customer Information</legend>
        <div className="mt-3 space-y-4">
          <div>
            <label htmlFor="purchase-customer-name" className="block text-sm font-medium text-slate-700">
              Customer Name <span className="text-danger-600">*</span>
            </label>
            <input
              id="purchase-customer-name"
              value={customerName}
              onChange={(event) => setCustomerName(event.target.value)}
              required
              className={inputClass}
              placeholder="e.g. John Mensah"
            />
          </div>
          <div>
            <label htmlFor="purchase-customer-phone" className="block text-sm font-medium text-slate-700">
              Customer Phone <span className="text-danger-600">*</span>
            </label>
            <input
              id="purchase-customer-phone"
              type="tel"
              value={customerPhone}
              onChange={(event) => setCustomerPhone(event.target.value)}
              required
              className={inputClass}
              placeholder="e.g. 0240000000"
            />
          </div>
        </div>
      </fieldset>

      <fieldset>
        <legend className="text-sm font-semibold text-slate-900">Purchase Information</legend>
        <div className="mt-3 space-y-4">
          <div>
            <label htmlFor="purchase-product" className="block text-sm font-medium text-slate-700">
              Product / Item <span className="text-danger-600">*</span>
            </label>
            <input
              id="purchase-product"
              value={product}
              onChange={(event) => setProduct(event.target.value)}
              required
              className={inputClass}
              placeholder="e.g. Samsung A25"
            />
          </div>
          <div>
            <label htmlFor="purchase-amount" className="block text-sm font-medium text-slate-700">
              Amount (GHS) <span className="text-danger-600">*</span>
            </label>
            <div className="relative">
              <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-sm text-slate-500">
                GHS
              </span>
              <input
                id="purchase-amount"
                type="text"
                inputMode="decimal"
                value={amount}
                onChange={(event) => setAmount(event.target.value)}
                required
                className={`${inputClass} pl-12`}
                placeholder="0.00"
              />
            </div>
          </div>
          {isSuperAdmin && (
            <div>
              <label htmlFor="purchase-shop" className="block text-sm font-medium text-slate-700">
                Shop <span className="text-danger-600">*</span>
              </label>
              <select
                id="purchase-shop"
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
          {!isSuperAdmin && (
            <div className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
              Shop: <span className="font-medium">{assignedShopName ?? 'Your assigned shop'}</span>
            </div>
          )}
        </div>
      </fieldset>

      <ErrorMessage message={error ?? undefined} title="Unable to record purchase" />

      <div className="flex justify-end gap-2 pt-1">
        {onCancel && (
          <button
            type="button"
            onClick={onCancel}
            className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Cancel
          </button>
        )}
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
        >
          {submitting && (
            <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
          )}
          {submitting ? 'Recording Purchase…' : 'Record Purchase & Send SMS'}
        </button>
      </div>
    </form>
  )
}
