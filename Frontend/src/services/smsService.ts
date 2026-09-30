import { api, buildQuery } from '../lib/api'
import type { Pagination, SMSListParams, SMSLog } from '../types'

export interface SMSListResponse {
  sms_logs: SMSLog[]
  pagination: Pagination
}

export function listSmsLogs(params: SMSListParams = {}): Promise<SMSListResponse> {
  return api.get<SMSListResponse>(`/sms${buildQuery(params)}`, { auth: true })
}

export function getSmsLog(id: string): Promise<{ sms: SMSLog }> {
  return api.get<{ sms: SMSLog }>(`/sms/${id}`, { auth: true })
}

export function retrySms(id: string): Promise<{ sms: SMSLog }> {
  return api.post<{ sms: SMSLog }>(`/sms/${id}/retry`, undefined, { auth: true })
}
