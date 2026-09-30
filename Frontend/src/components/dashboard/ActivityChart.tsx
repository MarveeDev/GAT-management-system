import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import type { ChartPoint } from '../../types/dashboard'
import EmptyState from '../EmptyState'
import ErrorMessage from '../ErrorMessage'
import LoadingSpinner from '../LoadingSpinner'

interface ActivityChartProps {
  data: ChartPoint[] | null
  loading: boolean
  error: string | null
}

export default function ActivityChart({ data, loading, error }: ActivityChartProps) {
  const isEmpty =
    !loading &&
    !error &&
    (!data || data.every((point) => point.purchases === 0 && point.smsSent === 0))

  return (
    <section className="rounded-2xl border border-slate-200 bg-white shadow-sm">
      <div className="border-b border-slate-200 px-5 py-4">
        <h2 className="text-base font-semibold text-slate-900">Last 7 Days</h2>
        <p className="text-xs text-slate-500">Purchases and SMS sent per day</p>
      </div>

      <div className="p-5">
        {loading ? (
          <LoadingSpinner />
        ) : error ? (
          <ErrorMessage message={error} />
        ) : isEmpty ? (
          <EmptyState
            title="No recent activity"
            description="No purchases or SMS were recorded in the last 7 days."
          />
        ) : (
          <div className="h-64" role="img" aria-label="Purchase and SMS activity for the last 7 days">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={data ?? []} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} />
                <XAxis dataKey="day" tickLine={false} axisLine={false} fontSize={12} />
                <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
                <Tooltip />
                <Legend />
                <Bar dataKey="purchases" name="Purchases" fill="#2563eb" radius={[4, 4, 0, 0]} />
                <Bar dataKey="smsSent" name="SMS Sent" fill="#16a34a" radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </section>
  )
}
