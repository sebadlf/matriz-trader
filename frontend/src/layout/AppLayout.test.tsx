import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { afterEach, beforeEach, describe, expect, it, type Mock, vi } from 'vitest';
import { routes } from '../routes';

const MENU_TEST_IDS = ['menu-orders', 'menu-strategies', 'menu-health'] as const;
type MenuTestId = (typeof MENU_TEST_IDS)[number];

function renderAt(path: string) {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  const router = createMemoryRouter(routes, { initialEntries: [path] });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router };
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function isSelected(testId: MenuTestId): boolean {
  const item = screen.getByTestId(testId).closest('li');
  return item?.classList.contains('ant-menu-item-selected') ?? false;
}

function expectOnlySelected(testId: MenuTestId) {
  for (const id of MENU_TEST_IDS) {
    expect(isSelected(id)).toBe(id === testId);
  }
}

describe('AppLayout', () => {
  let fetchMock: Mock<typeof fetch>;

  beforeEach(() => {
    fetchMock = vi.fn<typeof fetch>(async () =>
      jsonResponse(200, { status: 'ok', database: 'ok' }),
    );
    vi.stubGlobal('fetch', fetchMock);
  });

  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('muestra el logo y el menú con los tres ítems en orden', async () => {
    renderAt('/orders');

    expect(await screen.findByTestId('app-logo')).toHaveTextContent('Matriz Trader');
    const menu = screen.getByTestId('app-menu');
    const labels = within(menu)
      .getAllByRole('link')
      .map((link) => link.textContent);
    expect(labels).toEqual(['Órdenes', 'Estrategias', 'Estado']);
  });

  it('navega a Estrategias desde el menú manteniendo el layout montado', async () => {
    const { router } = renderAt('/orders');
    const logo = await screen.findByTestId('app-logo');

    fireEvent.click(screen.getByTestId('menu-strategies'));

    expect(await screen.findByTestId('page-estrategias')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/strategies');
    expectOnlySelected('menu-strategies');
    expect(screen.getByTestId('app-logo')).toBe(logo);
  });

  it('navega a Órdenes desde el menú', async () => {
    const { router } = renderAt('/strategies');
    await screen.findByTestId('page-estrategias');

    fireEvent.click(screen.getByTestId('menu-orders'));

    expect(await screen.findByTestId('page-ordenes')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/orders');
    expectOnlySelected('menu-orders');
  });

  it('el logo navega a /orders', async () => {
    const { router } = renderAt('/strategies');

    fireEvent.click(await screen.findByTestId('app-logo'));

    expect(await screen.findByTestId('page-ordenes')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/orders');
  });

  it.each(['/', '/no-existe'])('redirige %s a /orders', async (path) => {
    const { router } = renderAt(path);

    expect(await screen.findByTestId('page-ordenes')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/orders');
  });

  it('/orders muestra su título', async () => {
    renderAt('/orders');

    expect(await screen.findByTestId('page-ordenes')).toHaveTextContent('Órdenes');
  });

  it('/strategies muestra su título sin llamar al backend', async () => {
    renderAt('/strategies');

    expect(await screen.findByTestId('page-estrategias')).toHaveTextContent('Estrategias');
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it('/health renderiza HealthPage dentro del layout con solo «Estado» seleccionado', async () => {
    renderAt('/health');

    expect(await screen.findByTestId('health-status')).toHaveTextContent('ok');
    expect(screen.getByTestId('app-menu')).toBeInTheDocument();
    expectOnlySelected('menu-health');
  });

  it('atrás en el historial vuelve a la sección anterior y actualiza el menú', async () => {
    const { router } = renderAt('/orders');
    await screen.findByTestId('page-ordenes');

    await act(() => router.navigate('/strategies'));
    expect(await screen.findByTestId('page-estrategias')).toBeInTheDocument();
    expectOnlySelected('menu-strategies');

    await act(() => router.navigate(-1));
    expect(await screen.findByTestId('page-ordenes')).toBeInTheDocument();
    expect(router.state.location.pathname).toBe('/orders');
    expectOnlySelected('menu-orders');
  });
});
