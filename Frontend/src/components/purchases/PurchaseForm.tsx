import { useEffect, useRef, useState, type FormEvent } from 'react'

import type { Product, PurchaseCreatePayload, Shop } from '../../types'
import { formatCurrency } from '../../utils/format'
import StockBadge from '../products/StockBadge'
import ErrorMessage from '../ErrorMessage'
import ProductSearchSelect from './ProductSearchSelect'

export interface PurchasePreviewValues {
  customerName: string
  product: string
  amount: string
  shopName?: string
}

interface PurchaseFormProps {
  isSuperAdmin: boolean
  activeShops: Shop[]
  assignedShopId: string | null
  assignedShopName: string | null
  products: Product[]
  inventoryByProduct: Map<string, Map<string, number>>
  onSubmit: (payload: PurchaseCreatePayload) => Promise<void>
  onCancel?: () => void
  onValuesChange?: (values: PurchasePreviewValues) => void
}

const inputClass =
  'mt-1 w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

function toCents(value: string): number | null {
  const trimmed = value.trim()
  if (!/^\d+(\.\d{1,2})?$/.test(trimmed)) return null
  const [whole, frac = ''] = trimmed.split('.')
  const cents = parseInt(whole, 10) * 100 + parseInt((frac + '00').slice(0, 2), 10)
  if (!Number.isFinite(cents) || cents < 0) return null
  return cents
}

function centsToDisplay(cents: number): string {
  const dollars = Math.floor(cents / 100)
  const rem = cents % 100
  return `${dollars}.${String(rem).padStart(2, '0')}`
}

export default function PurchaseForm({
  isSuperAdmin,
  activeShops,
  assignedShopId,
  assignedShopName,
  products,
  inventoryByProduct,
  onSubmit,
  onCancel,
  onValuesChange,
}: PurchaseFormProps) {
  const [customerName, setCustomerName] = useState('')
  const [customerPhone, setCustomerPhone] = useState('')
  const [shopId, setShopId] = useState('')
  const [productId, setProductId] = useState('')
  const [quantity, setQuantity] = useState('1')
  const [unitPrice, setUnitPrice] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const submittingRef = useRef(false)

  const selectedShopName = isSuperAdmin
    ? activeShops.find((shop) => shop.id === shopId)?.name
    : assignedShopName ?? undefined

  const effectiveShopId = isSuperAdmin ? shopId : (assignedShopId ?? '')
  const selectedProduct = products.find((product) => product.id === productId)
  const availableStock =
    selectedProduct && effectiveShopId
      ? (inventoryByProduct.get(selectedProduct.id)?.get(effectiveShopId) ?? 0)
      : 0
  const outOfStock = selectedProduct !== undefined && availableStock <= 0

  const quantityNumber = /^\d+$/.test(quantity.trim()) ? parseInt(quantity.trim(), 10) : 0
  const unitPriceCents = toCents(unitPrice)
  const totalCents =
    quantityNumber > 0 && unitPriceCents !== null ? unitPriceCents * quantityNumber : null

  useEffect(() => {
    onValuesChange?.({
      customerName: customerName.trim(),
      product: selectedProduct?.name ?? '',
      amount: totalCents !== null ? centsToDisplay(totalCents) : '',
      shopName: selectedShopName,
    })
  }, [customerName, selectedProduct?.name, totalCents, selectedShopName, onValuesChange])

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
    if (isSuperAdmin && !shopId) {
      setError('Select a shop.')
      return
    }
    if (!selectedProduct) {
      setError('Select a product.')
      return
    }
    if (!/^\d+$/.test(quantity.trim()) || quantityNumber < 1) {
      setError('Quantity must be a positive whole number.')
      return
    }
    if (unitPriceCents === null) {
      setError('Enter a valid unit price.')
      return
    }
    const minCents = toCents(selectedProduct.minimum_price)
    const maxCents = toCents(selectedProduct.maximum_price)
    if (minCents !== null && maxCents !== null) {
      if (unitPriceCents < minCents || unitPriceCents > maxCents) {
        setError(
          `Unit price must be between ${formatCurrency(selectedProduct.minimum_price)} and ${formatCurrency(selectedProduct.maximum_price)}.`,
        )
        return
      }
    }
    if (availableStock <= 0) {
      setError('This product is out of stock in this shop.')
      return
    }
    if (quantityNumber > availableStock) {
      setError(`Insufficient stock. Available: ${availableStock}, requested: ${quantityNumber}.`)
      return
    }

    const payload: PurchaseCreatePayload = {
      customer: { name, phone: customerPhone.trim() },
      product_id: selectedProduct.id,
      quantity: quantityNumber,
      unit_price: unitPrice.trim(),
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
      setProductId('')
      setQuantity('1')
      setUnitPrice('')
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
          {isSuperAdmin && (
            <div>
              <label htmlFor="purchase-shop" className="block text-sm font-medium text-slate-700">
                Shop <span className="text-danger-600">*</span>
              </label>
              <select
                id="purchase-shop"
                value={shopId}
                onChange={(event) => {
                  setShopId(event.target.value)
                  setProductId('')
                  setUnitPrice('')
                }}
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

          <div>
            <label htmlFor="purchase-product" className="block text-sm font-medium text-slate-700">
              Product <span className="text-danger-600">*</span>
            </label>
            <div className="mt-1">
              <ProductSearchSelect
                inputId="purchase-product"
                products={products}
                stockByProductAndShop={inventoryByProduct}
                effectiveShopId={effectiveShopId}
                value={productId}
                onChange={(productId) => {
                  setProductId(productId)
                  setUnitPrice('')
                }}
              />
            </div>
          </div>

          {selectedProduct && (
            <div className="rounded-lg border border-slate-200 bg-slate-50 px-3 py-3 text-sm">
              <p className="font-medium text-slate-900">{selectedProduct.name}</p>
              {selectedProduct.category && (
                <p className="mt-0.5 text-xs text-slate-500">{selectedProduct.category}</p>
              )}
              <div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-1 text-slate-600">
                <span>
                  Available Stock: <span className="font-semibold text-slate-900">{availableStock}</span>
                </span>
                <StockBadge quantity={availableStock} />
              </div>
              <p className="mt-1 text-slate-600">
                Price Range: {formatCurrency(selectedProduct.minimum_price)} –{' '}
                {formatCurrency(selectedProduct.maximum_price)}
              </p>
            </div>
          )}

          {outOfStock && (
            <p className="text-sm text-danger-600">
              This product is out of stock in this shop and cannot be sold.
            </p>
          )}

          <div className="grid grid-cols-2 gap-3">
            <div>
              <label htmlFor="purchase-quantity" className="block text-sm font-medium text-slate-700">
                Quantity <span className="text-danger-600">*</span>
              </label>
              <input
                id="purchase-quantity"
                type="text"
                inputMode="numeric"
                value={quantity}
                onChange={(event) => setQuantity(event.target.value.replace(/\D/g, ''))}
                required
                className={inputClass}
                placeholder="1"
              />
            </div>
            <div>
              <label htmlFor="purchase-unit-price" className="block text-sm font-medium text-slate-700">
                Unit Price (GHS) <span className="text-danger-600">*</span>
              </label>
              <div className="relative">
                <span className="pointer-events-none absolute inset-y-0 left-0 flex items-center pl-3 text-sm text-slate-500">
                  GHS
                </span>
                <input
                  id="purchase-unit-price"
                  type="text"
                  inputMode="decimal"
                  value={unitPrice}
                  onChange={(event) => setUnitPrice(event.target.value)}
                  required
                  className={`${inputClass} pl-12`}
                  placeholder="0.00"
                />
              </div>
            </div>
          </div>

          <div className="flex items-center justify-between rounded-lg bg-slate-50 px-3 py-2 text-sm">
            <span className="text-slate-600">Total</span>
            <span className="font-semibold text-slate-900">
              {totalCents !== null ? formatCurrency(centsToDisplay(totalCents)) : 'GHS 0.00'}
            </span>
          </div>
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
          disabled={submitting || outOfStock}
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
