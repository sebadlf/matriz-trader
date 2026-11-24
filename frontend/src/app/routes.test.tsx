import { screen } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import { getListMarketDataMockHandler } from "@/api/generated/market-data/market-data.msw";
import { ROUTES } from "@/constants/routes";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { routes } from "./routes";

describe("routes", () => {
  it("/market-data carga la pantalla de market data (AC-11)", async () => {
    server.use(getListMarketDataMockHandler({ items: [], fetched_at: "2026-11-24T14:03:11Z" }));

    renderWithProviders(<></>, { route: ROUTES.marketData, routes });

    expect(await screen.findByRole("heading", { name: "Market data" })).toBeInTheDocument();
  });
});
