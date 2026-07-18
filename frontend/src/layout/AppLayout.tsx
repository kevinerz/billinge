import { useMemo, useState } from 'react'
import { Layout, Menu, Dropdown, Avatar, Space, Typography, type MenuProps } from 'antd'
import { UserOutlined, LogoutOutlined } from '@ant-design/icons'
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { NAV_ITEMS, filterNavByRole, type NavItem } from './nav'

const { Header, Sider, Content } = Layout

function toMenuItems(items: NavItem[]): MenuProps['items'] {
  return items.map((item) =>
    item.children
      ? { key: item.key, label: item.label, children: toMenuItems(item.children) }
      : { key: item.key, label: <Link to={item.path!}>{item.label}</Link> },
  )
}

function findSelectedKey(items: NavItem[], pathname: string): string | undefined {
  for (const item of items) {
    if (item.path === pathname) return item.key
    if (item.children) {
      const found = findSelectedKey(item.children, pathname)
      if (found) return found
    }
  }
  return undefined
}

export function AppLayout() {
  const { user, logout } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [collapsed, setCollapsed] = useState(false)

  const filteredNav = useMemo(() => (user ? filterNavByRole(NAV_ITEMS, user.role) : []), [user])
  const menuItems = useMemo(() => toMenuItems(filteredNav), [filteredNav])
  const selectedKey = useMemo(() => findSelectedKey(filteredNav, location.pathname), [filteredNav, location.pathname])

  const userMenuItems: MenuProps['items'] = [
    { key: 'logout', label: 'Keluar', icon: <LogoutOutlined /> },
  ]

  const handleUserMenuClick: MenuProps['onClick'] = ({ key }) => {
    if (key === 'logout') {
      logout()
      navigate('/login')
    }
  }

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Sider collapsible collapsed={collapsed} onCollapse={setCollapsed} theme="dark">
        <div style={{ height: 48, margin: 12, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <Typography.Text style={{ color: '#fff', fontWeight: 600 }}>
            {collapsed ? 'ISP' : 'ISP Billing'}
          </Typography.Text>
        </div>
        <Menu theme="dark" mode="inline" selectedKeys={selectedKey ? [selectedKey] : []} items={menuItems} />
      </Sider>
      <Layout>
        <Header style={{ background: '#fff', padding: '0 24px', display: 'flex', justifyContent: 'flex-end' }}>
          <Dropdown menu={{ items: userMenuItems, onClick: handleUserMenuClick }} placement="bottomRight">
            <Space style={{ cursor: 'pointer' }}>
              <Avatar icon={<UserOutlined />} />
              <span>{user?.email}</span>
              <Typography.Text type="secondary">({user?.role})</Typography.Text>
            </Space>
          </Dropdown>
        </Header>
        <Content style={{ margin: 24 }}>
          <Outlet />
        </Content>
      </Layout>
    </Layout>
  )
}
