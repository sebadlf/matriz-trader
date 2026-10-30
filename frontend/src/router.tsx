import { createBrowserRouter } from 'react-router';
import { HealthPage } from './pages/HealthPage';

export const router = createBrowserRouter([{ path: '/', element: <HealthPage /> }]);
