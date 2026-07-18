import type { TableColumnsType } from 'antd'
import { Typography } from 'antd'
import { ResourcePage } from '../../components/ResourcePage'
import { paymentGatewayEventsApi } from '../../api/resources'
import type { PaymentGatewayEvent } from '../../api/types'
import { formatDateTime } from '../../utils/format'

const columns: TableColumnsType<PaymentGatewayEvent> = [
  { title: 'Waktu', dataIndex: 'received_at', render: formatDateTime },
  { title: 'Tipe', dataIndex: 'payment_type' },
  { title: 'Payment ID', dataIndex: 'payment_id' },
  { title: 'Gateway', dataIndex: 'gateway' },
  { title: 'Event', dataIndex: 'event_type' },
  { title: 'Status Dilaporkan', dataIndex: 'status_reported' },
  {
    title: 'Payload',
    dataIndex: 'payload',
    render: (v: Record<string, unknown>) => (
      <Typography.Text code style={{ fontSize: 12 }}>
        {JSON.stringify(v).slice(0, 120)}
      </Typography.Text>
    ),
  },
]

export function PaymentGatewayEventsPage() {
  return (
    <ResourcePage<PaymentGatewayEvent>
      title="Event Webhook Gateway"
      queryKey="payment-gateway-events"
      fetchList={paymentGatewayEventsApi.list}
      columns={columns}
    />
  )
}
