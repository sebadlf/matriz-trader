import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react';
import { useState } from 'react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { NewOrderModal, type NewOrderModalProps } from './NewOrderModal';

const INSTRUMENTS = [
  { symbol: 'DLR/DIC26', market_id: 'ROFX' },
  { symbol: 'GGAL/DIC26', market_id: 'ROFX' },
];

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

type Handler = (init: RequestInit | undefined) => Promise<Response>;

/** `fetch` falso: instrumentos y alta configurables; registra cada `POST /orders`. */
function stubFetch({
  instruments = async () => jsonResponse(200, INSTRUMENTS),
  create = async () => jsonResponse(201, { cl_ord_id: 'C1', proprietary: 'P1' }),
}: {
  instruments?: Handler;
  create?: Handler;
} = {}) {
  const posts: unknown[] = [];
  const fetchMock = vi.fn((input: string | URL | Request, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith('/instruments')) {
      return instruments(init);
    }
    if (url.endsWith('/orders') && init?.method === 'POST') {
      posts.push(JSON.parse(String(init.body)));
      return create(init);
    }
    return Promise.reject(new Error(`URL inesperada: ${url}`));
  });
  vi.stubGlobal('fetch', fetchMock);
  return { posts, fetchMock };
}

type Props = Partial<NewOrderModalProps>;

function Harness({ onClose, onCreated, ...props }: Props) {
  const [open, setOpen] = useState(props.open ?? true);
  return (
    <>
      <button type="button" data-testid="reopen" onClick={() => setOpen(true)}>
        abrir
      </button>
      <NewOrderModal
        open={open}
        accounts={props.accounts ?? ['REM1', 'REM2']}
        defaultAccount={'defaultAccount' in props ? props.defaultAccount : 'REM1'}
        onClose={() => {
          onClose?.();
          setOpen(false);
        }}
        onCreated={(accountId) => {
          onCreated?.(accountId);
          setOpen(false);
        }}
      />
    </>
  );
}

function renderModal(props: Props = {}) {
  const client = new QueryClient({
    defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
  });
  return render(
    <QueryClientProvider client={client}>
      <Harness {...props} />
    </QueryClientProvider>,
  );
}

const submitButton = () => screen.getByTestId('new-order-submit');
const modal = () => screen.getByTestId('new-order-modal');

function combobox(testId: string): HTMLElement {
  return within(screen.getByTestId(testId)).getByRole('combobox');
}

async function chooseOption(testId: string, search: string, optionLabel: string) {
  const input = combobox(testId);
  fireEvent.mouseDown(input);
  fireEvent.change(input, { target: { value: search } });
  const option = await waitFor(() => {
    const found = document.querySelector<HTMLElement>(
      `.ant-select-item-option[title="${optionLabel}"]`,
    );
    if (!found) throw new Error(`opción ${optionLabel} no encontrada`);
    return found;
  });
  fireEvent.click(option);
}

function typeNumber(testId: string, value: string) {
  const input = screen.getByTestId(testId);
  fireEvent.change(input, { target: { value } });
  fireEvent.blur(input);
}

async function waitInstruments() {
  await waitFor(() => expect(submitButton()).toBeEnabled());
}

/** Completa un alta LIMIT válida en GGAL. */
async function fillValidLimit() {
  await waitInstruments();
  await chooseOption('new-order-instrument', 'GGAL', 'GGAL/DIC26');
  typeNumber('new-order-price', '1234.5');
  typeNumber('new-order-quantity', '3');
}

describe('NewOrderModal', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.useRealTimers();
  });

  it('se abre sin cambiar la ruta y con valores por defecto (EB-18)', async () => {
    stubFetch();
    const before = window.location.pathname;
    renderModal();
    expect(modal()).toBeInTheDocument();
    expect(window.location.pathname).toBe(before);
    expect(within(screen.getByTestId('new-order-account')).getByText('REM1')).toBeInTheDocument();
    expect(screen.getByRole('radio', { name: 'Compra' })).toBeChecked();
    expect(screen.getByRole('radio', { name: 'Limit' })).toBeChecked();
    await waitInstruments();
  });

  it.each([
    ['botón Cancelar', () => fireEvent.click(screen.getByRole('button', { name: 'Cancelar' }))],
    ['cruz', () => fireEvent.click(screen.getByRole('button', { name: /close/i }))],
    [
      'Escape',
      () => fireEvent.keyDown(screen.getByRole('dialog'), { key: 'Escape', code: 'Escape' }),
    ],
  ])('cerrar con %s no emite la orden (EB-19)', async (_, close) => {
    const { posts } = stubFetch();
    const onClose = vi.fn();
    const onCreated = vi.fn();
    renderModal({ onClose, onCreated });
    await fillValidLimit();

    close();

    await waitFor(() => expect(onClose).toHaveBeenCalledTimes(1));
    expect(onCreated).not.toHaveBeenCalled();
    expect(posts).toHaveLength(0);
  });

  it('Lado y Tipo ofrecen exactamente dos opciones cada uno (EB-24, EB-25)', async () => {
    stubFetch();
    renderModal();
    const side = within(screen.getByTestId('new-order-side')).getAllByRole('radio');
    expect(side.map((radio) => radio.getAttribute('value'))).toEqual(['BUY', 'SELL']);
    const type = within(screen.getByTestId('new-order-type')).getAllByRole('radio');
    expect(type.map((radio) => radio.getAttribute('value'))).toEqual(['MARKET', 'LIMIT']);
    await waitInstruments();
  });

  it('el selector de activo no acepta texto libre (EB-22)', async () => {
    const { posts } = stubFetch();
    renderModal();
    await waitInstruments();

    const input = combobox('new-order-instrument');
    fireEvent.mouseDown(input);
    fireEvent.change(input, { target: { value: 'INEXISTENTE' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    fireEvent.blur(input);
    typeNumber('new-order-quantity', '1');
    typeNumber('new-order-price', '10');
    fireEvent.click(submitButton());

    expect(await within(modal()).findByText('Elegí un activo')).toBeInTheDocument();
    expect(posts).toHaveLength(0);
  });

  it('el selector de cuenta no acepta texto libre (EB-20)', async () => {
    const { posts } = stubFetch();
    renderModal({ defaultAccount: undefined });
    await fillValidLimit();

    const input = combobox('new-order-account');
    fireEvent.mouseDown(input);
    fireEvent.change(input, { target: { value: 'OTRA' } });
    fireEvent.keyDown(input, { key: 'Enter', code: 'Enter' });
    fireEvent.blur(input);
    fireEvent.click(submitButton());

    expect(await within(modal()).findByText('Elegí una cuenta')).toBeInTheDocument();
    expect(posts).toHaveLength(0);
  });

  it('sin cuentas configuradas explica cómo cargarlas y bloquea el envío (EB-21)', async () => {
    stubFetch();
    renderModal({ accounts: [], defaultAccount: undefined });
    expect(within(modal()).getByText(/No hay cuentas configuradas/)).toBeInTheDocument();
    expect(within(modal()).getByText(/MATRIZ_ACCOUNTS/)).toBeInTheDocument();
    await waitFor(() => expect(screen.queryByText('Cargando instrumentos…')).toBeNull());
    expect(submitButton()).toBeDisabled();
  });

  it('mientras cargan los instrumentos muestra la carga y bloquea el envío (EB-23)', () => {
    stubFetch({ instruments: () => new Promise<Response>(() => undefined) });
    renderModal();
    expect(screen.getByText('Cargando instrumentos…')).toBeInTheDocument();
    expect(submitButton()).toBeDisabled();
  });

  it('si fallan los instrumentos muestra el error y bloquea el envío (EB-23)', async () => {
    stubFetch({
      instruments: async () => jsonResponse(502, { detail: 'Matriz: timeout' }),
    });
    renderModal();
    expect(await within(modal()).findByText(/Matriz: timeout/)).toBeInTheDocument();
    expect(submitButton()).toBeDisabled();
  });

  it('LIMIT sin precio muestra el error del campo y no llama a la API (EB-26, EB-30)', async () => {
    const { posts } = stubFetch();
    renderModal();
    await waitInstruments();
    await chooseOption('new-order-instrument', 'GGAL', 'GGAL/DIC26');
    typeNumber('new-order-quantity', '3');

    fireEvent.click(submitButton());

    expect(
      await within(modal()).findByText('El precio es obligatorio para órdenes Limit'),
    ).toBeInTheDocument();
    expect(posts).toHaveLength(0);
  });

  it.each(['0', '-5'])('LIMIT con precio %s no llama a la API (EB-26)', async (price) => {
    const { posts } = stubFetch();
    renderModal();
    await fillValidLimit();
    typeNumber('new-order-price', price);

    fireEvent.click(submitButton());

    expect(await within(modal()).findByText('El precio debe ser mayor a cero')).toBeInTheDocument();
    expect(posts).toHaveLength(0);
  });

  it.each([
    ['1.5', 'La cantidad debe ser un entero mayor a cero'],
    ['0', 'La cantidad debe ser un entero mayor a cero'],
    ['-1', 'La cantidad debe ser un entero mayor a cero'],
    ['', 'La cantidad es obligatoria'],
  ])('cantidad "%s" bloquea el envío (EB-28)', async (quantity, message) => {
    const { posts } = stubFetch();
    renderModal();
    await fillValidLimit();
    typeNumber('new-order-quantity', quantity);

    fireEvent.click(submitButton());

    expect(await within(modal()).findByText(message)).toBeInTheDocument();
    expect(posts).toHaveLength(0);
  });

  it('LIMIT envía símbolo, market_id y precio del instrumento elegido (EB-22, EB-29)', async () => {
    const { posts } = stubFetch();
    const onCreated = vi.fn();
    renderModal({ onCreated });
    await fillValidLimit();
    fireEvent.click(screen.getByRole('radio', { name: 'Venta' }));

    fireEvent.click(submitButton());

    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('REM1'));
    expect(posts).toEqual([
      {
        account_id: 'REM1',
        market_id: 'ROFX',
        symbol: 'GGAL/DIC26',
        side: 'SELL',
        order_type: 'LIMIT',
        quantity: 3,
        price: 1234.5,
      },
    ]);
  });

  it('MARKET oculta el precio y no lo envía (EB-27)', async () => {
    const { posts } = stubFetch();
    const onCreated = vi.fn();
    renderModal({ onCreated });
    await fillValidLimit();

    fireEvent.click(screen.getByRole('radio', { name: 'Market' }));
    await waitFor(() => expect(screen.queryByTestId('new-order-price')).toBeNull());
    fireEvent.click(submitButton());

    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
    expect(posts).toHaveLength(1);
    expect(posts[0]).not.toHaveProperty('price');
    expect(posts[0]).toMatchObject({ order_type: 'MARKET', quantity: 3, symbol: 'GGAL/DIC26' });
  });

  it('durante el envío muestra carga y un segundo clic no duplica el POST (EB-31)', async () => {
    let resolveCreate: (response: Response) => void = () => undefined;
    const { posts } = stubFetch({
      create: () =>
        new Promise<Response>((resolve) => {
          resolveCreate = resolve;
        }),
    });
    const onCreated = vi.fn();
    renderModal({ onCreated });
    await fillValidLimit();

    fireEvent.click(submitButton());
    await waitFor(() => expect(submitButton()).toHaveClass('ant-btn-loading'));
    fireEvent.click(submitButton());
    fireEvent.click(submitButton());
    await act(async () => {
      await Promise.resolve();
    });
    expect(posts).toHaveLength(1);

    resolveCreate(jsonResponse(201, { cl_ord_id: 'C1', proprietary: 'P1' }));
    await waitFor(() => expect(onCreated).toHaveBeenCalledTimes(1));
    expect(posts).toHaveLength(1);
  });

  it('si la API falla, el modal sigue abierto con los valores y el error (EB-32)', async () => {
    const { posts } = stubFetch({
      create: async () => jsonResponse(502, { detail: 'Matriz: orden rechazada' }),
    });
    const onCreated = vi.fn();
    const onClose = vi.fn();
    renderModal({ onCreated, onClose });
    await fillValidLimit();

    fireEvent.click(submitButton());

    expect(await screen.findByTestId('new-order-error')).toHaveTextContent(
      'Matriz: orden rechazada',
    );
    expect(posts).toHaveLength(1);
    expect(onCreated).not.toHaveBeenCalled();
    expect(onClose).not.toHaveBeenCalled();
    expect(
      within(screen.getByTestId('new-order-instrument')).getByText('GGAL/DIC26'),
    ).toBeInTheDocument();
    expect(screen.getByTestId('new-order-price')).toHaveValue('1234.5');
    expect(screen.getByTestId('new-order-quantity')).toHaveValue('3');
    expect(submitButton()).toBeEnabled();
  });

  it('con éxito cierra, notifica y la próxima apertura muestra el form reiniciado (EB-33)', async () => {
    stubFetch();
    const onCreated = vi.fn();
    renderModal({ onCreated });
    await fillValidLimit();
    fireEvent.click(screen.getByRole('radio', { name: 'Venta' }));

    fireEvent.click(submitButton());
    await waitFor(() => expect(onCreated).toHaveBeenCalledWith('REM1'));

    fireEvent.click(screen.getByTestId('reopen'));
    await waitInstruments();
    expect(within(screen.getByTestId('new-order-instrument')).queryByText('GGAL/DIC26')).toBeNull();
    expect(screen.getByTestId('new-order-quantity')).toHaveValue('');
    expect(screen.getByTestId('new-order-price')).toHaveValue('');
    expect(screen.getByRole('radio', { name: 'Compra' })).toBeChecked();
    expect(screen.queryByTestId('new-order-error')).toBeNull();
  });
});
