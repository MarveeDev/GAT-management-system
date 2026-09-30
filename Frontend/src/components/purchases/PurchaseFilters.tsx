import { Search } from 'lucide-react'

import type { Shop } from '../../types'

interface PurchaseFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  shop: string
  onShopChange: (value: string) => void
  dateFrom: string
  onDateFromChange: (value: string) => void
  dateTo: string
  onDateToChange: (value: string) => void
  shops: Shop[]
  showShopFilter: boolean
}

const selectClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

export default function PurchaseFilters({
  search,
  onSearchChange,
  shop,
  onShopChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  shops,
  showShopFilter,
}: PurchaseFiltersProps) {
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
          placeholder="Search purchases..."
          aria-label="Search purchases"
          className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      <div className="flex flex-wrap items-end gap-3">
        {showShopFilter && (
          <div>
            <label htmlFor="purchase-shop-filter" className="mb-1 block text-xs font-medium text-slate-500">
              Shop
            </label>
            <select
              id="purchase-shop-filter"
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
          <label htmlFor="purchase-date-from" className="mb-1 block text-xs font-medium text-slate-500">
            From
          </label>
          <input
            id="purchase-date-from"
            type="date"
            value={dateFrom}
            onChange={(event) => onDateFromChange(event.target.value)}
            className={selectClass}
          />
        </div>

        <div>
          <label htmlFor="purchase-date-to" className="mb-1 block text-xs font-medium text-slate-500">
            To
          </label>
          <input
            id="purchase-date-to"
            type="date"
            value={dateTo}
            onChange={(event) => onDateToChange(event.target.value)}
            className={selectClass}
          />
        </div>
      </div>
    </div>
  )
}
