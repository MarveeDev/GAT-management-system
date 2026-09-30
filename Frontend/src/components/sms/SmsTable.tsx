import { Eye, RotateCw } from 'lucide-react'

import type { SMSLog } from '../../types'
import { formatDateTime } from '../../utils/format'
import SmsStatusBadge from '../SmsStatusBadge'

interface SmsTableProps {
  logs: SMSLog[]
  shopNames: Map<string, string>
  onDetails: (log: SMSLog) => void
  onRetry: (log: SMSLog) => void
}

export default function SmsTable({ logs, shopNames, onDetails, onRetry }: SmsTableProps) {
  return (
    <div className="overflow-x-auto rounded-2xl border border-slate-200 bg-white shadow-sm">
      <table className="w-full min-w-[860px] text-sm">
        <thead>
          <tr className="border-b border-slate-200 bg-slate-50 text-left text-xs font-semibold uppercase tracking-wide text-slate-500">
            <th className="px-5 py-3 font-semibold">Date</th>
            <th className="px-5 py-3 font-semibold">Phone</th>
            <th className="px-5 py-3 font-semibold">Message</th>
            <th className="px-5 py-3 font-semibold">Status</th>
            <th className="px-5 py-3 font-semibold">Provider</th>
            <th className="px-5 py-3 font-semibold">Shop</th>
            <th className="px-5 py-3 text-right font-semibold">Actions</th>
          </tr>
        </thead>
        <tbody>
          {logs.map((log) => (
            <tr key={log.id} className="border-b border-slate-100 last:border-0">
              <td className="whitespace-nowrap px-5 py-3 text-slate-500">
                {formatDateTime(log.created_at)}
              </td>
              <td className="whitespace-nowrap px-5 py-3 text-slate-600">{log.phone_number}</td>
              <td className="px-5 py-3">
                <p className="max-w-xs truncate text-slate-700" title={log.message}>
                  {log.message || '—'}
                </p>
              </td>
              <td className="px-5 py-3">
                <SmsStatusBadge status={log.status} />
              </td>
              <td className="px-5 py-3 text-slate-600">{log.provider || '—'}</td>
              <td className="px-5 py-3 text-slate-600">
                {shopNames.get(log.shop_id) ?? '—'}
              </td>
              <td className="px-5 py-3 text-right">
                <div className="flex items-center justify-end gap-1">
                  <button
                    type="button"
                    onClick={() => onDetails(log)}
                    aria-label={`View SMS details`}
                    title="Details"
                    className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                  >
                    <Eye className="h-4 w-4" aria-hidden="true" />
                  </button>
                  {log.status === 'FAILED' && (
                    <button
                      type="button"
                      onClick={() => onRetry(log)}
                      aria-label={`Retry SMS to ${log.phone_number}`}
                      title="Retry"
                      className="rounded-lg p-2 text-slate-500 transition-colors hover:bg-slate-100 hover:text-slate-700"
                    >
                      <RotateCw className="h-4 w-4" aria-hidden="true" />
                    </button>
                  )}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
