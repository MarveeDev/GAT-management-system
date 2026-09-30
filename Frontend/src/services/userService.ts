import { api, buildQuery } from '../lib/api'
import type { User, UserCreatePayload, UserRole, UserStatus, UserUpdatePayload } from '../types'

export interface UserListParams {
  shop_id?: string
  role?: UserRole
  status?: UserStatus
}

export function listUsers(params: UserListParams = {}): Promise<{ users: User[] }> {
  return api.get<{ users: User[] }>(`/users${buildQuery(params)}`, { auth: true })
}

export function createUser(payload: UserCreatePayload): Promise<{ user: User }> {
  return api.post<{ user: User }>('/users', payload, { auth: true })
}

export function getUser(id: string): Promise<{ user: User }> {
  return api.get<{ user: User }>(`/users/${id}`, { auth: true })
}

export function updateUser(id: string, payload: UserUpdatePayload): Promise<{ user: User }> {
  return api.patch<{ user: User }>(`/users/${id}`, payload, { auth: true })
}

export function updateUserPassword(id: string, password: string): Promise<{ user: User }> {
  return api.patch<{ user: User }>(`/users/${id}/password`, { password }, { auth: true })
}
