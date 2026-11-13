import { Layout, Menu, type MenuProps } from 'antd';
import type { CSSProperties } from 'react';
import { Link, Outlet, useLocation } from 'react-router';

type NavItem = { path: '/orders' | '/strategies' | '/health'; label: string; testId: string };

const NAV_ITEMS: readonly NavItem[] = [
  { path: '/orders', label: 'Órdenes', testId: 'menu-orders' },
  { path: '/strategies', label: 'Estrategias', testId: 'menu-strategies' },
  { path: '/health', label: 'Estado', testId: 'menu-health' },
];

const MENU_ITEMS: MenuProps['items'] = NAV_ITEMS.map((item) => ({
  key: item.path,
  label: (
    <Link to={item.path} data-testid={item.testId}>
      {item.label}
    </Link>
  ),
}));

const LOGO_STYLE: CSSProperties = {
  display: 'block',
  padding: '16px 24px',
  color: '#fff',
  fontSize: 18,
  fontWeight: 600,
  lineHeight: '32px',
  whiteSpace: 'nowrap',
};

function selectedKeysFor(pathname: string): string[] {
  const normalized = pathname.length > 1 ? pathname.replace(/\/+$/, '') : pathname;
  return NAV_ITEMS.some((item) => item.path === normalized) ? [normalized] : [];
}

export function AppLayout() {
  const { pathname } = useLocation();
  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Layout.Sider width={220} theme="dark">
        <Link to="/orders" data-testid="app-logo" style={LOGO_STYLE}>
          Matriz Trader
        </Link>
        <Menu
          data-testid="app-menu"
          mode="inline"
          theme="dark"
          items={MENU_ITEMS}
          selectedKeys={selectedKeysFor(pathname)}
        />
      </Layout.Sider>
      <Layout.Content style={{ padding: 24 }}>
        <Outlet />
      </Layout.Content>
    </Layout>
  );
}
