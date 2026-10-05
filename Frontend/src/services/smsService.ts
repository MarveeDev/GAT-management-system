import { api, buildQuery } from '../lib/api'
import type { Pagination, SMSListParams, SMSLog } from '../types'

export interface SMSListResponse {
  sms_logs: SMSLog[]
  pagination: Pagination
}

export function listSmsLogs(params: SMSListParams = {}): Promise<SMSListResponse> {
  return api.get<SMSListResponse>(`/sms${buildQuery(params)}`, { auth: true })
}

export async function listSmsLogsForPurchases(purchaseIds: string[]): Promise<SMSLog[]> {
  if (purchaseIds.length === 0) return []
  const all: SMSLog[] = []
  let page = 1
  while (true) {
    const res = await listSmsLogs({ purchase_ids: purchaseIds, per_page: 100, page })
    all.push(...res.sms_logs)
    if (page >= res.pagination.pages) break
    page += 1
  }
  return all
}

export function getSmsLog(id: string): Promise<{ sms: SMSLog }> {
  return api.get<{ sms: SMSLog }>(`/sms/${id}`, { auth: true })
}

export function retrySms(id: string): Promise<{ sms: SMSLog }> {
  return api.post<{ sms: SMSLog }>(`/sms/${id}/retry`, undefined, { auth: true })
}
