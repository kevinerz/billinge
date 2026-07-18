import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { subscriberSubscriptionsApi } from '../../api/resources'
import type { SubscriberSubscription } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { formatDate, StatusTag } from '../../utils/format'

const STATUS_OPTIONS = [
  { label: 'Trialing', value: 'trialing' },
  { label: 'Active', value: 'active' },
  { label: 'Past Due', value: 'past_due' },
  { label: 'Canceled', value: 'canceled' },
]

export function SubscriberSubscriptionsPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin' || user?.role === 'tenant_admin'
  const isSuperAdmin = user?.role === 'super_admin'

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'subscriber', label: 'Subscriber ID', type: 'number', required: true },
    { name: 'service_plan', label: 'Service Plan ID', type: 'number', required: true },
    { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, required: true },
    { name: 'current_period_start', label: 'Mulai Periode', required: true, extra: 'Format: YYYY-MM-DD' },
    { name: 'current_period_end', label: 'Akhir Periode', required: true, extra: 'Format: YYYY-MM-DD' },
    { name: 'gateway', label: 'Gateway' },
    { name: 'gateway_subscription_id', label: 'Gateway Subscription ID' },
    { name: 'cancellation_reason', label: 'Alasan Pembatalan', type: 'textarea' },
  ]

  const columns: TableColumnsType<SubscriberSubscription> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Subscriber', dataIndex: 'subscriber' },
    { title: 'Paket', dataIndex: 'service_plan_name' },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Akhir Periode', dataIndex: 'current_period_end', render: formatDate },
  ]

  return (
    <ResourcePage<SubscriberSubscription>
      title="Langganan Pelanggan"
      queryKey="subscriber-subscriptions"
      fetchList={subscriberSubscriptionsApi.list}
      create={canWrite ? subscriberSubscriptionsApi.create : undefined}
      update={canWrite ? subscriberSubscriptionsApi.update : undefined}
      remove={canWrite ? subscriberSubscriptionsApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
