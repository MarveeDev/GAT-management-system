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

const ALL_PURCHASES_PAGE_SIZE = 100
const ALL_PURCHASES_MAX_PAGES = 100

export async function listAllPurchases(): Promise<Purchase[]> {
  const all: Purchase[] = []
  let page = 1
  while (page <= ALL_PURCHASES_MAX_PAGES) {
    const res = await listPurchases({ page, per_page: ALL_PURCHASES_PAGE_SIZE })
    all.push(...res.purchases)
    if (page >= res.pagination.pages) break
    page += 1
  }
  return all
}
