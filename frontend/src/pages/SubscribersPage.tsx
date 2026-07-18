import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../components/ResourcePage'
import { subscribersApi } from '../api/resources'
import type { TenantSubscriber } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { StatusTag } from '../utils/format'

const IDENTITY_OPTIONS = [
  { label: 'KTP', value: 'ktp' },
  { label: 'Lainnya', value: 'other' },
]

const STATUS_OPTIONS = [
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
  { label: 'Terminated', value: 'terminated' },
]

export function SubscribersPage() {
  const { user } = useAuth()
  const canDelete = user?.role === 'super_admin' || user?.role === 'tenant_admin'
  const isSuperAdmin = user?.role === 'super_admin'

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'username', label: 'Username', required: true },
    { name: 'full_name', label: 'Nama Lengkap' },
    { name: 'phone', label: 'No. HP' },
    { name: 'email', label: 'Email' },
    { name: 'identity_type', label: 'Jenis Identitas', type: 'select', options: IDENTITY_OPTIONS },
    { name: 'identity_number', label: 'No. Identitas' },
    { name: 'address', label: 'Alamat', type: 'textarea' },
    { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
  ]

  const columns: TableColumnsType<TenantSubscriber> = [
    { title: 'Tenant', dataIndex: 'tenant_slug' },
    { title: 'Username', dataIndex: 'username' },
    { title: 'Nama', dataIndex: 'full_name' },
    { title: 'No. HP', dataIndex: 'phone' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
  ]

  return (
    <ResourcePage<TenantSubscriber>
      title="Pelanggan"
      queryKey="subscribers"
      fetchList={subscribersApi.list}
      create={subscribersApi.create}
      update={subscribersApi.update}
      remove={canDelete ? subscribersApi.remove : undefined}
      columns={columns}
      formFields={formFields}
    />
  )
}
