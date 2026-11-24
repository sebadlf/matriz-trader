import { Table } from "antd";
import type { ColumnsType } from "antd/es/table";
import type { ReactNode } from "react";

import type { MarketDataRow } from "@/api/generated/model";
import { EMPTY_CELL } from "@/constants/marketData";
import { formatPercent, formatQuantity, formatTime } from "@/utils/format";

type MarketDataTableProps = {
  rows: MarketDataRow[];
  /** Contenido cuando no hay filas (p. ej. filtros sin coincidencias, AC-19). */
  emptyText: ReactNode;
};

/** Hasta 8 decimales sin ceros finales: no hay tick size por instrumento todavía (AC-12). */
const MARKET_DECIMALS = 8;
const STALENESS_DECIMALS = 1;

type StringKey = {
  [K in keyof MarketDataRow]: MarketDataRow[K] extends string | null ? K : never;
}[keyof MarketDataRow];

/** `null` → `—`, nunca `"0"` (AC-9, AC-26); el valor se formatea desde el string (AC-12). */
const cell =
  (format: (value: string) => string) =>
  (value: string | null): string =>
    value === null ? EMPTY_CELL : format(value);

const market = cell((v) => formatQuantity(v, MARKET_DECIMALS));

const numeric = (
  title: string,
  key: StringKey,
  render = market,
): ColumnsType<MarketDataRow>[number] => ({
  title,
  dataIndex: key,
  key,
  align: "right",
  render,
});

// Constante de módulo: las columnas no se recrean en cada refresco de 5 s.
const COLUMNS: ColumnsType<MarketDataRow> = [
  { title: "Símbolo", dataIndex: "symbol", key: "symbol" },
  { title: "Mercado", dataIndex: "market_id", key: "market_id", render: cell((v) => v) },
  numeric("Bid", "bid_price"),
  numeric("Cant. bid", "bid_size"),
  numeric("Ask", "ask_price"),
  numeric("Cant. ask", "ask_size"),
  numeric("Spread %", "spread_pct", cell(formatPercent)),
  numeric("Último", "last_price"),
  numeric("Cant. último", "last_size"),
  numeric("Hora último", "last_at", cell(formatTime)),
  numeric("Apertura", "open_price"),
  numeric("Máximo", "high_price"),
  numeric("Mínimo", "low_price"),
  numeric("Cierre", "close_price"),
  numeric("Settlement", "settlement_price"),
  numeric("Interés abierto", "open_interest"),
  numeric("Volumen", "volume"),
  numeric(
    "Antigüedad (s)",
    "staleness_seconds",
    cell((v) => formatQuantity(v, STALENESS_DECIMALS)),
  ),
  numeric("Recibido", "received_at", cell(formatTime)),
];

const rowKey = (row: MarketDataRow): string => `${row.market_id ?? ""}:${row.symbol}`;

/** Tabla de market data con una columna por campo de la API más `Spread %` (AC-11). */
export function MarketDataTable({ rows, emptyText }: MarketDataTableProps) {
  // El scroll horizontal lo hace este contenedor y no `scroll.x` de AntD: el `.ant-table-body`
  // de AntD no es enfocable y falla axe `scrollable-region-focusable` (WCAG 2.1.1). Así el
  // usuario de teclado enfoca la región y la desplaza con las flechas.
  return (
    // oxlint-disable-next-line jsx-a11y/no-noninteractive-tabindex -- región con scroll: axe exige que sea enfocable
    <section aria-label="Tabla de market data" tabIndex={0} style={{ overflowX: "auto" }}>
      <Table<MarketDataRow>
        columns={COLUMNS}
        dataSource={rows}
        rowKey={rowKey}
        pagination={false}
        size="small"
        locale={{ emptyText }}
      />
    </section>
  );
}
