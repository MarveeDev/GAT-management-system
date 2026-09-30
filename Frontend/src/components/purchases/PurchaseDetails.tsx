import type { Purchase } from '../../types'
import { formatCurrency, formatDateTime, formatRole } from '../../utils/format'
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
    ['Purchase ID', purchase.id],
  ]

  const staff = purchase.staff
  const recordedBy: [string, string][] = [
    ['Name', staff?.name ?? '—'],
    ['Email', staff?.email ?? '—'],
    ['Role', staff ? formatRole(staff.role) : '—'],
    ['Shop', shopName || '—'],
    ['Recorded', formatDateTime(purchase.created_at)],
  ]

  return (
    <div className="space-y-5">
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

      <div className="border-t border-slate-100 pt-4">
        <h3 className="text-xs font-semibold uppercase tracking-wide text-slate-500">
          Sale Recorded By
        </h3>
        <dl className="mt-2 space-y-3">
          {recordedBy.map(([label, value]) => (
            <div
              key={label}
              className="flex items-start justify-between gap-4 border-b border-slate-100 pb-2 text-sm last:border-0 last:pb-0"
            >
              <dt className="shrink-0 text-slate-500">{label}</dt>
              <dd className="min-w-0 break-all text-right font-medium text-slate-900">{value}</dd>
            </div>
          ))}
        </dl>
      </div>

      <p className="rounded-lg bg-slate-50 px-3 py-2 text-xs text-slate-500">
        Purchases cannot be edited or deleted.
      </p>
    </div>
  )
}
