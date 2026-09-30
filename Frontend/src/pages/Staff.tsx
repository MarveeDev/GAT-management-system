import { useCallback, useEffect, useMemo, useState } from 'react'
import { Plus } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import PasswordForm from '../components/staff/PasswordForm'
import StaffDetails from '../components/staff/StaffDetails'
import StaffEditForm, { type StaffEditValues } from '../components/staff/StaffEditForm'
import StaffFilters, {
  type RoleFilter,
  type ShopFilter,
  type StatusFilter,
} from '../components/staff/StaffFilters'
import StaffForm, { type StaffCreateValues } from '../components/staff/StaffForm'
import StaffTable from '../components/staff/StaffTable'
import { useAuth } from '../contexts/authContext'
import { ApiError } from '../lib/api'
import { listShops } from '../services/shopService'
import {
  createUser,
  listUsers,
  updateUser,
  updateUserPassword,
} from '../services/userService'
import type { Shop, User } from '../types'

function userErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return 'You do not have permission to manage staff.'
  }
  return error instanceof Error ? error.message : 'Unable to load staff.'
}

export default function Staff() {
  const { user: currentUser } = useAuth()
  const isSuperAdmin = currentUser?.role === 'SUPER_ADMIN'
  const isShopManager = currentUser?.role === 'SHOP_MANAGER'
  const canAddStaff = isSuperAdmin || isShopManager

  const [users, setUsers] = useState<User[] | null>(null)
  const [shops, setShops] = useState<Shop[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [roleFilter, setRoleFilter] = useState<RoleFilter>('ALL')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [shopFilter, setShopFilter] = useState<ShopFilter>('ALL')

  const [createOpen, setCreateOpen] = useState(false)
  const [editingUser, setEditingUser] = useState<User | null>(null)
  const [passwordUser, setPasswordUser] = useState<User | null>(null)
  const [detailsUser, setDetailsUser] = useState<User | null>(null)

  const [success, setSuccess] = useState<string | null>(null)

  const refreshUsers = useCallback(async () => {
    const res = await listUsers()
    setUsers(res.users)
  }, [])

  useEffect(() => {
    let active = true
    listUsers()
      .then((res) => {
        if (active) {
          setUsers(res.users)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) setError(userErrorMessage(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // shop list is best-effort; the page still works without it
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!success) return
    const timer = setTimeout(() => setSuccess(null), 4000)
    return () => clearTimeout(timer)
  }, [success])

  const shopNames = useMemo(() => new Map(shops.map((shop) => [shop.id, shop.name])), [shops])
  const activeShops = useMemo(() => shops.filter((shop) => shop.status === 'ACTIVE'), [shops])
  const ownShop = isSuperAdmin ? null : (shops[0] ?? null)

  const filtered = useMemo(() => {
    if (!users) return []
    const query = search.trim().toLowerCase()
    return users.filter((user) => {
      if (roleFilter !== 'ALL' && user.role !== roleFilter) return false
      if (statusFilter !== 'ALL' && user.status !== statusFilter) return false
      if (shopFilter !== 'ALL' && user.shop_id !== shopFilter) return false
      if (!query) return true
      return [user.name, user.email, user.phone].some((value) =>
        (value ?? '').toLowerCase().includes(query),
      )
    })
  }, [users, search, roleFilter, statusFilter, shopFilter])

  function canManage(target: User): boolean {
    if (isSuperAdmin) return true
    if (isShopManager) return target.role === 'STAFF'
    return false
  }

  function closeCreate() {
    setCreateOpen(false)
  }

  function closeEdit() {
    setEditingUser(null)
  }

  function closePassword() {
    setPasswordUser(null)
  }

  async function handleCreate(values: StaffCreateValues) {
    await createUser(values)
    setSuccess('Staff created successfully.')
    closeCreate()
    try {
      await refreshUsers()
    } catch {
      // ignore refresh failure; creation succeeded
    }
  }

  async function handleEdit(values: StaffEditValues) {
    if (!editingUser) return
    await updateUser(editingUser.id, values)
    setSuccess('Staff updated successfully.')
    closeEdit()
    try {
      await refreshUsers()
    } catch {
      // ignore refresh failure; update succeeded
    }
  }

  async function handlePassword(password: string) {
    if (!passwordUser) return
    await updateUserPassword(passwordUser.id, password)
    setSuccess('Password updated successfully.')
    closePassword()
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Staff Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage staff accounts, roles, shop assignments, and account status.
          </p>
        </div>
        {canAddStaff && (
          <button
            type="button"
            onClick={() => setCreateOpen(true)}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add Staff
          </button>
        )}
      </header>

      {success && (
        <div
          role="status"
          className="rounded-lg border border-success-600/20 bg-success-50 px-4 py-3 text-sm text-success-700"
        >
          {success}
        </div>
      )}

      <StaffFilters
        search={search}
        onSearchChange={setSearch}
        role={roleFilter}
        onRoleChange={setRoleFilter}
        status={statusFilter}
        onStatusChange={setStatusFilter}
        shop={shopFilter}
        onShopChange={setShopFilter}
        shops={shops}
        showShopFilter={isSuperAdmin}
      />

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="space-y-3">
          <ErrorMessage message={error} />
          <button
            type="button"
            onClick={() => {
              setLoading(true)
              refreshUsers()
                .catch((err) => setError(userErrorMessage(err)))
                .finally(() => setLoading(false))
            }}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Retry
          </button>
        </div>
      ) : !users || users.length === 0 ? (
        <EmptyState
          title="No staff yet"
          description={canAddStaff ? 'Create your first staff account to get started.' : 'No staff are available.'}
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching staff" description="No staff match your search or filters." />
      ) : (
        <StaffTable
          users={filtered}
          shopNames={shopNames}
          currentUserId={currentUser?.id ?? null}
          canManage={canManage}
          onEdit={setEditingUser}
          onPassword={setPasswordUser}
          onDetails={setDetailsUser}
        />
      )}

      {createOpen && (
        <Modal title="Add Staff" onClose={closeCreate}>
          <StaffForm
            isSuperAdmin={isSuperAdmin}
            ownShop={ownShop}
            activeShops={activeShops}
            onSubmit={handleCreate}
            onCancel={closeCreate}
          />
        </Modal>
      )}

      {editingUser && (
        <Modal title="Edit Staff" onClose={closeEdit}>
          <StaffEditForm
            key={editingUser.id}
            target={editingUser}
            isSuperAdmin={isSuperAdmin}
            isSelf={currentUser?.id === editingUser.id}
            activeShops={activeShops}
            onSubmit={handleEdit}
            onCancel={closeEdit}
          />
        </Modal>
      )}

      {passwordUser && (
        <Modal title="Change Password" onClose={closePassword}>
          <PasswordForm onSubmit={handlePassword} onCancel={closePassword} />
        </Modal>
      )}

      {detailsUser && (
        <Modal title="Staff Details" onClose={() => setDetailsUser(null)}>
          <StaffDetails
            user={detailsUser}
            shopName={detailsUser.shop_id ? (shopNames.get(detailsUser.shop_id) ?? null) : null}
          />
        </Modal>
      )}
    </div>
  )
}
