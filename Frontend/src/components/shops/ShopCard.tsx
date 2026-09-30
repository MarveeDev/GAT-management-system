import { Eye, MapPin, Pencil, Phone } from 'lucide-react'

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

export default function ShopCard({ shop, onEdit, onDetails }: ShopCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-3">
        <div className="min-w-0">
          <h3 className="truncate text-base font-semibold text-slate-900">{shop.name}</h3>
          {shop.location && (
            <p className="mt-1 flex items-center gap-1.5 text-sm text-slate-500">
              <MapPin className="h-3.5 w-3.5 shrink-0" aria-hidden="true" />
              <span className="truncate">{shop.location}</span>
            </p>
          )}
        </div>
        <StatusBadge status={shop.status} />
      </div>

      <dl className="mt-4 space-y-1.5 text-sm">
        {shop.phone && (
          <div className="flex items-center gap-1.5 text-slate-600">
            <Phone className="h-3.5 w-3.5 shrink-0 text-slate-400" aria-hidden="true" />
            <dd>{shop.phone}</dd>
          </div>
        )}
        {shop.sender_id && (
          <div className="text-slate-600">
            <span className="text-slate-400">Sender ID:</span> {shop.sender_id}
          </div>
        )}
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
