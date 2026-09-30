import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react'

import { setUnauthorizedHandler } from '../lib/api'
import { clearAccessToken, getAccessToken, setAccessToken } from '../lib/tokenStorage'
import { getCurrentUser, login as loginRequest } from '../services/authService'
import type { User } from '../types'
import { AuthContext, type AuthContextValue } from './authContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(() => getAccessToken() !== null)

  const logout = useCallback(() => {
    clearAccessToken()
    setUser(null)
  }, [])

  // When any authenticated request returns 401 (expired/invalid token),
  // clear the session so route protection redirects to /login.
  useEffect(() => {
    setUnauthorizedHandler(() => {
      clearAccessToken()
      setUser(null)
    })
    return () => setUnauthorizedHandler(null)
  }, [])

  // Restore a session on startup when a token already exists.
  useEffect(() => {
    let active = true
    if (!getAccessToken()) {
      return
    }

    getCurrentUser()
      .then((res) => {
        if (active) setUser(res.user)
      })
      .catch(() => {
        if (active) {
          clearAccessToken()
          setUser(null)
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })

    return () => {
      active = false
    }
  }, [])

  const login = useCallback(async (email: string, password: string) => {
    const res = await loginRequest({ email, password })
    setAccessToken(res.access_token)
    setUser(res.user)
  }, [])

  const refreshUser = useCallback(async () => {
    const res = await getCurrentUser()
    setUser(res.user)
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isAuthenticated: user !== null,
      isLoading,
      login,
      logout,
      refreshUser,
    }),
    [user, isLoading, login, logout, refreshUser],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
