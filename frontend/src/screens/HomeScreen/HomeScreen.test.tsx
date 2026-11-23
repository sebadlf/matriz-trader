import { screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { renderWithProviders } from "@/test/render";

import { HomeScreen } from "./HomeScreen";

const jsonResponse = (body: unknown, status = 200): Response =>
  new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });

describe("HomeScreen", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it("muestra un indicador de carga mientras consulta el backend", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => new Promise<Response>(() => {})),
    );

    renderWithProviders(<HomeScreen />);

    expect(screen.getByLabelText("Cargando estado del backend")).toBeInTheDocument();
  });

  it("muestra el estado del backend cuando /api/health responde", async () => {
    const fetchMock = vi.fn(async () =>
      jsonResponse({ status: "ok", service: "matriz-trader-backend", version: "0.1.0" }),
    );
    vi.stubGlobal("fetch", fetchMock);

    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("Backend: ok")).toBeInTheDocument();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/health",
      expect.objectContaining({ method: "GET" }),
    );
  });

  it("muestra un error cuando el backend falla", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse({ detail: "boom" }, 500)),
    );

    renderWithProviders(<HomeScreen />);

    expect(await screen.findByText("No se pudo conectar con el backend")).toBeInTheDocument();
  });
});
