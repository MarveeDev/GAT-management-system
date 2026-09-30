import type { LucideIcon } from 'lucide-react'
import {
  BarChart3,
  LayoutDashboard,
  MessageSquare,
  ShoppingCart,
  Store,
  UserRound,
  Users,
} from 'lucide-react'

export interface NavItem {
  label: string
  path: string
  icon: LucideIcon
}

export interface NavGroup {
  title: string
  items: NavItem[]
}

export const NAV_GROUPS: NavGroup[] = [
  {
    title: 'Main',
    items: [{ label: 'Dashboard', path: '/dashboard', icon: LayoutDashboard }],
  },
  {
    title: 'Management',
    items: [
      { label: 'Shops', path: '/shops', icon: Store },
      { label: 'Staff', path: '/staff', icon: Users },
      { label: 'Purchases', path: '/purchases', icon: ShoppingCart },
      { label: 'Customers', path: '/customers', icon: UserRound },
    ],
  },
  {
    title: 'Communication',
    items: [{ label: 'SMS', path: '/sms', icon: MessageSquare }],
  },
  {
    title: 'Insights',
    items: [{ label: 'Reports', path: '/reports', icon: BarChart3 }],
  },
]
