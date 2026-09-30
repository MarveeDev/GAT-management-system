import type { Shop } from '../../types'
import { formatDateTime } from '../../utils/format'

export default function ShopDetails({ shop }: { shop: Shop }) {
  const rows: [string, string][] = [
    ['Name', shop.name],
    ['Location', shop.location || '—'],
    ['Phone', shop.phone || '—'],
    ['Sender ID', shop.sender_id || '—'],
    ['Status', shop.status === 'ACTIVE' ? 'Active' : 'Inactive'],
    ['Created', formatDateTime(shop.created_at)],
    ['Updated', formatDateTime(shop.updated_at)],
  ]

  return (
    <dl className="space-y-3">
      {rows.map(([label, value]) => (
        <div
          key={label}
          className="flex items-center justify-between gap-4 border-b border-slate-100 pb-2 text-sm last:border-0 last:pb-0"
        >
          <dt className="text-slate-500">{label}</dt>
          <dd className="text-right font-medium text-slate-900">{value}</dd>
        </div>
      ))}
    </dl>
  )
}
