import { Alert, Form, InputNumber, Modal, Radio, Select } from 'antd';
import { useEffect } from 'react';
import {
  type listInstrumentsResponse,
  useCreateOrder,
  useListInstruments,
} from '../../api/generated/matriz';
import type { NewOrderRequest } from '../../api/generated/model';
import { describeApiError } from './format';

/** El catálogo de instrumentos casi no cambia en el día: sin polling y con `staleTime` largo. */
const INSTRUMENTS_STALE_MS = 3_600_000;

export const NO_ACCOUNTS_MESSAGE =
  'No hay cuentas configuradas. Cargá MATRIZ_ACCOUNTS en el .env raíz (separadas por coma) y reiniciá el backend.';

export type NewOrderModalProps = {
  open: boolean;
  accounts: string[];
  defaultAccount: string | undefined;
  /** Cancelar, cruz o Escape (EB-19). */
  onClose: () => void;
  /** Alta aceptada por la API (EB-33). Recibe la cuenta usada. */
  onCreated: (accountId: string) => void;
};

export type NewOrderFormValues = {
  account_id: string;
  /** `${market_id}|${symbol}` */
  instrument: string;
  side: 'BUY' | 'SELL';
  order_type: 'MARKET' | 'LIMIT';
  quantity: number;
  price?: number;
};

const instrumentValue = (marketId: string, symbol: string) => `${marketId}|${symbol}`;

function toRequest(values: NewOrderFormValues): NewOrderRequest {
  const separator = values.instrument.indexOf('|');
  const body: NewOrderRequest = {
    account_id: values.account_id,
    // El backend valida el `Literal["ROFX"]`; el valor sale siempre de `GET /instruments` (EB-22).
    market_id: values.instrument.slice(0, separator) as NewOrderRequest['market_id'],
    symbol: values.instrument.slice(separator + 1),
    side: values.side,
    order_type: values.order_type,
    quantity: values.quantity,
  };
  // MARKET no lleva precio: ni siquiera la clave (EB-27).
  if (values.order_type === 'LIMIT') {
    body.price = values.price;
  }
  return body;
}

function isPositive(value: unknown): boolean {
  return typeof value === 'number' && Number.isFinite(value) && value > 0;
}

export function NewOrderModal({
  open,
  accounts,
  defaultAccount,
  onClose,
  onCreated,
}: NewOrderModalProps) {
  const [form] = Form.useForm<NewOrderFormValues>();
  const orderType = Form.useWatch('order_type', form);
  const instruments = useListInstruments<listInstrumentsResponse, Error>({
    query: { enabled: open, staleTime: INSTRUMENTS_STALE_MS },
  });
  const createOrder = useCreateOrder<Error>();

  // Las cuentas pueden llegar después del primer render: completar la cuenta por defecto al abrir.
  useEffect(() => {
    if (open && defaultAccount !== undefined && form.getFieldValue('account_id') === undefined) {
      form.setFieldsValue({ account_id: defaultAccount });
    }
  }, [open, defaultAccount, form]);

  const noAccounts = accounts.length === 0;
  const submitBlocked = noAccounts || instruments.isPending || instruments.isError;

  const instrumentOptions = (instruments.data?.data ?? []).map((instrument) => ({
    value: instrumentValue(instrument.market_id, instrument.symbol),
    label: instrument.symbol,
  }));

  async function handleSubmit() {
    if (createOrder.isPending || submitBlocked) {
      return; // anti-doble-envío (EB-31) y envío bloqueado (EB-21, EB-23)
    }
    let values: NewOrderFormValues;
    try {
      values = await form.validateFields();
    } catch {
      return; // inválido: los errores quedan en los campos y no se llama a la API (EB-30)
    }
    createOrder.mutate(
      { data: toRequest(values) },
      {
        onSuccess: () => {
          form.resetFields();
          createOrder.reset();
          onCreated(values.account_id);
        },
      },
    );
  }

  function handleCancel() {
    createOrder.reset();
    onClose();
  }

  return (
    <Modal
      open={open}
      title="Nueva orden"
      okText="Enviar orden"
      cancelText="Cancelar"
      onOk={handleSubmit}
      onCancel={handleCancel}
      keyboard
      maskClosable={false}
      forceRender
      okButtonProps={{
        'data-testid': 'new-order-submit',
        loading: createOrder.isPending,
        disabled: submitBlocked,
      }}
    >
      <div data-testid="new-order-modal">
        {createOrder.isError && (
          <Alert
            data-testid="new-order-error"
            type="error"
            showIcon
            title="No se pudo emitir la orden"
            description={describeApiError(createOrder.error)}
            style={{ marginBottom: 16 }}
          />
        )}
        <Form
          form={form}
          layout="vertical"
          initialValues={{ account_id: defaultAccount, side: 'BUY', order_type: 'LIMIT' }}
        >
          <Form.Item
            name="account_id"
            label="Cuenta"
            rules={[{ required: true, message: 'Elegí una cuenta' }]}
            {...(noAccounts ? { validateStatus: 'error' as const, help: NO_ACCOUNTS_MESSAGE } : {})}
          >
            <Select
              data-testid="new-order-account"
              showSearch={{ optionFilterProp: 'label' }}
              placeholder="Elegí una cuenta"
              options={accounts.map((account) => ({ value: account, label: account }))}
              notFoundContent={noAccounts ? NO_ACCOUNTS_MESSAGE : 'Sin coincidencias'}
            />
          </Form.Item>
          <Form.Item
            name="instrument"
            label="Activo"
            rules={[{ required: true, message: 'Elegí un activo' }]}
            {...(instruments.isError
              ? {
                  validateStatus: 'error' as const,
                  help: `No se pudieron cargar los instrumentos: ${describeApiError(instruments.error)}`,
                }
              : {})}
          >
            <Select
              data-testid="new-order-instrument"
              showSearch={{ optionFilterProp: 'label' }}
              loading={instruments.isPending}
              placeholder={instruments.isPending ? 'Cargando instrumentos…' : 'Buscá por símbolo'}
              options={instrumentOptions}
              notFoundContent={
                instruments.isError ? describeApiError(instruments.error) : 'Sin coincidencias'
              }
            />
          </Form.Item>
          <Form.Item name="side" label="Lado" rules={[{ required: true }]}>
            <Radio.Group
              data-testid="new-order-side"
              options={[
                { value: 'BUY', label: 'Compra' },
                { value: 'SELL', label: 'Venta' },
              ]}
            />
          </Form.Item>
          <Form.Item name="order_type" label="Tipo" rules={[{ required: true }]}>
            <Radio.Group
              data-testid="new-order-type"
              options={[
                { value: 'MARKET', label: 'Market' },
                { value: 'LIMIT', label: 'Limit' },
              ]}
            />
          </Form.Item>
          {orderType === 'LIMIT' && (
            <Form.Item
              name="price"
              label="Precio"
              rules={[
                { required: true, message: 'El precio es obligatorio para órdenes Limit' },
                {
                  validator: (_, value: unknown) =>
                    value == null || isPositive(value)
                      ? Promise.resolve()
                      : Promise.reject(new Error('El precio debe ser mayor a cero')),
                },
              ]}
            >
              <InputNumber data-testid="new-order-price" style={{ width: '100%' }} />
            </Form.Item>
          )}
          <Form.Item
            name="quantity"
            label="Cantidad"
            rules={[
              { required: true, message: 'La cantidad es obligatoria' },
              {
                validator: (_, value: unknown) =>
                  value == null || (Number.isInteger(value) && isPositive(value))
                    ? Promise.resolve()
                    : Promise.reject(new Error('La cantidad debe ser un entero mayor a cero')),
              },
            ]}
          >
            <InputNumber data-testid="new-order-quantity" step={1} style={{ width: '100%' }} />
          </Form.Item>
        </Form>
      </div>
    </Modal>
  );
}
