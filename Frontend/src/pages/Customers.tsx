import { useEffect, useMemo, useState } from 'react'
import { Search } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import CustomerDetails from '../components/customers/CustomerDetails'
import CustomerTable from '../components/customers/CustomerTable'
import { listAllPurchases } from '../services/purchaseService'
import { listShops } from '../services/shopService'
import type { CustomerEntry, Purchase, Shop } from '../types'

function customerErrorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to load customers.'
}

export default function Customers() {
  const [purchases, setPurchases] = useState<Purchase[]>([])
  const [shops, setShops] = useState<Shop[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [search, setSearch] = useState('')
  const [detailsEntry, setDetailsEntry] = useState<CustomerEntry | null>(null)

  useEffect(() => {
    let active = true
    listAllPurchases()
      .then((all) => {
        if (active) {
          setPurchases(all)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) setError(customerErrorMessage(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // best-effort
      })

    return () => {
      active = false
    }
  }, [])

  const shopNames = useMemo(() => new Map(shops.map((shop) => [shop.id, shop.name])), [shops])

  const customers = useMemo<CustomerEntry[]>(() => {
    const map = new Map<string, CustomerEntry>()
    for (const purchase of purchases) {
      if (!purchase.customer) continue
      const existing = map.get(purchase.customer_id)
      if (existing) {
        existing.purchases.push(purchase)
        existing.purchaseCount += 1
        if (
          purchase.created_at &&
          (!existing.lastPurchaseAt || purchase.created_at > existing.lastPurchaseAt)
        ) {
          existing.lastPurchaseAt = purchase.created_at
        }
      } else {
        map.set(purchase.customer_id, {
          customer: purchase.customer,
          purchases: [purchase],
          purchaseCount: 1,
          lastPurchaseAt: purchase.created_at,
        })
      }
    }
    const list = Array.from(map.values())
    list.sort((a, b) => (b.lastPurchaseAt ?? '').localeCompare(a.lastPurchaseAt ?? ''))
    return list
  }, [purchases])

  const filtered = useMemo(() => {
    const query = search.trim().toLowerCase()
    if (!query) return customers
    return customers.filter((entry) =>
      [entry.customer.name, entry.customer.phone, entry.customer.email].some((value) =>
        (value ?? '').toLowerCase().includes(query),
      ),
    )
  }, [customers, search])

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Customers</h1>
        <p className="mt-1 text-sm text-slate-500">
          Customers derived from purchase records across your accessible shops.
        </p>
      </header>

      <div className="relative">
        <Search
          className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400"
          aria-hidden="true"
        />
        <input
          type="search"
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          placeholder="Search customers..."
          aria-label="Search customers"
          className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-3 text-sm text-slate-900 placeholder:text-slate-400 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/30"
        />
      </div>

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} />
      ) : customers.length === 0 ? (
        <EmptyState
          title="No customers yet"
          description="Customers will appear here once purchases are recorded."
        />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching customers" description="No customers match your search." />
      ) : (
        <CustomerTable entries={filtered} onDetails={setDetailsEntry} />
      )}

      {detailsEntry && (
        <Modal title="Customer Details" onClose={() => setDetailsEntry(null)}>
          <CustomerDetails entry={detailsEntry} shopNames={shopNames} />
        </Modal>
      )}
    </div>
  )
}
