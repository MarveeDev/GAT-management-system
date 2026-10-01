import { api, buildQuery } from '../lib/api'
import type {
  CustomerReport,
  PagedReportQueryParams,
  ReportQueryParams,
  SalesReport,
  ShopReport,
  SmsReport,
  StaffReport,
  SummaryReport,
} from '../types'

export function getReportSummary(
  params: ReportQueryParams = {},
): Promise<{ summary: SummaryReport }> {
  return api.get<{ summary: SummaryReport }>(
    `/reports/summary${buildQuery(params)}`,
    { auth: true },
  )
}

export function getSalesReport(
  params: PagedReportQueryParams = {},
): Promise<SalesReport> {
  return api.get<SalesReport>(`/reports/sales${buildQuery(params)}`, {
    auth: true,
  })
}

export function getSmsReport(
  params: PagedReportQueryParams = {},
): Promise<SmsReport> {
  return api.get<SmsReport>(`/reports/sms${buildQuery(params)}`, { auth: true })
}

export function getShopReport(
  params: ReportQueryParams = {},
): Promise<ShopReport> {
  return api.get<ShopReport>(`/reports/shops${buildQuery(params)}`, {
    auth: true,
  })
}

export function getStaffReport(
  params: ReportQueryParams = {},
): Promise<StaffReport> {
  return api.get<StaffReport>(`/reports/staff${buildQuery(params)}`, {
    auth: true,
  })
}

export function getCustomerReport(
  params: ReportQueryParams = {},
): Promise<CustomerReport> {
  return api.get<CustomerReport>(`/reports/customers${buildQuery(params)}`, {
    auth: true,
  })
}
