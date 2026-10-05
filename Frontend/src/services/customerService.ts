import { api } from '../lib/api'
import type { CustomerSummary } from '../types'

export function listCustomers(): Promise<{ customers: CustomerSummary[] }> {
  return api.get<{ customers: CustomerSummary[] }>('/customers', { auth: true })
}
