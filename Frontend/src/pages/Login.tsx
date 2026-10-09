import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Lock, Mail } from 'lucide-react'

import ErrorMessage from '../components/ErrorMessage'
import { BRAND_NAME } from '../config/branding'
import { useAuth } from '../contexts/authContext'

const inputClass =
  'w-full rounded-xl border border-[#E4EAF2] bg-white py-[15px] text-base text-[#142B49] placeholder:text-[#7186A5] transition-colors focus:border-[#2864F0] focus:outline-none focus:ring-2 focus:ring-[#2864F0]/30'

export default function Login() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const from =
    (location.state as { from?: { pathname?: string } } | null)?.from?.pathname ?? '/dashboard'

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)
    setSubmitting(true)
    try {
      await login(email, password)
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unable to sign in.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#F1F4F9] p-2.5">
      <div className="flex w-full max-w-[1628px] flex-col overflow-hidden rounded-[20px] border border-[#E4EAF2] bg-[#F8FAFD] shadow-[0_16px_50px_-20px_rgba(20,43,73,0.25)] lg:min-h-[calc(100vh-20px)] lg:flex-row">
        <div className="relative h-56 shrink-0 overflow-hidden bg-white lg:h-auto lg:w-[49.5%]">
          <img
            src="/gat-products-hero.jpg"
            alt="GREAT ALEXANDER TECH product range"
            className="absolute inset-0 block h-full w-full object-contain object-center"
          />
        </div>

        <div className="flex flex-1 items-center justify-center bg-[#F8FAFD] px-5 py-10 sm:px-8 lg:py-12">
          <div className="w-full max-w-[616px] rounded-[20px] border border-[#E4EAF2] bg-white p-7 shadow-[0_8px_30px_-18px_rgba(20,43,73,0.3)] sm:p-11">
            <div className="flex h-[70px] w-[71px] items-center justify-center rounded-2xl bg-[#2864F0] text-[26px] font-bold leading-none text-white">
              {BRAND_NAME}
            </div>

            <h1 className="mt-5 text-[30px] font-bold leading-tight text-[#142B49]">
              Welcome back
            </h1>
            <p className="mt-2.5 text-lg text-[#7186A5]">
              Sign in to your GAT account to continue.
            </p>

            <form onSubmit={handleSubmit} noValidate className="mt-10">
              <div>
                <label
                  htmlFor="email"
                  className="block text-base font-medium text-[#142B49]"
                >
                  Email
                </label>
                <div className="relative mt-2">
                  <Mail
                    className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-[#7186A5]"
                    aria-hidden="true"
                  />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className={`${inputClass} pl-12 pr-4`}
                    placeholder="you@example.com"
                  />
                </div>
              </div>

              <div className="mt-7">
                <label
                  htmlFor="password"
                  className="block text-base font-medium text-[#142B49]"
                >
                  Password
                </label>
                <div className="relative mt-2">
                  <Lock
                    className="pointer-events-none absolute left-3.5 top-1/2 h-5 w-5 -translate-y-1/2 text-[#7186A5]"
                    aria-hidden="true"
                  />
                  <input
                    id="password"
                    name="password"
                    type={showPassword ? 'text' : 'password'}
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className={`${inputClass} pl-12 pr-16`}
                    placeholder="Enter your password"
                  />
                  <button
                    type="button"
                    onClick={() => setShowPassword((v) => !v)}
                    aria-label={showPassword ? 'Hide password' : 'Show password'}
                    className="absolute inset-y-0 right-0 flex items-center px-4 text-[15px] font-semibold text-[#2864F0] transition-colors hover:text-[#1d4ed8]"
                  >
                    {showPassword ? 'Hide' : 'Show'}
                  </button>
                </div>
              </div>

              {error && (
                <div className="mt-6">
                  <ErrorMessage message={error} title="Unable to sign in" />
                </div>
              )}

              <button
                type="submit"
                disabled={submitting}
                className="mt-6 flex h-[57px] w-full items-center justify-center gap-2 rounded-xl bg-[#2864F0] px-4 text-[17px] font-semibold text-white transition-colors hover:bg-[#1d4ed8] focus:outline-none focus:ring-2 focus:ring-[#2864F0] focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {submitting && (
                  <span className="h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
                )}
                {submitting ? 'Signing in…' : 'Sign in'}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  )
}
