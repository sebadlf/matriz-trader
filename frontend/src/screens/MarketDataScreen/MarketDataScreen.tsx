import { Alert, Button, Empty, Flex, Spin, Typography, theme } from "antd";

import { useListMarketData } from "@/api/generated/market-data/market-data";
import { MARKET_DATA_POLL_INTERVAL_MS } from "@/constants/marketData";
import { formatTime } from "@/utils/format";

import { filterRows, marketOptions } from "./filterRows";
import { MarketDataFilters } from "./MarketDataFilters";
import { MarketDataTable } from "./MarketDataTable";
import { useMarketDataFilters } from "./useMarketDataFilters";

/** Market data de los instrumentos suscriptos, refrescada cada 5 s (US-1, US-5). */
export function MarketDataScreen() {
  const { token } = theme.useToken();
  const { filters, setSymbol, setMarkets, clear, isActive } = useMarketDataFilters();
  const { data, error, isPending, isError, isFetching, refetch, dataUpdatedAt } = useListMarketData(
    {
      query: {
        refetchInterval: MARKET_DATA_POLL_INTERVAL_MS, // AC-23
        refetchIntervalInBackground: false, // pausa con la pestaña oculta
        refetchOnWindowFocus: true,
        staleTime: 0, // al volver a la pestaña refresca enseguida
      },
    },
  );

  const retry = (): void => {
    void refetch();
  };

  // `customFetch` lanza `ApiError` ante un status no-ok: solo el 200 llega como `data`.
  const items = data?.status === 200 ? data.data.items : undefined;
  const padding = { padding: token.paddingLG };

  if (isPending) {
    return (
      <Flex justify="center" style={padding}>
        <Spin size="large" aria-label="Cargando market data" />
      </Flex>
    );
  }

  if (items === undefined) {
    return (
      <Flex vertical style={padding}>
        <Alert
          type="error"
          showIcon
          title={error?.title ?? "No se pudo obtener la market data"}
          description={
            <>
              {error?.detail !== undefined && <div>{error.detail}</div>}
              {error?.correlationId !== undefined && (
                <div>Correlation ID: {error.correlationId}</div>
              )}
            </>
          }
          action={<Button onClick={retry}>Reintentar</Button>}
        />
      </Flex>
    );
  }

  const lastUpdate = formatTime(dataUpdatedAt);
  const rows = filterRows(items, filters);

  return (
    <Flex vertical gap="middle" style={padding}>
      <Typography.Title level={1}>Market data</Typography.Title>
      {isError && (
        <Alert
          type="warning"
          showIcon
          title={`No se pudo actualizar. Última actualización: ${lastUpdate}`}
        />
      )}
      {items.length === 0 ? (
        <Empty description="No hay instrumentos suscriptos" />
      ) : (
        <>
          <Flex justify="space-between" align="center" gap="middle" wrap>
            <MarketDataFilters
              filters={filters}
              markets={marketOptions(items)}
              onSymbolChange={setSymbol}
              onMarketsChange={setMarkets}
            />
            <Flex align="center" gap="small">
              <Typography.Text>Última actualización: {lastUpdate}</Typography.Text>
              <Button onClick={retry} loading={isFetching}>
                Actualizar
              </Button>
            </Flex>
          </Flex>
          <MarketDataTable
            rows={rows}
            emptyText={
              <Empty description="Ningún instrumento coincide con los filtros">
                {isActive && <Button onClick={clear}>Limpiar filtros</Button>}
              </Empty>
            }
          />
        </>
      )}
    </Flex>
  );
}
