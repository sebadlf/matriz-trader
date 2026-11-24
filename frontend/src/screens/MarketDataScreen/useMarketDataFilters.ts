import { useSearchParams } from "react-router";

import type { MarketDataFilters } from "./filterRows";

const SYMBOL_PARAM = "symbol";
const MARKET_PARAM = "market";

type UseMarketDataFiltersResult = {
  filters: MarketDataFilters;
  setSymbol: (value: string) => void;
  setMarkets: (value: string[]) => void;
  clear: () => void;
  isActive: boolean;
};

/**
 * Filtros de la tabla sincronizados con la URL: `?symbol=al30&market=ROFX&market=BYMA` (AC-18).
 * Escribe con `replace` para no llenar el historial con cada tecla.
 */
export function useMarketDataFilters(): UseMarketDataFiltersResult {
  const [searchParams, setSearchParams] = useSearchParams();

  const filters: MarketDataFilters = {
    symbol: searchParams.get(SYMBOL_PARAM) ?? "",
    markets: searchParams.getAll(MARKET_PARAM),
  };

  const setSymbol = (value: string): void => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        if (value === "") next.delete(SYMBOL_PARAM);
        else next.set(SYMBOL_PARAM, value);
        return next;
      },
      { replace: true },
    );
  };

  const setMarkets = (value: string[]): void => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete(MARKET_PARAM);
        for (const market of value) next.append(MARKET_PARAM, market);
        return next;
      },
      { replace: true },
    );
  };

  const clear = (): void => {
    setSearchParams(
      (prev) => {
        const next = new URLSearchParams(prev);
        next.delete(SYMBOL_PARAM);
        next.delete(MARKET_PARAM);
        return next;
      },
      { replace: true },
    );
  };

  return {
    filters,
    setSymbol,
    setMarkets,
    clear,
    isActive: filters.symbol.trim() !== "" || filters.markets.length > 0,
  };
}
