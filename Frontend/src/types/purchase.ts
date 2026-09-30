import type { Customer } from './customer'

export interface Purchase {
  id: string
  shop_id: string
  staff_id: string
  customer_id: string
  product: string
  amount: string
  currency: string
  created_at: string | null
  updated_at: string | null
  customer?: Customer
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
  product: string
  amount: number | string
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
