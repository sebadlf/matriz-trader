import "@testing-library/jest-dom/vitest";

import { cleanup } from "@testing-library/react";
import { afterAll, afterEach, beforeAll } from "vite-plus/test";

import { server } from "./server";

// La red se mockea en el borde con MSW: un request sin handler hace fallar el test.
beforeAll(() => {
  server.listen({ onUnhandledRequest: "error" });
});

afterEach(() => {
  cleanup();
  server.resetHandlers();
});

afterAll(() => {
  server.close();
});

// Ant Design consulta `matchMedia` (Grid/responsive), que jsdom no implementa.
Object.defineProperty(window, "matchMedia", {
  writable: true,
  value: (query: string): MediaQueryList => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: () => {},
    removeListener: () => {},
    addEventListener: () => {},
    removeEventListener: () => {},
    dispatchEvent: () => false,
  }),
});

// Los popups de Ant Design (`Select`, `Table`) observan su tamaño con `ResizeObserver`,
// que jsdom no implementa.
class ResizeObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
}
Object.defineProperty(window, "ResizeObserver", { writable: true, value: ResizeObserverStub });
