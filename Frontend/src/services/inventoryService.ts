import { api, buildQuery } from '../lib/api'
import type { Inventory, InventorySetPayload } from '../types'

export interface InventoryListParams {
  shop_id?: string
  product_id?: string
}

export function listInventory(
  params: InventoryListParams = {},
): Promise<{ inventory: Inventory[] }> {
  return api.get<{ inventory: Inventory[] }>(`/inventory${buildQuery(params)}`, { auth: true })
}

export function setInventory(payload: InventorySetPayload): Promise<{ inventory: Inventory }> {
  return api.post<{ inventory: Inventory }>('/inventory', payload, { auth: true })
}
