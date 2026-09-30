import type { LucideIcon } from 'lucide-react'

import type { AsyncSection } from '../../types/api'
import LoadingSpinner from '../LoadingSpinner'

interface StatCardProps {
  label: string
  icon: LucideIcon
  section: AsyncSection<number>
}

export default function StatCard({ label, icon: Icon, section }: StatCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>

      <div className="mt-3">
        {section.loading ? (
          <LoadingSpinner size="sm" />
        ) : section.error ? (
          <p className="text-sm font-medium text-danger-600">Unavailable</p>
        ) : (
          <p className="text-2xl font-semibold text-slate-900">{section.data ?? 0}</p>
        )}
      </div>
    </div>
  )
}
