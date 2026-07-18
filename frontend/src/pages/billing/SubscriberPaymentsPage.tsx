import type { TableColumnsType } from 'antd'
import { ResourcePage } from '../../components/ResourcePage'
import { subscriberPaymentsApi } from '../../api/resources'
import type { SubscriberPayment } from '../../api/types'
import { formatDateTime, StatusTag } from '../../utils/format'

const columns: TableColumnsType<SubscriberPayment> = [
  { title: 'ID', dataIndex: 'id' },
  { title: 'Invoice', dataIndex: 'invoice' },
  { title: 'Tenant', dataIndex: 'tenant' },
  { title: 'Gateway', dataIndex: 'gateway' },
  { title: 'Order ID', dataIndex: 'gateway_order_id' },
  { title: 'Jumlah', render: (_, r) => `${r.currency} ${r.amount}` },
  { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
  { title: 'Dibayar', dataIndex: 'paid_at', render: formatDateTime },
]

export function SubscriberPaymentsPage() {
  return (
    <ResourcePage<SubscriberPayment>
      title="Pembayaran Pelanggan"
      queryKey="subscriber-payments"
      fetchList={subscriberPaymentsApi.list}
      columns={columns}
    />
  )
}
