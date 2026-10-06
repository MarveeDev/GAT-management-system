import type { StaffReportRow } from '../../types'
import { formatCurrency, formatRole } from '../../utils/format'

interface StaffReportTableProps {
  rows: StaffReportRow[]
}

export default function StaffReportTable({ rows }: StaffReportTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[760px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Staff</th>
            <th className="px-5 py-3 font-semibold">Role</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 font-semibold">Purchases</th>
            <th className="px-5 py-3 font-semibold">Sales</th>
            <th className="px-5 py-3 font-semibold">Avg Purchase</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={`${row.staff.id}-${row.shop?.id ?? 'none'}`} className="border-b border-slate-100 last:border-0">
              <td className="px-5 py-3 font-medium text-slate-900">{row.staff.name}</td>
              <td className="px-5 py-3 text-slate-600">{formatRole(row.staff.role)}</td>
              <td className="px-5 py-3 text-slate-600">{row.shop?.name ?? '—'}</td>
              <td className="px-5 py-3 text-slate-700">{row.metrics.total_purchases}</td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.total_sales)}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-700">
                {formatCurrency(row.metrics.average_purchase_value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
