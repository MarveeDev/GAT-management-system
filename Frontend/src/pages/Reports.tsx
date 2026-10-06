import { useEffect, useMemo, useState } from 'react'
import {
  Banknote,
  CircleAlert,
  CircleCheck,
  MessageSquare,
  ShoppingCart,
  Users,
} from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import CustomerReportTable from '../components/reports/CustomerReportTable'
import ReportFilters from '../components/reports/ReportFilters'
import ReportKpiCard from '../components/reports/ReportKpiCard'
import SalesReportTable from '../components/reports/SalesReportTable'
import ShopReportTable from '../components/reports/ShopReportTable'
import SmsReportTable from '../components/reports/SmsReportTable'
import StaffReportTable from '../components/reports/StaffReportTable'
import { useAuth } from '../contexts/authContext'
import {
  getCustomerReport,
  getReportSummary,
  getSalesReport,
  getShopReport,
  getSmsReport,
  getStaffReport,
} from '../services/reportService'
import { listShops } from '../services/shopService'
import type {
  CustomerReport,
  ReportPreset,
  ReportQueryParams,
  SalesReport,
  Shop,
  ShopReport,
  SmsReport,
  StaffReport,
  SummaryReport,
} from '../types'
import { formatCurrency, formatDateTime } from '../utils/format'

type Tab = 'summary' | 'sales' | 'sms' | 'shops' | 'staff' | 'customers'

const TABS: { id: Tab; label: string }[] = [
  { id: 'summary', label: 'Summary' },
  { id: 'sales', label: 'Sales' },
  { id: 'sms', label: 'SMS' },
  { id: 'shops', label: 'Shops' },
  { id: 'staff', label: 'Staff' },
  { id: 'customers', label: 'Customers' },
]

const PER_PAGE = 25

type ReportData =
  | { tab: 'summary'; summary: SummaryReport }
  | { tab: 'sales'; sales: SalesReport }
  | { tab: 'sms'; sms: SmsReport }
  | { tab: 'shops'; shops: ShopReport }
  | { tab: 'staff'; staff: StaffReport }
  | { tab: 'customers'; customers: CustomerReport }

function isReady(preset: ReportPreset, dateFrom: string, dateTo: string): boolean {
  if (preset !== 'custom') return true
  return Boolean(dateFrom) && Boolean(dateTo) && dateFrom <= dateTo
}

function rangeText(range: { start: string | null; end: string | null } | undefined): string | null {
  if (!range || (!range.start && !range.end)) return null
  return `Period: ${formatDateTime(range.start)} to ${formatDateTime(range.end)}`
}

function periodLabelOf(data: ReportData): string | null {
  if (data.tab === 'summary') return rangeText(data.summary.range)
  if (data.tab === 'sales') return rangeText(data.sales.range)
  if (data.tab === 'sms') return rangeText(data.sms.range)
  if (data.tab === 'shops') return rangeText(data.shops.range)
  if (data.tab === 'staff') return rangeText(data.staff.range)
  return rangeText(data.customers.range)
}

interface PaginationProps {
  page: number
  pages: number
  onChange: (page: number) => void
}

function Pagination({ page, pages, onChange }: PaginationProps) {
  if (pages <= 1) return null
  return (
    <div className="flex items-center justify-between">
      <p className="text-sm text-slate-500">
        Page {page} of {pages}
      </p>
      <div className="flex items-center gap-2">
        <button
          type="button"
          onClick={() => onChange(page - 1)}
          disabled={page <= 1}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Previous
        </button>
        <button
          type="button"
          onClick={() => onChange(page + 1)}
          disabled={page >= pages}
          className="rounded-lg border border-slate-200 px-3 py-1.5 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:cursor-not-allowed disabled:opacity-50"
        >
          Next
        </button>
      </div>
    </div>
  )
}

function TotalsStrip({ items }: { items: { label: string; value: string }[] }) {
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-5">
      {items.map((item) => (
        <div key={item.label} className="rounded-xl bg-slate-50 px-4 py-3">
          <p className="text-xs font-medium text-slate-500">{item.label}</p>
          <p className="mt-1 text-lg font-semibold text-slate-900">{item.value}</p>
        </div>
      ))}
    </div>
  )
}

export default function Reports() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [preset, setPreset] = useState<ReportPreset>('last_7_days')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [shopId, setShopId] = useState(isSuperAdmin ? '' : (user?.shop_id ?? ''))
  const [tab, setTab] = useState<Tab>('summary')
  const [page, setPage] = useState(1)

  const [shops, setShops] = useState<Shop[]>([])
  const [data, setData] = useState<ReportData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // best-effort; reports still load without the shop list
      })
    return () => {
      active = false
    }
  }, [])

  const ready = isReady(preset, dateFrom, dateTo)

  useEffect(() => {
    if (!ready) return

    let active = true

    const base: ReportQueryParams = {}
    if (preset === 'custom') {
      base.date_from = dateFrom
      base.date_to = dateTo
    } else {
      base.preset = preset
    }
    if (shopId) base.shop_id = shopId

    let request: Promise<ReportData>
    if (tab === 'summary') {
      request = getReportSummary(base).then((r) => ({ tab: 'summary' as const, summary: r.summary }))
    } else if (tab === 'sales') {
      request = getSalesReport({ ...base, page, per_page: PER_PAGE }).then((r) => ({
        tab: 'sales' as const,
        sales: r,
      }))
    } else if (tab === 'sms') {
      request = getSmsReport({ ...base, page, per_page: PER_PAGE }).then((r) => ({
        tab: 'sms' as const,
        sms: r,
      }))
    } else if (tab === 'shops') {
      request = getShopReport(base).then((r) => ({ tab: 'shops' as const, shops: r }))
    } else if (tab === 'staff') {
      request = getStaffReport(base).then((r) => ({ tab: 'staff' as const, staff: r }))
    } else {
      request = getCustomerReport(base).then((r) => ({ tab: 'customers' as const, customers: r }))
    }

    request
      .then((d) => {
        if (active) {
          setData(d)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) {
          setError(err instanceof Error ? err.message : 'Unable to load report.')
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [tab, preset, dateFrom, dateTo, shopId, page, ready])

  const assignedShopName = useMemo(() => {
    if (isSuperAdmin) return null
    return shops.find((shop) => shop.id === user?.shop_id)?.name ?? null
  }, [shops, isSuperAdmin, user?.shop_id])

  function goToPage(next: number) {
    setLoading(true)
    setError(null)
    setPage(next)
  }

  function changeTab(next: Tab) {
    setTab(next)
    setPage(1)
    setLoading(true)
    setError(null)
  }

  function changePreset(value: ReportPreset) {
    setPreset(value)
    setPage(1)
    setLoading(true)
    setError(null)
  }

  function changeDateFrom(value: string) {
    setDateFrom(value)
    setPage(1)
    setLoading(true)
    setError(null)
  }

  function changeDateTo(value: string) {
    setDateTo(value)
    setPage(1)
    setLoading(true)
    setError(null)
  }

  function changeShop(value: string) {
    setShopId(value)
    setPage(1)
    setLoading(true)
    setError(null)
  }

  function renderData(current: ReportData) {
    if (current.tab === 'summary') {
      const s = current.summary
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <ReportKpiCard label="Total Purchases" icon={ShoppingCart} accent="blue" value={String(s.total_purchases)} />
            <ReportKpiCard label="Total Sales" icon={Banknote} accent="green" value={formatCurrency(s.total_sales)} />
            <ReportKpiCard label="Unique Customers" icon={Users} accent="purple" value={String(s.unique_customers)} />
            <ReportKpiCard label="SMS Sent" icon={MessageSquare} accent="blue" value={String(s.sms_sent)} />
          </div>
          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">Additional Metrics</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <p className="text-sm text-slate-500">SMS Failed</p>
                <p className="mt-1 text-xl font-semibold text-danger-600">{s.sms_failed}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">SMS Pending</p>
                <p className="mt-1 text-xl font-semibold text-warning-600">{s.sms_pending}</p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Average Purchase Value</p>
                <p className="mt-1 text-xl font-semibold text-slate-900">
                  {formatCurrency(s.average_purchase_value)}
                </p>
              </div>
            </div>
          </section>
        </div>
      )
    }

    if (current.tab === 'sales') {
      const r = current.sales
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
            <ReportKpiCard label="Purchases" icon={ShoppingCart} accent="blue" value={String(r.summary.total_purchases)} />
            <ReportKpiCard label="Total Sales" icon={Banknote} accent="green" value={formatCurrency(r.summary.total_sales)} />
            <ReportKpiCard label="Avg Purchase" icon={CircleCheck} accent="purple" value={formatCurrency(r.summary.average_purchase_value)} />
          </div>
          {r.sales.length === 0 ? (
            <EmptyState title="No sales" description="No sales match the selected filters." />
          ) : (
            <SalesReportTable rows={r.sales} />
          )}
          <Pagination page={r.pagination.page} pages={r.pagination.pages} onChange={goToPage} />
        </div>
      )
    }

    if (current.tab === 'sms') {
      const r = current.sms
      return (
        <div className="space-y-6">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 xl:grid-cols-5">
            <ReportKpiCard label="Total SMS" icon={MessageSquare} accent="blue" value={String(r.summary.total_sms)} />
            <ReportKpiCard label="Sent" icon={CircleCheck} accent="green" value={String(r.summary.sms_sent)} />
            <ReportKpiCard label="Failed" icon={CircleAlert} accent="red" value={String(r.summary.sms_failed)} />
            <ReportKpiCard label="Pending" icon={MessageSquare} accent="purple" value={String(r.summary.sms_pending)} />
            <ReportKpiCard label="Success Rate" icon={CircleCheck} accent="blue" value={`${r.summary.success_rate}%`} />
          </div>
          {r.sms.length === 0 ? (
            <EmptyState title="No SMS" description="No SMS records match the selected filters." />
          ) : (
            <SmsReportTable rows={r.sms} />
          )}
          <Pagination page={r.pagination.page} pages={r.pagination.pages} onChange={goToPage} />
        </div>
      )
    }

    if (current.tab === 'shops') {
      const r = current.shops
      return (
        <div className="space-y-6">
          <TotalsStrip
            items={[
              { label: 'Purchases', value: String(r.totals.total_purchases) },
              { label: 'Total Sales', value: formatCurrency(r.totals.total_sales) },
              { label: 'Customers', value: String(r.totals.unique_customers) },
              { label: 'SMS Sent', value: String(r.totals.sms_sent) },
              { label: 'SMS Failed', value: String(r.totals.sms_failed) },
            ]}
          />
          {r.shops.length === 0 ? (
            <EmptyState title="No shop activity" description="No shop data matches the selected filters." />
          ) : (
            <ShopReportTable rows={r.shops} />
          )}
        </div>
      )
    }

    if (current.tab === 'staff') {
      const r = current.staff
      return (
        <div className="space-y-6">
          <TotalsStrip
            items={[
              { label: 'Purchases', value: String(r.totals.total_purchases) },
              { label: 'Total Sales', value: formatCurrency(r.totals.total_sales) },
            ]}
          />
          {r.staff.length === 0 ? (
            <EmptyState title="No staff activity" description="No staff recorded purchases in this period." />
          ) : (
            <StaffReportTable rows={r.staff} />
          )}
        </div>
      )
    }

    const r = current.customers
    return (
      <div className="space-y-6">
        <TotalsStrip
          items={[
            { label: 'Customers', value: String(r.totals.total_customers) },
            { label: 'Purchases', value: String(r.totals.total_purchases) },
            { label: 'Total Spent', value: formatCurrency(r.totals.total_spent) },
          ]}
        />
        {r.customers.length === 0 ? (
          <EmptyState title="No customer activity" description="No customer data matches the selected filters." />
        ) : (
          <CustomerReportTable rows={r.customers} />
        )}
      </div>
    )
  }

  const periodLabel = data ? periodLabelOf(data) : null

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">Reports</h1>
        <p className="mt-1 text-sm text-slate-500">
          Business performance and activity overview
        </p>
      </header>

      <ReportFilters
        preset={preset}
        onPresetChange={changePreset}
        dateFrom={dateFrom}
        onDateFromChange={changeDateFrom}
        dateTo={dateTo}
        onDateToChange={changeDateTo}
        shops={shops}
        shopId={shopId}
        onShopChange={changeShop}
        isSuperAdmin={isSuperAdmin}
        assignedShopName={assignedShopName}
      />

      <nav aria-label="Report sections" className="flex flex-wrap gap-1.5">
        {TABS.map((item) => (
          <button
            key={item.id}
            type="button"
            onClick={() => changeTab(item.id)}
            className={`rounded-lg px-3 py-2 text-sm font-medium transition-colors ${
              tab === item.id
                ? 'bg-brand-600 text-white'
                : 'bg-white text-slate-600 hover:bg-slate-100 hover:text-slate-900'
            }`}
          >
            {item.label}
          </button>
        ))}
      </nav>

      {periodLabel && <p className="text-sm text-slate-500">{periodLabel}</p>}

      {!ready ? (
        <EmptyState title="Select a date range" description="Choose start and end dates to view this report." />
      ) : loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} title="Unable to load reports" />
      ) : data ? (
        renderData(data)
      ) : (
        <EmptyState title="No report data" description="Adjust the filters and try again." />
      )}
    </div>
  )
}
