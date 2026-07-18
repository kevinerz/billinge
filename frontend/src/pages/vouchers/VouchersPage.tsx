import type { TableColumnsType } from 'antd'
import { ResourcePage } from '../../components/ResourcePage'
import { vouchersApi } from '../../api/resources'
import type { Voucher } from '../../api/types'
import { formatDateTime, StatusTag } from '../../utils/format'

const columns: TableColumnsType<Voucher> = [
  { title: 'Tenant', dataIndex: 'tenant' },
  { title: 'Batch', dataIndex: 'batch' },
  { title: 'Username', dataIndex: 'username' },
  { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
  { title: 'Ditebus', dataIndex: 'redeemed_at', render: formatDateTime },
  { title: 'Dibuat', dataIndex: 'created_at', render: formatDateTime },
]

export function VouchersPage() {
  return (
    <ResourcePage<Voucher>
      title="Daftar Voucher"
      queryKey="vouchers"
      fetchList={vouchersApi.list}
      columns={columns}
    />
  )
}
