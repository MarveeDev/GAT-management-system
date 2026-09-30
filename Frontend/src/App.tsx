import { useCallback, useEffect, useState } from 'react'
import { getHealth, type HealthResponse } from './lib/api'

type ConnectionState =
  | { kind: 'checking' }
  | { kind: 'connected'; data: HealthResponse }
  | { kind: 'error'; message: string }

function errorMessage(error: unknown): string {
  return error instanceof Error ? error.message : 'Unknown error'
}

function App() {
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
    <div className="flex min-h-screen flex-col">
      <header className="bg-navy-900 text-white">
        <div className="mx-auto flex h-16 max-w-5xl items-center justify-between px-6">
          <div className="flex items-center gap-3">
            <div className="flex h-9 w-9 items-center justify-center rounded-lg bg-brand-600 text-sm font-bold">
              GAE
            </div>
            <div>
              <h1 className="text-base font-semibold leading-tight">
                Great Alexender Enterprise
              </h1>
              <p className="text-xs text-white/60">System Foundation</p>
            </div>
          </div>
          <span className="rounded-full bg-white/10 px-3 py-1 text-xs font-medium text-white/80">
            Phase 1
          </span>
        </div>
      </header>

      <main className="flex flex-1 items-center justify-center px-6 py-12">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-8 shadow-sm">
          <h2 className="text-lg font-semibold text-slate-900">
            Backend Connection
          </h2>
          <p className="mt-1 text-sm text-slate-500">
            Verifying connectivity to the Great Alexender Enterprise API.
          </p>

          <div className="mt-6 flex items-center gap-3 rounded-xl border border-slate-200 bg-slate-50 px-4 py-4">
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
              API status:{' '}
              <span className="font-semibold">{state.data.status}</span>
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
      </main>

      <footer className="border-t border-slate-200 bg-white py-4">
        <p className="text-center text-xs text-slate-400">
          Great Alexender Enterprise &mdash; Centralized Management System
        </p>
      </footer>
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

export default App
