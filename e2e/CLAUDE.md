# CLAUDE.md — e2e

Tests de integración con pytest + Playwright (Python), miembro del workspace `uv` (`matriz-e2e`). Abren la página raíz del frontend en Chromium headless y verifican `health-status` y `health-database` = `ok`.

- `tests/conftest.py` — fixture `base_url`: `E2E_BASE_URL` del entorno, luego del `.env` raíz, luego `http://localhost:8080`.
- `tests/test_health_page.py` — depende de los `data-testid` de `frontend/src/pages/HealthPage.tsx`.

## Comandos (desde la raíz del repo)

```bash
uv run playwright install chromium               # una sola vez
docker compose up --build -d                     # el stack tiene que estar levantado
uv run pytest e2e
```

Con una `E2E_BASE_URL` inalcanzable la suite falla con exit ≠ 0.

No está en `scripts/check.sh`, porque necesita el stack levantado.
