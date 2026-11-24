import { expect, type Page, test } from "@playwright/test";

import { mockMarketData, symbolAt } from "./marketData";

// `/api/market-data` se mockea: no depende del backend ni del servicio de market data.
const ROW_COUNT = 500;

test.beforeEach(async ({ page }) => {
  await mockMarketData(page, ROW_COUNT);
});

/** Filas de datos de la tabla: las que tienen una celda con un símbolo del fixture. */
const dataRows = (page: Page) =>
  page.getByRole("row").filter({ has: page.getByRole("cell", { name: /^INS\d{4}$/ }) });

test("muestra una fila por instrumento con las 500 filas mockeadas (AC-11)", async ({ page }) => {
  await page.goto("/market-data");

  await expect(page.getByRole("heading", { name: "Market data" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Spread %" })).toBeVisible();
  await expect(dataRows(page)).toHaveCount(ROW_COUNT);
  await expect(page.getByRole("cell", { name: symbolAt(ROW_COUNT - 1) })).toBeAttached();
});

test("aplica el filtro de símbolo que viene en la URL (AC-15, AC-18)", async ({ page }) => {
  await page.goto(`/market-data?symbol=${symbolAt(42).toLowerCase()}`);

  await expect(page.getByRole("textbox", { name: "Filtrar por símbolo" })).toHaveValue(
    symbolAt(42).toLowerCase(),
  );
  await expect(dataRows(page)).toHaveCount(1);
  await expect(page.getByRole("cell", { name: symbolAt(42) })).toBeVisible();
});

test("escribir en el filtro de símbolo actualiza la URL (AC-15, AC-18)", async ({ page }) => {
  await page.goto("/market-data");
  await expect(dataRows(page)).toHaveCount(ROW_COUNT);

  await page.getByRole("textbox", { name: "Filtrar por símbolo" }).fill("ins001");

  await expect(page).toHaveURL(/[?&]symbol=ins001(&|$)/);
  // INS0010 … INS0019
  await expect(dataRows(page)).toHaveCount(10);
});

test("sin coincidencias, 'Limpiar filtros' vuelve a mostrar todas las filas (AC-19)", async ({
  page,
}) => {
  await page.goto("/market-data?symbol=no-existe&market=ROFX");

  await expect(page.getByText("Ningún instrumento coincide con los filtros")).toBeVisible();
  await expect(dataRows(page)).toHaveCount(0);

  await page.getByRole("button", { name: "Limpiar filtros" }).click();

  await expect(dataRows(page)).toHaveCount(ROW_COUNT);
  await expect(page).not.toHaveURL(/[?&](symbol|market)=/);
});
