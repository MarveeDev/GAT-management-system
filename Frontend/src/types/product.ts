export type ProductStatus = 'ACTIVE' | 'INACTIVE'

export interface Product {
  id: string
  name: string
  category: string | null
  minimum_price: string
  maximum_price: string
  status: ProductStatus
  created_at: string | null
  updated_at: string | null
}

export interface ProductCreatePayload {
  name: string
  category?: string
  minimum_price: string
  maximum_price: string
  status?: ProductStatus
}

export interface ProductUpdatePayload {
  name?: string
  category?: string
  minimum_price?: string
  maximum_price?: string
  status?: ProductStatus
}
