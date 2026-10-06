import type { SalesReportRow } from '../../types'
import { formatCurrency, formatDateTime } from '../../utils/format'

interface SalesReportTableProps {
  rows: SalesReportRow[]
}

export default function SalesReportTable({ rows }: SalesReportTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[820px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Date</th>
            <th className="px-5 py-3 font-semibold">Customer</th>
            <th className="px-5 py-3 font-semibold">Product</th>
            <th className="px-5 py-3 font-semibold">Amount</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 font-semibold">Recorded By</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-slate-100 last:border-0">
              <td className="whitespace-nowrap px-5 py-3 text-slate-500">
                {formatDateTime(row.date)}
              </td>
              <td className="px-5 py-3 text-slate-700">{row.customer?.name ?? '—'}</td>
              <td className="px-5 py-3 text-slate-700">{row.product}</td>
              <td className="whitespace-nowrap px-5 py-3 font-medium text-slate-900">
                {formatCurrency(row.amount, row.currency)}
              </td>
              <td className="px-5 py-3 text-slate-600">{row.shop?.name ?? '—'}</td>
              <td className="px-5 py-3 text-slate-600">{row.recorded_by?.name ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
