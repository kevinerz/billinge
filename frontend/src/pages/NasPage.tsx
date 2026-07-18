import { useState } from 'react'
import type { TableColumnsType } from 'antd'
import { Modal, Typography, Alert, message } from 'antd'
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
  const [created, setCreated] = useState<Nas | null>(null)
  const [scriptModal, setScriptModal] = useState<{ nasname: string; script: string } | null>(null)

  const formFields: FieldConfig[] = [
    ...(isSuperAdmin ? [{ name: 'tenant', label: 'Tenant ID', type: 'number' as const, required: true }] : []),
    { name: 'nasname', label: 'IP Address NAS', required: true, extra: 'IP Mikrotik seperti terlihat oleh server RADIUS. Untuk VPN Hub, pakai IP dari pool 10.201.0.0/24.' },
    { name: 'shortname', label: 'Nama Singkat' },
    { name: 'type', label: 'Jenis', type: 'select', options: TYPE_OPTIONS },
    { name: 'ports', label: 'Ports', type: 'number' },
    { name: 'server', label: 'Server' },
    { name: 'community', label: 'SNMP Community' },
    { name: 'description', label: 'Deskripsi', type: 'textarea' },
    {
      name: 'via_vpn',
      label: 'Konek lewat VPN Hub',
      type: 'switch',
      hideOnEdit: true,
      extra: 'Kalau aktif, backend otomatis daftar PPP secret+IP ke CHR (RouterOS API) dan generate script buat Mikrotik tenant.',
    },
  ]

  const columns: TableColumnsType<Nas> = [
    { title: 'Tenant', dataIndex: 'tenant_slug' },
    { title: 'IP NAS', dataIndex: 'nasname' },
    { title: 'Nama', dataIndex: 'shortname' },
    { title: 'Jenis', dataIndex: 'type' },
    { title: 'VPN', render: (_, r) => (r.vpn_username ? 'Ya' : '-') },
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
        onCreateSuccess={(record) => setCreated(record)}
        extraActions={(record) =>
          record.vpn_client_script ? (
            <a onClick={() => setScriptModal({ nasname: record.nasname, script: record.vpn_client_script! })}>
              Copy Script VPN
            </a>
          ) : null
        }
      />

      {/* Modal setelah create: secret RADIUS + (kalau via VPN) kredensial & script tenant */}
      <Modal
        title="NAS baru dibuat"
        open={!!created}
        onOk={() => setCreated(null)}
        onCancel={() => setCreated(null)}
        cancelButtonProps={{ style: { display: 'none' } }}
        width={created?.vpn_client_script ? 720 : 520}
      >
        <Alert
          type="warning"
          showIcon
          message="Secret & kredensial VPN ini paling aman disalin sekarang. Simpan/berikan ke tenant."
          style={{ marginBottom: 16 }}
        />
        <Typography.Paragraph>
          <strong>NAS:</strong> {created?.nasname}
        </Typography.Paragraph>
        {created?.secret && (
          <Typography.Paragraph copyable={{ text: created.secret }}>
            <strong>Secret RADIUS:</strong> <code>{created.secret}</code>
          </Typography.Paragraph>
        )}
        {created?.vpn_username && (
          <Typography.Paragraph>
            <strong>Username VPN:</strong> <code>{created.vpn_username}</code>
          </Typography.Paragraph>
        )}
        {created?.vpn_client_script && (
          <>
            <Typography.Paragraph type="secondary" style={{ marginBottom: 4 }}>
              Script buat dijalankan di Mikrotik tenant (upload billinge-ca.crt dulu):
            </Typography.Paragraph>
            <div style={{ textAlign: 'right', marginBottom: 4 }}>
              <a
                onClick={() => {
                  navigator.clipboard.writeText(created.vpn_client_script!)
                  message.success('Script disalin')
                }}
              >
                Copy Script
              </a>
            </div>
            <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, maxHeight: 300, overflowY: 'auto', margin: 0 }}>
              {created.vpn_client_script}
            </pre>
          </>
        )}
      </Modal>

      {/* Modal dari action "Copy Script VPN" per baris */}
      <Modal
        title={`Script VPN — ${scriptModal?.nasname ?? ''}`}
        open={!!scriptModal}
        onCancel={() => setScriptModal(null)}
        onOk={() => {
          if (scriptModal) {
            navigator.clipboard.writeText(scriptModal.script)
            message.success('Script disalin')
          }
        }}
        okText="Copy"
        width={720}
      >
        <pre style={{ whiteSpace: 'pre-wrap', fontSize: 12, maxHeight: 400, overflowY: 'auto', margin: 0 }}>
          {scriptModal?.script}
        </pre>
      </Modal>
    </>
  )
}
