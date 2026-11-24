import { describe, expect, it } from "vite-plus/test";

import type { MarketDataRow } from "@/api/generated/model";

import { filterRows, marketOptions } from "./filterRows";

function row(symbol: string, marketId: string | null): MarketDataRow {
  return {
    symbol,
    market_id: marketId,
    bid_price: null,
    bid_size: null,
    ask_price: null,
    ask_size: null,
    last_price: null,
    last_size: null,
    last_at: null,
    open_price: null,
    high_price: null,
    low_price: null,
    close_price: null,
    settlement_price: null,
    open_interest: null,
    volume: null,
    spread_pct: null,
    staleness_seconds: null,
    received_at: "2026-11-24T14:03:11Z",
  };
}

const ROWS = [
  row("AL30", "BYMA"),
  row("AL30D", "ROFX"),
  row("GD30", "BYMA"),
  row("GGAL", "ROFX"),
  row("YPFD", null),
];

const symbols = (rows: MarketDataRow[]): string[] => rows.map((r) => r.symbol);

describe("filterRows", () => {
  it("sin filtros devuelve todas las filas", () => {
    expect(filterRows(ROWS, { symbol: "", markets: [] })).toEqual(ROWS);
  });

  it("filtra por símbolo sin distinguir mayúsculas (AC-15)", () => {
    expect(symbols(filterRows(ROWS, { symbol: "al3", markets: [] }))).toEqual(["AL30", "AL30D"]);
    expect(symbols(filterRows(ROWS, { symbol: "  gGa ", markets: [] }))).toEqual(["GGAL"]);
  });

  it("filtra por uno o más mercados (AC-16)", () => {
    expect(symbols(filterRows(ROWS, { symbol: "", markets: ["ROFX"] }))).toEqual(["AL30D", "GGAL"]);
    expect(symbols(filterRows(ROWS, { symbol: "", markets: ["ROFX", "BYMA"] }))).toEqual([
      "AL30",
      "AL30D",
      "GD30",
      "GGAL",
    ]);
  });

  it("combina símbolo y mercado con AND (AC-17)", () => {
    expect(symbols(filterRows(ROWS, { symbol: "30", markets: ["BYMA"] }))).toEqual([
      "AL30",
      "GD30",
    ]);
    expect(filterRows(ROWS, { symbol: "ggal", markets: ["BYMA"] })).toEqual([]);
  });

  it("un mercado que no está en los datos no deja filas", () => {
    expect(filterRows(ROWS, { symbol: "", markets: ["MATBA"] })).toEqual([]);
  });
});

describe("marketOptions", () => {
  it("devuelve los mercados presentes, únicos, sin null y ordenados (AC-16)", () => {
    expect(marketOptions(ROWS)).toEqual(["BYMA", "ROFX"]);
  });

  it("sin filas no ofrece opciones", () => {
    expect(marketOptions([])).toEqual([]);
  });
});
