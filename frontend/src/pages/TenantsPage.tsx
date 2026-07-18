import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../components/ResourcePage'
import { tenantsApi } from '../api/resources'
import type { Tenant } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { formatDateTime, StatusTag } from '../utils/format'

const STATUS_OPTIONS = [
  { label: 'Trial', value: 'trial' },
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
]

const formFields: FieldConfig[] = [
  { name: 'slug', label: 'Slug', required: true, hideOnEdit: true },
  { name: 'name', label: 'Nama', required: true },
  { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, required: true },
]

export function TenantsPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'

  const columns: TableColumnsType<Tenant> = [
    { title: 'Slug', dataIndex: 'slug' },
    { title: 'Nama', dataIndex: 'name' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Nama Legal', render: (_, r) => r.billing_profile?.legal_name ?? '-' },
    { title: 'Dibuat', dataIndex: 'created_at', render: formatDateTime },
  ]

  return (
    <ResourcePage<Tenant>
      title="Tenants"
      queryKey="tenants"
      fetchList={tenantsApi.list}
      create={isSuperAdmin ? tenantsApi.create : undefined}
      update={tenantsApi.update}
      remove={isSuperAdmin ? tenantsApi.remove : undefined}
      columns={columns}
      formFields={formFields}
    />
  )
}
