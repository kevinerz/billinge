import type { TableColumnsType } from 'antd'
import { Typography } from 'antd'
import { ResourcePage } from '../components/ResourcePage'
import { auditLogsApi } from '../api/resources'
import type { AuditLog } from '../api/types'
import { formatDateTime } from '../utils/format'

const columns: TableColumnsType<AuditLog> = [
  { title: 'Waktu', dataIndex: 'created_at', render: formatDateTime },
  { title: 'Aksi', dataIndex: 'action' },
  { title: 'Tenant ID', dataIndex: 'tenant_id', render: (v: number | null) => v ?? '-' },
  { title: 'User ID', dataIndex: 'user_id', render: (v: number | null) => v ?? <em>sistem</em> },
  { title: 'Entitas', render: (_, r) => (r.entity_type ? `${r.entity_type} #${r.entity_id}` : '-') },
  {
    title: 'Detail',
    dataIndex: 'metadata',
    render: (v: Record<string, unknown> | null) =>
      v ? (
        <Typography.Text code style={{ fontSize: 12 }}>
          {JSON.stringify(v)}
        </Typography.Text>
      ) : (
        '-'
      ),
  },
]

export function AuditLogsPage() {
  return (
    <ResourcePage<AuditLog>
      title="Audit Log"
      queryKey="audit-logs"
      fetchList={auditLogsApi.list}
      columns={columns}
    />
  )
}
