import type { ShopReportRow } from '../../types'
import { formatCurrency } from '../../utils/format'

interface ShopReportTableProps {
  rows: ShopReportRow[]
}

export default function ShopReportTable({ rows }: ShopReportTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[900px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 font-semibold">Purchases</th>
            <th className="px-5 py-3 font-semibold">Sales</th>
            <th className="px-5 py-3 font-semibold">Avg Purchase</th>
            <th className="px-5 py-3 font-semibold">Customers</th>
            <th className="px-5 py-3 font-semibold">SMS Sent</th>
            <th className="px-5 py-3 font-semibold">SMS Failed</th>
            <th className="px-5 py-3 font-semibold">Success Rate</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.shop.id} className="border-b border-slate-100 last:border-0">
              <td className="px-5 py-3 font-medium text-slate-900">{row.shop.name}</td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.total_purchases}</td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.total_sales)}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.average_purchase_value)}
              </td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.unique_customers}</td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.sms_sent}</td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.sms_failed}</td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.sms_success_rate}%</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
