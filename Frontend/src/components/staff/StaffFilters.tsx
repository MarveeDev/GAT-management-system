import { Search } from 'lucide-react'

import type { Shop, UserRole, UserStatus } from '../../types'

export type RoleFilter = 'ALL' | UserRole
export type StatusFilter = 'ALL' | UserStatus
export type ShopFilter = 'ALL' | string

interface StaffFiltersProps {
  search: string
  onSearchChange: (value: string) => void
  role: RoleFilter
  onRoleChange: (value: RoleFilter) => void
  status: StatusFilter
  onStatusChange: (value: StatusFilter) => void
  shop: ShopFilter
  onShopChange: (value: ShopFilter) => void
  shops: Shop[]
  showShopFilter: boolean
}

const selectClass =
  'w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30 sm:w-auto'

export default function StaffFilters({
  search,
  onSearchChange,
  role,
  onRoleChange,
  status,
  onStatusChange,
  shop,
  onShopChange,
  shops,
  showShopFilter,
}: StaffFiltersProps) {
  return (
    <div className="flex flex-col gap-3">
      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          type="search"
          value={search}
          onChange={(event) => onSearchChange(event.target.value)}
          placeholder="Search staff..."
          aria-label="Search staff"
          className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      <div className="grid grid-cols-2 gap-3 sm:flex sm:flex-wrap sm:items-center">
        <div>
          <label htmlFor="role-filter" className="sr-only">
            Filter by role
          </label>
          <select
            id="role-filter"
            value={role}
            onChange={(event) => onRoleChange(event.target.value as RoleFilter)}
            className={selectClass}
          >
            <option value="ALL">All roles</option>
            <option value="SUPER_ADMIN">Super Admin</option>
            <option value="SHOP_MANAGER">Shop Manager</option>
            <option value="STAFF">Staff</option>
          </select>
        </div>

        <div>
          <label htmlFor="status-filter" className="sr-only">
            Filter by status
          </label>
          <select
            id="status-filter"
            value={status}
            onChange={(event) => onStatusChange(event.target.value as StatusFilter)}
            className={selectClass}
          >
            <option value="ALL">All statuses</option>
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
          </select>
        </div>

        {showShopFilter && (
          <div>
            <label htmlFor="shop-filter" className="sr-only">
              Filter by shop
            </label>
            <select
              id="shop-filter"
              value={shop}
              onChange={(event) => onShopChange(event.target.value as ShopFilter)}
              className={selectClass}
            >
              <option value="ALL">All shops</option>
              {shops.map((s) => (
                <option key={s.id} value={s.id}>
                  {s.name}
                </option>
              ))}
            </select>
          </div>
        )}
      </div>
    </div>
  )
}
