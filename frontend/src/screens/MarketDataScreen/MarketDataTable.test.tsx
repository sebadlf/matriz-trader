import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import type { MarketDataRow } from "@/api/generated/model";

import { MarketDataTable } from "./MarketDataTable";

const EMPTY_ROW: MarketDataRow = {
  symbol: "GGAL",
  market_id: null,
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

const FULL_ROW: MarketDataRow = {
  ...EMPTY_ROW,
  symbol: "AL30",
  market_id: "ROFX",
  bid_price: "12345678901234567.12345678",
  bid_size: "100",
  ask_price: "101.5",
  ask_size: "200",
  last_price: "101",
  last_size: "5",
  last_at: "2026-11-24T14:03:10Z",
  open_price: "99",
  high_price: "102",
  low_price: "98",
  close_price: "97",
  settlement_price: "96",
  open_interest: "1000",
  volume: "25000",
  spread_pct: "0.1250",
  staleness_seconds: "2.5",
};

const cellsOf = (symbol: string): string[] => {
  const row = screen.getByRole("row", { name: new RegExp(`^${symbol}\\b`) });
  return within(row)
    .getAllByRole("cell")
    .map((cell) => cell.textContent);
};

const HEADERS = [
  "Símbolo",
  "Mercado",
  "Bid",
  "Cant. bid",
  "Ask",
  "Cant. ask",
  "Spread %",
  "Último",
  "Cant. último",
  "Hora último",
  "Apertura",
  "Máximo",
  "Mínimo",
  "Cierre",
  "Settlement",
  "Interés abierto",
  "Volumen",
  "Antigüedad (s)",
  "Recibido",
];

describe("MarketDataTable", () => {
  it("muestra las 19 columnas en orden (AC-11)", () => {
    render(<MarketDataTable rows={[FULL_ROW]} emptyText="vacío" />);

    expect(screen.getAllByRole("columnheader").map((h) => h.textContent)).toEqual(HEADERS);
  });

  it("formatea desde el string sin perder precisión y el spread con 2 decimales y % (AC-12, AC-26)", () => {
    render(<MarketDataTable rows={[FULL_ROW]} emptyText="vacío" />);

    const cells = cellsOf("AL30");
    expect(cells[1]).toBe("ROFX");
    expect(cells[2]).toBe("12.345.678.901.234.567,12345678");
    expect(cells[4]).toBe("101,5");
    expect(cells[6]).toBe("0,12%");
    expect(cells[16]).toBe("25.000");
    expect(cells[17]).toBe("2,5");
  });

  it("muestra — en los campos null, nunca 0 (AC-9, AC-26)", () => {
    render(<MarketDataTable rows={[EMPTY_ROW]} emptyText="vacío" />);

    const cells = cellsOf("GGAL");
    // Todas las celdas salvo símbolo y recibido son `null`.
    expect(cells.slice(1, 18).every((c) => c === "—")).toBe(true);
    expect(cells[18]).not.toBe("—");
  });

  it("sin filas muestra el contenido vacío recibido", () => {
    render(<MarketDataTable rows={[]} emptyText="Nada por acá" />);

    expect(screen.getByText("Nada por acá")).toBeInTheDocument();
  });
});
