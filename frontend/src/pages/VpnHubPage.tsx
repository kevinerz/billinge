import { useMemo, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Alert,
  Button,
  Card,
  Form,
  Input,
  Select,
  Space,
  Table,
  Typography,
  message,
  type TableColumnsType,
} from 'antd'
import { ReloadOutlined } from '@ant-design/icons'
import { useAuth } from '../auth/AuthContext'
import { tenantIntegrationsApi, tenantsApi } from '../api/resources'
import type { TenantIntegration } from '../api/types'

const CHR_ADDRESS = '103.139.163.150'
const LAN_CIDR = '192.168.38.0/24'
const RADIUS_VM_IP = '192.168.38.2'

function randomSecret(length: number): string {
  const bytes = new Uint8Array(length)
  crypto.getRandomValues(bytes)
  return Array.from(bytes, (b) => b.toString(36).padStart(2, '0')).join('').slice(0, length)
}

interface FormValues {
  tenant?: number
  tenantSlug: string
  username: string
  password: string
  remoteAddress: string
  ipsecPsk: string
}

function buildChrScript(v: FormValues): string {
  return `# Jalankan di CHR (${CHR_ADDRESS}) untuk mendaftarkan tenant ini.
:local tenantSlug "${v.tenantSlug}"
:local vpnUsername "${v.username}"
:local vpnPassword "${v.password}"
:local vpnIp "${v.remoteAddress}"

/ppp secret add name=$vpnUsername password=$vpnPassword service=any \\
    profile=billinge-vpn remote-address=$vpnIp comment=("billinge tenant: " . $tenantSlug)

:put ("Tenant VPN IP (daftarkan sebagai nasname): " . $vpnIp)
:put "Selesai. Kirim kredensial + script tenant di bawah ke tenant ini."`
}

function buildTenantScript(v: FormValues): string {
  return `# Jalankan di Mikrotik TENANT. Upload billinge-ca.crt (dari admin) ke
# Files dulu sebelum menjalankan ini. Bikin 3 tunnel sekaligus (OpenVPN,
# SSTP, L2TP/IPsec) dengan failover otomatis lewat route distance.
:local vpnUsername "${v.username}"
:local vpnPassword "${v.password}"
:local ipsecPsk "${v.ipsecPsk}"

/certificate import file-name=billinge-ca.crt passphrase=""

/interface ovpn-client add name=vpn-billinge-ovpn connect-to=${CHR_ADDRESS} port=1194 \\
    protocol=udp user=$vpnUsername password=$vpnPassword \\
    cipher=aes256-cbc auth=sha256 verify-server-certificate=yes add-default-route=no

/interface sstp-client add name=vpn-billinge-sstp connect-to=${CHR_ADDRESS} \\
    user=$vpnUsername password=$vpnPassword \\
    verify-server-certificate=yes add-default-route=no

/interface l2tp-client add name=vpn-billinge-l2tp connect-to=${CHR_ADDRESS} \\
    user=$vpnUsername password=$vpnPassword \\
    use-ipsec=yes ipsec-secret=$ipsecPsk add-default-route=no

/ip route add dst-address=${LAN_CIDR} gateway=vpn-billinge-ovpn distance=1 comment="billinge: primer (OpenVPN)"
/ip route add dst-address=${LAN_CIDR} gateway=vpn-billinge-sstp distance=2 comment="billinge: cadangan 1 (SSTP)"
/ip route add dst-address=${LAN_CIDR} gateway=vpn-billinge-l2tp distance=3 comment="billinge: cadangan 2 (L2TP)"

:put "Selesai. Cek: /interface ovpn-client print; /interface sstp-client print; /interface l2tp-client print"
:put "Lanjut: /radius add service=ppp address=${RADIUS_VM_IP} secret=<nas-secret-dari-dashboard> authentication-port=1812 accounting-port=1813"
:put "Lalu: /ppp aaa set use-radius=yes accounting=yes interim-update=5m"`
}

function ScriptBlock({ title, script }: { title: string; script: string }) {
  return (
    <Card
      size="small"
      title={title}
      style={{ marginBottom: 16 }}
      extra={
        <Button
          size="small"
          onClick={() => {
            navigator.clipboard.writeText(script)
            message.success('Script disalin')
          }}
        >
          Copy
        </Button>
      }
    >
      <pre style={{ margin: 0, whiteSpace: 'pre-wrap', fontSize: 12, maxHeight: 300, overflowY: 'auto' }}>
        {script}
      </pre>
    </Card>
  )
}

export function VpnHubPage() {
  const { user } = useAuth()
  const isSuperAdmin = user?.role === 'super_admin'
  const qc = useQueryClient()
  const [form] = Form.useForm<FormValues>()
  const [generated, setGenerated] = useState<FormValues | null>(null)

  const tenantsQuery = useQuery({ queryKey: ['tenants'], queryFn: tenantsApi.list, enabled: isSuperAdmin })
  const existingQuery = useQuery({ queryKey: ['tenant-integrations'], queryFn: tenantIntegrationsApi.list })

  const vpnHubEntries = useMemo(
    () => (existingQuery.data ?? []).filter((i) => i.integration_type === 'vpn_hub'),
    [existingQuery.data],
  )

  const mutation = useMutation({
    mutationFn: (values: FormValues) =>
      tenantIntegrationsApi.create({
        ...(isSuperAdmin ? { tenant: values.tenant } : {}),
        integration_type: 'vpn_hub',
        provider: 'billinge-hub',
        credentials: {
          username: values.username,
          password: values.password,
          remote_address: values.remoteAddress,
          ipsec_psk: values.ipsecPsk,
        },
        is_active: true,
      }),
    onSuccess: (_created, values) => {
      message.success('Kredensial VPN tersimpan')
      qc.invalidateQueries({ queryKey: ['tenant-integrations'] })
      setGenerated(values)
    },
    onError: () => message.error('Gagal menyimpan — cek apakah tenant sudah punya integrasi VPN Hub (satu per tenant)'),
  })

  const columns: TableColumnsType<TenantIntegration> = [
    { title: 'Tenant', dataIndex: 'tenant' },
    { title: 'Provider', dataIndex: 'provider' },
    { title: 'Aktif', dataIndex: 'is_active', render: (v: boolean) => (v ? 'Ya' : 'Tidak') },
  ]

  return (
    <div>
      <Typography.Title level={3}>VPN Hub — Onboarding Tenant</Typography.Title>
      <Typography.Paragraph type="secondary">
        Generate kredensial VPN dial-in buat tenant baru (OpenVPN + SSTP + L2TP sekaligus, failover otomatis),
        lalu salin dua script di bawah ke CHR dan ke Mikrotik tenant.
      </Typography.Paragraph>

      <Card style={{ marginBottom: 24 }}>
        <Form<FormValues>
          form={form}
          layout="vertical"
          onFinish={(values) => mutation.mutate(values)}
          initialValues={{ remoteAddress: '10.201.0.' }}
        >
          {isSuperAdmin && (
            <Form.Item name="tenant" label="Tenant" rules={[{ required: true, message: 'Pilih tenant' }]}>
              <Select
                loading={tenantsQuery.isLoading}
                options={(tenantsQuery.data ?? []).map((t) => ({ label: `${t.name} (${t.slug})`, value: t.id }))}
                onChange={(_, option) => {
                  const opt = option as { label?: string } | undefined
                  const slug = opt?.label?.match(/\(([^)]+)\)/)?.[1]
                  if (slug) form.setFieldValue('tenantSlug', slug)
                }}
              />
            </Form.Item>
          )}
          <Form.Item name="tenantSlug" label="Slug Tenant (buat komentar di CHR)" rules={[{ required: true }]}>
            <Input placeholder="mis. isp-maju" />
          </Form.Item>
          <Form.Item name="username" label="Username VPN" rules={[{ required: true }]}>
            <Input placeholder="mis. isp-maju" />
          </Form.Item>
          <Form.Item label="Password VPN" required>
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name="password" noStyle rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Button icon={<ReloadOutlined />} onClick={() => form.setFieldValue('password', randomSecret(20))}>
                Generate
              </Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item
            name="remoteAddress"
            label="IP Tetap Tenant (dari pool 10.201.0.0/24)"
            rules={[{ required: true, pattern: /^10\.201\.0\.\d{1,3}$/, message: 'Format: 10.201.0.x' }]}
            extra="Pastikan belum dipakai tenant lain (lihat tabel di bawah)."
          >
            <Input placeholder="10.201.0.10" />
          </Form.Item>
          <Form.Item label="IPsec PSK (untuk opsi L2TP)" required>
            <Space.Compact style={{ width: '100%' }}>
              <Form.Item name="ipsecPsk" noStyle rules={[{ required: true }]}>
                <Input.Password />
              </Form.Item>
              <Button icon={<ReloadOutlined />} onClick={() => form.setFieldValue('ipsecPsk', randomSecret(24))}>
                Generate
              </Button>
            </Space.Compact>
          </Form.Item>
          <Form.Item>
            <Button type="primary" htmlType="submit" loading={mutation.isPending}>
              Simpan & Buat Script
            </Button>
          </Form.Item>
        </Form>
      </Card>

      {generated && (
        <>
          <Alert
            type="warning"
            showIcon
            message="Password & PSK di script ini cuma ditampilkan sekali sekarang. Salin dan kirim ke tenant sekarang, halaman ini tidak menyimpan riwayatnya."
            style={{ marginBottom: 16 }}
          />
          <ScriptBlock title="1. Jalankan di CHR (sekali per tenant)" script={buildChrScript(generated)} />
          <ScriptBlock title="2. Kirim ke tenant, jalankan di Mikrotik mereka" script={buildTenantScript(generated)} />
        </>
      )}

      <Typography.Title level={4} style={{ marginTop: 32 }}>
        Tenant yang sudah punya VPN Hub
      </Typography.Title>
      <Table<TenantIntegration>
        rowKey="id"
        size="small"
        loading={existingQuery.isLoading}
        columns={columns}
        dataSource={vpnHubEntries}
        pagination={{ pageSize: 10 }}
      />
    </div>
  )
}
