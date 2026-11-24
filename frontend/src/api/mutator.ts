// Único punto del frontend que hace `fetch` (AC-25). Todo cliente generado por Orval pasa por acá.

import type { ProblemDetails } from "@/api/generated/model";

/** Cuerpo RFC 9457 que devuelve el backend en toda respuesta de error (AC-48). */
const isProblemDetails = (body: unknown): body is ProblemDetails =>
  typeof body === "object" &&
  body !== null &&
  "title" in body &&
  typeof body.title === "string" &&
  "status" in body &&
  typeof body.status === "number";

export class ApiError<TBody = unknown> extends Error {
  readonly status: number;
  readonly body: TBody;
  /** `title` del `ProblemDetails`; `undefined` si el cuerpo no es RFC 9457 (p. ej. un 502 HTML). */
  readonly title: string | undefined;
  readonly detail: string | undefined;
  /** Mismo valor que el header `X-Request-ID`: permite seguir el error en los logs del backend. */
  readonly correlationId: string | undefined;

  constructor(status: number, body: TBody) {
    const problem = isProblemDetails(body) ? body : undefined;
    super(problem?.title ?? `HTTP ${status}`);
    this.name = "ApiError";
    this.status = status;
    this.body = body;
    this.title = problem?.title;
    // El backend serializa los opcionales ausentes como `null`; se normalizan a `undefined`.
    this.detail = problem?.detail ?? undefined;
    this.correlationId = problem?.correlation_id ?? undefined;
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

  // Contrato del mutator de Orval: `T` es la unión `{ data, status, headers }` que el cliente
  // generado declara para cada operación; el cuerpo no se valida en runtime, se confía en el
  // contrato de `backend/openapi.json` (verificado por `test_openapi_export.py`).
  // oxlint-disable-next-line typescript/no-unsafe-type-assertion -- ver comentario anterior
  return { data: body, status: response.status, headers: response.headers } as T;
};
