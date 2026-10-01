import type { LucideIcon } from 'lucide-react'

type Accent = 'blue' | 'green' | 'red' | 'purple'

const ACCENT_CLASSES: Record<Accent, string> = {
  blue: 'bg-brand-50 text-brand-600',
  green: 'bg-success-50 text-success-600',
  red: 'bg-danger-50 text-danger-600',
  purple: 'bg-purple-50 text-purple-600',
}

interface ReportKpiCardProps {
  label: string
  icon: LucideIcon
  accent?: Accent
  value: string
}

export default function ReportKpiCard({
  label,
  icon: Icon,
  accent = 'blue',
  value,
}: ReportKpiCardProps) {
  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-center justify-between">
        <p className="text-sm font-medium text-slate-500">{label}</p>
        <span
          className={`flex h-9 w-9 items-center justify-center rounded-lg ${ACCENT_CLASSES[accent]}`}
        >
          <Icon className="h-5 w-5" aria-hidden="true" />
        </span>
      </div>
      <p className="mt-3 text-2xl font-semibold text-slate-900">{value}</p>
    </div>
  )
}
