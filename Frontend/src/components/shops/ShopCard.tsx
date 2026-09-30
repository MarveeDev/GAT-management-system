import { Eye, Hash, MapPin, Pencil, Phone } from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

import type { Shop } from '../../types'

interface ShopCardProps {
  shop: Shop
  onEdit?: (shop: Shop) => void
  onDetails?: (shop: Shop) => void
}

function StatusBadge({ status }: { status: Shop['status'] }) {
  if (status === 'ACTIVE') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-medium text-success-700">
        <span className="h-1.5 w-1.5 rounded-full bg-success-600" aria-hidden="true" />
        Active
      </span>
    )
  }
  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-medium text-slate-600">
      <span className="h-1.5 w-1.5 rounded-full bg-slate-400" aria-hidden="true" />
      Inactive
    </span>
  )
}

function InfoRow({
  icon: Icon,
  label,
  value,
}: {
  icon: LucideIcon
  label: string
  value: string | undefined
}) {
  return (
    <div className="flex items-start gap-1.5">
      <Icon className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
      <dt className="shrink-0 font-medium text-slate-500">{label}</dt>
      <dd className={`min-w-0 break-words ${value ? 'text-slate-700' : 'text-slate-400'}`}>
        {value || 'Not provided'}
      </dd>
    </div>
  )
}

export default function ShopCard({ shop, onEdit, onDetails }: ShopCardProps) {
  const location = shop.location?.trim() || undefined
  const phone = shop.phone?.trim() || undefined
  const senderId = shop.sender_id?.trim() || undefined

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <h3 className="min-w-0 break-words text-base font-semibold leading-snug text-slate-900">
          {shop.name}
        </h3>
        <span className="shrink-0">
          <StatusBadge status={shop.status} />
        </span>
      </div>

      <dl className="mt-4 space-y-2 text-sm">
        <InfoRow icon={MapPin} label="Location:" value={location} />
        <InfoRow icon={Phone} label="Phone:" value={phone} />
        <InfoRow icon={Hash} label="Sender ID:" value={senderId} />
      </dl>

      {(onEdit || onDetails) && (
        <div className="mt-4 flex items-center gap-2 border-t border-slate-100 pt-3">
          {onDetails && (
            <button
              type="button"
              onClick={() => onDetails(shop)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
            >
              <Eye className="h-4 w-4" aria-hidden="true" />
              Details
            </button>
          )}
          {onEdit && (
            <button
              type="button"
              onClick={() => onEdit(shop)}
              className="inline-flex items-center gap-1.5 rounded-lg bg-brand-600 px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-brand-700"
            >
              <Pencil className="h-4 w-4" aria-hidden="true" />
              Edit
            </button>
          )}
        </div>
      )}
    </div>
  )
}
