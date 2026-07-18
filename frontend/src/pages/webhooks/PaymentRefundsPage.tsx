import type { TableColumnsType } from 'antd'
import { ResourcePage } from '../../components/ResourcePage'
import { paymentRefundsApi } from '../../api/resources'
import type { PaymentRefund } from '../../api/types'
import { formatDateTime, StatusTag } from '../../utils/format'

const columns: TableColumnsType<PaymentRefund> = [
  { title: 'Tipe', dataIndex: 'payment_type' },
  { title: 'Payment ID', dataIndex: 'payment_id' },
  { title: 'Jumlah', dataIndex: 'amount' },
  { title: 'Alasan', dataIndex: 'reason' },
  { title: 'ID Refund Gateway', dataIndex: 'gateway_refund_id' },
  { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
  { title: 'Dibuat', dataIndex: 'created_at', render: formatDateTime },
]

export function PaymentRefundsPage() {
  return (
    <ResourcePage<PaymentRefund>
      title="Refund Pembayaran"
      queryKey="payment-refunds"
      fetchList={paymentRefundsApi.list}
      columns={columns}
    />
  )
}
