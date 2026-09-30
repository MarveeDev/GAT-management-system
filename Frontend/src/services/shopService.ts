import { api } from '../lib/api'
import type { Shop, ShopCreatePayload, ShopUpdatePayload } from '../types'

export function listShops(): Promise<{ shops: Shop[] }> {
  return api.get<{ shops: Shop[] }>('/shops', { auth: true })
}

export function createShop(payload: ShopCreatePayload): Promise<{ shop: Shop }> {
  return api.post<{ shop: Shop }>('/shops', payload, { auth: true })
}

export function getShop(id: string): Promise<{ shop: Shop }> {
  return api.get<{ shop: Shop }>(`/shops/${id}`, { auth: true })
}

export function updateShop(id: string, payload: ShopUpdatePayload): Promise<{ shop: Shop }> {
  return api.patch<{ shop: Shop }>(`/shops/${id}`, payload, { auth: true })
}
