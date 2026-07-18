import { Spin } from 'antd'
import { Navigate, Outlet } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { Role } from '../api/types'

export function ProtectedRoute() {
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh' }}>
        <Spin size="large" />
      </div>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace />
  }

  return <Outlet />
}

export function RoleGuard({ allow }: { allow: Role[] }) {
  const { user } = useAuth()

  if (!user || !allow.includes(user.role)) {
    return <Navigate to="/" replace />
  }

  return <Outlet />
}
