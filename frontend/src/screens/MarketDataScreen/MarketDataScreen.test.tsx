import { act, screen, waitFor } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { getListMarketDataMockHandler } from "@/api/generated/market-data/market-data.msw";
import type { MarketDataResponse, MarketDataRow } from "@/api/generated/model";
import { MARKET_DATA_POLL_INTERVAL_MS } from "@/constants/marketData";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { MarketDataScreen } from "./MarketDataScreen";

function row(symbol: string, marketId: string): MarketDataRow {
  return {
    symbol,
    market_id: marketId,
    bid_price: "100",
    bid_size: "10",
    ask_price: "101",
    ask_size: "20",
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
    spread_pct: "0.9950",
    staleness_seconds: null,
    received_at: "2026-11-24T14:03:11Z",
  };
}

const RESPONSE: MarketDataResponse = {
  items: [row("AL30", "BYMA"), row("GD30", "BYMA"), row("GGAL", "ROFX")],
  fetched_at: "2026-11-24T14:03:11Z",
};

const PROBLEM = {
  type: "about:blank",
  title: "Market data no disponible",
  status: 502,
  detail: "No se pudo obtener la market data. Reintentá en unos segundos.",
  instance: "/api/market-data",
  correlation_id: "corr-123",
  errors: null,
};

const problemResponse = (): Response =>
  HttpResponse.json(PROBLEM, {
    status: 502,
    headers: { "content-type": "application/problem+json" },
  });

const renderScreen = (route = "/market-data") =>
  renderWithProviders(<MarketDataScreen />, { route });

const dataRows = (): HTMLElement[] =>
  screen.getAllByRole("row").filter((r) => r.querySelector("td") !== null);

afterEach(() => {
  vi.useRealTimers();
});

describe("MarketDataScreen", () => {
  it("muestra un indicador de carga en la primera carga (AC-13)", () => {
    server.use(
      http.get("*/api/market-data", async () => {
        await delay("infinite");
        return HttpResponse.json({});
      }),
    );

    renderScreen();

    expect(screen.getByLabelText("Cargando market data")).toBeInTheDocument();
  });

  it("muestra una fila por instrumento y la última actualización (AC-11, AC-24)", async () => {
    server.use(getListMarketDataMockHandler(RESPONSE));

    renderScreen();

    expect(await screen.findByRole("cell", { name: "GGAL" })).toBeInTheDocument();
    expect(dataRows()).toHaveLength(3);
    expect(screen.getByText(/^Última actualización: \d{2}:\d{2}:\d{2}$/)).toBeInTheDocument();
    expect(screen.getAllByRole("cell", { name: "1,00%" })).toHaveLength(3);
  });

  it("muestra un estado vacío sin instrumentos suscriptos (AC-14)", async () => {
    server.use(getListMarketDataMockHandler({ items: [], fetched_at: RESPONSE.fetched_at }));

    renderScreen();

    expect(await screen.findByText("No hay instrumentos suscriptos")).toBeInTheDocument();
  });

  it("aplica los filtros de la URL y 'Limpiar filtros' los quita cuando no hay coincidencias (AC-19)", async () => {
    server.use(getListMarketDataMockHandler(RESPONSE));

    const { user } = renderScreen("/market-data?symbol=zzz");

    expect(
      await screen.findByText("Ningún instrumento coincide con los filtros"),
    ).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Limpiar filtros" }));

    expect(await screen.findByRole("cell", { name: "GGAL" })).toBeInTheDocument();
    expect(dataRows()).toHaveLength(3);
  });

  it("filtra por símbolo al escribir (AC-15)", async () => {
    server.use(getListMarketDataMockHandler(RESPONSE));

    const { user } = renderScreen();
    await screen.findByRole("cell", { name: "GGAL" });

    await user.type(screen.getByLabelText("Filtrar por símbolo"), "d3");

    expect(dataRows()).toHaveLength(1);
    expect(screen.getByRole("cell", { name: "GD30" })).toBeInTheDocument();
  });

  it("muestra el error con title, detail y correlationId, y 'Reintentar' vuelve a pedir (AC-22)", async () => {
    let calls = 0;
    server.use(
      http.get("*/api/market-data", () => {
        calls += 1;
        return calls === 1 ? problemResponse() : HttpResponse.json(RESPONSE);
      }),
    );

    const { user } = renderScreen();

    expect(await screen.findByText("Market data no disponible")).toBeInTheDocument();
    expect(screen.getByText(PROBLEM.detail)).toBeInTheDocument();
    expect(screen.getByText("Correlation ID: corr-123")).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Reintentar" }));

    expect(await screen.findByRole("cell", { name: "GGAL" })).toBeInTheDocument();
    expect(calls).toBe(2);
  });

  it("vuelve a pedir cada 5 s sin spinner y conservando los filtros (AC-23)", async () => {
    vi.useFakeTimers({ shouldAdvanceTime: true });
    let calls = 0;
    server.use(
      http.get("*/api/market-data", () => {
        calls += 1;
        return HttpResponse.json(RESPONSE);
      }),
    );

    renderScreen("/market-data?market=ROFX");
    await screen.findByRole("cell", { name: "GGAL" });
    expect(calls).toBe(1);

    await act(async () => {
      await vi.advanceTimersByTimeAsync(MARKET_DATA_POLL_INTERVAL_MS);
    });

    await waitFor(() => {
      expect(calls).toBe(2);
    });
    expect(screen.queryByLabelText("Cargando market data")).not.toBeInTheDocument();
    expect(dataRows()).toHaveLength(1);
    expect(screen.getByRole("cell", { name: "GGAL" })).toBeInTheDocument();
  });

  it("si una actualización falla conserva los datos y avisa con la hora (AC-25)", async () => {
    let calls = 0;
    server.use(
      http.get("*/api/market-data", () => {
        calls += 1;
        return calls === 1 ? HttpResponse.json(RESPONSE) : problemResponse();
      }),
    );

    const { user } = renderScreen();
    await screen.findByRole("cell", { name: "GGAL" });

    await user.click(screen.getByRole("button", { name: "Actualizar" }));

    expect(
      await screen.findByText(/^No se pudo actualizar\. Última actualización: \d{2}:\d{2}:\d{2}$/),
    ).toBeInTheDocument();
    expect(dataRows()).toHaveLength(3);
  });
});
