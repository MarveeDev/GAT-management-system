import { Link } from 'react-router-dom'

export default function NotFound() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50 px-6">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-slate-900">404</h1>
        <p className="mt-2 text-sm text-slate-500">The page you requested was not found.</p>
        <Link
          to="/"
          className="mt-4 inline-block rounded-lg bg-brand-600 px-4 py-2 text-sm font-semibold text-white hover:bg-brand-700"
        >
          Back to Overview
        </Link>
      </div>
    </div>
  )
}
