import { useCallback, useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from '../services/healthService'

type ConnectionState =
  | { kind: 'checking' }
  | { kind: 'connected'; data: HealthResponse }
  | { kind: 'error'; message: string }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error'
}

export default function Home() {
  const [state, setState] = useState<ConnectionState>({ kind: 'checking' })

  useEffect(() => {
    let active = true
    getHealth()
      .then((data) => {
        if (active) setState({ kind: 'connected', data })
      })
      .catch((error: unknown) => {
        if (active) setState({ kind: 'error', message: errorMessage(error) })
      })
    return () => {
      active = false
    }
  }, [])

  const checkConnection = useCallback(() => {
    setState({ kind: 'checking' })
    getHealth()
      .then((data) => setState({ kind: 'connected', data }))
      .catch((error: unknown) =>
        setState({ kind: 'error', message: errorMessage(error) }),
      )
  }, [])

  return (
    <div className="mx-auto max-w-md">
      <h1 className="text-xl font-semibold text-slate-900">System Status</h1>
      <p className="mt-1 text-sm text-slate-500">
        Verifying connectivity to the Great Alexender Enterprise API.
      </p>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-white p-6 shadow-sm">
        <div className="flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
          <StatusDot state={state} />
          <div>
            <p className="text-sm font-medium text-slate-900">
              {state.kind === 'checking' && 'Checking…'}
              {state.kind === 'connected' && 'Connected'}
              {state.kind === 'error' && 'Connection failed'}
            </p>
            <p className="text-xs text-slate-500">
              {state.kind === 'connected' && state.data.service}
              {state.kind === 'error' && state.message}
              {state.kind === 'checking' && 'Contacting /api/health'}
            </p>
          </div>
        </div>

        {state.kind === 'connected' && (
          <div className="mt-4 rounded-xl bg-success-50 px-4 py-3 text-sm text-success-700">
            API status: <span className="font-semibold">{state.data.status}</span>
          </div>
        )}

        <button
          type="button"
          onClick={checkConnection}
          className="mt-6 w-full rounded-lg bg-brand-600 px-4 py-2.5 text-sm font-semibold text-white transition-colors hover:bg-brand-700 focus:outline-none focus:ring-2 focus:ring-brand-500 focus:ring-offset-2"
        >
          Re-check Connection
        </button>
      </div>
    </div>
  )
}

function StatusDot({ state }: { state: ConnectionState }) {
  const color =
    state.kind === 'connected'
      ? 'bg-success-600'
      : state.kind === 'error'
        ? 'bg-danger-600'
        : 'bg-amber-400'

  return (
    <span className="relative flex h-3 w-3">
      {state.kind === 'checking' && (
        <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-amber-400 opacity-75" />
      )}
      <span className={`relative inline-flex h-3 w-3 rounded-full ${color}`} />
    </span>
  )
}
