import { api } from '../lib/api'

export interface HealthResponse {
  status: string
  service: string
}

export interface DbHealthResponse {
  status: string
  database: string
}

export function getHealth(): Promise<HealthResponse> {
  return api.get<HealthResponse>('/health')
}

export function getDbHealth(): Promise<DbHealthResponse> {
  return api.get<DbHealthResponse>('/health/db')
}
