import { Eye } from 'lucide-react'

import type { Purchase } from '../../types'
import { formatCurrency, formatDateTime } from '../../utils/format'
import SmsStatusBadge from '../SmsStatusBadge'

interface PurchaseTableProps {
  purchases: Purchase[]
  shopNames: Map<string, string>
  smsStatus: Map<string, string>
  onDetails: (purchase: Purchase) => void
}

export default function PurchaseTable({
  purchases,
  shopNames,
  smsStatus,
  onDetails,
}: PurchaseTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[820px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Date</th>
            <th className="px-5 py-3 font-semibold">Customer</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Product</th>
            <th className="px-5 py-3 font-semibold">Amount</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 font-semibold">SMS</th>
            <th className="px-5 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {purchases.map((purchase) => (
            <tr key={purchase.id} className="border-b border-slate-100 last:border-0">
              <td className="whitespace-nowrap px-5 py-3 text-slate-500">
                {formatDateTime(purchase.created_at)}
              </td>
              <td className="px-5 py-3 font-medium text-slate-900">
                {purchase.customer?.name ?? '—'}
              </td>
              <td className="px-5 py-3 text-slate-600">{purchase.customer?.phone || '—'}</td>
              <td className="px-5 py-3 text-slate-600">{purchase.product}</td>
              <td className="px-5 py-3 text-slate-900">{formatCurrency(purchase.amount)}</td>
              <td className="px-5 py-3 text-slate-600">
                {shopNames.get(purchase.shop_id) ?? '—'}
              </td>
              <td className="px-5 py-3">
                <SmsStatusBadge status={smsStatus.get(purchase.id)} />
              </td>
              <td className="px-5 py-3 text-right">
                <button
                  type="button"
                  onClick={() => onDetails(purchase)}
                  aria-label={`View details for ${purchase.product}`}
                  title="Details"
                  className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                >
                  <Eye className="h-4 w-4" aria-hidden="true" />
                </button>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
