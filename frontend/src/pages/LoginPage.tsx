import { useState } from 'react'
import { Button, Card, Form, Input, Typography, message } from 'antd'
import { UserOutlined, LockOutlined } from '@ant-design/icons'
import { Navigate, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

interface LoginFormValues {
  email: string
  password: string
}

export function LoginPage() {
  const { user, loading, login } = useAuth()
  const navigate = useNavigate()
  const [submitting, setSubmitting] = useState(false)

  if (!loading && user) {
    return <Navigate to="/" replace />
  }

  const onFinish = async (values: LoginFormValues) => {
    setSubmitting(true)
    try {
      await login(values.email, values.password)
      navigate('/')
    } catch {
      message.error('Email atau password salah')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', background: '#f0f2f5' }}>
      <Card style={{ width: 380 }}>
        <Typography.Title level={3} style={{ textAlign: 'center', marginBottom: 24 }}>
          ISP Billing
        </Typography.Title>
        <Form layout="vertical" onFinish={onFinish} disabled={submitting}>
          <Form.Item name="email" label="Email" rules={[{ required: true, message: 'Email wajib diisi' }]}>
            <Input prefix={<UserOutlined />} autoFocus autoComplete="username" />
          </Form.Item>
          <Form.Item name="password" label="Password" rules={[{ required: true, message: 'Password wajib diisi' }]}>
            <Input.Password prefix={<LockOutlined />} autoComplete="current-password" />
          </Form.Item>
          <Form.Item style={{ marginBottom: 0 }}>
            <Button type="primary" htmlType="submit" block loading={submitting}>
              Masuk
            </Button>
          </Form.Item>
        </Form>
      </Card>
    </div>
  )
}
