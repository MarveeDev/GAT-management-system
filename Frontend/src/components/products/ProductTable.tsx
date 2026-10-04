import { PackagePlus, Pencil } from 'lucide-react'

import type { Product, Shop } from '../../types'
import { formatCurrency } from '../../utils/format'
import { stockLevel } from '../../utils/inventory'
import ProductStatusBadge from './ProductStatusBadge'
import StockBadge from './StockBadge'

interface ProductTableProps {
  products: Product[]
  shops: Shop[]
  selectedShopId: string
  inventoryByProduct: Map<string, Map<string, number>>
  isSuperAdmin: boolean
  onEdit?: (product: Product) => void
  onAdjustStock?: (product: Product) => void
}

function quantityColor(quantity: number): string {
  const level = stockLevel(quantity)
  if (level === 'OUT_OF_STOCK') return 'text-danger-600'
  if (level === 'LOW_STOCK') return 'text-warning-600'
  return 'text-slate-900'
}

function totalStock(productId: string, inventoryByProduct: Map<string, Map<string, number>>): number {
  const byShop = inventoryByProduct.get(productId)
  if (!byShop) return 0
  let total = 0
  for (const quantity of byShop.values()) total += quantity
  return total
}

export default function ProductTable({
  products,
  shops,
  selectedShopId,
  inventoryByProduct,
  isSuperAdmin,
  onEdit,
  onAdjustStock,
}: ProductTableProps) {
  const allShops = selectedShopId === 'ALL'
  const showActions = isSuperAdmin

  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[760px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Product</th>
            <th className="px-5 py-3 font-semibold">Category</th>
            <th className="px-5 py-3 font-semibold">Price Range</th>
            {allShops ? (
              <>
                {shops.map((shop) => (
                  <th key={shop.id} className="px-5 py-3 font-semibold">
                    {shop.name}
                  </th>
                ))}
                <th className="px-5 py-3 font-semibold">Total</th>
              </>
            ) : (
              <>
                <th className="px-5 py-3 font-semibold">Stock</th>
                <th className="px-5 py-3 font-semibold">Availability</th>
              </>
            )}
            <th className="px-5 py-3 font-semibold">Product Status</th>
            {showActions && (
              <th className="px-5 py-3 text-right font-semibold">Actions</th>
            )}
          </tr>
        </thead>
        <tbody>
          {products.map((product) => {
            const byShop = inventoryByProduct.get(product.id)
            const total = totalStock(product.id, inventoryByProduct)
            const shopQuantity = byShop?.get(selectedShopId) ?? 0
            return (
              <tr key={product.id} className="border-b border-slate-100 last:border-0">
                <td className="px-5 py-3 font-medium text-slate-900">{product.name}</td>
                <td className="px-5 py-3 text-slate-600">{product.category || '—'}</td>
                <td className="whitespace-nowrap px-5 py-3 text-slate-600">
                  {formatCurrency(product.minimum_price)} – {formatCurrency(product.maximum_price)}
                </td>

                {allShops ? (
                  <>
                    {shops.map((shop) => {
                      const quantity = byShop?.get(shop.id) ?? 0
                      return (
                        <td key={shop.id} className="px-5 py-3">
                          <div className="flex flex-col items-start gap-1">
                            <span className={`font-medium ${quantityColor(quantity)}`}>{quantity}</span>
                            <StockBadge quantity={quantity} />
                          </div>
                        </td>
                      )
                    })}
                    <td className={`px-5 py-3 font-medium ${quantityColor(total)}`}>{total}</td>
                  </>
                ) : (
                  <>
                    <td className={`px-5 py-3 font-medium ${quantityColor(shopQuantity)}`}>
                      {shopQuantity}
                    </td>
                    <td className="px-5 py-3">
                      <StockBadge quantity={shopQuantity} />
                    </td>
                  </>
                )}

                <td className="px-5 py-3">
                  <ProductStatusBadge status={product.status} />
                </td>

                {showActions && (
                  <td className="px-5 py-3">
                    <div className="flex items-center justify-end gap-1">
                      {onEdit && (
                        <button
                          type="button"
                          onClick={() => onEdit(product)}
                          aria-label={`Edit ${product.name}`}
                          title="Edit"
                          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                        >
                          <Pencil className="h-4 w-4" aria-hidden="true" />
                        </button>
                      )}
                      {!allShops && onAdjustStock && (
                        <button
                          type="button"
                          onClick={() => onAdjustStock(product)}
                          aria-label={`Adjust stock for ${product.name}`}
                          title="Adjust Stock"
                          className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                        >
                          <PackagePlus className="h-4 w-4" aria-hidden="true" />
                        </button>
                      )}
                    </div>
                  </td>
                )}
              </tr>
            )
          })}
        </tbody>
      </table>
    </div>
  )
}
