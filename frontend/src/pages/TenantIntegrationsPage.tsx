import type { TableColumnsType } from 'antd'
import { Tag } from 'antd'
import { ResourcePage, type FieldConfig } from '../components/ResourcePage'
import { tenantIntegrationsApi } from '../api/resources'
import type { TenantIntegration } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { formatDateTime } from '../utils/format'

const TYPE_OPTIONS = [
  { label: 'Payment Gateway', value: 'payment_gateway' },
  { label: 'WhatsApp', value: 'whatsapp' },
  { label: 'SMS', value: 'sms' },
  { label: 'Email', value: 'email' },
  // vpn_hub sengaja tidak di sini — kredensial VPN dikelola otomatis lewat
  // halaman NAS (auto-provision ke CHR), bukan diisi manual di sini.
]

export function TenantIntegrationsPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'integration_type', label: 'Jenis Integrasi', type: 'select', options: TYPE_OPTIONS, required: true },
    { name: 'provider', label: 'Provider', required: true, extra: 'mis. midtrans, xendit, fonnte, starsender, smtp' },
    {
      name: 'credentials',
      label: 'Kredensial (JSON)',
      type: 'textarea',
      required: true,
      extra: 'Contoh: {"server_key": "..."} — tidak pernah ditampilkan lagi setelah disimpan',
    },
    { name: 'is_active', label: 'Aktif', type: 'switch' },
  ]

  const columns: TableColumnsType<TenantIntegration> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Jenis', dataIndex: 'integration_type' },
    { title: 'Provider', dataIndex: 'provider' },
    { title: 'Aktif', dataIndex: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Ya' : 'Tidak'}</Tag> },
    { title: 'Dibuat', dataIndex: 'created_at', render: formatDateTime },
  ]

  return (
    <ResourcePage<TenantIntegration>
      title="Integrasi Tenant"
      queryKey="tenant-integrations"
      fetchList={tenantIntegrationsApi.list}
      create={tenantIntegrationsApi.create}
      update={tenantIntegrationsApi.update}
      remove={tenantIntegrationsApi.remove}
      columns={columns}
      formFields={formFields}
      transformValues={(values) => {
        if (typeof values.credentials === 'string') {
          try {
            return { ...values, credentials: JSON.parse(values.credentials) }
          } catch {
            throw new Error('Format JSON kredensial tidak valid')
          }
        }
        return values
      }}
    />
  )
}
