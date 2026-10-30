// Mutator de Orval: agrega la URL base, un timeout y convierte respuestas no-2xx en `ApiError` (AC-8).

export class ApiError extends Error {
  readonly status: number;
  readonly body: unknown;

  constructor(status: number, body: unknown) {
    super(`HTTP ${status}`);
    this.name = 'ApiError';
    this.status = status;
    this.body = body;
  }
}

export const REQUEST_TIMEOUT_MS = 5000;

async function readBody(res: Response): Promise<unknown> {
  const text = await res.text();
  if (!text) {
    return null;
  }
  try {
    return JSON.parse(text);
  } catch {
    return null;
  }
}

export async function customFetch<T>(url: string, options: RequestInit): Promise<T> {
  const signals = [options.signal, AbortSignal.timeout(REQUEST_TIMEOUT_MS)].filter(
    (signal): signal is AbortSignal => signal != null,
  );
  const res = await fetch(`${import.meta.env.VITE_API_BASE_URL ?? ''}${url}`, {
    ...options,
    signal: AbortSignal.any(signals),
  });
  const body = await readBody(res);
  if (!res.ok) {
    throw new ApiError(res.status, body);
  }
  return { data: body, status: res.status, headers: res.headers } as T;
}
