import { useQuery } from '@tanstack/react-query'
import { Card, Col, Row, Statistic, Typography } from 'antd'
import { useAuth } from '../auth/AuthContext'
import { tenantsApi, nasApi, tenantSubscriptionsApi, platformInvoicesApi } from '../api/resources'

export function DashboardPage() {
  const { user } = useAuth()

  const tenantsQuery = useQuery({ queryKey: ['tenants'], queryFn: tenantsApi.list })
  const nasQuery = useQuery({ queryKey: ['nas'], queryFn: nasApi.list })
  const subsQuery = useQuery({ queryKey: ['tenant-subscriptions'], queryFn: tenantSubscriptionsApi.list })
  const invoicesQuery = useQuery({ queryKey: ['platform-invoices'], queryFn: platformInvoicesApi.list })

  const activeSubs = (subsQuery.data ?? []).filter((s) => s.status === 'active').length
  const overdueInvoices = (invoicesQuery.data ?? []).filter((i) => i.status === 'overdue').length

  return (
    <div>
      <Typography.Title level={3}>Selamat datang, {user?.full_name || user?.email}</Typography.Title>
      <Typography.Paragraph type="secondary">Dashboard Platform — kelola & tagih tenant, sediakan VPN/NAS.</Typography.Paragraph>

      <Row gutter={16} style={{ marginTop: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic title="Total Tenant" value={tenantsQuery.data?.length ?? 0} loading={tenantsQuery.isLoading} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="NAS / VPN" value={nasQuery.data?.length ?? 0} loading={nasQuery.isLoading} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic title="Langganan Aktif" value={activeSubs} loading={subsQuery.isLoading} />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="Invoice Overdue"
              value={overdueInvoices}
              valueStyle={overdueInvoices > 0 ? { color: '#cf1322' } : undefined}
              loading={invoicesQuery.isLoading}
            />
          </Card>
        </Col>
      </Row>
    </div>
  )
}
