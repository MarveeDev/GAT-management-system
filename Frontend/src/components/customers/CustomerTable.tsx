import { Eye } from 'lucide-react'

import type { CustomerSummary } from '../../types'
import { formatDateTime } from '../../utils/format'

interface CustomerTableProps {
  entries: CustomerSummary[]
  onDetails: (entry: CustomerSummary) => void
}

export default function CustomerTable({ entries, onDetails }: CustomerTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[720px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Customer</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Purchases</th>
            <th className="px-5 py-3 font-semibold">Last Purchase</th>
            <th className="px-5 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {entries.map((entry) => (
            <tr key={entry.customer.id} className="border-b border-slate-100 last:border-0">
              <td className="px-5 py-3">
                <span className="font-medium text-slate-900">{entry.customer.name}</span>
                {entry.customer.email && (
                  <p className="text-xs text-slate-500">{entry.customer.email}</p>
                )}
              </td>
              <td className="px-5 py-3 text-slate-600">{entry.customer.phone || '—'}</td>
              <td className="px-5 py-3 text-slate-600">{entry.purchase_count}</td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">
                {formatDateTime(entry.last_purchase_at)}
              </td>
              <td className="px-5 py-3 text-right">
                <button
                  type="button"
                  onClick={() => onDetails(entry)}
                  aria-label={`View details for ${entry.customer.name}`}
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
