import { AxeBuilder } from "@axe-core/playwright";
import { expect, test } from "@playwright/test";

// Accesibilidad (AC-37): axe sobre cada pantalla con las etiquetas WCAG 2.2 AA.
// El backend se mockea igual que en home.spec.ts: no depende de la API ni de PostgreSQL.
const WCAG_TAGS = ["wcag2a", "wcag2aa", "wcag21aa", "wcag22aa"];

// Resumen legible de cada violación: regla, impacto y nodos afectados con su mensaje.
const summarize = (violations: Awaited<ReturnType<AxeBuilder["analyze"]>>["violations"]) =>
  violations.map(({ id, impact, nodes }) => ({
    id,
    impact,
    nodes: nodes.map(({ target, failureSummary }) => ({ target, failureSummary })),
  }));

test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      json: { status: "ok", service: "matriz-trader-backend", version: "0.1.0" },
    }),
  );
});

test("la home no tiene violaciones WCAG 2.2 AA", async ({ page }) => {
  await page.goto("/");
  // Espera a que la pantalla termine de cargar los datos antes de analizar.
  await expect(page.getByText("Backend: ok")).toBeVisible();

  const { violations } = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();

  expect(summarize(violations)).toEqual([]);
});

test("la pantalla 404 no tiene violaciones WCAG 2.2 AA", async ({ page }) => {
  await page.goto("/no-existe");
  await expect(page.getByText("Página no encontrada")).toBeVisible();

  const { violations } = await new AxeBuilder({ page }).withTags(WCAG_TAGS).analyze();

  expect(summarize(violations)).toEqual([]);
});
