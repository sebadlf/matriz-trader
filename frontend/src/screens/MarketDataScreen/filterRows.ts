import type { MarketDataRow } from "@/api/generated/model";

/** Filtros de la tabla de market data; viven en los query params (AC-18). */
export interface MarketDataFilters {
  /** Texto a buscar dentro del símbolo, sin distinguir mayúsculas (AC-15). */
  symbol: string;
  /** `market_id` seleccionados; vacío = sin filtro de mercado (AC-16). */
  markets: string[];
}

/** Filas que cumplen el filtro de símbolo y el de mercado a la vez (AC-15, AC-16, AC-17). */
export function filterRows(rows: MarketDataRow[], filters: MarketDataFilters): MarketDataRow[] {
  const needle = filters.symbol.trim().toLowerCase();
  const markets = new Set(filters.markets);

  return rows.filter(
    (row) =>
      (needle === "" || row.symbol.toLowerCase().includes(needle)) &&
      (markets.size === 0 || (row.market_id !== null && markets.has(row.market_id))),
  );
}

/** `market_id` únicos presentes en los datos, sin `null` y en orden alfabético (AC-16). */
export function marketOptions(rows: MarketDataRow[]): string[] {
  const markets = new Set<string>();
  for (const row of rows) {
    if (row.market_id !== null) markets.add(row.market_id);
  }
  return [...markets].toSorted((a, b) => a.localeCompare(b));
}
