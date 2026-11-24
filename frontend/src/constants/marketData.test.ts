import { describe, expect, it } from "vite-plus/test";

import { EMPTY_CELL, MARKET_DATA_POLL_INTERVAL_MS } from "./marketData";

describe("constantes de market data", () => {
  it("refresca cada 5 segundos (AC-23)", () => {
    expect(MARKET_DATA_POLL_INTERVAL_MS).toBe(5_000);
  });

  it("muestra un guion largo en las celdas sin valor (AC-9, AC-26)", () => {
    expect(EMPTY_CELL).toBe("—");
  });
});
