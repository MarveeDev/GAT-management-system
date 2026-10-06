import type { CustomerReportRow } from '../../types'
import { formatCurrency } from '../../utils/format'

interface CustomerReportTableProps {
  rows: CustomerReportRow[]
}

export default function CustomerReportTable({ rows }: CustomerReportTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[760px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Customer</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Purchases</th>
            <th className="px-5 py-3 font-semibold">Total Spent</th>
            <th className="px-5 py-3 font-semibold">Avg Purchase</th>
            <th className="px-5 py-3 font-semibold">Shops</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.customer.id} className="border-b border-slate-100 last:border-0">
              <td className="px-5 py-3">
                <span className="font-medium text-slate-900">{row.customer.name}</span>
                {row.customer.email && (
                  <p className="text-xs text-slate-500">{row.customer.email}</p>
                )}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">
                {row.customer.phone || '—'}
              </td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.total_purchases}</td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.total_spent)}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.average_purchase_value)}
              </td>
              <td className="px-5 py-3 text-slate-600">
                {row.shops.map((shop) => shop.name).join(', ') || '—'}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
