import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { tenantSubscriptionsApi } from '../../api/resources'
import type { TenantSubscription } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { formatDate, StatusTag } from '../../utils/format'

const STATUS_OPTIONS = [
  { label: 'Trialing', value: 'trialing' },
  { label: 'Active', value: 'active' },
  { label: 'Past Due', value: 'past_due' },
  { label: 'Canceled', value: 'canceled' },
]

const formFields: FieldConfig[] = [
  { name: 'tenant', label: 'Tenant ID', type: 'number', required: true },
  { name: 'platform_plan', label: 'Platform Plan ID', type: 'number', required: true },
  { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, required: true },
  { name: 'current_period_start', label: 'Mulai Periode', required: true, extra: 'Format: YYYY-MM-DD' },
  { name: 'current_period_end', label: 'Akhir Periode', required: true, extra: 'Format: YYYY-MM-DD' },
  { name: 'gateway', label: 'Gateway' },
  { name: 'gateway_subscription_id', label: 'Gateway Subscription ID' },
  { name: 'cancellation_reason', label: 'Alasan Pembatalan', type: 'textarea' },
]

export function TenantSubscriptionsPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin'

  const columns: TableColumnsType<TenantSubscription> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Plan', dataIndex: 'platform_plan_name' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Mulai', dataIndex: 'current_period_start', render: formatDate },
    { title: 'Akhir', dataIndex: 'current_period_end', render: formatDate },
  ]

  return (
    <ResourcePage<TenantSubscription>
      title="Langganan Tenant"
      queryKey="tenant-subscriptions"
      fetchList={tenantSubscriptionsApi.list}
      create={canWrite ? tenantSubscriptionsApi.create : undefined}
      update={canWrite ? tenantSubscriptionsApi.update : undefined}
      remove={canWrite ? tenantSubscriptionsApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
