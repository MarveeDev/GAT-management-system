import type { Customer } from './customer'
import type { UserRole } from './user'

export interface PurchaseStaff {
  id: string
  name: string
  email: string
  role: UserRole
}

export interface Purchase {
  id: string
  shop_id: string
  staff_id: string
  customer_id: string
  product: string
  amount: string
  currency: string
  product_id?: string | null
  quantity?: number | null
  unit_price?: string | null
  product_info?: { id: string; name: string; category: string | null } | null
  remaining_stock?: number | null
  created_at: string | null
  updated_at: string | null
  customer?: Customer
  staff?: PurchaseStaff
}

export interface CustomerInput {
  name: string
  phone: string
  email?: string
}

export interface PurchaseCreatePayload {
  shop_id?: string
  customer_id?: string
  customer?: CustomerInput
  product?: string
  product_id?: string
  quantity?: number
  unit_price?: string
  amount?: number | string
  currency?: string
}

export interface PurchaseSmsResult {
  status: string
  provider_message_id?: string
  error?: string
}

export interface PurchaseCreateResponse {
  purchase: Purchase
  sms: PurchaseSmsResult
}

export interface PurchaseListParams {
  page?: number
  per_page?: number
  shop_id?: string
  staff_id?: string
  customer_id?: string
  date_from?: string
  date_to?: string
  search?: string
}
