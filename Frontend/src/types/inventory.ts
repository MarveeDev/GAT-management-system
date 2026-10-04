import type { Product } from './product'

export interface InventoryShop {
  id: string
  name: string
}

export interface Inventory {
  id: string
  shop_id: string
  product_id: string
  quantity: number
  created_at: string | null
  updated_at: string | null
  product?: Product
  shop?: InventoryShop
}

export interface InventorySetPayload {
  product_id: string
  shop_id: string
  quantity: number
}
