import type { Inventory } from '../types/inventory'

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

export function worstStockLevel(quantities: number[]): StockLevel {
  let level: StockLevel = 'IN_STOCK'
  for (const quantity of quantities) {
    const candidate = stockLevel(quantity)
    if (candidate === 'OUT_OF_STOCK') return 'OUT_OF_STOCK'
    if (candidate === 'LOW_STOCK') level = 'LOW_STOCK'
  }
  return level
}

export function buildInventoryByProduct(
  inventory: Inventory[],
): Map<string, Map<string, number>> {
  const map = new Map<string, Map<string, number>>()
  for (const row of inventory) {
    let byShop = map.get(row.product_id)
    if (!byShop) {
      byShop = new Map()
      map.set(row.product_id, byShop)
    }
    byShop.set(row.shop_id, row.quantity)
  }
  return map
}
