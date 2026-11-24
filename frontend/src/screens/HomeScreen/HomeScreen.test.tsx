import { screen } from "@testing-library/react";
import { delay, http, HttpResponse } from "msw";
import { describe, expect, it } from "vite-plus/test";

import { getGetHealthMockHandler } from "@/api/generated/health/health.msw";
import { renderWithProviders } from "@/test/render";
import { server } from "@/test/server";

import { HomeScreen } from "./HomeScreen";

describe("HomeScreen", () => {
  it("muestra un indicador de carga mientras consulta el backend", () => {
    server.use(
      http.get("*/api/health", async () => {
        await delay("infinite");
        return HttpResponse.json({});
      }),
    );

    renderWithProviders(<HomeScreen />);

    expect(screen.getByLabelText("Cargando estado del backend")).toBeInTheDocument();
  });

  it("muestra el estado del backend cuando /api/health responde", async () => {
    server.use(
      getGetHealthMockHandler({
        status: "ok",
        service: "matriz-trader-backend",
        version: "0.1.0",
      }),
    );

    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("Backend: ok")).toBeInTheDocument();
  });

  it("muestra un error cuando el backend falla", async () => {
    server.use(
      http.get("*/api/health", () =>
        HttpResponse.json(
          { type: "about:blank", title: "Error interno", status: 500 },
          { status: 500, headers: { "content-type": "application/problem+json" } },
        ),
      ),
    );

    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("No se pudo conectar con el backend")).toBeInTheDocument();
  });
});
