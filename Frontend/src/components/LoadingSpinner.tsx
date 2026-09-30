interface LoadingSpinnerProps {
  size?: 'sm' | 'md'
}

export default function LoadingSpinner({ size = 'md' }: LoadingSpinnerProps) {
  const spinner =
    size === 'sm' ? 'h-4 w-4 border-2' : 'h-8 w-8 border-4'
  const padding = size === 'sm' ? 'py-1' : 'py-10'

  return (
    <div className={`flex items-center justify-center ${padding}`} role="status" aria-label="Loading">
      <div className={`animate-spin rounded-full border-slate-200 border-t-brand-600 ${spinner}`} />
    </div>
  )
}
