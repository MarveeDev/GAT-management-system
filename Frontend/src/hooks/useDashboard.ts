import { useCallback, useEffect, useState } from 'react'

import { listAllPurchases, listPurchases } from '../services/purchaseService'
import { listShops } from '../services/shopService'
import { listSmsLogs } from '../services/smsService'
import type { AsyncSection } from '../types/api'
import type { ChartPoint } from '../types/dashboard'
import type { Purchase, Shop, SMSLog } from '../types'

const CHART_PAGE_SIZE = 100

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unable to load data.'
}

function emptySection<T>(): AsyncSection<T> {
  return { data: null, loading: true, error: null }
}

function startOfDayISO(daysAgo: number): string {
  const date = new Date()
  date.setDate(date.getDate() - daysAgo)
  date.setHours(0, 0, 0, 0)
  return date.toISOString()
}

function startOfLocalDay(iso: string): number {
  const date = new Date(iso)
  date.setHours(0, 0, 0, 0)
  return date.getTime()
}

function buildChartData(purchases: Purchase[], smsLogs: SMSLog[]): ChartPoint[] {
  const today = new Date()
  today.setHours(0, 0, 0, 0)

  const points: ChartPoint[] = []
  const indexByDay = new Map<number, number>()

  for (let i = 6; i >= 0; i--) {
    const date = new Date(today)
    date.setDate(date.getDate() - i)
    points.push({
      day: date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' }),
      purchases: 0,
      smsSent: 0,
    })
    indexByDay.set(date.getTime(), points.length - 1)
  }

  for (const purchase of purchases) {
    if (!purchase.created_at) continue
    const index = indexByDay.get(startOfLocalDay(purchase.created_at))
    if (index !== undefined) points[index].purchases += 1
  }

  for (const sms of smsLogs) {
    const timestamp = sms.sent_at ?? sms.created_at
    if (!timestamp) continue
    const index = indexByDay.get(startOfLocalDay(timestamp))
    if (index !== undefined) points[index].smsSent += 1
  }

  return points
}

export function useDashboard() {
  const [shops, setShops] = useState<AsyncSection<Shop[]>>(emptySection)
  const [totalPurchases, setTotalPurchases] = useState<AsyncSection<number>>(emptySection)
  const [smsSent, setSmsSent] = useState<AsyncSection<number>>(emptySection)
  const [smsFailed, setSmsFailed] = useState<AsyncSection<number>>(emptySection)
  const [uniqueCustomers, setUniqueCustomers] = useState<AsyncSection<number>>(emptySection)
  const [recentPurchases, setRecentPurchases] = useState<AsyncSection<Purchase[]>>(emptySection)
  const [chart, setChart] = useState<AsyncSection<ChartPoint[]>>(emptySection)
  const [reloadToken, setReloadToken] = useState(0)

  useEffect(() => {
    let active = true

    listShops()
      .then((res) => {
        if (active) setShops({ data: res.shops, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setShops({ data: null, loading: false, error: errorMessage(error) })
      })

    listPurchases({ per_page: 1 })
      .then((res) => {
        if (active) setTotalPurchases({ data: res.pagination.total, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setTotalPurchases({ data: null, loading: false, error: errorMessage(error) })
      })

    listSmsLogs({ status: 'SENT', per_page: 1 })
      .then((res) => {
        if (active) setSmsSent({ data: res.pagination.total, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setSmsSent({ data: null, loading: false, error: errorMessage(error) })
      })

    listSmsLogs({ status: 'FAILED', per_page: 1 })
      .then((res) => {
        if (active) setSmsFailed({ data: res.pagination.total, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setSmsFailed({ data: null, loading: false, error: errorMessage(error) })
      })

    listAllPurchases()
      .then((all) => {
        if (!active) return
        const count = new Set(all.map((p) => p.customer_id)).size
        setUniqueCustomers({ data: count, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setUniqueCustomers({ data: null, loading: false, error: errorMessage(error) })
      })

    listPurchases({ per_page: 10 })
      .then((res) => {
        if (active) setRecentPurchases({ data: res.purchases, loading: false, error: null })
      })
      .catch((error: unknown) => {
        if (active) setRecentPurchases({ data: null, loading: false, error: errorMessage(error) })
      })

    const dateFrom = startOfDayISO(6)
    Promise.all([
      listPurchases({ date_from: dateFrom, per_page: CHART_PAGE_SIZE }),
      listSmsLogs({ status: 'SENT', date_from: dateFrom, per_page: CHART_PAGE_SIZE }),
    ])
      .then(([purchasesRes, smsRes]) => {
        if (active) {
          setChart({
            data: buildChartData(purchasesRes.purchases, smsRes.sms_logs),
            loading: false,
            error: null,
          })
        }
      })
      .catch((error: unknown) => {
        if (active) setChart({ data: null, loading: false, error: errorMessage(error) })
      })

    return () => {
      active = false
    }
  }, [reloadToken])

  const refresh = useCallback(() => setReloadToken((token) => token + 1), [])

  return {
    shops,
    totalPurchases,
    smsSent,
    smsFailed,
    uniqueCustomers,
    recentPurchases,
    chart,
    refresh,
  }
}
