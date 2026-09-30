import type { UserRole } from '../types'

const ROLE_LABELS: Record<UserRole, string> = {
  SUPER_ADMIN: 'Super Admin',
  SHOP_MANAGER: 'Shop Manager',
  STAFF: 'Staff',
}

export function formatRole(role: UserRole): string {
  return ROLE_LABELS[role] ?? role
}

export function shopScopeLabel(shopId: string | null): string {
  return shopId ? 'Assigned Shop' : 'All Shops'
}
