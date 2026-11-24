import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { formatPrice, formatQuantity } from "./format";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("formatPrice", () => {
  it("formatea con separadores de es-AR y decimales fijos", () => {
    expect(formatPrice("1234.5", 2)).toBe("1.234,50");
  });

  it("no pierde precisión con 18 dígitos significativos", () => {
    expect(formatPrice("123456789012345678", 0)).toBe("123.456.789.012.345.678");
    expect(formatPrice("1234567890.12345678", 8)).toBe("1.234.567.890,12345678");
  });

  it("redondea al par más cercano (half-even)", () => {
    expect(formatPrice("0.125", 2)).toBe("0,12");
    expect(formatPrice("0.135", 2)).toBe("0,14");
  });
});

describe("formatQuantity", () => {
  it("omite los ceros finales hasta el máximo de decimales", () => {
    expect(formatQuantity("10", 4)).toBe("10");
    expect(formatQuantity("1500.25", 4)).toBe("1.500,25");
  });

  it("devuelve NaN ante un string no numérico", () => {
    expect(formatQuantity("abc", 2)).toBe("NaN");
  });
});

describe("cache de formatters", () => {
  it("reutiliza la instancia de Intl.NumberFormat para los mismos decimales", () => {
    const spy = vi.spyOn(Intl, "NumberFormat");

    formatPrice("1", 7);
    formatPrice("2", 7);
    formatQuantity("3", 7);

    // formatPrice(…, 7) usa la clave 7:7 y formatQuantity(…, 7) la clave 0:7.
    expect(spy).toHaveBeenCalledTimes(2);
  });
});
