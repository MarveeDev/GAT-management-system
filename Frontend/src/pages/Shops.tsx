import { useCallback, useEffect, useMemo, useState } from 'react'
import { Plus } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import ShopCard from '../components/shops/ShopCard'
import ShopDetails from '../components/shops/ShopDetails'
import ShopFilters, { type StatusFilter } from '../components/shops/ShopFilters'
import ShopForm, { type ShopFormValues } from '../components/shops/ShopForm'
import { useAuth } from '../contexts/authContext'
import { createShop, listShops, updateShop } from '../services/shopService'
import type { Shop } from '../types'

export default function Shops() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [shops, setShops] = useState<Shop[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')

  const [formOpen, setFormOpen] = useState(false)
  const [editingShop, setEditingShop] = useState<Shop | null>(null)
  const [detailsShop, setDetailsShop] = useState<Shop | null>(null)

  const [success, setSuccess] = useState<string | null>(null)

  const loadShops = useCallback(async (showSpinner = true) => {
    if (showSpinner) setLoading(true)
    setError(null)
    try {
      const res = await listShops()
      setShops(res.shops)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to load shops.')
    } finally {
      if (showSpinner) setLoading(false)
    }
  }, [])

  useEffect(() => {
    let active = true
    listShops()
      .then((res) => {
        if (active) {
          setShops(res.shops)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) setError(err instanceof Error ? err.message : 'Unable to load shops.')
      })
      .finally(() => {
        if (active) setLoading(false)
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

  const filtered = useMemo(() => {
    if (!shops) return []
    const query = search.trim().toLowerCase()
    return shops.filter((shop) => {
      if (statusFilter !== 'ALL' && shop.status !== statusFilter) return false
      if (!query) return true
      return [shop.name, shop.location, shop.phone].some((value) =>
        (value ?? '').toLowerCase().includes(query),
      )
    })
  }, [shops, search, statusFilter])

  function openCreate() {
    setEditingShop(null)
    setFormOpen(true)
  }

  function openEdit(shop: Shop) {
    setEditingShop(shop)
    setFormOpen(true)
  }

  function closeForm() {
    setFormOpen(false)
    setEditingShop(null)
  }

  async function handleSubmit(values: ShopFormValues) {
    if (editingShop) {
      await updateShop(editingShop.id, values)
      setSuccess('Shop updated successfully.')
    } else {
      await createShop(values)
      setSuccess('Shop created successfully.')
    }
    closeForm()
    await loadShops(false)
  }

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Shop Management</h1>
          <p className="mt-1 text-sm text-slate-500">
            Manage your shops, locations, and operating status.
          </p>
        </div>
        {isSuperAdmin && (
          <button
            type="button"
            onClick={openCreate}
            className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
          >
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add New Shop
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

      <ShopFilters
        search={search}
        onSearchChange={setSearch}
        status={statusFilter}
        onStatusChange={setStatusFilter}
      />

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <div className="space-y-3">
          <ErrorMessage message={error} />
          <button
            type="button"
            onClick={() => loadShops()}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Retry
          </button>
        </div>
      ) : !shops || shops.length === 0 ? (
        <EmptyState
          title="No shops yet"
          description={
            isSuperAdmin
              ? 'Create your first shop to get started.'
              : 'No shops are available.'
          }
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching shops" description="No shops match your search or filter." />
      ) : (
        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
          {filtered.map((shop) => (
            <ShopCard
              key={shop.id}
              shop={shop}
              onDetails={setDetailsShop}
              onEdit={isSuperAdmin ? openEdit : undefined}
            />
          ))}
        </div>
      )}

      {formOpen && (
        <Modal title={editingShop ? 'Edit Shop' : 'Add New Shop'} onClose={closeForm}>
          <ShopForm
            key={editingShop?.id ?? 'new'}
            initial={editingShop ?? undefined}
            onSubmit={handleSubmit}
            onCancel={closeForm}
          />
        </Modal>
      )}

      {detailsShop && (
        <Modal title="Shop Details" onClose={() => setDetailsShop(null)}>
          <ShopDetails shop={detailsShop} />
        </Modal>
      )}
    </div>
  )
}
