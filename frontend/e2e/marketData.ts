import type { Page } from "@playwright/test";

// Fixture compartido por los e2e de `/market-data`: el backend no participa, la respuesta de
// `GET /api/market-data` se arma acá con la forma de `MarketDataResponse` (numéricos como string).
const MARKETS = ["BYMA", "ROFX"] as const;

/** `INS0000`, `INS0001`, …: 4 dígitos para que un símbolo no sea prefijo de otro. */
export const symbolAt = (index: number): string => `INS${String(index).padStart(4, "0")}`;

const row = (index: number) => ({
  symbol: symbolAt(index),
  market_id: MARKETS[index % MARKETS.length],
  bid_price: "100.5",
  bid_size: "10",
  ask_price: "101",
  ask_size: "5",
  last_price: "100.75",
  last_size: "3",
  last_at: "2026-11-24T14:03:11Z",
  open_price: "99",
  high_price: "102",
  low_price: "98.5",
  close_price: "99.5",
  settlement_price: null,
  open_interest: null,
  volume: "1500",
  spread_pct: "0.4963",
  staleness_seconds: "2.5",
  received_at: "2026-11-24T14:03:11.250000Z",
});

/** Mockea `GET /api/market-data` (también los refetch del polling) con `count` filas. */
export const mockMarketData = async (page: Page, count: number): Promise<void> => {
  const body = {
    items: Array.from({ length: count }, (_, index) => row(index)),
    fetched_at: "2026-11-24T14:03:11.500000Z",
  };
  await page.route("**/api/market-data", (route) =>
    route.fulfill({ status: 200, contentType: "application/json", json: body }),
  );
};
