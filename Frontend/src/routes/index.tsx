import { Navigate, Outlet, Route, Routes, useLocation } from 'react-router-dom'

import LoadingSpinner from '../components/LoadingSpinner'
import { useAuth } from '../contexts/authContext'
import AppLayout from '../layouts/AppLayout'
import Login from '../pages/Login'
import NotFound from '../pages/NotFound'
import Placeholder from '../pages/Placeholder'

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
          <Route path="/dashboard" element={<Placeholder title="Dashboard" />} />
          <Route path="/shops" element={<Placeholder title="Shop Management" />} />
          <Route path="/staff" element={<Placeholder title="Staff Management" />} />
          <Route path="/purchases" element={<Placeholder title="Purchases" />} />
          <Route path="/customers" element={<Placeholder title="Customers" />} />
          <Route path="/sms" element={<Placeholder title="SMS" />} />
          <Route path="/reports" element={<Placeholder title="Reports" />} />
        </Route>
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
