import type { TableColumnsType } from 'antd'
import { Tag } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { platformPlansApi } from '../../api/resources'
import type { PlatformPlan } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'

const CYCLE_OPTIONS = [
  { label: 'Bulanan', value: 'monthly' },
  { label: 'Tahunan', value: 'yearly' },
]

const formFields: FieldConfig[] = [
  { name: 'slug', label: 'Slug', required: true },
  { name: 'name', label: 'Nama', required: true },
  { name: 'price', label: 'Harga', type: 'number', required: true },
  { name: 'currency', label: 'Mata Uang', required: true },
  { name: 'billing_cycle', label: 'Siklus Billing', type: 'select', options: CYCLE_OPTIONS, required: true },
  { name: 'max_subscribers', label: 'Maks. Pelanggan (kosongkan = unlimited)', type: 'number' },
  { name: 'max_nas', label: 'Maks. NAS (kosongkan = unlimited)', type: 'number' },
  { name: 'is_active', label: 'Aktif', type: 'switch' },
]

export function PlatformPlansPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin'

  const columns: TableColumnsType<PlatformPlan> = [
    { title: 'Slug', dataIndex: 'slug' },
    { title: 'Nama', dataIndex: 'name' },
    { title: 'Harga', render: (_, r) => `${r.currency} ${r.price}` },
    { title: 'Siklus', dataIndex: 'billing_cycle' },
    { title: 'Aktif', dataIndex: 'is_active', render: (v: boolean) => <Tag color={v ? 'green' : 'default'}>{v ? 'Ya' : 'Tidak'}</Tag> },
  ]

  return (
    <ResourcePage<PlatformPlan>
      title="Paket Platform"
      queryKey="platform-plans"
      fetchList={platformPlansApi.list}
      create={canWrite ? platformPlansApi.create : undefined}
      update={canWrite ? platformPlansApi.update : undefined}
      remove={canWrite ? platformPlansApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
