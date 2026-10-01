import type { ReportPreset, Shop } from '../../types'

const PRESET_OPTIONS: { label: string; value: ReportPreset }[] = [
  { label: 'Today', value: 'today' },
  { label: 'Yesterday', value: 'yesterday' },
  { label: 'Last 7 Days', value: 'last_7_days' },
  { label: 'Last 30 Days', value: 'last_30_days' },
  { label: 'This Month', value: 'this_month' },
  { label: 'Previous Month', value: 'previous_month' },
  { label: 'Custom', value: 'custom' },
]

const inputClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30'

interface ReportFiltersProps {
  preset: ReportPreset
  onPresetChange: (value: ReportPreset) => void
  dateFrom: string
  onDateFromChange: (value: string) => void
  dateTo: string
  onDateToChange: (value: string) => void
  shops: Shop[]
  shopId: string
  onShopChange: (value: string) => void
  isSuperAdmin: boolean
  assignedShopName: string | null
}

export default function ReportFilters({
  preset,
  onPresetChange,
  dateFrom,
  onDateFromChange,
  dateTo,
  onDateToChange,
  shops,
  shopId,
  onShopChange,
  isSuperAdmin,
  assignedShopName,
}: ReportFiltersProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex flex-col gap-4 lg:flex-row lg:flex-wrap lg:items-end">
        <div className="w-full sm:w-auto">
          <label htmlFor="report-preset" className="mb-1 block text-xs font-medium text-slate-500">
            Date Range
          </label>
          <select
            id="report-preset"
            value={preset}
            onChange={(event) => onPresetChange(event.target.value as ReportPreset)}
            className={inputClass}
          >
            {PRESET_OPTIONS.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        {preset === 'custom' && (
          <>
            <div className="w-full sm:w-auto">
              <label htmlFor="report-date-from" className="mb-1 block text-xs font-medium text-slate-500">
                From
              </label>
              <input
                id="report-date-from"
                type="date"
                value={dateFrom}
                onChange={(event) => onDateFromChange(event.target.value)}
                className={inputClass}
              />
            </div>
            <div className="w-full sm:w-auto">
              <label htmlFor="report-date-to" className="mb-1 block text-xs font-medium text-slate-500">
                To
              </label>
              <input
                id="report-date-to"
                type="date"
                value={dateTo}
                onChange={(event) => onDateToChange(event.target.value)}
                className={inputClass}
              />
            </div>
          </>
        )}

        {isSuperAdmin ? (
          <div className="w-full sm:w-auto">
            <label htmlFor="report-shop" className="mb-1 block text-xs font-medium text-slate-500">
              Shop
            </label>
            <select
              id="report-shop"
              value={shopId}
              onChange={(event) => onShopChange(event.target.value)}
              className={inputClass}
            >
              <option value="">All Shops</option>
              {shops.map((shop) => (
                <option key={shop.id} value={shop.id}>
                  {shop.name}
                </option>
              ))}
            </select>
          </div>
        ) : (
          <div className="w-full sm:w-auto">
            <p className="mb-1 block text-xs font-medium text-slate-500">Shop</p>
            <p className="rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-600">
              {assignedShopName ?? 'Your assigned shop'}
            </p>
          </div>
        )}
      </div>
    </section>
  )
}
