import { useEffect, useMemo, useState } from 'react'
import { Banknote, MessageSquare, ShoppingCart, Users } from 'lucide-react'

import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import ReportFilters from '../components/reports/ReportFilters'
import ReportKpiCard from '../components/reports/ReportKpiCard'
import { useAuth } from '../contexts/authContext'
import { getReportSummary } from '../services/reportService'
import { listShops } from '../services/shopService'
import type { ReportPreset, ReportQueryParams, Shop, SummaryReport } from '../types'
import { formatCurrency, formatDateTime } from '../utils/format'

function isReady(preset: ReportPreset, dateFrom: string, dateTo: string): boolean {
  if (preset !== 'custom') return true
  return Boolean(dateFrom) && Boolean(dateTo) && dateFrom <= dateTo
}

export default function Reports() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [preset, setPreset] = useState<ReportPreset>('last_7_days')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')
  const [shopId, setShopId] = useState(isSuperAdmin ? '' : (user?.shop_id ?? ''))

  const [shops, setShops] = useState<Shop[]>([])
  const [summary, setSummary] = useState<SummaryReport | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    listShops()
      .then((res) => {
        if (active) setShops(res.shops)
      })
      .catch(() => {
        // best-effort; the summary still loads without the shop list
      })
    return () => {
      active = false
    }
  }, [])

  const assignedShopName = useMemo(() => {
    if (isSuperAdmin) return null
    return shops.find((shop) => shop.id === user?.shop_id)?.name ?? null
  }, [shops, isSuperAdmin, user?.shop_id])

  useEffect(() => {
    if (!isReady(preset, dateFrom, dateTo)) return

    let active = true
    const params: ReportQueryParams = {}
    if (preset === 'custom') {
      params.date_from = dateFrom
      params.date_to = dateTo
    } else {
      params.preset = preset
    }
    if (shopId) {
      params.shop_id = shopId
    }

    getReportSummary(params)
      .then((res) => {
        if (active) {
          setSummary(res.summary)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) {
          setError(
            err instanceof Error ? err.message : 'Unable to load report summary.',
          )
        }
      })
      .finally(() => {
        if (active) setLoading(false)
      })

    return () => {
      active = false
    }
  }, [preset, dateFrom, dateTo, shopId])

  function changePreset(value: ReportPreset) {
    if (isReady(value, dateFrom, dateTo)) setLoading(true)
    setPreset(value)
  }

  function changeDateFrom(value: string) {
    if (isReady(preset, value, dateTo)) setLoading(true)
    setDateFrom(value)
  }

  function changeDateTo(value: string) {
    if (isReady(preset, dateFrom, value)) setLoading(true)
    setDateTo(value)
  }

  function changeShop(value: string) {
    if (isReady(preset, dateFrom, dateTo)) setLoading(true)
    setShopId(value)
  }

  const hasRange = Boolean(summary && (summary.range.start || summary.range.end))

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

      {summary && !loading && !error && hasRange && (
        <p className="text-sm text-slate-500">
          Period: {formatDateTime(summary.range.start)} to{' '}
          {formatDateTime(summary.range.end)}
        </p>
      )}

      {loading ? (
        <LoadingSpinner />
      ) : error ? (
        <ErrorMessage message={error} title="Unable to load reports" />
      ) : summary ? (
        <>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
            <ReportKpiCard
              label="Total Purchases"
              icon={ShoppingCart}
              accent="blue"
              value={String(summary.total_purchases)}
            />
            <ReportKpiCard
              label="Total Sales"
              icon={Banknote}
              accent="green"
              value={formatCurrency(summary.total_sales)}
            />
            <ReportKpiCard
              label="Unique Customers"
              icon={Users}
              accent="purple"
              value={String(summary.unique_customers)}
            />
            <ReportKpiCard
              label="SMS Sent"
              icon={MessageSquare}
              accent="blue"
              value={String(summary.sms_sent)}
            />
          </div>

          <section className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
            <h2 className="text-base font-semibold text-slate-900">Additional Metrics</h2>
            <div className="mt-4 grid grid-cols-1 gap-4 sm:grid-cols-3">
              <div>
                <p className="text-sm text-slate-500">SMS Failed</p>
                <p className="mt-1 text-xl font-semibold text-danger-600">
                  {summary.sms_failed}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">SMS Pending</p>
                <p className="mt-1 text-xl font-semibold text-warning-600">
                  {summary.sms_pending}
                </p>
              </div>
              <div>
                <p className="text-sm text-slate-500">Average Purchase Value</p>
                <p className="mt-1 text-xl font-semibold text-slate-900">
                  {formatCurrency(summary.average_purchase_value)}
                </p>
              </div>
            </div>
          </section>
        </>
      ) : null}
    </div>
  )
}
