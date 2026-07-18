export type Role = 'super_admin' | 'tenant_admin' | 'tenant_staff'

export interface Me {
  id: number
  tenant_id: number | null
  role: Role
  email: string
  full_name: string | null
  status: 'active' | 'suspended'
  last_login: string | null
}

export interface User {
  id: number
  tenant_id: number | null
  role: Role
  email: string
  password?: string
  full_name: string | null
  status: 'active' | 'suspended'
  last_login: string | null
  created_at: string
  updated_at: string
}

export interface TenantBillingProfile {
  legal_name: string
  tax_id: string | null
  billing_email: string | null
  billing_phone: string | null
  billing_address: string | null
  pic_name: string | null
}

export interface Tenant {
  id: number
  slug: string
  name: string
  status: 'trial' | 'active' | 'suspended'
  created_at: string
  updated_at: string
  billing_profile: TenantBillingProfile | null
}

export interface TenantIntegration {
  id: number
  tenant: number
  integration_type: 'payment_gateway' | 'whatsapp' | 'sms' | 'email' | 'vpn_hub'
  provider: string
  credentials?: Record<string, unknown>
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TenantSubscriber {
  id: number
  tenant: number
  tenant_slug: string
  username: string
  full_name: string | null
  phone: string | null
  email: string | null
  identity_type: 'ktp' | 'other'
  identity_number: string | null
  address: string | null
  install_lat: string | null
  install_lng: string | null
  status: 'active' | 'suspended' | 'terminated'
  created_at: string
  updated_at: string
}

export interface Nas {
  id: number
  tenant: number
  tenant_slug: string
  nasname: string
  shortname: string | null
  type: string
  ports: number | null
  secret?: string
  server: string | null
  community: string | null
  description: string | null
  last_contact_at: string | null
}

export type BillingCycle = 'monthly' | 'yearly'
export type SubscriptionStatus = 'trialing' | 'active' | 'past_due' | 'canceled'
export type InvoiceStatus = 'draft' | 'pending' | 'paid' | 'overdue' | 'void'
export type PaymentStatus = 'pending' | 'settlement' | 'expired' | 'failed' | 'refunded' | 'chargeback'

export interface PlatformPlan {
  id: number
  slug: string
  name: string
  price: string
  currency: string
  billing_cycle: BillingCycle
  max_subscribers: number | null
  max_nas: number | null
  is_active: boolean
  created_at: string
  updated_at: string
}

export interface TenantSubscription {
  id: number
  tenant: number
  platform_plan: number
  platform_plan_name?: string
  status: SubscriptionStatus
  current_period_start: string
  current_period_end: string
  gateway: string | null
  gateway_subscription_id: string | null
  canceled_at: string | null
  cancellation_reason: string | null
  created_at: string
  updated_at: string
}

export interface PlatformInvoiceItem {
  id: number
  description: string
  quantity: number
  unit_price: string
  amount: string
}

export interface PlatformInvoice {
  id: number
  tenant: number
  subscription: number | null
  billing_name: string | null
  billing_tax_id: string | null
  billing_address: string | null
  invoice_number: string
  currency: string
  subtotal: string
  tax_amount: string
  total_amount: string
  status: InvoiceStatus
  period_start: string
  period_end: string
  due_date: string
  paid_at: string | null
  items: PlatformInvoiceItem[]
  created_at: string
  updated_at: string
}

export interface PlatformPayment {
  id: number
  invoice: number
  tenant: number
  gateway: string
  gateway_order_id: string | null
  gateway_transaction_id: string | null
  payment_method: string | null
  payment_url: string | null
  amount: string
  gateway_fee: string | null
  currency: string
  status: PaymentStatus
  paid_at: string | null
  created_at: string
  updated_at: string
}

export interface ServicePlan {
  id: number
  tenant: number
  name: string
  price: string
  mikrotik_rate_limit: string | null
  radius_groupname: string
  created_at: string
  updated_at: string
}

export interface SubscriberSubscription {
  id: number
  tenant: number
  subscriber: number
  service_plan: number
  service_plan_name?: string
  status: SubscriptionStatus
  current_period_start: string
  current_period_end: string
  gateway: string | null
  gateway_subscription_id: string | null
  canceled_at: string | null
  cancellation_reason: string | null
  created_at: string
  updated_at: string
}

export interface SubscriberInvoice {
  id: number
  tenant: number
  subscriber: number
  subscription: number | null
  billing_name: string | null
  billing_address: string | null
  invoice_number: string
  currency: string
  subtotal: string
  tax_amount: string
  total_amount: string
  status: InvoiceStatus
  period_start: string
  period_end: string
  due_date: string
  paid_at: string | null
  created_at: string
  updated_at: string
}

export interface SubscriberPayment {
  id: number
  invoice: number
  tenant: number
  gateway: string | null
  gateway_order_id: string | null
  gateway_transaction_id: string | null
  payment_method: string | null
  payment_url: string | null
  amount: string
  gateway_fee: string | null
  currency: string
  status: PaymentStatus
  paid_at: string | null
  created_at: string
  updated_at: string
}

export interface Voucher {
  id: number
  batch: number
  tenant: number
  username: string
  status: 'unused' | 'active' | 'expired'
  redeemed_at: string | null
  created_at: string
}

export interface VoucherBatch {
  id: number
  tenant: number
  service_plan: number | null
  batch_code: string
  quantity: number
  price_each: string
  generated_by_user: number | null
  generated_by_user_email?: string
  created_at: string
  vouchers: Voucher[]
}

export interface AuditLog {
  id: number
  tenant_id: number | null
  user_id: number | null
  action: string
  entity_type: string | null
  entity_id: number | null
  metadata: Record<string, unknown> | null
  created_at: string
}

export interface PaymentGatewayEvent {
  id: number
  payment_type: 'platform' | 'subscriber'
  payment_id: number
  gateway: string
  event_type: string | null
  status_reported: string | null
  payload: Record<string, unknown>
  received_at: string
}

export interface PaymentRefund {
  id: number
  payment_type: 'platform' | 'subscriber'
  payment_id: number
  amount: string
  reason: string | null
  gateway_refund_id: string | null
  status: 'pending' | 'completed' | 'failed'
  created_at: string
  updated_at: string
}
