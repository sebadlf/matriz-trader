import type { RouteObject } from "react-router";

import { ROUTES } from "@/constants/routes";
import { RootLayout } from "@/layouts/RootLayout";
import { NotFoundScreen } from "@/screens/NotFoundScreen";

// Separado de `router.tsx` para que ese archivo solo exporte componentes (fast refresh).
export const routes: RouteObject[] = [
  {
    path: ROUTES.home,
    element: <RootLayout />,
    errorElement: <NotFoundScreen />,
    children: [
      {
        index: true,
        lazy: async () => ({ Component: (await import("@/screens/HomeScreen")).HomeScreen }),
      },
      {
        path: ROUTES.marketData,
        lazy: async () => ({
          Component: (await import("@/screens/MarketDataScreen")).MarketDataScreen,
        }),
      },
      { path: ROUTES.notFound, element: <NotFoundScreen /> },
    ],
  },
];
