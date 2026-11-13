import { ApiError } from '../../api/http';

/** Marcador neutro para campos vacíos (EB-3). */
export const EMPTY = '—';

const numberFormat = new Intl.NumberFormat('es-AR', { maximumFractionDigits: 6 });

export function formatNumber(value: number | null | undefined): string {
  if (value == null || Number.isNaN(value)) {
    return EMPTY;
  }
  return numberFormat.format(value);
}

export function formatText(value: string | null | undefined): string {
  return value == null || value === '' ? EMPTY : value;
}

function detailOf(body: unknown): unknown {
  return typeof body === 'object' && body !== null && 'detail' in body ? body.detail : undefined;
}

function messageOf(item: unknown): string | undefined {
  return typeof item === 'object' && item !== null && 'msg' in item && typeof item.msg === 'string'
    ? item.msg
    : undefined;
}

/** Mensaje legible para un error de la API (EB-5, EB-16, EB-32). */
export function describeApiError(error: unknown): string {
  if (!(error instanceof ApiError)) {
    return 'El backend no responde';
  }
  const detail = detailOf(error.body);
  if (typeof detail === 'string' && detail !== '') {
    return detail;
  }
  if (Array.isArray(detail)) {
    const messages = detail.map(messageOf).filter((msg): msg is string => msg !== undefined);
    if (messages.length > 0) {
      return messages.join('; ');
    }
  }
  return `HTTP ${error.status}`;
}
