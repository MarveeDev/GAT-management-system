import { lazy, Suspense } from 'react'
import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'

import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../contexts/authContext'
import AppLayout from '../layouts/AppLayout'
import Customers from '../pages/Customers'
import Login from '../pages/Login'
import NotFound from '../pages/NotFound'
import Purchases from '../pages/Purchases'
import Reports from '../pages/Reports'
import Shops from '../pages/Shops'
import Sms from '../pages/Sms'
import Staff from '../pages/Staff'

const Dashboard = lazy(() => import('../pages/Dashboard'))

function FullScreenLoader() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-slate-50">
      <LoadingSpinner />
    </div>
  )
}

function ProtectedLayout() {
  const { isAuthenticated, isLoading } = useAuth()
  const location = useLocation()

  if (isLoading) {
    return <FullScreenLoader />
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace state={{ from: location }} />
  }

  return <Outlet />
}

function LoginRoute() {
  const { isAuthenticated, isLoading } = useAuth()

  if (isLoading) {
    return <FullScreenLoader />
  }

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />
  }

  return <Login />
}

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<LoginRoute />} />

      <Route element={<ProtectedLayout />}>
        <Route element={<AppLayout />}>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route
            path="/dashboard"
            element={
              <Suspense fallback={<LoadingSpinner />}>
                <Dashboard />
              </Suspense>
            }
          />
          <Route path="/shops" element={<Shops />} />
          <Route path="/staff" element={<Staff />} />
          <Route path="/purchases" element={<Purchases />} />
          <Route path="/customers" element={<Customers />} />
          <Route path="/sms" element={<Sms />} />
          <Route path="/reports" element={<Reports />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
