import type { SmsReportRow } from '../../types'
import { formatDateTime } from '../../utils/format'
import SmsStatusBadge from '../SmsStatusBadge'

interface SmsReportTableProps {
  rows: SmsReportRow[]
}

export default function SmsReportTable({ rows }: SmsReportTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[820px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Date</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Customer</th>
            <th className="px-5 py-3 font-semibold">Status</th>
            <th className="px-5 py-3 font-semibold">Provider</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row) => (
            <tr key={row.id} className="border-b border-slate-100 last:border-0">
              <td className="whitespace-nowrap px-5 py-3 text-slate-500">
                {formatDateTime(row.date)}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">{row.phone_number}</td>
              <td className="px-5 py-3 text-slate-700">{row.customer?.name ?? '—'}</td>
              <td className="px-5 py-3">
                <SmsStatusBadge status={row.status} />
                {row.error_message && (
                  <p className="mt-1 max-w-xs truncate text-xs text-slate-400" title={row.error_message}>
                    {row.error_message}
                  </p>
                )}
              </td>
              <td className="px-5 py-3 text-slate-600">{row.provider || '—'}</td>
              <td className="px-5 py-3 text-slate-600">{row.shop?.name ?? '—'}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
