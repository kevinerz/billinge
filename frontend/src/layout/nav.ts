import type { Role } from '../api/types'

export interface NavItem {
  key: string
  label: string
  path?: string
  roles?: Role[] // omit = visible to everyone logged in
  children?: NavItem[]
}

// Dashboard PLATFORM: kelola tenant, tagih tenant, sediakan infrastruktur
// (VPN/NAS/IP). BUKAN urus pelanggan/voucher/tagihan-pelanggan tenant —
// itu domain tenant (portal terpisah nanti). Semua super_admin.
export const NAV_ITEMS: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', path: '/' },
  { key: 'tenants', label: 'Tenants', path: '/tenants', roles: ['super_admin'] },
  { key: 'nas', label: 'NAS / VPN', path: '/nas', roles: ['super_admin'] },
  {
    key: 'billing',
    label: 'Tagihan Tenant',
    roles: ['super_admin'],
    children: [
      { key: 'platform-plans', label: 'Paket Platform', path: '/billing/platform-plans' },
      { key: 'tenant-subscriptions', label: 'Langganan Tenant', path: '/billing/tenant-subscriptions' },
      { key: 'platform-invoices', label: 'Invoice Tenant', path: '/billing/platform-invoices' },
      { key: 'platform-payments', label: 'Pembayaran Tenant', path: '/billing/platform-payments' },
    ],
  },
  { key: 'users', label: 'Pengguna', path: '/users', roles: ['super_admin'] },
  { key: 'audit-logs', label: 'Audit Log', path: '/audit-logs', roles: ['super_admin'] },
  {
    key: 'webhooks',
    label: 'Webhook',
    roles: ['super_admin'],
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
