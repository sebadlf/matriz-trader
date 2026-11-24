const LOCALE = "es-AR";

const cache = new Map<string, Intl.NumberFormat>();

/** Devuelve un `Intl.NumberFormat` reutilizado por combinación de decimales mínimos y máximos. */
const formatter = (min: number, max: number): Intl.NumberFormat => {
  const key = `${min}:${max}`;
  const cached = cache.get(key);
  if (cached) {
    return cached;
  }
  const created = new Intl.NumberFormat(LOCALE, {
    minimumFractionDigits: min,
    maximumFractionDigits: max,
    // Coincide con ROUND_HALF_EVEN del backend (app/domain/numeric.py).
    roundingMode: "halfEven",
  });
  cache.set(key, created);
  return created;
};

/**
 * Guard para pasarle el string tal cual a Intl (sin convertirlo a `float`, así no pierde precisión).
 * `Number(value)` solo se usa para validar, no para formatear.
 */
const isNumericLiteral = (value: string): value is Intl.StringNumericLiteral =>
  value.trim() !== "" && !Number.isNaN(Number(value));

/** Un string no numérico se formatea como `"NaN"`: la API garantiza strings decimales. */
const toFormattable = (value: string): Intl.StringNumericLiteral | number =>
  isNumericLiteral(value) ? value : Number.NaN;

/**
 * Formatea un precio con exactamente `decimals` decimales.
 * `value` es el string decimal de la API; Intl lo formatea sin pasar por `float`.
 */
export const formatPrice = (value: string, decimals: number): string =>
  formatter(decimals, decimals).format(toFormattable(value));

/** Formatea una cantidad con hasta `maxDecimals` decimales, sin ceros finales. */
export const formatQuantity = (value: string, maxDecimals: number): string =>
  formatter(0, maxDecimals).format(toFormattable(value));
