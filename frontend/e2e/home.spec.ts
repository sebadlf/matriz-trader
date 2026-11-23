import { expect, test } from "@playwright/test";

// El e2e no depende del backend ni de PostgreSQL: `/api/health` se mockea.
test.beforeEach(async ({ page }) => {
  await page.route("**/api/health", (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      json: { status: "ok", service: "matriz-trader-backend", version: "0.1.0" },
    }),
  );
});

test("la home muestra el estado del backend", async ({ page }) => {
  await page.goto("/");

  await expect(page.getByText("matriz-trader")).toBeVisible();
  await expect(page.getByText("Backend: ok")).toBeVisible();
});

test("una ruta inexistente muestra la pantalla 404", async ({ page }) => {
  await page.goto("/no-existe");

  await expect(page.getByText("404", { exact: true })).toBeVisible();
  await expect(page.getByText("Página no encontrada")).toBeVisible();
  await expect(page.getByRole("link", { name: "Volver al inicio" })).toBeVisible();
});
