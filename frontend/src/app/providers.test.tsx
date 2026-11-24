import { useQueryClient } from "@tanstack/react-query";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vite-plus/test";

import { AppProviders } from "./providers";

function QueryClientProbe() {
  const client = useQueryClient();
  return <p>staleTime: {String(client.getDefaultOptions().queries?.staleTime)}</p>;
}

describe("AppProviders", () => {
  // Se usa `render` directo y no `renderWithProviders`: este test verifica justamente el
  // `QueryClient` que `AppProviders` crea cuando no recibe uno (camino de `main.tsx`).
  it("crea su propio QueryClient cuando no recibe uno", () => {
    render(
      <AppProviders>
        <QueryClientProbe />
      </AppProviders>,
    );

    expect(screen.getByText("staleTime: 30000")).toBeInTheDocument();
  });
});
