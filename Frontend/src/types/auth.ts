import type { User } from './user'

export interface LoginRequest {
  email: string
  password: string
}

export interface LoginResponse {
  access_token: string
  user: User
}

export interface MeResponse {
  user: User
}
