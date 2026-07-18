import { useState, type ReactNode } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  Table,
  Button,
  Modal,
  Form,
  Space,
  Popconfirm,
  message,
  Typography,
  Input,
  InputNumber,
  Select,
  Switch,
  type TableColumnsType,
} from 'antd'
import { PlusOutlined } from '@ant-design/icons'

export interface FieldConfig {
  name: string
  label: string
  type?: 'text' | 'number' | 'password' | 'select' | 'textarea' | 'switch'
  options?: { label: string; value: string | number }[]
  required?: boolean
  hideOnEdit?: boolean
  hideOnCreate?: boolean
  extra?: string
}

export interface ResourcePageConfig<T extends object> {
  title: string
  queryKey: string
  fetchList: () => Promise<T[]>
  create?: (values: Record<string, unknown>) => Promise<T>
  update?: (id: number, values: Record<string, unknown>) => Promise<T>
  remove?: (id: number) => Promise<void>
  columns: TableColumnsType<T>
  formFields?: FieldConfig[]
  rowKey?: string
  extraActions?: (record: T) => ReactNode
  extraHeaderActions?: ReactNode
  onCreateSuccess?: (created: T) => void
  transformValues?: (values: Record<string, unknown>) => Record<string, unknown>
}

function renderField(f: FieldConfig) {
  switch (f.type) {
    case 'password':
      return <Input.Password autoComplete="new-password" />
    case 'number':
      return <InputNumber style={{ width: '100%' }} />
    case 'select':
      return <Select options={f.options} allowClear />
    case 'textarea':
      return <Input.TextArea rows={3} />
    case 'switch':
      return <Switch />
    default:
      return <Input />
  }
}

function extractErrorMessage(error: unknown): string {
  const e = error as { response?: { data?: unknown } }
  const data = e?.response?.data
  if (!data) return 'Terjadi kesalahan'
  if (typeof data === 'string') return data
  try {
    return Object.entries(data as Record<string, unknown>)
      .map(([field, msgs]) => `${field}: ${Array.isArray(msgs) ? msgs.join(', ') : String(msgs)}`)
      .join(' | ')
  } catch {
    return 'Terjadi kesalahan'
  }
}

export function ResourcePage<T extends object>(config: ResourcePageConfig<T>) {
  const qc = useQueryClient()
  const rowKey = config.rowKey ?? 'id'
  const { data, isLoading } = useQuery({ queryKey: [config.queryKey], queryFn: config.fetchList })
  const [modalOpen, setModalOpen] = useState(false)
  const [editing, setEditing] = useState<T | null>(null)
  const [form] = Form.useForm()

  const createMutation = useMutation({
    mutationFn: (values: Record<string, unknown>) => config.create!(values),
    onSuccess: (created) => {
      message.success('Berhasil dibuat')
      qc.invalidateQueries({ queryKey: [config.queryKey] })
      setModalOpen(false)
      config.onCreateSuccess?.(created)
    },
    onError: (e) => message.error(extractErrorMessage(e)),
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, values }: { id: number; values: Record<string, unknown> }) => config.update!(id, values),
    onSuccess: () => {
      message.success('Berhasil diupdate')
      qc.invalidateQueries({ queryKey: [config.queryKey] })
      setModalOpen(false)
    },
    onError: (e) => message.error(extractErrorMessage(e)),
  })

  const removeMutation = useMutation({
    mutationFn: (id: number) => config.remove!(id),
    onSuccess: () => {
      message.success('Berhasil dihapus')
      qc.invalidateQueries({ queryKey: [config.queryKey] })
    },
    onError: (e) => message.error(extractErrorMessage(e)),
  })

  const openCreate = () => {
    setEditing(null)
    form.resetFields()
    setModalOpen(true)
  }

  const openEdit = (record: T) => {
    setEditing(record)
    form.setFieldsValue(record)
    setModalOpen(true)
  }

  const handleSubmit = () => {
    form.validateFields().then((rawValues) => {
      let values = rawValues
      if (config.transformValues) {
        try {
          values = config.transformValues(rawValues)
        } catch (e) {
          message.error(e instanceof Error ? e.message : 'Data tidak valid')
          return
        }
      }
      if (editing) {
        updateMutation.mutate({ id: (editing as Record<string, unknown>)[rowKey] as number, values })
      } else {
        createMutation.mutate(values)
      }
    })
  }

  const columns: TableColumnsType<T> = [...config.columns]
  if (config.update || config.remove || config.extraActions) {
    columns.push({
      title: 'Aksi',
      key: '__actions',
      render: (_: unknown, record: T) => (
        <Space>
          {config.update && <a onClick={() => openEdit(record)}>Edit</a>}
          {config.remove && (
            <Popconfirm title="Yakin ingin menghapus?" onConfirm={() => removeMutation.mutate((record as Record<string, unknown>)[rowKey] as number)}>
              <a style={{ color: '#ff4d4f' }}>Hapus</a>
            </Popconfirm>
          )}
          {config.extraActions?.(record)}
        </Space>
      ),
    })
  }

  const visibleFields = (config.formFields ?? []).filter(
    (f) => !(editing && f.hideOnEdit) && !(!editing && f.hideOnCreate),
  )

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <Typography.Title level={3} style={{ margin: 0 }}>
          {config.title}
        </Typography.Title>
        <Space>
          {config.extraHeaderActions}
          {config.create && (
            <Button type="primary" icon={<PlusOutlined />} onClick={openCreate}>
              Tambah
            </Button>
          )}
        </Space>
      </div>
      <Table<T>
        rowKey={rowKey}
        loading={isLoading}
        columns={columns}
        dataSource={data}
        pagination={{ pageSize: 20, showSizeChanger: true }}
        scroll={{ x: 'max-content' }}
      />
      {config.formFields && (
        <Modal
          title={editing ? `Edit ${config.title}` : `Tambah ${config.title}`}
          open={modalOpen}
          onCancel={() => setModalOpen(false)}
          onOk={handleSubmit}
          confirmLoading={createMutation.isPending || updateMutation.isPending}
          destroyOnHidden
        >
          <Form form={form} layout="vertical">
            {visibleFields.map((f) => (
              <Form.Item
                key={f.name}
                name={f.name}
                label={f.label}
                extra={f.extra}
                valuePropName={f.type === 'switch' ? 'checked' : 'value'}
                rules={f.required ? [{ required: true, message: `${f.label} wajib diisi` }] : []}
              >
                {renderField(f)}
              </Form.Item>
            ))}
          </Form>
        </Modal>
      )}
    </div>
  )
}
