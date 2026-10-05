export interface Customer {
  id: string
  name: string
  phone: string | null
  email: string | null
}

export interface CustomerSummary {
  customer: Customer
  purchase_count: number
  last_purchase_at: string | null
}
