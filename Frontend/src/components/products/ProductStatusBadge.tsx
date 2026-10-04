import type { ProductStatus } from '../../types'

interface ProductStatusBadgeProps {
  status: ProductStatus
}

export default function ProductStatusBadge({ status }: ProductStatusBadgeProps) {
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
