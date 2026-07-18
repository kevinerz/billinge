import { useState } from 'react'
import type { TableColumnsType } from 'antd'
import { Modal, List, Typography, Tag } from 'antd'
import { ResourcePage, type FieldConfig } from '../../components/ResourcePage'
import { voucherBatchesApi } from '../../api/resources'
import type { VoucherBatch } from '../../api/types'
import { useAuth } from '../../auth/AuthContext'
import { formatDateTime, StatusTag } from '../../utils/format'

export function VoucherBatchesPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'
  const [viewingBatch, setViewingBatch] = useState<VoucherBatch | null>(null)

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'service_plan', label: 'Service Plan ID (opsional)', type: 'number' },
    { name: 'batch_code', label: 'Kode Batch', required: true, extra: 'mis. PROMO-AGUSTUS-2026' },
    { name: 'quantity', label: 'Jumlah Voucher', type: 'number', required: true },
    { name: 'price_each', label: 'Harga per Voucher', type: 'number', required: true },
  ]

  const columns: TableColumnsType<VoucherBatch> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Kode Batch', dataIndex: 'batch_code' },
    { title: 'Jumlah', dataIndex: 'quantity' },
    { title: 'Harga/Voucher', dataIndex: 'price_each' },
    { title: 'Dibuat Oleh', dataIndex: 'generated_by_user_email' },
    { title: 'Dibuat', dataIndex: 'created_at', render: formatDateTime },
  ]

  return (
    <>
      <ResourcePage<VoucherBatch>
        title="Batch Voucher"
        queryKey="voucher-batches"
        fetchList={voucherBatchesApi.list}
        create={voucherBatchesApi.create}
        remove={voucherBatchesApi.remove}
        columns={columns}
        formFields={formFields}
        extraActions={(record) => <a onClick={() => setViewingBatch(record)}>Lihat Kode</a>}
        onCreateSuccess={(created) => setViewingBatch(created)}
      />
      <Modal
        title={`Kode Voucher — ${viewingBatch?.batch_code ?? ''}`}
        open={!!viewingBatch}
        onOk={() => setViewingBatch(null)}
        onCancel={() => setViewingBatch(null)}
        cancelButtonProps={{ style: { display: 'none' } }}
        width={500}
      >
        <List
          size="small"
          bordered
          dataSource={viewingBatch?.vouchers ?? []}
          style={{ maxHeight: 400, overflowY: 'auto' }}
          renderItem={(v) => (
            <List.Item>
              <Typography.Text copyable style={{ fontFamily: 'monospace' }}>
                {v.username}
              </Typography.Text>
              <StatusTag status={v.status} />
            </List.Item>
          )}
        />
        {viewingBatch && viewingBatch.vouchers.length === 0 && (
          <Tag color="default">Belum ada data voucher (batch lama, coba muat ulang)</Tag>
        )}
      </Modal>
    </>
  )
}
