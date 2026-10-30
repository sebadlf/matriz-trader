import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HealthPage } from './HealthPage';

function renderPage() {
  const client = new QueryClient({ defaultOptions: { queries: { retry: false } } });
  render(
    <QueryClientProvider client={client}>
      <HealthPage />
    </QueryClientProvider>,
  );
}

function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  });
}

describe('HealthPage', () => {
  afterEach(() => {
    vi.unstubAllGlobals();
  });

  it('muestra el indicador de carga mientras la petición está en curso', () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(() => new Promise<Response>(() => undefined)),
    );

    renderPage();

    expect(screen.getByTestId('health-loading')).toBeInTheDocument();
  });

  it('muestra status y database ok', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(200, { status: 'ok', database: 'ok' })),
    );

    renderPage();

    expect(await screen.findByTestId('health-status')).toHaveTextContent('ok');
    expect(screen.getByTestId('health-database')).toHaveTextContent('ok');
  });

  it('muestra un error cuando el backend responde 503', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn(async () => jsonResponse(503, { status: 'degraded', database: 'unavailable' })),
    );

    renderPage();

    const alert = await screen.findByTestId('health-error');
    expect(alert).toHaveTextContent('No se pudo obtener el estado del backend');
    expect(alert).toHaveTextContent('HTTP 503 — database: unavailable');
  });
});
