import { Flex, Input, Select } from "antd";

import type { MarketDataFilters as MarketDataFilterValues } from "./filterRows";

type MarketDataFiltersProps = {
  filters: MarketDataFilterValues;
  /** Mercados presentes en los datos (`marketOptions`) (AC-16). */
  markets: string[];
  onSymbolChange: (value: string) => void;
  onMarketsChange: (value: string[]) => void;
};

/** Filtro de texto por símbolo y selección múltiple de mercados (AC-15, AC-16). */
export function MarketDataFilters({
  filters,
  markets,
  onSymbolChange,
  onMarketsChange,
}: MarketDataFiltersProps) {
  return (
    <Flex gap="small" wrap>
      <Input
        aria-label="Filtrar por símbolo"
        placeholder="Símbolo"
        allowClear
        value={filters.symbol}
        onChange={(event) => onSymbolChange(event.target.value)}
        style={{ width: 200 }}
      />
      <Select
        aria-label="Filtrar por mercado"
        placeholder="Mercado"
        mode="multiple"
        allowClear
        value={filters.markets}
        options={markets.map((market) => ({ label: market, value: market }))}
        onChange={onMarketsChange}
        style={{ minWidth: 200 }}
      />
    </Flex>
  );
}
