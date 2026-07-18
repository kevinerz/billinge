import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Statistic, Typography } from 'antd'
import { useAuth } from '../auth/AuthContext'
import { tenantsApi, subscribersApi, nasApi, voucherBatchesApi } from '../api/resources'

export function DashboardPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'

  const tenantsQuery = useQuery({ queryKey: ['tenants'], queryFn: tenantsApi.list, enabled: isSuperAdmin })
  const subscribersQuery = useQuery({ queryKey: ['subscribers'], queryFn: subscribersApi.list })
  const nasQuery = useQuery({ queryKey: ['nas'], queryFn: nasApi.list, enabled: user?.role !== 'tenant_staff' })
  const voucherBatchesQuery = useQuery({
    queryKey: ['voucher-batches'],
    queryFn: voucherBatchesApi.list,
    enabled: user?.role !== 'tenant_staff',
  })

  return (
    <div>
      <Typography.Title level={3}>Selamat datang, {user?.full_name || user?.email}</Typography.Title>
      <Typography.Paragraph type="secondary">
        Login sebagai <strong>{user?.role}</strong>
        {user?.tenant_id ? ` — tenant #${user.tenant_id}` : ' — platform'}
      </Typography.Paragraph>

      <Row gutter={16} style={{ marginTop: 24 }}>
        {isSuperAdmin && (
          <Col span={6}>
            <Card>
              <Statistic title="Total Tenant" value={tenantsQuery.data?.length ?? 0} loading={tenantsQuery.isLoading} />
            </Card>
          </Col>
        )}
        <Col span={6}>
          <Card>
            <Statistic
              title="Pelanggan"
              value={subscribersQuery.data?.length ?? 0}
              loading={subscribersQuery.isLoading}
            />
          </Card>
        </Col>
        {user?.role !== 'tenant_staff' && (
          <Col span={6}>
            <Card>
              <Statistic title="NAS / Mikrotik" value={nasQuery.data?.length ?? 0} loading={nasQuery.isLoading} />
            </Card>
          </Col>
        )}
        {user?.role !== 'tenant_staff' && (
          <Col span={6}>
            <Card>
              <Statistic
                title="Batch Voucher"
                value={voucherBatchesQuery.data?.length ?? 0}
                loading={voucherBatchesQuery.isLoading}
              />
            </Card>
          </Col>
        )}
      </Row>
    </div>
  )
}
