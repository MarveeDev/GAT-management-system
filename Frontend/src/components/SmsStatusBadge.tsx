interface SmsStatusBadgeProps {
  status: string | null | undefined
}

export default function SmsStatusBadge({ status }: SmsStatusBadgeProps) {
  if (!status) {
    return <span className="text-sm text-slate-400">—</span>
  }

  if (status === 'SENT') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-success-50 px-2.5 py-0.5 text-xs font-medium text-success-700">
        <span className="h-1.5 w-1.5 rounded-full bg-success-600" aria-hidden="true" />
        Sent
      </span>
    )
  }

  if (status === 'FAILED') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-danger-50 px-2.5 py-0.5 text-xs font-medium text-danger-700">
        <span className="h-1.5 w-1.5 rounded-full bg-danger-600" aria-hidden="true" />
        Failed
      </span>
    )
  }

  if (status === 'PENDING') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-warning-50 px-2.5 py-0.5 text-xs font-medium text-warning-600">
        <span className="h-1.5 w-1.5 rounded-full bg-warning-500" aria-hidden="true" />
        Pending
      </span>
    )
  }

  if (status === 'REVIEW') {
    return (
      <span className="inline-flex items-center gap-1.5 rounded-full bg-purple-50 px-2.5 py-0.5 text-xs font-medium text-purple-700">
        <span className="h-1.5 w-1.5 rounded-full bg-purple-600" aria-hidden="true" />
        Review
      </span>
    )
  }

  return <span className="text-sm text-slate-600">{status}</span>
}
