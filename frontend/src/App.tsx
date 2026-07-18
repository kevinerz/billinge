import { Routes, Route } from 'react-router-dom'
import { LoginPage } from './pages/LoginPage'
import { DashboardPage } from './pages/DashboardPage'
import { TenantsPage } from './pages/TenantsPage'
import { TenantIntegrationsPage } from './pages/TenantIntegrationsPage'
import { SubscribersPage } from './pages/SubscribersPage'
import { NasPage } from './pages/NasPage'
import { VpnHubPage } from './pages/VpnHubPage'
import { PlatformPlansPage } from './pages/billing/PlatformPlansPage'
import { TenantSubscriptionsPage } from './pages/billing/TenantSubscriptionsPage'
import { PlatformInvoicesPage } from './pages/billing/PlatformInvoicesPage'
import { PlatformPaymentsPage } from './pages/billing/PlatformPaymentsPage'
import { ServicePlansPage } from './pages/billing/ServicePlansPage'
import { SubscriberSubscriptionsPage } from './pages/billing/SubscriberSubscriptionsPage'
import { SubscriberInvoicesPage } from './pages/billing/SubscriberInvoicesPage'
import { SubscriberPaymentsPage } from './pages/billing/SubscriberPaymentsPage'
import { VoucherBatchesPage } from './pages/vouchers/VoucherBatchesPage'
import { VouchersPage } from './pages/vouchers/VouchersPage'
import { UsersPage } from './pages/UsersPage'
import { AuditLogsPage } from './pages/AuditLogsPage'
import { PaymentGatewayEventsPage } from './pages/webhooks/PaymentGatewayEventsPage'
import { PaymentRefundsPage } from './pages/webhooks/PaymentRefundsPage'
import { AppLayout } from './layout/AppLayout'
import { ProtectedRoute, RoleGuard } from './auth/ProtectedRoute'

const TENANT_ADMIN_PLUS = ['super_admin' as const, 'tenant_admin' as const]

function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />

      <Route element={<ProtectedRoute />}>
        <Route element={<AppLayout />}>
          <Route index element={<DashboardPage />} />
          <Route path="tenants" element={<TenantsPage />} />
          <Route path="subscribers" element={<SubscribersPage />} />

          <Route path="billing">
            <Route path="platform-plans" element={<PlatformPlansPage />} />
            <Route path="tenant-subscriptions" element={<TenantSubscriptionsPage />} />
            <Route path="platform-invoices" element={<PlatformInvoicesPage />} />
            <Route path="platform-payments" element={<PlatformPaymentsPage />} />
            <Route path="service-plans" element={<ServicePlansPage />} />
            <Route path="subscriber-subscriptions" element={<SubscriberSubscriptionsPage />} />
            <Route path="subscriber-invoices" element={<SubscriberInvoicesPage />} />
            <Route path="subscriber-payments" element={<SubscriberPaymentsPage />} />
          </Route>

          <Route element={<RoleGuard allow={TENANT_ADMIN_PLUS} />}>
            <Route path="tenant-integrations" element={<TenantIntegrationsPage />} />
            <Route path="nas" element={<NasPage />} />
            <Route path="vpn-hub" element={<VpnHubPage />} />
            <Route path="vouchers">
              <Route path="batches" element={<VoucherBatchesPage />} />
              <Route path="list" element={<VouchersPage />} />
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
