import type { TableColumnsType } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { subscriberInvoicesApi } from '../../api/resources'
import type { SubscriberInvoice } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { formatDate, formatDateTime, StatusTag } from '../../utils/format'

const STATUS_OPTIONS = [
  { label: 'Draft', value: 'draft' },
  { label: 'Pending', value: 'pending' },
  { label: 'Paid', value: 'paid' },
  { label: 'Overdue', value: 'overdue' },
  { label: 'Void', value: 'void' },
]

export function SubscriberInvoicesPage() {
  const { user } = useAuth()
  const canWrite = user?.role === 'super_admin' || user?.role === 'tenant_admin'
  const isSuperAdmin = user?.role === 'super_admin'

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'subscriber', label: 'Subscriber ID', type: 'number', required: true },
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
    { name: 'billing_address', label: 'Alamat Penagihan', type: 'textarea' },
  ]

  const columns: TableColumnsType<SubscriberInvoice> = [
    { title: 'No. Invoice', dataIndex: 'invoice_number' },
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Subscriber', dataIndex: 'subscriber' },
    { title: 'Total', render: (_, r) => `${r.currency} ${r.total_amount}` },
    { title: 'Status', dataIndex: 'status', render: (v: string) => <StatusTag status={v} /> },
    { title: 'Jatuh Tempo', dataIndex: 'due_date', render: formatDate },
    { title: 'Dibayar', dataIndex: 'paid_at', render: formatDateTime },
  ]

  return (
    <ResourcePage<SubscriberInvoice>
      title="Invoice Pelanggan"
      queryKey="subscriber-invoices"
      fetchList={subscriberInvoicesApi.list}
      create={canWrite ? subscriberInvoicesApi.create : undefined}
      update={canWrite ? subscriberInvoicesApi.update : undefined}
      remove={canWrite ? subscriberInvoicesApi.remove : undefined}
      columns={columns}
      formFields={canWrite ? formFields : undefined}
    />
  )
}
