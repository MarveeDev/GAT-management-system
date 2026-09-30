export type UserRole = 'SUPER_ADMIN' | 'SHOP_MANAGER' | 'STAFF'

export type UserStatus = 'ACTIVE' | 'INACTIVE'

export interface User {
  id: string
  name: string
  email: string
  phone: string | null
  role: UserRole
  shop_id: string | null
  status: UserStatus
  created_at: string | null
  updated_at: string | null
}

export interface UserCreatePayload {
  name: string
  email: string
  phone?: string
  password: string
  role: 'SHOP_MANAGER' | 'STAFF'
  shop_id: string
}

export interface UserUpdatePayload {
  name?: string
  phone?: string
  role?: 'SHOP_MANAGER' | 'STAFF'
  shop_id?: string
  status?: UserStatus
}
