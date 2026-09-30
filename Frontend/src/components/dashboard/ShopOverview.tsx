import type { Shop } from '../../types'
import EmptyState from '../EmptyState'
import ErrorMessage from '../ErrorMessage'
import LoadingSpinner from '../LoadingSpinner'

interface ShopOverviewProps {
  shops: Shop[] | null
  loading: boolean
  error: string | null
}

export default function ShopOverview({ shops, loading, error }: ShopOverviewProps) {
  const active = shops?.filter((shop) => shop.status === 'ACTIVE').length ?? 0
  const inactive = shops?.filter((shop) => shop.status === 'INACTIVE').length ?? 0

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-900">Shops</h2>
      </div>

      <div className="p-5">
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : !shops || shops.length === 0 ? (
          <EmptyState title="No shops" description="Shops will appear here once created." />
        ) : (
          <div>
            <div className="grid grid-cols-2 gap-3">
              <div className="rounded-xl bg-slate-50 px-4 py-3">
                <p className="text-xs font-medium text-slate-500">Active</p>
                <p className="text-2xl font-semibold text-success-600">{active}</p>
              </div>
              <div className="rounded-xl bg-slate-50 px-4 py-3">
                <p className="text-xs font-medium text-slate-500">Inactive</p>
                <p className="text-2xl font-semibold text-slate-500">{inactive}</p>
              </div>
            </div>

            {active > 0 && (
              <ul className="mt-4 space-y-1.5">
                {shops
                  .filter((shop) => shop.status === 'ACTIVE')
                  .map((shop) => (
                    <li
                      key={shop.id}
                      className="flex items-center gap-2 text-sm text-slate-600"
                    >
                      <span className="h-2 w-2 rounded-full bg-success-600" aria-hidden="true" />
                      <span className="truncate">{shop.name}</span>
                    </li>
                  ))}
              </ul>
            )}
          </div>
        )}
      </div>
    </section>
  )
}
