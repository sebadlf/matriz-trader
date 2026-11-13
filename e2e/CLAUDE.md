# CLAUDE.md — e2e

Tests de integración con pytest + Playwright (Python), miembro del workspace `uv` (`matriz-e2e`). Corren en Chromium headless contra el frontend servido.

- `tests/conftest.py` — fixture `base_url`: `E2E_BASE_URL` del entorno, luego del `.env` raíz, luego `http://localhost:8080`.
- `tests/test_health_page.py` — abre `/health` y verifica `health-status` y `health-database` = `ok`; depende de los `data-testid` de `frontend/src/pages/HealthPage.tsx`.
- `tests/test_navigation.py` — `/` redirige a `/orders` (`page-ordenes`); clic en `menu-strategies` navega a `/strategies` sin recargar el documento; la carga directa de `/strategies` responde 200 y muestra `page-estrategias` y `app-menu`. Contrato de `data-testid` en `frontend/CLAUDE.md`.

## Comandos (desde la raíz del repo)

```bash
uv run playwright install chromium               # una sola vez
docker compose up --build -d                     # el stack tiene que estar levantado
uv run pytest e2e
```

Con una `E2E_BASE_URL` inalcanzable la suite falla con exit ≠ 0.

No está en `scripts/check.sh`, porque necesita el stack levantado.
