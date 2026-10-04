import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  Boxes,
  LayoutDashboard,
  MessageSquare,
  ShoppingCart,
  Store,
  UserRound,
  Users,
} from 'lucide-react'
import type { UserRole } from '../types'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
  roles?: UserRole[]
}

export interface NavGroup {
  title: string
  items: NavItem[]
}

const ALL_ROLES: UserRole[] = ['SUPER_ADMIN', 'SHOP_MANAGER', 'STAFF']
const MANAGER_AND_ADMIN: UserRole[] = ['SUPER_ADMIN', 'SHOP_MANAGER']

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Main',
    items: [{ label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard, roles: ALL_ROLES }],
  },
  {
    title: 'Management',
    items: [
      { label: 'Shops', path: '/shops', icon: Store, roles: ['SUPER_ADMIN'] },
      { label: 'Staff', path: '/staff', icon: Users, roles: MANAGER_AND_ADMIN },
      { label: 'Purchases', path: '/purchases', icon: ShoppingCart, roles: ALL_ROLES },
      { label: 'Products & Inventory', path: '/products', icon: Boxes, roles: ALL_ROLES },
      { label: 'Customers', path: '/customers', icon: UserRound, roles: ALL_ROLES },
    ],
  },
  {
    title: 'Communication',
    items: [{ label: 'SMS', path: '/sms', icon: MessageSquare, roles: ALL_ROLES }],
  },
  {
    title: 'Insights',
    items: [{ label: 'Reports', path: '/reports', icon: BarChart3, roles: MANAGER_AND_ADMIN }],
  },
]
