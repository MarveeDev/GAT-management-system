import type { Purchase } from '../../types'
import { formatCurrency, formatDateTime } from '../../utils/format'
import EmptyState from '../EmptyState'
import ErrorMessage from '../ErrorMessage'
import LoadingSpinner from '../LoadingSpinner'

interface RecentPurchasesProps {
  purchases: Purchase[] | null
  loading: boolean
  error: string | null
  shopNames: Map<string, string>
}

export default function RecentPurchases({
  purchases,
  loading,
  error,
  shopNames,
}: RecentPurchasesProps) {
  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-900">Recent Purchases</h2>
      </div>

      <div className="p-5">
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : !purchases || purchases.length === 0 ? (
          <EmptyState
            title="No purchases yet"
            description="Purchases will appear here once they are recorded."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full min-w-[560px] text-sm">
              <thead>
                <tr className="border-b border-slate-200 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="pb-2 pr-4 font-semibold">Customer</th>
                  <th className="pb-2 pr-4 font-semibold">Product</th>
                  <th className="pb-2 pr-4 font-semibold">Amount</th>
                  <th className="pb-2 pr-4 font-semibold">Shop</th>
                  <th className="pb-2 font-semibold">Date</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((purchase) => (
                  <tr key={purchase.id} className="border-b border-slate-100 last:border-0">
                    <td className="py-2.5 pr-4 font-medium text-slate-900">
                      {purchase.customer?.name ?? '—'}
                    </td>
                    <td className="py-2.5 pr-4 text-slate-600">{purchase.product}</td>
                    <td className="py-2.5 pr-4 text-slate-900">{formatCurrency(purchase.amount)}</td>
                    <td className="py-2.5 pr-4 text-slate-600">
                      {shopNames.get(purchase.shop_id) ?? '—'}
                    </td>
                    <td className="py-2.5 text-slate-500">{formatDateTime(purchase.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </section>
  )
}
