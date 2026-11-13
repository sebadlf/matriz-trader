import { useQueryClient } from '@tanstack/react-query';
import { Alert, Button, Flex, Select, Space, Spin, Typography } from 'antd';
import { useEffect, useState } from 'react';
import {
  getListOrdersQueryKey,
  type listAccountsResponse,
  type listOrdersResponse,
  useCancelOrder,
  useListAccounts,
  useListOrders,
} from '../api/generated/matriz';
import type { OrderOut } from '../api/generated/model';
import { describeApiError } from './orders/format';
import { NewOrderModal, NO_ACCOUNTS_MESSAGE } from './orders/NewOrderModal';
import { OrdersTable } from './orders/OrdersTable';
import { effectiveStatus, hasNonFinal, isFinalStatus } from './orders/orderStatus';

/** Intervalo del refresco periódico mientras haya órdenes no finales (PA-4: fijo en código). */
export const ORDERS_REFRESH_MS = 5000;

const EMPTY_ORDERS: OrderOut[] = [];

/** Misma clave que usa `OrdersTable`; `null` si la orden no es cancelable por falta de ids. */
function orderKey(order: OrderOut): string | null {
  return order.cl_ord_id && order.proprietary ? `${order.cl_ord_id}|${order.proprietary}` : null;
}

function ordersOf(response: listOrdersResponse | undefined): OrderOut[] {
  return response?.status === 200 ? response.data : EMPTY_ORDERS;
}

function effectiveStatuses(orders: OrderOut[], pendingCancel: ReadonlySet<string>) {
  return orders.map((order) => {
    const key = orderKey(order);
    return effectiveStatus(order.status, key !== null && pendingCancel.has(key));
  });
}

export function OrdersPage() {
  const queryClient = useQueryClient();
  const accountsQuery = useListAccounts<listAccountsResponse, Error>();
  const accounts = accountsQuery.data?.data.accounts ?? [];

  const [selectedAccount, setSelectedAccount] = useState<string | undefined>(undefined);
  const accountId =
    selectedAccount !== undefined && accounts.includes(selectedAccount)
      ? selectedAccount
      : accounts[0];

  const [modalOpen, setModalOpen] = useState(false);
  const [pendingCancel, setPendingCancel] = useState<ReadonlySet<string>>(() => new Set());

  const ordersQuery = useListOrders<listOrdersResponse, Error>(
    { account_id: accountId ?? '' },
    {
      query: {
        enabled: accountId !== undefined,
        // Polling solo con al menos una orden no final (estados efectivos); vacío o todo final ⇒ se detiene (EB-7, EB-8).
        refetchInterval: (query) =>
          hasNonFinal(effectiveStatuses(ordersOf(query.state.data), pendingCancel))
            ? ORDERS_REFRESH_MS
            : false,
      },
    },
  );
  const orders = ordersOf(ordersQuery.data);

  // El override `PENDING_CANCEL` se descarta cuando la API informa un estado final para esa fila (EB-15).
  useEffect(() => {
    setPendingCancel((current) => {
      if (current.size === 0) {
        return current;
      }
      const next = new Set(current);
      for (const order of orders) {
        const key = orderKey(order);
        if (key !== null && isFinalStatus(order.status)) {
          next.delete(key);
        }
      }
      return next.size === current.size ? current : next;
    });
  }, [orders]);

  const cancelOrder = useCancelOrder<Error>();
  const cancelingKey = cancelOrder.isPending
    ? `${cancelOrder.variables.data.cl_ord_id}|${cancelOrder.variables.data.proprietary}`
    : null;

  function invalidateOrders(account: string) {
    void queryClient.invalidateQueries({
      queryKey: getListOrdersQueryKey({ account_id: account }),
    });
  }

  function handleCancel(order: OrderOut) {
    const key = orderKey(order);
    if (cancelOrder.isPending || key === null || !order.cl_ord_id || !order.proprietary) {
      return; // evita dobles envíos (EB-14)
    }
    cancelOrder.mutate(
      { data: { cl_ord_id: order.cl_ord_id, proprietary: order.proprietary } },
      {
        onSuccess: () => {
          setPendingCancel((current) => new Set(current).add(key));
          if (accountId !== undefined) {
            invalidateOrders(accountId);
          }
        },
      },
    );
  }

  function handleCreated(createdAccount: string) {
    setModalOpen(false);
    // Si la orden se emitió en otra cuenta, se muestra esa cuenta para que aparezca (EB-33).
    setSelectedAccount(createdAccount);
    invalidateOrders(createdAccount);
  }

  function renderContent() {
    if (accountsQuery.isPending) {
      return (
        <div data-testid="orders-loading">
          <Spin size="large" />
        </div>
      );
    }
    if (accountsQuery.isError) {
      return (
        <Alert
          data-testid="orders-error"
          type="error"
          showIcon
          title="No se pudieron obtener las cuentas"
          description={describeApiError(accountsQuery.error)}
          action={
            <Button size="small" onClick={() => void accountsQuery.refetch()}>
              Reintentar
            </Button>
          }
        />
      );
    }
    if (accounts.length === 0) {
      return (
        <Alert
          data-testid="orders-no-accounts"
          type="warning"
          showIcon
          title={NO_ACCOUNTS_MESSAGE}
        />
      );
    }
    if (ordersQuery.isPending) {
      return (
        <div data-testid="orders-loading">
          <Spin size="large" />
        </div>
      );
    }
    return (
      <Space direction="vertical" style={{ width: '100%' }}>
        {ordersQuery.isError && (
          <Alert
            data-testid="orders-error"
            type="error"
            showIcon
            title="No se pudo obtener el listado de órdenes"
            description={describeApiError(ordersQuery.error)}
            action={
              <Button size="small" onClick={() => void ordersQuery.refetch()}>
                Reintentar
              </Button>
            }
          />
        )}
        {cancelOrder.isError && (
          <Alert
            data-testid="orders-action-error"
            type="error"
            showIcon
            closable
            onClose={() => cancelOrder.reset()}
            title="No se pudo cancelar la orden"
            description={describeApiError(cancelOrder.error)}
          />
        )}
        {/* Con error y datos previos se conserva la última tabla (EB-10). */}
        {(ordersQuery.data !== undefined || !ordersQuery.isError) && (
          <OrdersTable
            orders={orders}
            pendingCancel={pendingCancel}
            cancelingKey={cancelingKey}
            onCancel={handleCancel}
          />
        )}
      </Space>
    );
  }

  return (
    <>
      <Typography.Title level={2} data-testid="page-ordenes">
        Órdenes
      </Typography.Title>
      <Flex gap={8} wrap align="center" style={{ marginBottom: 16 }}>
        <Select
          data-testid="orders-account-select"
          showSearch={{ optionFilterProp: 'label' }}
          placeholder="Cuenta"
          style={{ minWidth: 200 }}
          value={accountId}
          options={accounts.map((account) => ({ value: account, label: account }))}
          onChange={(value: string) => setSelectedAccount(value)}
          disabled={accounts.length === 0}
        />
        <Button
          data-testid="orders-refresh"
          disabled={accountId === undefined}
          loading={ordersQuery.isFetching}
          onClick={() => void ordersQuery.refetch()}
        >
          Actualizar
        </Button>
        <Button data-testid="orders-new" type="primary" onClick={() => setModalOpen(true)}>
          Nueva orden
        </Button>
      </Flex>
      {renderContent()}
      <NewOrderModal
        open={modalOpen}
        accounts={accounts}
        defaultAccount={accountId}
        onClose={() => setModalOpen(false)}
        onCreated={handleCreated}
      />
    </>
  );
}
