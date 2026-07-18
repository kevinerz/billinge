import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { servicePlansApi } from '../../api/resources'
import type { ServicePlan } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'

export function ServicePlansPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin' || user?.role === 'tenant_admin'
  const isSuperAdmin = user?.role === 'super_admin'

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'name', label: 'Nama Paket', required: true },
    { name: 'price', label: 'Harga', type: 'number', required: true },
    { name: 'mikrotik_rate_limit', label: 'Rate Limit Mikrotik', extra: 'mis. 5M/5M' },
    { name: 'radius_groupname', label: 'RADIUS Group Name', required: true },
  ]

  const columns: TableColumnsType<ServicePlan> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Nama', dataIndex: 'name' },
    { title: 'Harga', dataIndex: 'price' },
    { title: 'Rate Limit', dataIndex: 'mikrotik_rate_limit' },
    { title: 'RADIUS Group', dataIndex: 'radius_groupname' },
  ]

  return (
    <ResourcePage<ServicePlan>
      title="Paket Layanan"
      queryKey="service-plans"
      fetchList={servicePlansApi.list}
      create={canWrite ? servicePlansApi.create : undefined}
      update={canWrite ? servicePlansApi.update : undefined}
      remove={canWrite ? servicePlansApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
