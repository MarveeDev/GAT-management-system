export type SMSStatus = 'PENDING' | 'SENT' | 'FAILED'

export interface SMSLog {
  id: string
  shop_id: string
  purchase_id: string
  customer_id: string
  phone_number: string
  message: string
  provider: string | null
  provider_message_id: string | null
  status: SMSStatus
  error_message: string | null
  sent_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface SMSListParams {
  page?: number
  per_page?: number
  shop_id?: string
  purchase_id?: string
  customer_id?: string
  status?: SMSStatus
  date_from?: string
  date_to?: string
}
