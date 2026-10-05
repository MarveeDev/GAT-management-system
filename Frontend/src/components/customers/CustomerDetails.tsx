import type { CustomerSummary, Purchase } from '../../types'
import { formatCurrency, formatDateTime } from '../../utils/format'

interface CustomerDetailsProps {
  entry: CustomerSummary
  purchases: Purchase[]
  shopNames: Map<string, string>
}

export default function CustomerDetails({ entry, purchases, shopNames }: CustomerDetailsProps) {
  const info: [string, string][] = [
    ['Name', entry.customer.name],
    ['Phone', entry.customer.phone || '—'],
    ['Email', entry.customer.email || '—'],
    ['Customer ID', entry.customer.id],
    ['Total Purchases', String(entry.purchase_count)],
    ['Last Purchase', formatDateTime(entry.last_purchase_at)],
  ]

  return (
    <div className="space-y-5">
      <dl className="space-y-3">
        {info.map(([label, value]) => (
          <div
            key={label}
            className="flex items-start justify-between gap-4 border-b border-slate-100 pb-2 text-sm last:border-0 last:pb-0"
          >
            <dt className="shrink-0 text-slate-500">{label}</dt>
            <dd className="min-w-0 break-all text-right font-medium text-slate-900">{value}</dd>
          </div>
        ))}
      </dl>

      <div>
        <h3 className="text-sm font-semibold text-slate-900">Purchase History</h3>
        {purchases.length === 0 ? (
          <p className="mt-2 text-sm text-slate-500">No purchases recorded.</p>
        ) : (
          <div className="mt-2 overflow-x-auto rounded-lg border border-slate-200">
            <table className="w-full min-w-[480px] text-sm">
              <thead>
                <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
                  <th className="px-3 py-2 font-semibold">Date</th>
                  <th className="px-3 py-2 font-semibold">Product</th>
                  <th className="px-3 py-2 font-semibold">Amount</th>
                  <th className="px-3 py-2 font-semibold">Shop</th>
                </tr>
              </thead>
              <tbody>
                {purchases.map((purchase) => (
                  <tr key={purchase.id} className="border-b border-slate-100 last:border-0">
                    <td className="whitespace-nowrap px-3 py-2 text-slate-500">
                      {formatDateTime(purchase.created_at)}
                    </td>
                    <td className="px-3 py-2 text-slate-700">{purchase.product}</td>
                    <td className="px-3 py-2 text-slate-900">{formatCurrency(purchase.amount)}</td>
                    <td className="px-3 py-2 text-slate-600">
                      {shopNames.get(purchase.shop_id) ?? '—'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  )
}
