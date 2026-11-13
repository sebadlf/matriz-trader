import { Navigate, type RouteObject } from 'react-router';
import { AppLayout } from './layout/AppLayout';
import { HealthPage } from './pages/HealthPage';
import { OrdersPage } from './pages/OrdersPage';
import { StrategiesPage } from './pages/StrategiesPage';

export const DEFAULT_PATH = '/orders';

export const routes: RouteObject[] = [
  {
    element: <AppLayout />,
    children: [
      { index: true, element: <Navigate to={DEFAULT_PATH} replace /> },
      { path: 'orders', element: <OrdersPage /> },
      { path: 'strategies', element: <StrategiesPage /> },
      { path: 'health', element: <HealthPage /> },
      { path: '*', element: <Navigate to={DEFAULT_PATH} replace /> },
    ],
  },
];
