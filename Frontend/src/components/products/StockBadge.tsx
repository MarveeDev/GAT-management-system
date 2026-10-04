import { stockLevel } from '../../utils/inventory'

interface StockBadgeProps {
  quantity: number
}

export default function StockBadge({ quantity }: StockBadgeProps) {
  const level = stockLevel(quantity)

  if (level === 'OUT_OF_STOCK') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-danger-50 px-2.5 py-0.5 text-xs font-medium text-danger-700">
        <span className="h-1.5 w-1.5 rounded-full bg-danger-600" aria-hidden="true" />
        Out of Stock
      </span>
    )
  }

  if (level === 'LOW_STOCK') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-warning-50 px-2.5 py-0.5 text-xs font-medium text-warning-600">
        <span className="h-1.5 w-1.5 rounded-full bg-warning-500" aria-hidden="true" />
        Low Stock
      </span>
    )
  }

  return (
    <span className="inline-flex items-center gap-1.5 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-medium text-success-700">
      <span className="h-1.5 w-1.5 rounded-full bg-success-600" aria-hidden="true" />
      In Stock
    </span>
  )
}
