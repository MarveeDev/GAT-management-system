import { useEffect, useMemo, useState } from 'react'
import { CircleAlert, Clock, MessageSquare, Send } from 'lucide-react'

import EmptyState from '../components/EmptyState'
import ErrorMessage from '../components/ErrorMessage'
import LoadingSpinner from '../components/LoadingSpinner'
import Modal from '../components/Modal'
import StatCard from '../components/dashboard/StatCard'
import SmsDetails from '../components/sms/SmsDetails'
import SmsFilters, { type StatusFilter } from '../components/sms/SmsFilters'
import SmsTable from '../components/sms/SmsTable'
import { useAuth } from '../contexts/authContext'
import { ApiError } from '../lib/api'
import { listShops } from '../services/shopService'
import { listSmsLogs, retrySms, type SMSListResponse } from '../services/smsService'
import type { AsyncSection } from '../types/api'
import type { Pagination } from '../types/api'
import type { Shop, SMSLog } from '../types'

const PER_PAGE = 20

type SummaryKey = 'total' | 'sent' | 'failed' | 'pending'
type SummaryState = Record<SummaryKey, AsyncSection<number>>

const INITIAL_SUMMARY: SummaryState = {
  total: { data: null, loading: true, error: null },
  sent: { data: null, loading: true, error: null },
  failed: { data: null, loading: true, error: null },
  pending: { data: null, loading: true, error: null },
}

function smsErrorMessage(error: unknown): string {
  if (error instanceof ApiError && error.status === 403) {
    return 'You do not have permission to view SMS.'
  }
  return error instanceof Error ? error.message : 'Unable to load SMS.'
}

export default function Sms() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'SUPER_ADMIN'

  const [summary, setSummary] = useState<SummaryState>(INITIAL_SUMMARY)
  const [summaryReloadToken, setSummaryReloadToken] = useState(0)

  const [logs, setLogs] = useState<SMSLog[] | null>(null)
  const [pagination, setPagination] = useState<Pagination | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const [page, setPage] = useState(1)
  const [reloadToken, setReloadToken] = useState(0)
  const [statusFilter, setStatusFilter] = useState<StatusFilter>('ALL')
  const [shopFilter, setShopFilter] = useState('ALL')
  const [dateFrom, setDateFrom] = useState('')
  const [dateTo, setDateTo] = useState('')

  const [search, setSearch] = useState('')

  const [shops, setShops] = useState<Shop[]>([])
  const [detailsLog, setDetailsLog] = useState<SMSLog | null>(null)
  const [retryingLog, setRetryingLog] = useState<SMSLog | null>(null)
  const [retrying, setRetrying] = useState(false)
  const [retryError, setRetryError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)

  useEffect(() => {
    let active = true
    const fetchers: Array<[SummaryKey, () => Promise<SMSListResponse>]> = [
      ['total', () => listSmsLogs({ per_page: 1 })],
      ['sent', () => listSmsLogs({ status: 'SENT', per_page: 1 })],
      ['failed', () => listSmsLogs({ status: 'FAILED', per_page: 1 })],
      ['pending', () => listSmsLogs({ status: 'PENDING', per_page: 1 })],
    ]
    for (const [key, fetchCount] of fetchers) {
      fetchCount()
        .then((res) => {
          if (active) {
            setSummary((prev) => ({
              ...prev,
              [key]: { data: res.pagination.total, loading: false, error: null },
            }))
          }
        })
        .catch((err) => {
          if (active) {
            setSummary((prev) => ({
              ...prev,
              [key]: { data: null, loading: false, error: smsErrorMessage(err) },
            }))
          }
        })
    }
    return () => {
      active = false
    }
  }, [summaryReloadToken])

  useEffect(() => {
    let active = true
    listSmsLogs({
      page,
      per_page: PER_PAGE,
      status: statusFilter === 'ALL' ? undefined : statusFilter,
      shop_id: shopFilter === 'ALL' ? undefined : shopFilter,
      date_from: dateFrom || undefined,
      date_to: dateTo || undefined,
    })
      .then((res) => {
        if (active) {
          setLogs(res.sms_logs)
          setPagination(res.pagination)
          setError(null)
        }
      })
      .catch((err) => {
        if (active) setError(smsErrorMessage(err))
      })
      .finally(() => {
        if (active) setLoading(false)
      })
    return () => {
      active = false
    }
  }, [page, statusFilter, shopFilter, dateFrom, dateTo, reloadToken])

  useEffect(() => {
    let active = true
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

  useEffect(() => {
    if (!success) return
    const timer = setTimeout(() => setSuccess(null), 4000)
    return () => clearTimeout(timer)
  }, [success])

  const shopNames = useMemo(() => new Map(shops.map((shop) => [shop.id, shop.name])), [shops])

  const filtered = useMemo(() => {
    if (!logs) return []
    const query = search.trim().toLowerCase()
    if (!query) return logs
    return logs.filter((log) =>
      [log.phone_number, log.message].some((value) =>
        (value ?? '').toLowerCase().includes(query),
      ),
    )
  }, [logs, search])

  function goToPage(newPage: number) {
    setLoading(true)
    setPage(newPage)
  }

  function changeStatusFilter(value: StatusFilter) {
    setLoading(true)
    setPage(1)
    setStatusFilter(value)
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

  function openRetry(log: SMSLog) {
    setRetryingLog(log)
    setRetryError(null)
  }

  function closeRetry() {
    setRetryingLog(null)
    setRetryError(null)
  }

  async function confirmRetry() {
    if (!retryingLog) return
    setRetrying(true)
    setRetryError(null)
    try {
      await retrySms(retryingLog.id)
      setSuccess('SMS retried successfully.')
      setRetrying(false)
      setRetryingLog(null)
      setLoading(true)
      setReloadToken((t) => t + 1)
      setSummaryReloadToken((t) => t + 1)
    } catch (err) {
      setRetryError(err instanceof Error ? err.message : 'Unable to retry SMS.')
      setRetrying(false)
    }
  }

  const totalPages = pagination?.pages ?? 0
  const currentPage = pagination?.page ?? page

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-xl font-semibold text-slate-900">SMS Monitoring</h1>
        <p className="mt-1 text-sm text-slate-500">
          Monitor SMS delivery for purchase notifications.
        </p>
      </header>

      {success && (
        <div
          role="status"
          className="rounded-lg border border-success-600/20 bg-success-50 px-4 py-3 text-sm text-success-700"
        >
          {success}
        </div>
      )}

      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 xl:grid-cols-4">
        <StatCard label="Total SMS" icon={MessageSquare} section={summary.total} />
        <StatCard label="Sent" icon={Send} section={summary.sent} />
        <StatCard label="Failed" icon={CircleAlert} section={summary.failed} />
        <StatCard label="Pending" icon={Clock} section={summary.pending} />
      </div>

      <SmsFilters
        search={search}
        onSearchChange={setSearch}
        status={statusFilter}
        onStatusChange={changeStatusFilter}
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
      ) : !logs || logs.length === 0 ? (
        <EmptyState title="No SMS activity" description="SMS logs will appear here once purchases are recorded." />
      ) : filtered.length === 0 ? (
        <EmptyState title="No matching SMS" description="No SMS records match your search." />
      ) : (
        <>
          <SmsTable
            logs={filtered}
            shopNames={shopNames}
            onDetails={setDetailsLog}
            onRetry={openRetry}
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

      {detailsLog && (
        <Modal title="SMS Details" onClose={() => setDetailsLog(null)}>
          <SmsDetails log={detailsLog} shopName={shopNames.get(detailsLog.shop_id) ?? null} />
        </Modal>
      )}

      {retryingLog && (
        <Modal title="Retry SMS" onClose={closeRetry}>
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Retry sending the SMS to{' '}
              <span className="font-medium text-slate-900">{retryingLog.phone_number}</span>?
            </p>
            {retryError && <ErrorMessage message={retryError} />}
            <div className="flex justify-end gap-2">
              <button
                type="button"
                onClick={closeRetry}
                disabled={retrying}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm font-medium text-slate-700 transition-colors hover:bg-slate-50 disabled:opacity-50"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmRetry}
                disabled={retrying}
                className="inline-flex items-center justify-center gap-2 rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {retrying && (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                )}
                {retrying ? 'Retrying…' : 'Retry'}
              </button>
            </div>
          </div>
        </Modal>
      )}
    </div>
  )
}
