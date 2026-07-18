import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../components/ResourcePage'
import { usersApi } from '../api/resources'
import type { User } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { formatDateTime, StatusTag } from '../utils/format'

const ALL_ROLE_OPTIONS = [
  { label: 'Super Admin', value: 'super_admin' },
  { label: 'Tenant Admin', value: 'tenant_admin' },
  { label: 'Tenant Staff', value: 'tenant_staff' },
]

const STATUS_OPTIONS = [
  { label: 'Active', value: 'active' },
  { label: 'Suspended', value: 'suspended' },
]

export function UsersPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'
  const roleOptions = isSuperAdmin ? ALL_ROLE_OPTIONS : ALL_ROLE_OPTIONS.filter((r) => r.value !== 'super_admin')

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant_id', label: 'Tenant ID (kosongkan untuk super_admin)', type: 'number' as const }] : []),
    { name: 'role', label: 'Role', type: 'select', options: roleOptions, required: true },
    { name: 'email', label: 'Email', required: true },
    {
      name: 'password',
      label: 'Password',
      type: 'password',
      extra: 'Wajib diisi saat membuat user baru. Kosongkan saat edit kalau tidak ingin mengganti password.',
    },
    { name: 'full_name', label: 'Nama Lengkap' },
    { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS },
  ]

  const columns: TableColumnsType<User> = [
    { title: 'Email', dataIndex: 'email' },
    { title: 'Role', dataIndex: 'role' },
    { title: 'Tenant ID', dataIndex: 'tenant_id', render: (v: number | null) => v ?? '-' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Login Terakhir', dataIndex: 'last_login', render: formatDateTime },
  ]

  return (
    <ResourcePage<User>
      title="Pengguna Dashboard"
      queryKey="users"
      fetchList={usersApi.list}
      create={usersApi.create}
      update={usersApi.update}
      remove={usersApi.remove}
      columns={columns}
      formFields={formFields}
      transformValues={(values) => {
        // Jangan kirim password kosong saat edit (biar tidak menimpa password lama)
        if (!values.password) {
          const { password: _password, ...rest } = values
          return rest
        }
        return values
      }}
    />
  )
}
