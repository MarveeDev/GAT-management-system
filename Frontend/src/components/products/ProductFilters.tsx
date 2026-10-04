import { Search } from 'lucide-react'

import type { Shop } from '../../types'

export type StockFilter = 'ALL' | 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK'
export type ProductStatusFilter = 'ALL' | 'ACTIVE' | 'INACTIVE'

interface ProductFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  stock: StockFilter
  onStockChange: (value: StockFilter) => void
  status: ProductStatusFilter
  onStatusChange: (value: ProductStatusFilter) => void
  shop: string
  onShopChange: (value: string) => void
  shops: Shop[]
  showShopSelector: boolean
  showStatusFilter: boolean
}

const selectClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function ProductFilters({
  search,
  onSearchChange,
  stock,
  onStockChange,
  status,
  onStatusChange,
  shop,
  onShopChange,
  shops,
  showShopSelector,
  showStatusFilter,
}: ProductFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search by product name or category..."
          aria-label="Search products"
          className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      <div className="flex flex-wrap items-end gap-3">
        {showShopSelector && (
          <div>
            <label htmlFor="product-shop-filter" className="mb-1 block text-xs font-medium text-slate-500">
              Shop
            </label>
            <select
              id="product-shop-filter"
              value={shop}
              onChange={(event) => onShopChange(event.target.value)}
              className={selectClass}
            >
              <option value="ALL">All shops</option>
              {shops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        )}

        <div>
          <label htmlFor="product-stock-filter" className="mb-1 block text-xs font-medium text-slate-500">
            Stock
          </label>
          <select
            id="product-stock-filter"
            value={stock}
            onChange={(event) => onStockChange(event.target.value as StockFilter)}
            className={selectClass}
          >
            <option value="ALL">All Stock</option>
            <option value="IN_STOCK">In Stock</option>
            <option value="LOW_STOCK">Low Stock</option>
            <option value="OUT_OF_STOCK">Out of Stock</option>
          </select>
        </div>

        {showStatusFilter && (
          <div>
            <label htmlFor="product-status-filter" className="mb-1 block text-xs font-medium text-slate-500">
              Product Status
            </label>
            <select
              id="product-status-filter"
              value={status}
              onChange={(event) => onStatusChange(event.target.value as ProductStatusFilter)}
              className={selectClass}
            >
              <option value="ALL">All</option>
              <option value="ACTIVE">Active</option>
              <option value="INACTIVE">Inactive</option>
            </select>
          </div>
        )}
      </div>
    </div>
  )
}
