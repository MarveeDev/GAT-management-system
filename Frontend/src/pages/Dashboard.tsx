import { useCallback, useState } from 'react'
import { CircleAlert, MessageSquare, ShoppingCart, Users } from 'lucide-react'

import ActivityChart from '../components/dashboard/ActivityChart'
import MessagePreview from '../components/dashboard/MessagePreview'
import QuickActions from '../components/dashboard/QuickActions'
import RecentPurchases from '../components/dashboard/RecentPurchases'
import ShopOverview from '../components/dashboard/ShopOverview'
import StatCard from '../components/dashboard/StatCard'
import PurchaseForm, {
  type PurchasePreviewValues,
} from '../components/purchases/PurchaseForm'
import { useAuth } from '../contexts/authContext'
import { useDashboard } from '../hooks/useDashboard'
import { createPurchase } from '../services/purchaseService'
import type { PurchaseCreatePayload, PurchaseSmsResult } from '../types'

const TODAY = new Date().toLocaleDateString(undefined, {
  weekday: 'long',
  year: 'numeric',
  month: 'long',
  day: 'numeric',
})

export default function Dashboard() {
  const { user } = useAuth()
  const {
    shops,
    totalPurchases,
    smsSent,
    smsFailed,
    uniqueCustomers,
    recentPurchases,
    chart,
    refresh,
  } = useDashboard()

  const isSuperAdmin = user?.role === 'SUPER_ADMIN'
  const shopNames = new Map((shops.data ?? []).map((shop) => [shop.id, shop.name]))
  const activeShops = (shops.data ?? []).filter((shop) => shop.status === 'ACTIVE')
  const assignedShopName = isSuperAdmin
    ? null
    : (shopNames.get(user?.shop_id ?? '') ?? null)

  const [preview, setPreview] = useState<PurchasePreviewValues | null>(null)
  const [purchaseResult, setPurchaseResult] = useState<PurchaseSmsResult | null>(null)

  const handleValuesChange = useCallback((values: PurchasePreviewValues) => {
    setPreview(values)
  }, [])

  const handleCreatePurchase = useCallback(
    async (payload: PurchaseCreatePayload) => {
      const res = await createPurchase(payload)
      setPurchaseResult(res.sms)
      refresh()
    },
    [refresh],
  )

  const firstName = user?.name?.trim().split(/\s+/)[0] ?? ''
  const subtitle = isSuperAdmin
    ? 'Here is an overview of activity across all shops.'
    : 'Here is an overview of activity for your assigned shop.'

  return (
    <div className="space-y-6">
      <header className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
        <div className="flex items-center gap-3">
          <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-50 text-brand-600">
            <ShoppingCart className="h-5 w-5" aria-hidden="true" />
          </span>
          <div>
            <h1 className="text-2xl font-semibold text-slate-900">
              Welcome back{firstName ? `, ${firstName}` : ''}!
            </h1>
            <p className="mt-0.5 text-sm text-slate-500">{subtitle}</p>
          </div>
        </div>
        <p className="text-sm text-slate-500 md:text-right">{TODAY}</p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Purchases" icon={ShoppingCart} section={totalPurchases} accent="blue" />
        <StatCard label="SMS Sent" icon={MessageSquare} section={smsSent} accent="green" />
        <StatCard label="Failed SMS" icon={CircleAlert} section={smsFailed} accent="red" />
        <StatCard label="Unique Customers" icon={Users} section={uniqueCustomers} accent="purple" />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">
        <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
          <div className="flex items-center gap-2 border-b border-slate-200 px-5 py-4">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
              <ShoppingCart className="h-4 w-4" aria-hidden="true" />
            </span>
            <div>
              <h2 className="text-base font-semibold text-slate-900">Record New Purchase</h2>
              <p className="text-xs text-slate-500">Customer details, product, and amount</p>
            </div>
          </div>
          <div className="p-5">
            {purchaseResult &&
              (purchaseResult.status === 'SENT' ? (
                <div
                  role="status"
                  className="mb-4 rounded-lg border border-success-600/20 bg-success-50 px-4 py-3 text-sm text-success-700"
                >
                  <p className="font-medium">Purchase recorded and SMS sent successfully.</p>
                </div>
              ) : (
                <div
                  role="status"
                  className="mb-4 rounded-lg border border-warning-500/30 bg-warning-50 px-4 py-3 text-sm text-slate-700"
                >
                  <p className="font-medium text-slate-900">
                    Purchase recorded, but SMS could not be sent.
                  </p>
                  {purchaseResult.error && (
                    <p className="mt-0.5 text-danger-700">{purchaseResult.error}</p>
                  )}
                  <p className="mt-1 text-xs text-slate-500">
                    You can retry this SMS from the SMS Monitoring page.
                  </p>
                </div>
              ))}
            <PurchaseForm
              isSuperAdmin={isSuperAdmin}
              activeShops={activeShops}
              assignedShopName={assignedShopName}
              onSubmit={handleCreatePurchase}
              onValuesChange={handleValuesChange}
            />
          </div>
        </section>

        <MessagePreview values={preview} />
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <RecentPurchases
            purchases={recentPurchases.data}
            loading={recentPurchases.loading}
            error={recentPurchases.error}
            shopNames={shopNames}
          />
        </div>
        <ShopOverview shops={shops.data} loading={shops.loading} error={shops.error} />
      </div>

      <ActivityChart data={chart.data} loading={chart.loading} error={chart.error} />

      <QuickActions />
    </div>
  )
}
