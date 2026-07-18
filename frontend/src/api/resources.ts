import { makeCrudApi, makeReadOnlyApi } from './factory'
import type {
  AuditLog,
  Nas,
  PaymentGatewayEvent,
  PaymentRefund,
  PlatformInvoice,
  PlatformPayment,
  PlatformPlan,
  ServicePlan,
  SubscriberInvoice,
  SubscriberPayment,
  SubscriberSubscription,
  Tenant,
  TenantIntegration,
  TenantSubscriber,
  TenantSubscription,
  User,
  Voucher,
  VoucherBatch,
} from './types'

export const tenantsApi = makeCrudApi<Tenant>('/tenants')
export const tenantIntegrationsApi = makeCrudApi<TenantIntegration>('/tenant-integrations')
export const subscribersApi = makeCrudApi<TenantSubscriber>('/subscribers')
export const nasApi = makeCrudApi<Nas>('/nas')

export const platformPlansApi = makeCrudApi<PlatformPlan>('/platform-plans')
export const tenantSubscriptionsApi = makeCrudApi<TenantSubscription>('/tenant-subscriptions')
export const platformInvoicesApi = makeCrudApi<PlatformInvoice>('/platform-invoices')
export const platformPaymentsApi = makeReadOnlyApi<PlatformPayment>('/platform-payments')

export const servicePlansApi = makeCrudApi<ServicePlan>('/service-plans')
export const subscriberSubscriptionsApi = makeCrudApi<SubscriberSubscription>('/subscriber-subscriptions')
export const subscriberInvoicesApi = makeCrudApi<SubscriberInvoice>('/subscriber-invoices')
export const subscriberPaymentsApi = makeReadOnlyApi<SubscriberPayment>('/subscriber-payments')

export const voucherBatchesApi = makeCrudApi<VoucherBatch>('/voucher-batches')
export const vouchersApi = makeReadOnlyApi<Voucher>('/vouchers')

export const usersApi = makeCrudApi<User>('/users')
export const auditLogsApi = makeReadOnlyApi<AuditLog>('/audit-logs')

export const paymentGatewayEventsApi = makeReadOnlyApi<PaymentGatewayEvent>('/payment-gateway-events')
export const paymentRefundsApi = makeReadOnlyApi<PaymentRefund>('/payment-refunds')
