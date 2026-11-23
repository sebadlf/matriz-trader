// Único punto del frontend que hace `fetch` (AC-25). Todo cliente generado por Orval pasa por acá.

export class ApiError<TBody = unknown> extends Error {
  readonly status: number;
  readonly body: TBody;

  constructor(status: number, body: TBody) {
    super(`HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
  }
}

/** Tipo de error que Orval usa para tipar `error` en los hooks generados. */
export type ErrorType<TBody> = ApiError<TBody>;

/** Mismo origen: el proxy de Vite (dev) o nginx (prod) reenvían `/api` al backend. */
const BASE_URL = "";

const parseBody = async (response: Response): Promise<unknown> => {
  if (response.status === 204) return undefined;
  const text = await response.text();
  if (!text) return undefined;
  const contentType = response.headers.get("content-type") ?? "";
  return contentType.includes("json") ? JSON.parse(text) : text;
};

export const customFetch = async <T>(url: string, init?: RequestInit): Promise<T> => {
  const response = await fetch(`${BASE_URL}${url}`, init);
  const body = await parseBody(response);

  if (!response.ok) {
    throw new ApiError(response.status, body);
  }

  return { data: body, status: response.status, headers: response.headers } as T;
};
