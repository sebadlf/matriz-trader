import { Button, Empty, Popconfirm, Table, Tag } from 'antd';
import type { TableColumnsType } from 'antd';
import type { OrderOut } from '../../api/generated/model';
import { formatNumber, formatText } from './format';
import { effectiveStatus, isCancelable } from './orderStatus';

export type OrdersTableProps = {
  orders: OrderOut[];
  /** Claves `${cl_ord_id}|${proprietary}` con cancelación aceptada (override `PENDING_CANCEL`). */
  pendingCancel: ReadonlySet<string>;
  /** Fila con cancelación en curso. */
  cancelingKey: string | null;
  /** Se invoca solo tras confirmar el `Popconfirm` (EB-13, EB-17). */
  onCancel: (order: OrderOut) => void;
};

/** Clave estable de una orden, o `null` si falta `cl_ord_id` o `proprietary` (no cancelable). */
function orderKey(order: OrderOut): string | null {
  return order.cl_ord_id && order.proprietary ? `${order.cl_ord_id}|${order.proprietary}` : null;
}

const SIDE_LABELS: Record<string, string> = { BUY: 'Compra', SELL: 'Venta' };

function formatSide(side: string | null): string {
  return side != null && side in SIDE_LABELS ? SIDE_LABELS[side] : formatText(side);
}

const KNOWN_STATUS_COLORS: Record<string, string> = {
  FILLED: 'green',
  REJECTED: 'red',
  CANCELLED: 'default',
  REPLACED: 'default',
  NEW: 'blue',
  PENDING_NEW: 'blue',
  PENDING_REPLACE: 'blue',
  PENDING_CANCEL: 'blue',
  PENDING_APPROVAL: 'blue',
  PARTIALLY_FILLED: 'blue',
};

function StatusTag({ status }: { status: string | null | undefined }) {
  if (status == null || status === '') {
    return <>{formatText(status)}</>;
  }
  // Azul no final, verde FILLED, rojo REJECTED, gris CANCELLED/REPLACED; sin color si desconocido.
  const color: string | undefined = KNOWN_STATUS_COLORS[status];
  return <Tag color={color}>{status}</Tag>;
}

export function OrdersTable({ orders, pendingCancel, cancelingKey, onCancel }: OrdersTableProps) {
  const statusOf = (order: OrderOut) => {
    const key = orderKey(order);
    return effectiveStatus(order.status, key !== null && pendingCancel.has(key));
  };

  const columns: TableColumnsType<OrderOut> = [
    { title: 'Cuenta', key: 'account', render: (_, o) => formatText(o.account_id) },
    { title: 'Símbolo', key: 'symbol', render: (_, o) => formatText(o.symbol) },
    { title: 'Lado', key: 'side', render: (_, o) => formatSide(o.side) },
    { title: 'Tipo', key: 'type', render: (_, o) => formatText(o.ord_type) },
    { title: 'Cantidad', key: 'qty', align: 'right', render: (_, o) => formatNumber(o.order_qty) },
    { title: 'Precio', key: 'price', align: 'right', render: (_, o) => formatNumber(o.price) },
    { title: 'Ejecutada', key: 'cum', align: 'right', render: (_, o) => formatNumber(o.cum_qty) },
    {
      title: 'Remanente',
      key: 'leaves',
      align: 'right',
      render: (_, o) => formatNumber(o.leaves_qty),
    },
    { title: 'Estado', key: 'status', render: (_, o) => <StatusTag status={statusOf(o)} /> },
    { title: 'Hora', key: 'time', render: (_, o) => formatText(o.transact_time) },
    {
      title: 'Acciones',
      key: 'actions',
      render: (_, o) => {
        const key = orderKey(o);
        const status = statusOf(o);
        if (key === null || (!isCancelable(status) && status !== 'PENDING_CANCEL')) {
          return null;
        }
        const canceling = cancelingKey === key;
        const disabled = status === 'PENDING_CANCEL' || canceling;
        return (
          <Popconfirm
            title={`¿Cancelar la orden de ${formatText(o.symbol)}?`}
            okText="Sí, cancelar"
            cancelText="No"
            disabled={disabled}
            onConfirm={() => onCancel(o)}
          >
            <Button
              danger
              size="small"
              data-testid={`order-cancel-${o.cl_ord_id}`}
              disabled={disabled}
              loading={canceling}
            >
              Cancelar
            </Button>
          </Popconfirm>
        );
      },
    },
  ];

  return (
    <Table<OrderOut>
      data-testid="orders-table"
      size="small"
      columns={columns}
      dataSource={orders}
      rowKey={(o) => orderKey(o) ?? `row-${orders.indexOf(o)}`}
      pagination={false}
      locale={{ emptyText: <Empty data-testid="orders-empty" description="No hay órdenes" /> }}
    />
  );
}
