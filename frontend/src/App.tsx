import { Routes, Route } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { TenantsPage } from './pages/TenantsPage'
import { NasPage } from './pages/NasPage'
import { PlatformPlansPage } from './pages/billing/PlatformPlansPage'
import { TenantSubscriptionsPage } from './pages/billing/TenantSubscriptionsPage'
import { PlatformInvoicesPage } from './pages/billing/PlatformInvoicesPage'
import { PlatformPaymentsPage } from './pages/billing/PlatformPaymentsPage'
import { UsersPage } from './pages/UsersPage'
import { AuditLogsPage } from './pages/AuditLogsPage'
import { PaymentGatewayEventsPage } from './pages/webhooks/PaymentGatewayEventsPage'
import { PaymentRefundsPage } from './pages/webhooks/PaymentRefundsPage'
import { AppLayout } from './layout/AppLayout'
import { ProtectedRoute, RoleGuard } from './auth/ProtectedRoute'

// Dashboard ini adalah alat PLATFORM: kelola & tagih tenant + sediakan
// infrastruktur (VPN/NAS/IP). Urusan pelanggan/voucher/tagihan-pelanggan
// milik tenant BUKAN di sini — itu domain tenant, jadi proyek portal
// terpisah nanti. Semua halaman dibatasi super_admin.
const PLATFORM_ONLY = ['super_admin' as const]

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />

          <Route element={<RoleGuard allow={PLATFORM_ONLY} />}>
            <Route path="tenants" element={<TenantsPage />} />
            <Route path="nas" element={<NasPage />} />

            <Route path="billing">
              <Route path="platform-plans" element={<PlatformPlansPage />} />
              <Route path="tenant-subscriptions" element={<TenantSubscriptionsPage />} />
              <Route path="platform-invoices" element={<PlatformInvoicesPage />} />
              <Route path="platform-payments" element={<PlatformPaymentsPage />} />
            </Route>

            <Route path="users" element={<UsersPage />} />
            <Route path="audit-logs" element={<AuditLogsPage />} />
            <Route path="webhooks">
              <Route path="events" element={<PaymentGatewayEventsPage />} />
              <Route path="refunds" element={<PaymentRefundsPage />} />
            </Route>
          </Route>
        </Route>
      </Route>
    </Routes>
  )
}

export default App
