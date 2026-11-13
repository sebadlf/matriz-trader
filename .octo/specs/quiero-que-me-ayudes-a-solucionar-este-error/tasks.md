# Tasks — Quiero que me ayudes a solucionar este error

### Wave 1

- [x] T1: Realinear la contraseña del rol en el volumen local `matriz-trader_pgdata` con `docker compose up -d postgres` + `ALTER ROLE CURRENT_USER WITH PASSWORD :'pw'` por socket local, y relanzar `docker compose up --build` — _outcome: `backend` y `frontend` quedan `healthy`, `/health` responde 200 y las tablas existentes siguen presentes, confirmando la hipótesis (AC-1, AC-5, AC-13)_
- [x] T2: Implementar en `backend/src/backend/health.py` `probe_database`, `describe_db_error`, `DatabaseStatusTracker` y el nuevo `get_db_probe`, y en `backend/src/backend/main.py` `configure_logging` + `app.state.db_probe` + la llamada en `_default_app` — _outcome: con la base inaccesible el backend emite un único `ERROR` `Database unavailable: <tipo>: <mensaje>` sin contraseña ni URL y un `INFO` al recuperarse, con `/health` respondiendo igual que antes (AC-2, AC-3, AC-6, AC-7)_
- [x] T3: Agregar el comentario sobre `POSTGRES_PASSWORD` en `.env.example`, la sección `## Credenciales de Postgres y el volumen pgdata` en `CLAUDE.md` raíz y actualizar la línea de `health.py` en `backend/CLAUDE.md` — _outcome: los greps de AC-4 encuentran la advertencia, el comando `ALTER ROLE CURRENT_USER` y `down -v` con aviso de pérdida de datos (AC-4, AC-16)_

### Wave 2 (depends on T2)

- [x] T4: Agregar a `backend/tests/test_health.py` los tests del tracker (primer fallo, fallo repetido, recuperación, primer éxito silencioso), de `describe_db_error` con contraseña centinela y de `configure_logging` idempotente — _outcome: `cd backend && uv run pytest` pasa con los tests nuevos y los existentes intactos (AC-2, AC-3, AC-6, AC-7, AC-12)_

### Wave 3 (depends on T1, T3, T4)

- [x] T5: Correr `scripts/check.sh`, `git diff --exit-code frontend/openapi.json docker-compose.yml` y, con el stack levantado, `uv run pytest e2e` — _outcome: los tres comandos salen 0 (AC-6, AC-8, AC-9, AC-10, AC-11, AC-14, AC-15)_
- [x] T6: Reconstruir el backend (`docker compose up --build -d backend`), desalinear temporalmente la contraseña del rol (`ALTER ROLE` a un valor distinto) y luego restaurarla con el comando documentado en `CLAUDE.md` — _outcome: `docker compose logs backend` muestra exactamente un `ERROR … password authentication failed for user "matriz"` sin la contraseña y luego un `INFO Database connection restored`, y el stack vuelve a `healthy` (AC-2, AC-3, AC-4, AC-5)_
