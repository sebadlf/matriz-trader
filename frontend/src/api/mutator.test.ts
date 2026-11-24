import { http, HttpResponse } from "msw";
import { describe, expect, it } from "vite-plus/test";

import type { ProblemDetails } from "@/api/generated/model";
import { server } from "@/test/server";

import { ApiError, customFetch } from "./mutator";

const URL = "/api/health";

const captureError = async (): Promise<unknown> => {
  try {
    await customFetch(URL);
  } catch (error) {
    return error;
  }
  throw new Error("customFetch debía lanzar un error");
};

describe("customFetch", () => {
  it("devuelve data, status y headers cuando la respuesta es ok", async () => {
    server.use(http.get(`*${URL}`, () => HttpResponse.json({ status: "ok" })));

    const result = await customFetch<{ data: unknown; status: number }>(URL);

    expect(result.status).toBe(200);
    expect(result.data).toEqual({ status: "ok" });
  });

  it("convierte un 500 application/problem+json en ApiError con title, detail y correlationId", async () => {
    const problem: ProblemDetails = {
      type: "about:blank",
      title: "Error interno",
      status: 500,
      detail: "Falló la consulta a Matriz",
      instance: URL,
      correlation_id: "3f2b1c9e-8d4a-4b6f-9a1e-2c7d5e8f0a1b",
    };
    server.use(
      http.get(`*${URL}`, () =>
        HttpResponse.json(problem, {
          status: 500,
          headers: { "content-type": "application/problem+json" },
        }),
      ),
    );

    const error = await captureError();

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      name: "ApiError",
      message: "Error interno",
      status: 500,
      title: "Error interno",
      detail: "Falló la consulta a Matriz",
      correlationId: "3f2b1c9e-8d4a-4b6f-9a1e-2c7d5e8f0a1b",
      body: problem,
    });
  });

  it("normaliza a undefined los opcionales que el backend manda como null", async () => {
    server.use(
      http.get(`*${URL}`, () =>
        HttpResponse.json(
          { title: "No encontrado", status: 404, detail: null, correlation_id: null },
          { status: 404, headers: { "content-type": "application/problem+json" } },
        ),
      ),
    );

    const error = await captureError();

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({ status: 404, title: "No encontrado" });
    expect(error).toHaveProperty("detail", undefined);
    expect(error).toHaveProperty("correlationId", undefined);
  });

  it("deja title, detail y correlationId en undefined ante un 502 que no es JSON", async () => {
    server.use(
      http.get(
        `*${URL}`,
        () =>
          new HttpResponse("<html><body>502 Bad Gateway</body></html>", {
            status: 502,
            headers: { "content-type": "text/html" },
          }),
      ),
    );

    const error = await captureError();

    expect(error).toBeInstanceOf(ApiError);
    expect(error).toMatchObject({
      message: "HTTP 502",
      status: 502,
      body: "<html><body>502 Bad Gateway</body></html>",
    });
    expect(error).toHaveProperty("title", undefined);
    expect(error).toHaveProperty("detail", undefined);
    expect(error).toHaveProperty("correlationId", undefined);
  });
});
