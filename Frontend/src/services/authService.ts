import { api } from '../lib/api'
import type { LoginRequest, LoginResponse, MeResponse } from '../types'

export function login(credentials: LoginRequest): Promise<LoginResponse> {
  return api.post<LoginResponse>('/auth/login', credentials)
}

export function getCurrentUser(): Promise<MeResponse> {
  return api.get<MeResponse>('/auth/me', { auth: true })
}
