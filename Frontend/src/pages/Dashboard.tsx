import { CircleAlert, MessageSquare, ShoppingCart, Users } from 'lucide-react'

import ActivityChart from '../components/dashboard/ActivityChart'
import QuickActions from '../components/dashboard/QuickActions'
import RecentPurchases from '../components/dashboard/RecentPurchases'
import ShopOverview from '../components/dashboard/ShopOverview'
import StatCard from '../components/dashboard/StatCard'
import { useAuth } from '../contexts/authContext'
import { useDashboard } from '../hooks/useDashboard'

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
  } = useDashboard()

  const shopNames = new Map((shops.data ?? []).map((shop) => [shop.id, shop.name]))
  const subtitle =
    user?.role === 'SUPER_ADMIN'
      ? 'Overview of purchases, customers, and SMS activity across all shops.'
      : 'Overview of purchases, customers, and SMS activity for your assigned shop.'

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-500">{subtitle}</p>
      </header>

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total Purchases" icon={ShoppingCart} section={totalPurchases} />
        <StatCard label="SMS Sent" icon={MessageSquare} section={smsSent} />
        <StatCard label="Failed SMS" icon={CircleAlert} section={smsFailed} />
        <StatCard label="Unique Customers" icon={Users} section={uniqueCustomers} />
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
