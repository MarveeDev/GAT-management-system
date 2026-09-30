export type ShopStatus = 'ACTIVE' | 'INACTIVE'

export interface Shop {
  id: string
  name: string
  location: string | null
  phone: string | null
  sender_id: string | null
  status: ShopStatus
  created_at: string | null
  updated_at: string | null
}

export interface ShopCreatePayload {
  name: string
  location?: string
  phone?: string
  sender_id?: string
  status?: ShopStatus
}

export interface ShopUpdatePayload {
  name?: string
  location?: string
  phone?: string
  sender_id?: string
  status?: ShopStatus
}
