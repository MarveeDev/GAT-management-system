interface ErrorMessageProps {
  message?: string
  title?: string
}

export default function ErrorMessage({
  message,
  title = 'Something went wrong',
}: ErrorMessageProps) {
  if (!message) return null

  return (
    <div className="rounded-lg border border-danger-600/20 bg-danger-50 px-4 py-3 text-sm text-danger-700">
      <p className="font-semibold">{title}</p>
      <p className="mt-0.5">{message}</p>
    </div>
  )
}
