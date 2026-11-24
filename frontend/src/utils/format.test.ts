import { afterEach, describe, expect, it, vi } from "vite-plus/test";

import { formatPercent, formatPrice, formatQuantity, formatTime } from "./format";

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

describe("formatPercent", () => {
  it("muestra 2 decimales y el signo %, redondeando half-even", () => {
    expect(formatPercent("0.1250")).toBe("0,12%");
    expect(formatPercent("0.1350")).toBe("0,14%");
    expect(formatPercent("12.3456")).toBe("12,35%");
  });

  it("conserva el signo de un spread negativo (libro cruzado)", () => {
    expect(formatPercent("-0.9950")).toBe("-1,00%");
    expect(formatPercent("-0.9940")).toBe("-0,99%");
  });

  it("formatea desde el string sin pasar por number (no pierde precisión)", () => {
    // Como float, 12345678901234567.125 se redondearía a 12345678901234568.
    expect(formatPercent("12345678901234567.125")).toBe("12.345.678.901.234.567,12%");
  });
});

describe("formatTime", () => {
  it("formatea epoch en milisegundos como hora local HH:mm:ss", () => {
    const epochMs = new Date(2026, 10, 24, 14, 3, 11).getTime();
    expect(formatTime(epochMs)).toBe("14:03:11");
  });

  it("formatea un ISO 8601 con zona horaria", () => {
    const iso = new Date(2026, 10, 24, 9, 5, 7).toISOString();
    expect(formatTime(iso)).toBe("09:05:07");
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
