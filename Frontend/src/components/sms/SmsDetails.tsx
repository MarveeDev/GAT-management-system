import type { SMSLog } from '../../types'
import { formatDateTime } from '../../utils/format'
import SmsStatusBadge from '../SmsStatusBadge'

interface SmsDetailsProps {
  log: SMSLog
  shopName: string | null
}

function valueOrNa(value: string | null | undefined): string {
  return value || 'Not available'
}

export default function SmsDetails({ log, shopName }: SmsDetailsProps) {
  const rows: [string, string][] = [
    ['SMS ID', log.id],
    ['Date', formatDateTime(log.created_at)],
    ['Sent At', formatDateTime(log.sent_at)],
    ['Customer Phone', log.phone_number],
    ['Provider', valueOrNa(log.provider)],
    ['Provider Message ID', valueOrNa(log.provider_message_id)],
    ['Purchase ID', log.purchase_id],
    ['Shop', shopName || 'Not available'],
  ]

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="text-slate-500">Status</span>
        <SmsStatusBadge status={log.status} />
      </div>

      <dl className="space-y-3">
        {rows.map(([label, value]) => (
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
        <h3 className="text-sm font-semibold text-slate-900">Message</h3>
        <p className="mt-1 whitespace-pre-wrap rounded-lg bg-slate-50 px-3 py-2 text-sm text-slate-700">
          {log.message || '—'}
        </p>
      </div>

      {log.error_message && (
        <div className="rounded-lg border border-danger-600/20 bg-danger-50 px-3 py-2 text-sm text-danger-700">
          <p className="font-medium">Error</p>
          <p className="mt-0.5">{log.error_message}</p>
        </div>
      )}
    </div>
  )
}
