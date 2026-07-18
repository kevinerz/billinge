import { useState } from 'react'
import type { TableColumnsType } from 'antd'
import { Modal, Typography, Alert } from 'antd'
import { ResourcePage, type FieldConfig } from '../components/ResourcePage'
import { nasApi } from '../api/resources'
import type { Nas } from '../api/types'
import { useAuth } from '../auth/AuthContext'
import { formatDateTime } from '../utils/format'

const TYPE_OPTIONS = [
  { label: 'Mikrotik', value: 'mikrotik' },
  { label: 'Lainnya', value: 'other' },
]

export function NasPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'
  const [revealedSecret, setRevealedSecret] = useState<{ nasname: string; secret: string } | null>(null)

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'nasname', label: 'IP Address NAS', required: true, extra: 'IP Mikrotik seperti terlihat oleh server RADIUS' },
    { name: 'shortname', label: 'Nama Singkat' },
    { name: 'type', label: 'Jenis', type: 'select', options: TYPE_OPTIONS },
    { name: 'ports', label: 'Ports', type: 'number' },
    { name: 'server', label: 'Server' },
    { name: 'community', label: 'SNMP Community' },
    { name: 'description', label: 'Deskripsi', type: 'textarea' },
  ]

  const columns: TableColumnsType<Nas> = [
    { title: 'Tenant', dataIndex: 'tenant_slug' },
    { title: 'IP NAS', dataIndex: 'nasname' },
    { title: 'Nama', dataIndex: 'shortname' },
    { title: 'Jenis', dataIndex: 'type' },
    { title: 'Kontak Terakhir', dataIndex: 'last_contact_at', render: formatDateTime },
  ]

  return (
    <>
      <ResourcePage<Nas>
        title="NAS / Mikrotik"
        queryKey="nas"
        fetchList={nasApi.list}
        create={nasApi.create}
        update={nasApi.update}
        remove={nasApi.remove}
        columns={columns}
        formFields={formFields}
        onCreateSuccess={(created) => {
          if (created.secret) {
            setRevealedSecret({ nasname: created.nasname, secret: created.secret })
          }
        }}
      />
      <Modal
        title="Secret RADIUS untuk NAS baru"
        open={!!revealedSecret}
        onOk={() => setRevealedSecret(null)}
        onCancel={() => setRevealedSecret(null)}
        cancelButtonProps={{ style: { display: 'none' } }}
      >
        <Alert
          type="warning"
          showIcon
          message="Secret ini hanya ditampilkan sekali sekarang. Salin dan simpan untuk konfigurasi Mikrotik."
          style={{ marginBottom: 16 }}
        />
        <Typography.Paragraph>
          <strong>NAS:</strong> {revealedSecret?.nasname}
        </Typography.Paragraph>
        <Typography.Paragraph copyable={{ text: revealedSecret?.secret }}>
          <strong>Secret:</strong> <code>{revealedSecret?.secret}</code>
        </Typography.Paragraph>
      </Modal>
    </>
  )
}
