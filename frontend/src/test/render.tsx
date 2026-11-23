import { render, type RenderResult } from "@testing-library/react";
import userEvent, { type UserEvent } from "@testing-library/user-event";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider, type RouteObject } from "react-router";

import { createQueryClient } from "@/api/queryClient";
import { AppProviders } from "@/app/providers";

type RenderOptions = {
  /** Ruta inicial del router en memoria. */
  route?: string;
  /** Árbol de rutas a montar; si se omite, `ui` se monta en `route`. */
  routes?: RouteObject[];
};

export function renderWithProviders(
  ui: ReactElement,
  { route = "/", routes }: RenderOptions = {},
): RenderResult & { user: UserEvent } {
  const queryClient = createQueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routes ?? [{ path: "*", element: ui }], {
    initialEntries: [route],
  });

  return {
    user: userEvent.setup(),
    ...render(
      <AppProviders queryClient={queryClient}>
        <RouterProvider router={router} />
      </AppProviders>,
    ),
  };
}
