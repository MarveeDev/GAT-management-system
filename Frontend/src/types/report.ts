import type { Pagination } from './api'
import type { ShopStatus } from './shop'
import type { SMSStatus } from './sms'
import type { UserRole } from './user'

export type ReportPreset =
  | 'today'
  | 'yesterday'
  | 'last_7_days'
  | 'last_30_days'
  | 'this_month'
  | 'previous_month'
  | 'custom'

export interface ReportQueryParams {
  preset?: ReportPreset
  date_from?: string
  date_to?: string
  shop_id?: string
}

export interface PagedReportQueryParams extends ReportQueryParams {
  page?: number
  per_page?: number
}

export interface ReportDateRange {
  start: string | null
  end: string | null
}

export interface ReportShopRef {
  id: string
  name: string
}

export interface ReportShopSummary extends ReportShopRef {
  location: string | null
  status: ShopStatus
}

export interface ReportStaffSummary {
  id: string
  name: string
  email: string
  role: UserRole
}

export interface ReportCustomerRef {
  id: string
  name: string
  phone: string | null
}

export interface ReportCustomer extends ReportCustomerRef {
  email: string | null
}

// --- summary ---

export interface SummaryReport {
  range: ReportDateRange
  total_purchases: number
  total_sales: string
  average_purchase_value: string | null
  unique_customers: number
  sms_sent: number
  sms_failed: number
  sms_pending: number
}

// --- sales ---

export interface SalesReportRow {
  id: string
  date: string | null
  customer: ReportCustomerRef | null
  product: string
  amount: string
  currency: string
  shop: ReportShopRef | null
  recorded_by: ReportStaffSummary | null
}

export interface SalesReportSummary {
  total_purchases: number
  total_sales: string
  average_purchase_value: string | null
}

export interface SalesReport {
  sales: SalesReportRow[]
  pagination: Pagination
  summary: SalesReportSummary
  range: ReportDateRange
}

// --- sms ---

export interface SmsReportRow {
  id: string
  date: string | null
  phone_number: string
  status: SMSStatus
  provider: string | null
  shop: ReportShopRef | null
  customer: ReportCustomerRef | null
  purchase_id: string
  error_message: string | null
}

export interface SmsReportSummary {
  total_sms: number
  sms_sent: number
  sms_failed: number
  sms_pending: number
  success_rate: string
}

export interface SmsReport {
  summary: SmsReportSummary
  sms: SmsReportRow[]
  pagination: Pagination
  range: ReportDateRange
}

// --- shops ---

export interface ShopReportMetrics {
  total_purchases: number
  total_sales: string
  average_purchase_value: string
  unique_customers: number
  sms_sent: number
  sms_failed: number
  sms_pending: number
  sms_success_rate: string
}

export interface ShopReportRow {
  shop: ReportShopSummary
  metrics: ShopReportMetrics
}

export interface ShopReportTotals {
  total_purchases: number
  total_sales: string
  unique_customers: number
  sms_sent: number
  sms_failed: number
  sms_pending: number
}

export interface ShopReport {
  shops: ShopReportRow[]
  totals: ShopReportTotals
  range: ReportDateRange
}

// --- staff ---

export interface StaffReportMetrics {
  total_purchases: number
  total_sales: string
  average_purchase_value: string
}

export interface StaffReportRow {
  staff: ReportStaffSummary
  shop: ReportShopSummary | null
  metrics: StaffReportMetrics
}

export interface StaffReportTotals {
  total_purchases: number
  total_sales: string
}

export interface StaffReport {
  staff: StaffReportRow[]
  totals: StaffReportTotals
  range: ReportDateRange
}

// --- customers ---

export interface CustomerReportMetrics {
  total_purchases: number
  total_spent: string
  average_purchase_value: string
}

export interface CustomerReportRow {
  customer: ReportCustomer
  shops: ReportShopSummary[]
  metrics: CustomerReportMetrics
}

export interface CustomerReportTotals {
  total_customers: number
  total_purchases: number
  total_spent: string
}

export interface CustomerReport {
  customers: CustomerReportRow[]
  totals: CustomerReportTotals
  range: ReportDateRange
}
