import dayjs from 'dayjs'
import { Tag } from 'antd'

export function formatDateTime(value: string | null | undefined): string {
  if (!value) return '-'
  return dayjs(value).format('DD MMM YYYY HH:mm')
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return '-'
  return dayjs(value).format('DD MMM YYYY')
}

const STATUS_COLORS: Record<string, string> = {
  active: 'green',
  trial: 'blue',
  trialing: 'blue',
  suspended: 'red',
  terminated: 'red',
  canceled: 'default',
  past_due: 'orange',
  draft: 'default',
  pending: 'orange',
  paid: 'green',
  overdue: 'red',
  void: 'default',
  settlement: 'green',
  expired: 'default',
  failed: 'red',
  refunded: 'purple',
  chargeback: 'magenta',
  unused: 'blue',
  completed: 'green',
}

export function StatusTag({ status }: { status: string }) {
  return <Tag color={STATUS_COLORS[status] ?? 'default'}>{status}</Tag>
}
