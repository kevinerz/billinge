import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { platformInvoicesApi } from '../../api/resources'
import type { PlatformInvoice } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { formatDate, formatDateTime, StatusTag } from '../../utils/format'

const STATUS_OPTIONS = [
  { label: 'Draft', value: 'draft' },
  { label: 'Pending', value: 'pending' },
  { label: 'Paid', value: 'paid' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Void', value: 'void' },
]

const formFields: FieldConfig[] = [
  { name: 'tenant', label: 'Tenant ID', type: 'number', required: true },
  { name: 'subscription', label: 'Subscription ID (opsional)', type: 'number' },
  { name: 'invoice_number', label: 'Nomor Invoice', required: true },
  { name: 'currency', label: 'Mata Uang', required: true },
  { name: 'subtotal', label: 'Subtotal', type: 'number', required: true },
  { name: 'tax_amount', label: 'Pajak', type: 'number', required: true },
  { name: 'total_amount', label: 'Total', type: 'number', required: true },
  { name: 'status', label: 'Status', type: 'select', options: STATUS_OPTIONS, required: true },
  { name: 'period_start', label: 'Mulai Periode', required: true, extra: 'Format: YYYY-MM-DD' },
  { name: 'period_end', label: 'Akhir Periode', required: true, extra: 'Format: YYYY-MM-DD' },
  { name: 'due_date', label: 'Jatuh Tempo', required: true, extra: 'Format: YYYY-MM-DD' },
  { name: 'billing_name', label: 'Nama Penagihan' },
  { name: 'billing_tax_id', label: 'NPWP' },
  { name: 'billing_address', label: 'Alamat Penagihan', type: 'textarea' },
]

export function PlatformInvoicesPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin'

  const columns: TableColumnsType<PlatformInvoice> = [
    { title: 'No. Invoice', dataIndex: 'invoice_number' },
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Total', render: (_, r) => `${r.currency} ${r.total_amount}` },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Jatuh Tempo', dataIndex: 'due_date', render: formatDate },
    { title: 'Dibayar', dataIndex: 'paid_at', render: formatDateTime },
  ]

  return (
    <ResourcePage<PlatformInvoice>
      title="Invoice Platform"
      queryKey="platform-invoices"
      fetchList={platformInvoicesApi.list}
      create={canWrite ? platformInvoicesApi.create : undefined}
      update={canWrite ? platformInvoicesApi.update : undefined}
      remove={canWrite ? platformInvoicesApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
