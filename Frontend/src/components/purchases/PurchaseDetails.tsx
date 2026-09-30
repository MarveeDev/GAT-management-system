import type { Purchase } from '../../types'
import { formatCurrency, formatDateTime } from '../../utils/format'
import SmsStatusBadge from '../SmsStatusBadge'

interface PurchaseDetailsProps {
  purchase: Purchase
  shopName: string | null
  smsStatus: string | null
}

export default function PurchaseDetails({ purchase, shopName, smsStatus }: PurchaseDetailsProps) {
  const rows: [string, string][] = [
    ['Customer', purchase.customer?.name ?? '—'],
    ['Phone', purchase.customer?.phone || '—'],
    ['Product', purchase.product],
    ['Amount', formatCurrency(purchase.amount)],
    ['Currency', purchase.currency],
    ['Shop', shopName || '—'],
    ['Date', formatDateTime(purchase.created_at)],
    ['Purchase ID', purchase.id],
  ]

  return (
    <div className="space-y-4">
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

      <div className="flex items-center justify-between gap-4 text-sm">
        <span className="text-slate-500">SMS Status</span>
        <SmsStatusBadge status={smsStatus} />
      </div>

      <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
        Purchases cannot be edited or deleted.
      </p>
    </div>
  )
}
