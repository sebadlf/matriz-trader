import { fireEvent, render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';
import type { OrderOut } from '../../api/generated/model';
import { OrdersTable } from './OrdersTable';

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
    cum_qty: 2,
    leaves_qty: 8,
    status: 'NEW',
    transact_time: '20261112-10:15:00.000-0300',
    text: null,
    ...overrides,
  };
}

function renderTable(
  orders: OrderOut[],
  {
    pendingCancel = new Set<string>(),
    cancelingKey = null,
    onCancel = vi.fn(),
  }: {
    pendingCancel?: ReadonlySet<string>;
    cancelingKey?: string | null;
    onCancel?: (o: OrderOut) => void;
  } = {},
) {
  render(
    <OrdersTable
      orders={orders}
      pendingCancel={pendingCancel}
      cancelingKey={cancelingKey}
      onCancel={onCancel}
    />,
  );
  return { onCancel };
}

function dataRow(index = 0): HTMLElement {
  const rows = screen.getByTestId('orders-table').querySelectorAll('tbody tr[data-row-key]');
  return rows[index] as HTMLElement;
}

describe('OrdersTable', () => {
  it('muestra las columnas en orden y los valores de la fila (EB-2)', () => {
    renderTable([order()]);

    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent);
    expect(headers).toEqual([
      'Cuenta',
      'Símbolo',
      'Lado',
      'Tipo',
      'Cantidad',
      'Precio',
      'Ejecutada',
      'Remanente',
      'Estado',
      'Hora',
      'Acciones',
    ]);

    const cells = within(dataRow())
      .getAllByRole('cell')
      .map((c) => c.textContent);
    expect(cells.slice(0, 10)).toEqual([
      'REM1',
      'DLR/DIC26',
      'Compra',
      'LIMIT',
      '10',
      '1.234,5',
      '2',
      '8',
      'NEW',
      '20261112-10:15:00.000-0300',
    ]);
  });

  it('muestra «—» en campos vacíos (EB-3)', () => {
    renderTable([
      order({ ord_type: 'MARKET', price: null, cum_qty: null, transact_time: null, status: null }),
    ]);

    const cells = within(dataRow())
      .getAllByRole('cell')
      .map((c) => c.textContent);
    expect(cells[5]).toBe('—');
    expect(cells[6]).toBe('—');
    expect(cells[8]).toBe('—');
    expect(cells[9]).toBe('—');
    expect(dataRow().textContent).not.toMatch(/null|undefined|NaN/);
  });

  it('muestra «No hay órdenes» con lista vacía', () => {
    renderTable([]);

    expect(screen.getByTestId('orders-empty')).toHaveTextContent('No hay órdenes');
  });

  it.each(['NEW', 'PENDING_NEW', 'PENDING_REPLACE', 'PENDING_APPROVAL', 'PARTIALLY_FILLED', null])(
    'ofrece «Cancelar» habilitado en estado no final %s (EB-11)',
    (status) => {
      renderTable([order({ status })]);

      expect(screen.getByTestId('order-cancel-C1')).toBeEnabled();
    },
  );

  it.each(['REJECTED', 'CANCELLED', 'REPLACED', 'FILLED'])(
    'no ofrece «Cancelar» en estado final %s (EB-12)',
    (status) => {
      renderTable([order({ status })]);

      expect(screen.queryByTestId('order-cancel-C1')).not.toBeInTheDocument();
    },
  );

  it('deshabilita «Cancelar» en PENDING_CANCEL (EB-12)', () => {
    renderTable([order({ status: 'PENDING_CANCEL' })]);

    expect(screen.getByTestId('order-cancel-C1')).toBeDisabled();
  });

  it('aplica el override PENDING_CANCEL de una cancelación aceptada', () => {
    renderTable([order({ status: 'NEW' })], { pendingCancel: new Set(['C1|PBCP']) });

    expect(dataRow()).toHaveTextContent('PENDING_CANCEL');
    expect(screen.getByTestId('order-cancel-C1')).toBeDisabled();
  });

  it('no ofrece «Cancelar» si falta proprietary', () => {
    renderTable([order({ proprietary: null })]);

    expect(screen.queryByTestId('order-cancel-C1')).not.toBeInTheDocument();
  });

  it('deshabilita la fila con cancelación en curso', () => {
    renderTable([order()], { cancelingKey: 'C1|PBCP' });

    expect(screen.getByTestId('order-cancel-C1')).toBeDisabled();
  });

  it('pide confirmación y descartar no dispara onCancel (EB-13, EB-17)', async () => {
    const { onCancel } = renderTable([order()]);

    fireEvent.click(screen.getByTestId('order-cancel-C1'));

    expect(await screen.findByText('¿Cancelar la orden de DLR/DIC26?')).toBeInTheDocument();
    expect(onCancel).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole('button', { name: 'No' }));

    expect(onCancel).not.toHaveBeenCalled();
  });

  it('confirmar invoca onCancel con la orden de la fila (EB-13)', async () => {
    const target = order();
    const { onCancel } = renderTable([target]);

    fireEvent.click(screen.getByTestId('order-cancel-C1'));
    fireEvent.click(await screen.findByRole('button', { name: 'Sí, cancelar' }));

    expect(onCancel).toHaveBeenCalledTimes(1);
    expect(onCancel).toHaveBeenCalledWith(target);
  });
});
