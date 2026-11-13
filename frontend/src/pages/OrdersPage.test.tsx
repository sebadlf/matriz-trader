import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { createMemoryRouter, RouterProvider } from 'react-router';
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { OrderOut } from '../api/generated/model';
import { routes } from '../routes';
import { ORDERS_REFRESH_MS } from './OrdersPage';

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

function order(overrides: Partial<OrderOut> = {}): OrderOut {
  return {
    account_id: 'REM1',
    cl_ord_id: 'C1',
    proprietary: 'PBCP',
    symbol: 'DLR/DIC26',
    market_id: 'ROFX',
    side: 'BUY',
    ord_type: 'LIMIT',
    order_qty: 10,
    price: 1234.5,
    cum_qty: 0,
    leaves_qty: 10,
    status: 'NEW',
    transact_time: '20261112-10:15:00.000-0300',
    text: null,
    ...overrides,
  };
}

type Handler = (call: number, init: RequestInit | undefined) => Promise<Response>;

/** `fetch` falso por endpoint; cada handler recibe el número de llamada (desde 1) a ese endpoint. */
function stubFetch({
  accounts = async () => jsonResponse(200, { accounts: ['REM1'] }),
  orders = async () => jsonResponse(200, []),
  cancel = async () => jsonResponse(200, { cl_ord_id: 'C1', proprietary: 'PBCP' }),
  create = async () => jsonResponse(201, { cl_ord_id: 'C9', proprietary: 'PBCP' }),
  instruments = async () => jsonResponse(200, [{ symbol: 'GGAL/DIC26', market_id: 'ROFX' }]),
}: Partial<Record<'accounts' | 'orders' | 'cancel' | 'create' | 'instruments', Handler>> = {}) {
  const counts = { accounts: 0, orders: 0, cancel: 0, create: 0, instruments: 0 };
  const bodies = { cancel: [] as unknown[], create: [] as unknown[] };
  const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/accounts')) {
      counts.accounts += 1;
      return accounts(counts.accounts, init);
    }
    if (url.includes('/orders?')) {
      counts.orders += 1;
      return orders(counts.orders, init);
    }
    if (url.endsWith('/orders/cancel') && init?.method === 'POST') {
      counts.cancel += 1;
      bodies.cancel.push(JSON.parse(String(init.body)));
      return cancel(counts.cancel, init);
    }
    if (url.endsWith('/orders') && init?.method === 'POST') {
      counts.create += 1;
      bodies.create.push(JSON.parse(String(init.body)));
      return create(counts.create, init);
    }
    if (url.endsWith('/instruments')) {
      counts.instruments += 1;
      return instruments(counts.instruments, init);
    }
    return Promise.reject(new Error(`URL inesperada: ${url}`));
  });
  vi.stubGlobal('fetch', fetchMock);
  return { counts, bodies };
}

function renderOrders() {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  const router = createMemoryRouter(routes, { initialEntries: ['/orders'] });
  render(
    <QueryClientProvider client={client}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
  return { router };
}

async function advance(ms: number) {
  await act(() => vi.advanceTimersByTimeAsync(ms));
}

function statusCell(): HTMLElement {
  const row = screen
    .getByTestId('orders-table')
    .querySelector<HTMLElement>('tbody tr[data-row-key]');
  if (!row) throw new Error('sin filas');
  return within(row).getAllByRole('cell')[8];
}

async function confirmCancel(answer: 'Sí, cancelar' | 'No') {
  fireEvent.click(await screen.findByTestId('order-cancel-C1'));
  fireEvent.click(await screen.findByRole('button', { name: answer }));
}

describe('OrdersPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('conserva el título y muestra la carga mientras se pide el listado (UB-1, EB-1)', async () => {
    stubFetch({ orders: () => new Promise<Response>(() => undefined) });
    renderOrders();

    expect(screen.getByTestId('page-ordenes')).toHaveTextContent('Órdenes');
    expect(await screen.findByTestId('orders-loading')).toBeInTheDocument();
    await waitFor(() => expect(screen.getByTestId('orders-refresh')).toBeEnabled());
  });

  it('con listado vacío muestra «No hay órdenes» y «Nueva orden» disponible (EB-4)', async () => {
    stubFetch();
    renderOrders();

    expect(await screen.findByTestId('orders-empty')).toHaveTextContent('No hay órdenes');
    expect(screen.getByTestId('orders-new')).toBeEnabled();
  });

  it('sin cuentas configuradas lo explica y no pide el listado (EB-21)', async () => {
    const { counts } = stubFetch({ accounts: async () => jsonResponse(200, { accounts: [] }) });
    renderOrders();

    expect(await screen.findByTestId('orders-no-accounts')).toHaveTextContent('MATRIZ_ACCOUNTS');
    expect(counts.orders).toBe(0);
    expect(screen.getByTestId('orders-refresh')).toBeDisabled();
    expect(screen.getByTestId('orders-new')).toBeEnabled();
  });

  it('si falla el listado muestra el detalle y «Reintentar» vuelve a pedirlo (EB-5)', async () => {
    const { counts } = stubFetch({
      orders: async (call) =>
        call === 1 ? jsonResponse(502, { detail: 'Matriz: caído' }) : jsonResponse(200, []),
    });
    renderOrders();

    const error = await screen.findByTestId('orders-error');
    expect(error).toHaveTextContent('Matriz: caído');
    expect(screen.queryByTestId('orders-table')).not.toBeInTheDocument();
    expect(screen.getByTestId('orders-new')).toBeEnabled();

    fireEvent.click(within(error).getByRole('button', { name: 'Reintentar' }));

    expect(await screen.findByTestId('orders-empty')).toBeInTheDocument();
    expect(counts.orders).toBe(2);
  });

  it('el polling arranca con órdenes no finales y conserva la tabla si un refresco falla (EB-7, EB-10)', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { counts } = stubFetch({
      orders: async (call) =>
        call === 1 ? jsonResponse(200, [order()]) : jsonResponse(502, { detail: 'Matriz: caído' }),
    });
    renderOrders();
    await screen.findByTestId('orders-table');
    expect(counts.orders).toBe(1);

    await advance(ORDERS_REFRESH_MS);

    expect(counts.orders).toBe(2);
    expect(await screen.findByTestId('orders-error')).toHaveTextContent('Matriz: caído');
    expect(screen.getByTestId('orders-table')).toBeInTheDocument();
    expect(statusCell()).toHaveTextContent('NEW');
  });

  it.each([
    [
      'todas finales',
      [order({ status: 'FILLED' }), order({ cl_ord_id: 'C2', status: 'CANCELLED' })],
    ],
    ['vacío', []],
  ])('el polling se detiene con listado %s (EB-8)', async (_, list) => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { counts } = stubFetch({ orders: async () => jsonResponse(200, list) });
    renderOrders();
    await screen.findByTestId('orders-table');

    await advance(ORDERS_REFRESH_MS * 3);

    expect(counts.orders).toBe(1);
  });

  it('«Actualizar» vuelve a pedir el listado y reanuda el polling si aparece una no final (EB-9)', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { counts } = stubFetch({
      orders: async (call) => jsonResponse(200, [order({ status: call === 1 ? 'FILLED' : 'NEW' })]),
    });
    renderOrders();
    await screen.findByTestId('orders-table');
    await advance(ORDERS_REFRESH_MS * 2);
    expect(counts.orders).toBe(1);

    fireEvent.click(screen.getByTestId('orders-refresh'));
    await waitFor(() => expect(statusCell()).toHaveTextContent('NEW'));
    expect(counts.orders).toBe(2);

    await advance(ORDERS_REFRESH_MS);

    expect(counts.orders).toBe(3);
  });

  it('cancelar con éxito envía la fila, muestra PENDING_CANCEL y mantiene el polling (EB-14, EB-15)', async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    const { counts, bodies } = stubFetch({
      orders: async () => jsonResponse(200, [order()]),
    });
    renderOrders();
    await screen.findByTestId('orders-table');

    await confirmCancel('Sí, cancelar');

    await waitFor(() => expect(statusCell()).toHaveTextContent('PENDING_CANCEL'));
    expect(bodies.cancel).toEqual([{ cl_ord_id: 'C1', proprietary: 'PBCP' }]);
    expect(screen.getByTestId('order-cancel-C1')).toBeDisabled();
    await waitFor(() => expect(counts.orders).toBe(2)); // listado invalidado tras la cancelación

    await advance(ORDERS_REFRESH_MS);

    expect(counts.orders).toBe(3);
    expect(statusCell()).toHaveTextContent('PENDING_CANCEL');
  });

  it('cuando la API informa un estado final se deja de mostrar PENDING_CANCEL (EB-15)', async () => {
    stubFetch({
      orders: async (call) =>
        jsonResponse(200, [order({ status: call === 1 ? 'NEW' : 'CANCELLED' })]),
    });
    renderOrders();
    await screen.findByTestId('orders-table');

    await confirmCancel('Sí, cancelar');

    await waitFor(() => expect(statusCell()).toHaveTextContent('CANCELLED'));
    expect(screen.queryByTestId('order-cancel-C1')).not.toBeInTheDocument();
  });

  it('si la cancelación falla muestra el error y la fila conserva su estado (EB-16)', async () => {
    const { counts } = stubFetch({
      orders: async () => jsonResponse(200, [order()]),
      cancel: async () => jsonResponse(502, { detail: 'Matriz: orden inexistente' }),
    });
    renderOrders();
    await screen.findByTestId('orders-table');

    await confirmCancel('Sí, cancelar');

    expect(await screen.findByTestId('orders-action-error')).toHaveTextContent(
      'Matriz: orden inexistente',
    );
    expect(statusCell()).toHaveTextContent('NEW');
    expect(screen.getByTestId('order-cancel-C1')).toBeEnabled();
    expect(counts.cancel).toBe(1);
  });

  it('descartar la confirmación no llama a la API (EB-17)', async () => {
    const { counts } = stubFetch({ orders: async () => jsonResponse(200, [order()]) });
    renderOrders();
    await screen.findByTestId('orders-table');

    await confirmCancel('No');

    expect(counts.cancel).toBe(0);
    expect(statusCell()).toHaveTextContent('NEW');
  });

  it('un alta exitosa cierra el modal sin cambiar la ruta y vuelve a pedir el listado (EB-33)', async () => {
    const { counts, bodies } = stubFetch({
      orders: async (call) =>
        jsonResponse(200, call === 1 ? [] : [order({ cl_ord_id: 'C9', symbol: 'GGAL/DIC26' })]),
    });
    const { router } = renderOrders();
    await screen.findByTestId('orders-empty');

    fireEvent.click(screen.getByTestId('orders-new'));
    const submit = screen.getByTestId('new-order-submit');
    await waitFor(() => expect(submit).toBeEnabled());

    const instrument = within(screen.getByTestId('new-order-instrument')).getByRole('combobox');
    fireEvent.mouseDown(instrument);
    fireEvent.change(instrument, { target: { value: 'GGAL' } });
    const option = await waitFor(() => {
      const found = document.querySelector<HTMLElement>(
        '.ant-select-item-option[title="GGAL/DIC26"]',
      );
      if (!found) throw new Error('opción no encontrada');
      return found;
    });
    fireEvent.click(option);
    for (const [testId, value] of [
      ['new-order-price', '100'],
      ['new-order-quantity', '3'],
    ] as const) {
      fireEvent.change(screen.getByTestId(testId), { target: { value } });
      fireEvent.blur(screen.getByTestId(testId));
    }
    fireEvent.click(submit);

    await waitFor(() => expect(counts.create).toBe(1));
    expect(bodies.create).toEqual([
      {
        account_id: 'REM1',
        market_id: 'ROFX',
        symbol: 'GGAL/DIC26',
        side: 'BUY',
        order_type: 'LIMIT',
        quantity: 3,
        price: 100,
      },
    ]);
    await waitFor(() => expect(counts.orders).toBe(2));
    await waitFor(() => expect(statusCell()).toHaveTextContent('NEW'));
    // jsdom no completa la animación de salida de antd: el cierre se ve en la clase `ant-zoom-leave`.
    await waitFor(() =>
      expect(screen.getByTestId('new-order-modal').closest('.ant-modal')).toHaveClass(
        'ant-zoom-leave',
      ),
    );
    expect(screen.getByTestId('new-order-quantity')).toHaveValue('');
    expect(router.state.location.pathname).toBe('/orders');
  });
});
