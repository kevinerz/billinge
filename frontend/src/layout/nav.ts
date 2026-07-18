import type { Role } from '../api/types'

export interface NavItem {
  key: string
  label: string
  path?: string
  roles?: Role[] // omit = visible to everyone logged in
  children?: NavItem[]
}

export const NAV_ITEMS: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', path: '/' },
  { key: 'tenants', label: 'Tenants', path: '/tenants' },
  { key: 'tenant-integrations', label: 'Integrasi Tenant', path: '/tenant-integrations', roles: ['super_admin', 'tenant_admin'] },
  { key: 'subscribers', label: 'Pelanggan', path: '/subscribers' },
  { key: 'nas', label: 'NAS / Mikrotik', path: '/nas', roles: ['super_admin', 'tenant_admin'] },
  {
    key: 'billing',
    label: 'Billing',
    children: [
      { key: 'platform-plans', label: 'Paket Platform', path: '/billing/platform-plans' },
      { key: 'tenant-subscriptions', label: 'Langganan Tenant', path: '/billing/tenant-subscriptions' },
      { key: 'platform-invoices', label: 'Invoice Platform', path: '/billing/platform-invoices' },
      { key: 'platform-payments', label: 'Pembayaran Platform', path: '/billing/platform-payments' },
      { key: 'service-plans', label: 'Paket Layanan', path: '/billing/service-plans' },
      { key: 'subscriber-subscriptions', label: 'Langganan Pelanggan', path: '/billing/subscriber-subscriptions' },
      { key: 'subscriber-invoices', label: 'Invoice Pelanggan', path: '/billing/subscriber-invoices' },
      { key: 'subscriber-payments', label: 'Pembayaran Pelanggan', path: '/billing/subscriber-payments' },
    ],
  },
  {
    key: 'vouchers',
    label: 'Voucher',
    roles: ['super_admin', 'tenant_admin'],
    children: [
      { key: 'voucher-batches', label: 'Batch Voucher', path: '/vouchers/batches' },
      { key: 'voucher-list', label: 'Daftar Voucher', path: '/vouchers/list' },
    ],
  },
  { key: 'users', label: 'Pengguna', path: '/users', roles: ['super_admin', 'tenant_admin'] },
  { key: 'audit-logs', label: 'Audit Log', path: '/audit-logs', roles: ['super_admin', 'tenant_admin'] },
  {
    key: 'webhooks',
    label: 'Webhook',
    roles: ['super_admin', 'tenant_admin'],
    children: [
      { key: 'gateway-events', label: 'Event Gateway', path: '/webhooks/events' },
      { key: 'refunds', label: 'Refund', path: '/webhooks/refunds' },
    ],
  },
]

export function filterNavByRole(items: NavItem[], role: Role): NavItem[] {
  return items
    .filter((item) => !item.roles || item.roles.includes(role))
    .map((item) => (item.children ? { ...item, children: filterNavByRole(item.children, role) } : item))
    .filter((item) => !item.children || item.children.length > 0)
}
