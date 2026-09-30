import { Route, Routes } from 'react-router-dom'

import AppLayout from '../layouts/AppLayout'
import Home from '../pages/Home'
import NotFound from '../pages/NotFound'
import Placeholder from '../pages/Placeholder'

export default function AppRoutes() {
  return (
    <Routes>
      <Route path="/login" element={<Placeholder title="Login" />} />

      <Route element={<AppLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/dashboard" element={<Placeholder title="Dashboard" />} />
        <Route path="/shops" element={<Placeholder title="Shop Management" />} />
        <Route path="/staff" element={<Placeholder title="Staff Management" />} />
        <Route path="/purchases" element={<Placeholder title="Purchases" />} />
        <Route path="/customers" element={<Placeholder title="Customers" />} />
        <Route path="/sms" element={<Placeholder title="SMS" />} />
        <Route path="/reports" element={<Placeholder title="Reports" />} />
      </Route>

      <Route path="*" element={<NotFound />} />
    </Routes>
  )
}
