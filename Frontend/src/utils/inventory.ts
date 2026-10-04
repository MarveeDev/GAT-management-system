// UI-only low-stock threshold. The backend does not yet expose a configurable
// low-stock setting, so this value is used purely for visual indication and is
// intentionally easy to change. "Out of stock" always means quantity === 0.
export const LOW_STOCK_THRESHOLD = 5

export type StockLevel = 'IN_STOCK' | 'LOW_STOCK' | 'OUT_OF_STOCK'

export function stockLevel(quantity: number): StockLevel {
  if (quantity <= 0) return 'OUT_OF_STOCK'
  if (quantity <= LOW_STOCK_THRESHOLD) return 'LOW_STOCK'
  return 'IN_STOCK'
}
