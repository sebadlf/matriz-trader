import { screen } from "@testing-library/react";
import { Button } from "antd";
import { useLocation } from "react-router";
import { describe, expect, it } from "vite-plus/test";

import { renderWithProviders } from "@/test/render";

import { MarketDataFilters } from "./MarketDataFilters";
import { useMarketDataFilters } from "./useMarketDataFilters";

function Harness() {
  const { filters, setSymbol, setMarkets, clear, isActive } = useMarketDataFilters();
  const location = useLocation();

  return (
    <>
      <MarketDataFilters
        filters={filters}
        markets={["BYMA", "ROFX"]}
        onSymbolChange={setSymbol}
        onMarketsChange={setMarkets}
      />
      <Button onClick={clear}>Limpiar filtros</Button>
      <output aria-label="URL actual">{location.search}</output>
      <output aria-label="estado">{isActive ? "activos" : "inactivos"}</output>
      <output aria-label="filtros">{JSON.stringify(filters)}</output>
    </>
  );
}

const search = (): string => screen.getByLabelText("URL actual").textContent;
const filters = (): unknown => JSON.parse(screen.getByLabelText("filtros").textContent);

describe("useMarketDataFilters", () => {
  it("sin query params no hay filtros activos", () => {
    renderWithProviders(<Harness />, { route: "/market-data" });

    expect(filters()).toEqual({ symbol: "", markets: [] });
    expect(screen.getByLabelText("estado")).toHaveTextContent("inactivos");
  });

  it("aplica los filtros de la URL al abrirla (AC-18)", () => {
    renderWithProviders(<Harness />, {
      route: "/market-data?symbol=al30&market=ROFX&market=BYMA",
    });

    expect(filters()).toEqual({ symbol: "al30", markets: ["ROFX", "BYMA"] });
    expect(screen.getByLabelText("Filtrar por símbolo")).toHaveValue("al30");
    expect(screen.getByLabelText("estado")).toHaveTextContent("activos");
  });

  it("escribir en el filtro de símbolo actualiza ?symbol= (AC-15, AC-18)", async () => {
    const { user } = renderWithProviders(<Harness />, { route: "/market-data" });

    await user.type(screen.getByLabelText("Filtrar por símbolo"), "AL3");

    expect(search()).toBe("?symbol=AL3");
    expect(screen.getByLabelText("Filtrar por símbolo")).toHaveValue("AL3");

    await user.clear(screen.getByLabelText("Filtrar por símbolo"));

    expect(search()).toBe("");
  });

  it("seleccionar mercados actualiza ?market= conservando el símbolo (AC-16, AC-18)", async () => {
    const { user } = renderWithProviders(<Harness />, { route: "/market-data?symbol=gd" });

    await user.click(screen.getByLabelText("Filtrar por mercado"));
    await user.click(await screen.findByTitle("ROFX"));
    await user.click(await screen.findByTitle("BYMA"));

    expect(search()).toBe("?symbol=gd&market=ROFX&market=BYMA");
    expect(filters()).toEqual({ symbol: "gd", markets: ["ROFX", "BYMA"] });
  });

  it("clear quita ambos filtros de la URL y conserva otros params", async () => {
    const { user } = renderWithProviders(<Harness />, {
      route: "/market-data?symbol=al&market=ROFX&otro=1",
    });

    await user.click(screen.getByRole("button", { name: "Limpiar filtros" }));

    expect(search()).toBe("?otro=1");
    expect(screen.getByLabelText("estado")).toHaveTextContent("inactivos");
  });
});
