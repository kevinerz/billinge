import type { TableColumnsType } from 'antd'
import { ResourcePage } from '../../components/ResourcePage'
import { platformPaymentsApi } from '../../api/resources'
import type { PlatformPayment } from '../../api/types'
import { formatDateTime, StatusTag } from '../../utils/format'

const columns: TableColumnsType<PlatformPayment> = [
  { title: 'ID', dataIndex: 'id' },
  { title: 'Invoice', dataIndex: 'invoice' },
  { title: 'Tenant', dataIndex: 'tenant' },
  { title: 'Gateway', dataIndex: 'gateway' },
  { title: 'Order ID', dataIndex: 'gateway_order_id' },
  { title: 'Jumlah', render: (_, r) => `${r.currency} ${r.amount}` },
  { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
  { title: 'Dibayar', dataIndex: 'paid_at', render: formatDateTime },
]

export function PlatformPaymentsPage() {
  return (
    <ResourcePage<PlatformPayment>
      title="Pembayaran Platform"
      queryKey="platform-payments"
      fetchList={platformPaymentsApi.list}
      columns={columns}
    />
  )
}
