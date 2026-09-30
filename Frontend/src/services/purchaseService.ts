import { api, buildQuery } from '../lib/api'
import type {
  Pagination,
  Purchase,
  PurchaseCreatePayload,
  PurchaseCreateResponse,
  PurchaseListParams,
} from '../types'

export interface PurchaseListResponse {
  purchases: Purchase[]
  pagination: Pagination
}

export function createPurchase(payload: PurchaseCreatePayload): Promise<PurchaseCreateResponse> {
  return api.post<PurchaseCreateResponse>('/purchases', payload, { auth: true })
}

export function listPurchases(params: PurchaseListParams = {}): Promise<PurchaseListResponse> {
  return api.get<PurchaseListResponse>(`/purchases${buildQuery(params)}`, { auth: true })
}

export function getPurchase(id: string): Promise<{ purchase: Purchase }> {
  return api.get<{ purchase: Purchase }>(`/purchases/${id}`, { auth: true })
}
