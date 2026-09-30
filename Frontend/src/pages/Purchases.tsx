import { useCallback, useEffect, useMemo, useState } from 'react'
import { Plus } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import PurchaseDetails from '../components/purchases/PurchaseDetails'
import PurchaseFilters from '../components/purchases/PurchaseFilters'
import PurchaseForm from '../components/purchases/PurchaseForm'
import PurchaseTable from '../components/purchases/PurchaseTable'
import { useAuth } from '../contexts/authContext'
import { ApiError } from '../lib/api'
import {
  createPurchase,
  listPurchases,
  type PurchaseListResponse,
} from '../services/purchaseService'
import { listShops } from '../services/shopService'
import { listSmsLogs } from '../services/smsService'
import type { Pagination } from '../types/api'
import type { Purchase, PurchaseCreatePayload, Shop } from '../types'

const PER_PAGE = 20

function purchaseErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return 'You do not have permission to record purchases.'
  }
  return error instanceof Error ? error.message : 'Unable to load purchases.'
}

function smsLabel(status: string): string {
  if (status === 'SENT') return 'Sent'
  if (status === 'FAILED') return 'Failed'
  if (status === 'PENDING') return 'Pending'
  return status
}

interface CreateResult {
  sms: string
}

export default function Purchases() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [purchases, setPurchases] = useState<Purchase[] | null>(null)
  const [pagination, setPagination] = useState<Pagination | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [page, setPage] = useState(1)
  const [reloadToken, setReloadToken] = useState(0)
  const [shopFilter, setShopFilter] = useState('ALL')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [search, setSearch] = useState('')

  const [shops, setShops] = useState<Shop[]>([])
  const [smsMap, setSmsMap] = useState<Map<string, string>>(new Map())

  const [formOpen, setFormOpen] = useState(false)
  const [detailsPurchase, setDetailsPurchase] = useState<Purchase | null>(null)
  const [result, setResult] = useState<CreateResult | null>(null)

  const refreshPurchases = useCallback(
    async (params: {
      page: number
      shopId: string
      dateFrom: string
      dateTo: string
    }): Promise<PurchaseListResponse> => {
      return listPurchases({
        page: params.page,
        per_page: PER_PAGE,
        shop_id: params.shopId === 'ALL' ? undefined : params.shopId,
        date_from: params.dateFrom || undefined,
        date_to: params.dateTo || undefined,
      })
    },
    [],
  )

  useEffect(() => {
    let active = true
    refreshPurchases({ page, shopId: shopFilter, dateFrom, dateTo })
      .then((res) => {
        if (active) {
          setPurchases(res.purchases)
          setPagination(res.pagination)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) setError(purchaseErrorMessage(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [refreshPurchases, page, shopFilter, dateFrom, dateTo, reloadToken])

  useEffect(() => {
    let active = true
    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // best-effort
      })

    listSmsLogs({ per_page: 100 })
      .then((res) => {
        if (!active) return
        const map = new Map<string, string>()
        for (const log of res.sms_logs) {
          if (!map.has(log.purchase_id)) map.set(log.purchase_id, log.status)
        }
        setSmsMap(map)
      })
      .catch(() => {
        // best-effort
      })

    return () => {
      active = false
    }
  }, [])

  useEffect(() => {
    if (!result) return
    const timer = setTimeout(() => setResult(null), 6000)
    return () => clearTimeout(timer)
  }, [result])

  const shopNames = useMemo(() => new Map(shops.map((shop) => [shop.id, shop.name])), [shops])
  const activeShops = useMemo(() => shops.filter((shop) => shop.status === 'ACTIVE'), [shops])
  const assignedShopName = isSuperAdmin
    ? null
    : (shopNames.get(user?.shop_id ?? '') ?? null)

  const filtered = useMemo(() => {
    if (!purchases) return []
    const query = search.trim().toLowerCase()
    if (!query) return purchases
    return purchases.filter((purchase) => {
      const shopName = shopNames.get(purchase.shop_id) ?? ''
      return [
        purchase.customer?.name,
        purchase.customer?.phone,
        purchase.product,
        shopName,
      ].some((value) => (value ?? '').toLowerCase().includes(query))
    })
  }, [purchases, search, shopNames])

  function goToPage(newPage: number) {
    setLoading(true)
    setPage(newPage)
  }

  function changeShopFilter(value: string) {
    setLoading(true)
    setPage(1)
    setShopFilter(value)
  }

  function changeDateFrom(value: string) {
    setLoading(true)
    setPage(1)
    setDateFrom(value)
  }

  function changeDateTo(value: string) {
    setLoading(true)
    setPage(1)
    setDateTo(value)
  }

  async function handleCreate(payload: PurchaseCreatePayload) {
    const res = await createPurchase(payload)
    setSmsMap((prev) => {
      const next = new Map(prev)
      next.set(res.purchase.id, res.sms.status)
      return next
    })
    setResult({ sms: res.sms.status })
    setFormOpen(false)
    setLoading(true)
    setPage(1)
    setReloadToken((t) => t + 1)
  }

  const totalPages = pagination?.pages ?? 0
  const currentPage = pagination?.page ?? page

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h1 className="text-xl font-semibold text-slate-900">Purchases</h1>
          <p className="mt-1 text-sm text-slate-500">
            Record purchases and review your purchase history.
          </p>
        </div>
        <button
          type="button"
          onClick={() => setFormOpen(true)}
          className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
        >
          <Plus className="h-4 w-4" aria-hidden="true" />
          Record Purchase
        </button>
      </header>

      {result && (
        <div
          role="status"
          className="rounded-lg border border-success-600/20 bg-success-50 px-4 py-3 text-sm text-success-700"
        >
          <p className="font-medium">Purchase recorded successfully.</p>
          <p className="mt-0.5">SMS status: {smsLabel(result.sms)}</p>
        </div>
      )}

      <PurchaseFilters
        search={search}
        onSearchChange={setSearch}
        shop={shopFilter}
        onShopChange={changeShopFilter}
        dateFrom={dateFrom}
        onDateFromChange={changeDateFrom}
        dateTo={dateTo}
        onDateToChange={changeDateTo}
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
              setReloadToken((t) => t + 1)
            }}
            className="rounded-lg border border-slate-200 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50"
          >
            Retry
          </button>
        </div>
      ) : !purchases || purchases.length === 0 ? (
        <EmptyState
          title="No purchases yet"
          description="Purchases will appear here once they are recorded."
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching purchases" description="No purchases match your search." />
      ) : (
        <>
          <PurchaseTable
            purchases={filtered}
            shopNames={shopNames}
            smsStatus={smsMap}
            onDetails={setDetailsPurchase}
          />

          {totalPages > 0 && (
            <div className="flex items-center justify-between">
              <p className="text-sm text-slate-500">
                Page {currentPage} of {totalPages}
              </p>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => goToPage(currentPage - 1)}
                  disabled={currentPage <= 1}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Previous
                </button>
                <button
                  type="button"
                  onClick={() => goToPage(currentPage + 1)}
                  disabled={currentPage >= totalPages}
                  className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
                >
                  Next
                </button>
              </div>
            </div>
          )}
        </>
      )}

      {formOpen && (
        <Modal title="Record New Purchase" onClose={() => setFormOpen(false)}>
          <PurchaseForm
            isSuperAdmin={isSuperAdmin}
            activeShops={activeShops}
            assignedShopName={assignedShopName}
            onSubmit={handleCreate}
            onCancel={() => setFormOpen(false)}
          />
        </Modal>
      )}

      {detailsPurchase && (
        <Modal title="Purchase Details" onClose={() => setDetailsPurchase(null)}>
          <PurchaseDetails
            purchase={detailsPurchase}
            shopName={shopNames.get(detailsPurchase.shop_id) ?? null}
            smsStatus={smsMap.get(detailsPurchase.id) ?? null}
          />
        </Modal>
      )}
    </div>
  )
}
