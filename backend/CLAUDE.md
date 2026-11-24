# CLAUDE.md — backend

Convenciones del backend de `matriz-trader`. El contexto general, la Definición de terminado y la checklist están en el [`CLAUDE.md` de la raíz](../CLAUDE.md). Cuando una regla la hace cumplir una herramienta, la línea termina con «— lo verifica `<herramienta>`».

## 1. Comandos (desde `backend/`)

```bash
uv sync                                       # crea .venv e instala todo (requiere acceso SSH a market-libs)
uv run python -m app --reload                 # servidor de desarrollo en :8000
uv run ruff check .                           # lint
uv run ruff format --check .                  # formato (sin --check, formatea)
uv run mypy .                                 # tipado strict
uv run lint-imports                           # contratos de capas (import-linter)
uv run pytest                                 # tests + cobertura (sin PostgreSQL)
uv run pytest -m db --no-cov                  # tests contra PostgreSQL 17 con testcontainers (requiere Docker)
uv run alembic revision --autogenerate -m "<descripción>"   # nueva migración
uv run python -m app.scripts.export_openapi   # regenera backend/openapi.json
```

Para correr todo junto usá `scripts/gate.sh backend` y `scripts/gate.sh migrations` desde la raíz. `python -m app` valida la configuración antes de levantar uvicorn: si falta una variable obligatoria o es inválida, sale con código 1 y el mensaje `Configuración inválida: <VARIABLE>`.

## 2. Estructura y capas

```
backend/
├── app/
│   ├── __main__.py          # entrypoint: python -m app [--reload]; configura logging antes de uvicorn
│   ├── main.py              # create_app(), lifespan, middlewares y handlers de error
│   ├── scripts/             # export_openapi.py → backend/openapi.json
│   ├── api/
│   │   ├── router.py        # api_router con prefijo /api y PROBLEM_RESPONSES
│   │   ├── routes/          # un módulo por grupo de endpoints (health.py)
│   │   ├── deps.py          # SessionDep, ClockDep: única puerta de la API a la DB
│   │   ├── errors.py        # handlers RFC 9457 y PROBLEM_RESPONSES
│   │   └── middleware.py    # AccessLogMiddleware
│   ├── services/            # lógica de aplicación: orquesta dominio, DB y clientes externos
│   ├── db/                  # base.py (Base, TimestampMixin), session.py (engine, get_session)
│   ├── schemas/             # modelos Pydantic de request/response (health.py, problem.py)
│   ├── domain/              # reglas y tipos puros: numeric.py, errors.py
│   └── core/                # config.py (Settings), clock.py, logging.py
├── migrations/              # Alembic (plantilla async); versions/ con las migraciones
├── tests/                   # pytest (conftest.py con test_env, client y restore_logging)
├── alembic.ini
├── .squawk.toml             # reglas de Squawk para el SQL de las migraciones
├── openapi.json             # GENERADO y versionado: input de Orval
├── pyproject.toml           # Ruff, mypy, pytest, coverage e import-linter
└── uv.lock
```

- Las capas, de arriba hacia abajo, son `app.scripts` → `app.main` → `app.api` → `app.services` → `app.db | app.schemas` → `app.domain` → `app.core`. Una capa solo importa de las de abajo — lo verifica `lint-imports` (contrato «Capas»).
- `app.domain` no importa `fastapi`, `sqlalchemy`, `httpx` ni `matriz_client`: el dominio es Python puro y se prueba sin infraestructura — lo verifica `lint-imports` (contrato «Dominio puro»).
- `app.api` no importa `app.db` ni `sqlalchemy`, salvo `app/api/deps.py` para la sesión. Las rutas reciben `SessionDep` y delegan en `app.services` — lo verifica `lint-imports` (contrato «API sin acceso directo a la DB»).
- Los contratos de import-linter y los grupos de Ruff no se pueden quitar — lo verifica `tests/test_tooling.py`.
- `create_app()` no lee `Settings`: importar `app.main` (tests, export del OpenAPI) no requiere `.env` ni base de datos. La configuración, el logging y el engine se crean en el `lifespan`.
- Los endpoints nuevos van en `app/api/routes/<grupo>.py` y se registran en `app/api/router.py`. Los esquemas van en `app/schemas/`. Los modelos ORM heredan de `app.db.base.Base`. La lógica que no sea traducir HTTP va en `app/services/`.

## 3. Convenciones

- **Tipado completo.** Toda función anota parámetros y retorno, también en `tests/` — lo verifica Ruff (`ANN`, sin excepciones; `test_tooling.py` lo protege).
- **mypy `strict`** con el plugin `pydantic.mypy` y **sin** el plugin de SQLAlchemy — lo verifica `mypy`. Los modelos ORM se tipan con `Mapped[...]` y `mapped_column()`; nunca `Column(...)`.
- Ruff tiene activos, además de los grupos base, `ASYNC`, `FAST`, `S`, `DTZ`, `BLE`, `TRY`, `T20`, `ERA`, `PT`, `PIE`, `RET`, `C4`, `PTH`, `LOG`, `G`, `PERF`, `TC`, `ARG`, `FURB`, `TID`, `PL`, `C90` y `FBT`. Cada regla ignorada en `pyproject.toml` lleva un comentario que la justifica — lo verifica `test_tooling.py`.
- **`operation_id` explícito y `tags` en cada ruta** (por ejemplo `operation_id="getHealth"`, `tags=["health"]`). De ahí salen los nombres que genera Orval (`getHealth`, `useGetHealth`, `getGetHealthQueryKey`) y el archivo `generated/<tag>/<tag>.ts`.
- **El esquema de respuesta sale de la anotación de retorno** (`-> HealthResponse`, un modelo de `app/schemas/`). Usá `response_model` solo cuando difiere del tipo de retorno — lo verifica Ruff (`FAST001`).
- Dependencias con `Annotated[...]`, no con valores por defecto — lo verifica Ruff (`FAST002`).
- Sin `print`: usá el logger (`structlog.get_logger()`) — lo verifica Ruff (`T20`).
- Sin `requests`: usá `httpx.AsyncClient` — lo verifica Ruff (`TID251`). Sin llamadas bloqueantes dentro de `async def` (`time.sleep`, I/O síncrono) — lo verifica Ruff (`ASYNC`).
- Sin `except Exception` que trague errores: atrapá excepciones concretas o dejá que suban al handler de 500 — lo verifica Ruff (`BLE`, `TRY`).
- La configuración se lee solo a través de `Settings` (`get_settings()`); no uses `os.environ` directamente.

## 4. Dominio: números y tiempo

- **Precios, cantidades y montos son `Decimal`, nunca `float`.** Usá los tipos de `app/domain/numeric.py`: `Price`, `Quantity` y `Money` (`Annotated[Decimal, ...]`, se serializan como string en JSON). Un campo de esquema cuyo nombre contenga `price`, `qty`, `quantity`, `amount`, `notional`, `money`, `pnl` o `balance` tiene que ser `Decimal` — lo verifica `tests/test_domain_types.py`.
- Las columnas monetarias son `Numeric(precision, scale)` con `asdecimal=True`, nunca `Float` — lo verifica `tests/test_domain_types.py`.
- Las operaciones usan `DECIMAL_CONTEXT` (`ROUND_HALF_EVEN`). El redondeo a tick se hace con `round_to_tick(price, tick)` — lo verifica `tests/test_numeric.py` (Hypothesis: idempotencia, conmutatividad y serialización sin pérdida).
- **Toda fecha tiene zona horaria y está en UTC.** Prohibidos `datetime.utcnow()` y `datetime.now()` sin `tz` — lo verifica Ruff (`DTZ`, `TID251`).
- La hora actual se obtiene del `Clock` inyectable (`app/core/clock.py`): en las rutas, con `ClockDep`; en los tests, con `app.dependency_overrides[get_clock]`. No llames a `datetime.now(UTC)` en lógica de negocio que haya que testear.

## 5. Errores y observabilidad

- Todo error HTTP responde `application/problem+json` con un cuerpo RFC 9457 (`ProblemDetails` de `app/schemas/problem.py`: `type`, `title`, `status`, `detail`, `instance`, `correlation_id` y `errors` en las validaciones) — lo verifica `tests/test_errors.py`.
- Las reglas de negocio violadas se lanzan como subclases de `DomainError` (`app/domain/errors.py`) con `status` y `title` propios; no lances `HTTPException` desde `services/` ni `domain/`.
- Un 500 nunca expone el traceback: se loguea con `exc_info` y el cliente recibe el `correlation_id`.
- `PROBLEM_RESPONSES` está declarado en `api_router`, así que toda ruta publica `ProblemDetails` en el OpenAPI y Orval lo tipa. Si una ruta devuelve otro código de error (409, 403…), agregalo a su `responses=`.
- Los logs son estructurados con structlog: JSON con `APP_ENV=production` y formato de consola en otro caso. Cada request emite un evento `request` y todo log lleva `correlation_id` — lo verifica `tests/test_logging.py`.
- El `correlation_id` viaja en el header `X-Request-ID`: se reutiliza el del request si es un UUID válido y se genera uno si no.
- Los valores `SecretStr` y las claves que contienen `password`, `token`, `secret` o `api_key` se reemplazan por `"***"` antes de loguear — lo verifica `tests/test_logging.py`. No loguees credenciales del broker con otro nombre de clave.

## 6. Base de datos y migraciones

- Las sesiones se obtienen con `SessionDep` (`app/api/deps.py`), que usa `app.state.session_factory` creado en el `lifespan`.
- Todo cambio de modelos ORM lleva su migración en `migrations/versions/` (Alembic, plantilla async; la URL sale de `Settings`). Los modelos sin migración hacen fallar `alembic check` — lo verifica `scripts/gate.sh migrations` (`tests/test_migrations.py` contra PostgreSQL 17 con testcontainers).
- Las migraciones tienen que ser seguras para PostgreSQL: nada de columnas `NOT NULL` sin default sobre tablas existentes ni operaciones que tomen locks largos. `env.py` fija `lock_timeout` y `statement_timeout` — lo verifica Squawk sobre `alembic upgrade head --sql` (`scripts/gate.sh migrations`).
- Revisá cada migración autogenerada antes de commitearla: Alembic no detecta renombres y los toma como borrado más alta.

## 7. Tests

- Van en `tests/test_<tema>.py` y corren en orden aleatorio, con los warnings como errores — lo verifican pytest-randomly y `filterwarnings = ["error"]`.
- La cobertura de branches de `app/` no baja del 85 % — lo verifica pytest-cov (`fail_under = 85`).
- Los endpoints se prueban con el fixture `client` (`httpx.AsyncClient` + `ASGITransport`, que no ejecuta el `lifespan`, así que no hace falta PostgreSQL). El fixture autouse `test_env` define un `DATABASE_URL` de prueba.
- Toda respuesta cumple el `openapi.json` versionado — lo verifica `tests/test_contract.py` (Schemathesis contra la app ASGI).
- `openapi.json` coincide con `create_app().openapi()` — lo verifica `tests/test_openapi_export.py`.
- Los tests que necesitan PostgreSQL real se marcan con `@pytest.mark.db`; `uv run pytest` los excluye y los corre `scripts/gate.sh migrations`.
- `test_tooling.py` verifica que las libs de `market-libs` se importan y que las reglas de Ruff, los contratos de import-linter y el umbral de cobertura siguen activos; no lo debilites.
- Todo bug corregido incluye un test que lo reproduce.

## 8. Reglas obligatorias para la primera feature que envíe órdenes

Hoy ningún código envía órdenes. La primera feature que lo haga tiene que incluir, en el mismo PR, todo lo siguiente. Ninguna de estas reglas se puede posponer para «una próxima iteración».

1. **Idempotencia con `client_order_id`.** Cada orden lleva un `client_order_id` único generado por el sistema antes del envío, guardado en una columna con constraint `UNIQUE`. Un reintento reutiliza el mismo id; un duplicado se rechaza en la base, no solo en el código.
2. **Controles de riesgo previos al envío.** Antes de llamar a Matriz, un servicio de `app/services/` valida como mínimo: cantidad máxima por orden, notional máximo por orden, posición máxima por instrumento y órdenes por segundo. Los límites son configurables (`Settings` o tabla) y una orden que no los cumple se rechaza con una subclase de `DomainError`, sin llegar al broker.
3. **Kill switch persistido.** Un estado guardado en la base que, activado, bloquea todo envío de órdenes, manual o algorítmico. Se consulta en cada envío, sobrevive a reinicios y su activación y desactivación quedan auditadas.
4. **Auditoría de solo inserción.** Una tabla de auditoría de órdenes donde cada evento (creada, enviada, rechazada por riesgo, aceptada, ejecutada, cancelada, error) es una fila nueva, con `correlation_id`, `client_order_id` y fecha UTC. La aplicación nunca hace `UPDATE` ni `DELETE` sobre esa tabla.
5. **Rate limiting hacia Matriz.** Todas las llamadas a `matriz-client` pasan por un único punto con límite de requests por segundo y backoff ante errores de cuota, en lugar de llamar al cliente desde distintos servicios.

Además, los precios y cantidades de la orden usan `Price` y `Quantity`, y toda fecha sale del `Clock` (§4).
