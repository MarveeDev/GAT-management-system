import { api, buildQuery } from '../lib/api'
import type { Product, ProductCreatePayload, ProductUpdatePayload } from '../types'

export interface ProductListParams {
  search?: string
  status?: string
}

export function listProducts(params: ProductListParams = {}): Promise<{ products: Product[] }> {
  return api.get<{ products: Product[] }>(`/products${buildQuery(params)}`, { auth: true })
}

export function getProduct(id: string): Promise<{ product: Product }> {
  return api.get<{ product: Product }>(`/products/${id}`, { auth: true })
}

export function createProduct(payload: ProductCreatePayload): Promise<{ product: Product }> {
  return api.post<{ product: Product }>('/products', payload, { auth: true })
}

export function updateProduct(
  id: string,
  payload: ProductUpdatePayload,
): Promise<{ product: Product }> {
  return api.patch<{ product: Product }>(`/products/${id}`, payload, { auth: true })
}
