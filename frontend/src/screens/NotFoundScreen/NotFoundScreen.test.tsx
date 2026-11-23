import { screen } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import { routes } from "@/app/routes";
import { renderWithProviders } from "@/test/render";

import { NotFoundScreen } from "./NotFoundScreen";

describe("NotFoundScreen", () => {
  it("muestra la pantalla 404 en una ruta no definida", async () => {
    renderWithProviders(<NotFoundScreen />, { route: "/no-existe", routes });

    expect(await screen.findByText("404")).toBeInTheDocument();
    expect(screen.getByText("Página no encontrada")).toBeInTheDocument();
  });

  it("ofrece un link para volver al inicio", async () => {
    renderWithProviders(<NotFoundScreen />, { route: "/no-existe", routes });

    expect(await screen.findByRole("link", { name: "Volver al inicio" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});
