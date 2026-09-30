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

export function formatCurrency(amount: string | null | undefined, currency = 'GHS'): string {
  if (amount === null || amount === undefined || amount === '') {
    return `${currency} 0.00`
  }
  const value = Number(amount)
  if (!Number.isFinite(value)) {
    return `${currency} 0.00`
  }
  const formatted = value.toLocaleString('en-US', {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })
  return `${currency} ${formatted}`
}

export function formatDateTime(iso: string | null): string {
  if (!iso) return '—'
  const date = new Date(iso)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleString(undefined, {
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
