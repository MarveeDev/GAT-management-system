import type { Purchase } from './purchase'

export interface Customer {
  id: string
  name: string
  phone: string | null
  email: string | null
}

export interface CustomerEntry {
  customer: Customer
  purchases: Purchase[]
  purchaseCount: number
  lastPurchaseAt: string | null
}
