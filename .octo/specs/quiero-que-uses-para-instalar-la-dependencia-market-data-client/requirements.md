# Requirements — Integrar `market-data-client` como única fuente de market data

## Introducción

Hoy el `worker` depende de `matriz-client` 0.3.0 (wheel de GitHub Releases) y lo usa para autenticarse contra Matriz (`worker/src/worker/matriz_gateway.py`). Este feature incorpora la librería `market-data-client`, instalada desde Git con `uv add`, la deja configurada y lista para usar en el workspace `uv`, y establece como decisión de arquitectura que **toda obtención de market data se hace con `market-data-client`, nunca con `matriz-client`**. La decisión queda escrita en `CLAUDE.md`.

Estado verificado del repo al redactar:

- `worker/pyproject.toml` declara `matriz-client==0.3.0` vía `[tool.uv.sources]` (URL de wheel).
- `worker/Dockerfile` parte de `python:3.13-slim`, que **no trae `git`**, y ejecuta `uv sync --frozen`.
- Pyright corre en modo strict con `stubPath = "stubs"` (el directorio `stubs/` aún no existe).
- El repo `gravity-quant/market-data-client` no es resoluble con las credenciales actuales de `gh` (no existe o es privado): la `<org>` del comando sigue sin confirmar.

## User Stories

- **US-1**: Como desarrollador, quiero que `market-data-client` se instale con exactamente `uv add "market-data-client @ git+https://github.com/<org>/market-data-client.git"`, para que la dependencia quede declarada y bloqueada en el workspace `uv` igual que el resto.
- **US-2**: Como desarrollador, quiero que el proyecto quede configurado para usar la librería (settings, `.env.example`, tipado y build de Docker), para poder importarla y ejecutarla en dev y en producción sin pasos manuales extra.
- **US-3**: Como desarrollador, quiero un único punto de acceso tipado a `market-data-client` en el `worker`, para que el resto del código obtenga market data sin acoplarse a la librería y se pueda testear sin red.
- **US-4**: Como cualquier persona (o agente) que trabaje en el repo, quiero que `CLAUDE.md` deje asentado que el market data se obtiene siempre con `market-data-client` y nunca con `matriz-client`, para que la decisión no se pierda ni se revierta por accidente.

## Acceptance Criteria (EARS)

### Instalación (US-1)

- AC-1: WHEN se instala la dependencia THEN el sistema SHALL haberla agregado ejecutando `uv add "market-data-client @ git+https://github.com/<org>/market-data-client.git"` desde `worker/` (o con `--package matriz-worker` desde la raíz), con `<org>` reemplazado por la organización confirmada, sin editar `pyproject.toml` ni `uv.lock` a mano. (US-1)
- AC-2: WHEN termina `uv add` THEN `worker/pyproject.toml` SHALL listar `market-data-client` en `[project].dependencies` y SHALL declarar su origen Git en `[tool.uv.sources]`, y el `pyproject.toml` raíz SHALL quedar sin esa dependencia. (US-1)
- AC-3: WHEN termina `uv add` THEN `uv.lock` SHALL contener una entrada para `market-data-client` fijada a un commit concreto (SHA de 40 caracteres en la URL Git). (US-1)
- AC-4: WHEN se ejecuta `uv sync --frozen` sobre un checkout limpio THEN el comando SHALL salir con código 0 y `uv run python -c "import <módulo de market-data-client>"` SHALL salir con código 0. (US-1)
- AC-5: IF el repositorio de `market-data-client` es privado THEN el sistema SHALL documentar en `worker/CLAUDE.md` cómo autenticarse para `uv sync` (local y en Docker) sin commitear tokens en `pyproject.toml`, `uv.lock`, `Dockerfile` ni `.env.example`. (US-1)

### Configuración del proyecto (US-2)

- AC-6: IF `market-data-client` requiere parámetros de configuración (URL, credenciales, timeouts u otros, según su documentación) THEN el sistema SHALL exponerlos como campos de `WorkerSettings` leídos del `.env` raíz, y SHALL agregarlos a `.env.example` con valores de ejemplo no secretos y un comentario por variable. (US-2)
- AC-7: IF falta en el entorno alguna variable obligatoria de `market-data-client` THEN `uv run python -m worker` SHALL salir con código 2, igual que hoy con las variables `MATRIZ_*`. (US-2)
- AC-8: WHEN se ejecuta `uv run pyright` sin argumentos THEN SHALL reportar 0 errores en modo strict; IF `market-data-client` no publica `py.typed` THEN el sistema SHALL agregar stubs en `stubs/` (ya configurado como `stubPath`) en lugar de usar `# type: ignore` globales. (US-2)
- AC-9: WHEN se ejecuta `docker compose build worker` THEN el build SHALL completar con código 0 instalando `market-data-client` desde Git (incluyendo la instalación de `git` en la imagen si `uv` lo necesita). (US-2)
- AC-10: WHEN se ejecuta `scripts/check.sh` THEN SHALL salir con código 0. (US-2)

### Punto de acceso en el worker (US-3)

- AC-11: THE sistema SHALL tener un único módulo en `worker/src/worker/` que importe `market_data_client` (análogo a `matriz_gateway.py`), y ningún otro módulo del repo SHALL importarlo. (US-3)
- AC-12: THE módulo de AC-11 SHALL exponer un `Protocol` tipado para obtener market data y una implementación concreta que delegue en `market-data-client`, y SHALL traducir las excepciones de la librería a una excepción propia del worker. (US-3)
- AC-13: WHEN arranca el worker con configuración válida THEN el sistema SHALL inicializar el cliente de `market-data-client` a través del módulo de AC-11 y SHALL cerrarlo al recibir SIGINT/SIGTERM antes de salir con código 0. (US-3)
- AC-14: IF la inicialización de `market-data-client` falla THEN el worker SHALL registrar el error en el log y salir con código 1. (US-3)
- AC-15: WHEN se ejecuta `cd worker && uv run pytest` THEN SHALL existir al menos un test que use un fake del `Protocol` de AC-12 (sin red ni credenciales) y cubra el arranque exitoso y el fallo de inicialización. (US-3)
- AC-16: THE código del repo SHALL no llamar a ninguna API de market data de `matriz-client`; `matriz_gateway.py` SHALL conservar únicamente el uso que no es market data (autenticación/conexión actual). (US-3, US-4)

### Decisión en CLAUDE.md (US-4)

- AC-17: THE `CLAUDE.md` raíz SHALL contener, en la sección `## Convenciones`, una regla explícita: "El market data se obtiene siempre con `market-data-client`; nunca con `matriz-client`", indicando el módulo de AC-11 como punto de acceso. (US-4)
- AC-18: THE `worker/CLAUDE.md` SHALL describir `market-data-client` (origen Git, módulo de acceso, variables de entorno) y SHALL repetir la regla de AC-17 junto a la descripción de `matriz-client`. (US-4)
- AC-19: WHEN se busca `market data` en `CLAUDE.md` y `worker/CLAUDE.md` THEN ninguna frase SHALL indicar o sugerir que `matriz-client` es fuente de market data. (US-4)

## Out of Scope

- Suscripciones, streaming o persistencia de market data en PostgreSQL (modelos SQLAlchemy, migraciones Alembic).
- Exponer market data por endpoints del `backend` o mostrarlo en el `frontend` (incluye regenerar `openapi.json`).
- Quitar `matriz-client` del proyecto: sigue siendo dependencia del `worker` para lo que no es market data.
- Agregar `market-data-client` a `backend`, `model` o `e2e`.
- Publicar, versionar o modificar el repositorio de `market-data-client`.
- Tests contra el servicio real de market data (e2e con credenciales).

## Non-Functional Requirements

- NFR-1 (Reproducibilidad): la versión de `market-data-client` SHALL quedar fijada por commit en `uv.lock`; `uv sync --frozen` SHALL producir el mismo entorno en dev y en Docker.
- NFR-2 (Seguridad): ningún token, usuario o contraseña real SHALL aparecer en archivos versionados; los secretos se leen solo del `.env` raíz (convención existente) o de secretos de build de Docker.
- NFR-3 (Calidad): Ruff, Pyright strict y pytest SHALL pasar sin nuevos ignores globales; los ignores puntuales llevan regla (`# pyright: ignore[<regla>]`).
- NFR-4 (Convenciones del monorepo): un único `.env` en la raíz, layout `src/`, sin `.env` por proyecto.

## Preguntas abiertas

1. **`<org>`**: ¿cuál es la organización de GitHub de `market-data-client`? (`gravity-quant/market-data-client` no resuelve con las credenciales actuales de `gh`). Bloquea AC-1 a AC-4.
2. **¿Repo privado?** Si lo es, ¿qué mecanismo de autenticación preferís para `uv sync` en Docker (BuildKit secret con `GH_TOKEN`, deploy key SSH, otro)? Define AC-5 y AC-9.
3. **Configuración de la librería**: ¿qué variables de entorno o parámetros necesita `market-data-client` y cuál es su nombre de módulo importable? Sin acceso al repo no puedo listarlas; AC-6/AC-7 se concretan al leer su README.

## Open Questions
- [x] ¿Cuál es la organización de GitHub de `market-data-client` y a qué ref se fija en `uv add`? — **Resolved:** **`<org>` confirmada + tag de release (`@vX.Y.Z`)**: las actualizaciones quedan explícitas y legibles en `pyproject.toml`, y `uv.lock` igual fija el SHA, así que se cumplen AC-3 y NFR-1 sin el riesgo de la rama por defecto ni el mantenimiento manual de un SHA crudo.
  - `<org>` confirmada + tag de release (`@vX.Y.Z`) — actualizaciones explícitas y legibles; el lock igual fija el SHA
  - `<org>` confirmada + rama por defecto, sin ref — más simple, pero cada `uv lock --upgrade` puede traer cambios incompatibles
  - `<org>` confirmada + SHA concreto (`@<sha>`) — máxima reproducibilidad, pero actualizar es manual y poco legible
- [x] Si el repo es privado, ¿cómo se autentica `uv sync` dentro del build de Docker? — **Resolved:** **Elijo la deploy key SSH vía `--mount=type=ssh` con URL `git+ssh://`.** Es la única opción que mantiene `uv sync --frozen` instalando desde Git y fijado por SHA en `uv.lock` (AC-3, AC-4, AC-9, NFR-1), y no deja tokens en la imagen ni en archivos versionados (NFR-2).

Hay un ajuste para no romper AC-1: no hace falta cambiar a `git+ssh://` en `pyproject.toml`. Se puede dejar la URL `https://` y, solo dentro del build, aplicar `git config url."git@github.com:".insteadOf "https://github.com/"`.
  - Deploy key SSH vía `--mount=type=ssh` con URL `git+ssh://` — no expone un token amplio, pero cambia la URL en `pyproject.toml` y exige un agente SSH en el host
  - Pre-construir el wheel fuera de Docker y copiarlo al contexto — la imagen no necesita `git` ni credenciales, pero rompe el `uv sync --frozen` directo desde Git
- [x] ¿Cómo se instala `git` en la imagen del worker? — **Resolved:** **`apt-get install git` en la única stage actual**: es el cambio mínimo que cumple AC-9 y mantiene `uv sync --frozen` instalando desde Git. Como se eligió la deploy key SSH, también hay que instalar `openssh-client`, y conviene limpiar `/var/lib/apt/lists` para que la imagen no crezca de más.
  - `apt-get install git` en la única stage actual — cambio mínimo, pero la imagen final engorda y conserva `git`
- [x] ¿Qué hace el worker con `market-data-client` al arrancar (AC-13/AC-14)? — **Resolved:** Al arrancar, el worker crea el cliente de `market-data-client` con los campos de `WorkerSettings` a través de la implementación concreta del `Protocol` (AC-11/AC-12). Después hace una única verificación liviana de conectividad (por ejemplo, autenticarse o pedir el estado del servicio, según lo que ofrezca la librería) y registra en el log que el cliente está listo. No se suscribe, no consulta precios ni persiste datos, porque el streaming y la persistencia quedan fuera de alcance. Si la creación o la verificación fallan, la excepción propia del worker se registra en el log y el proceso sale con código 1 (AC-14). Si todo sale bien, el worker queda en su loop actual hasta recibir SIGINT/SIGTERM, cierra el cliente con `close()` y sale con código 0 (AC-13). Así el fake del `Protocol` alcanza para testear ambos caminos sin red (AC-15).
- [x] ¿Qué estilo de interfaz expone el `Protocol` de acceso a market data? — **Resolved:** 🔧 **Grep** `src/worker`worker/src/worker/__main__.py:3:import asyncio
worker/src/worker/__main__.py:36:    return asyncio.run(serve(MatrizClientGateway(settings), settings))
worker/src/worker/runner.py:3:import asyncio
worker/src/worker/runner.py:16:async def _close(gateway: MatrizGateway) -> None:
worker/src/worker/runner.py:18:        await asyncio.wait_for(asyncio.to_thread(gateway.close), CLOSE_TIMEOUT_SECONDS)
worker/src/worker/runner.py:23:async def run(gateway: MatrizGateway, settings: WorkerSettings, stop: asyncio.Event) -> int:
worker/src/worker/runner.py:25:        await asyncio.to_thread(gateway.connect)

… (truncated)**Sincrónico (`def get_quote(...)`, `def close()`).** Es el mismo patrón que ya usa el worker: `MatrizGateway` es un Protocol sincrónico y `runner.py` lo llama con `asyncio.to_thread`. Así el loop async no se bloquea, y el gateway de market data mantiene la misma forma que el que ya existe.
  - Sincrónico (`def get_quote(...)`, `def close()`) — calca la librería si es bloqueante, pero bloquea el loop si el worker es async
- [x] ¿Qué tipos devuelve el punto de acceso: los de la librería o unos propios del worker? — **Resolved:** Recomiendo que el punto de acceso devuelva **tipos propios del worker**: `dataclass(frozen=True, slots=True)` como `Quote`, definidos en el mismo módulo de AC-11 junto al `Protocol`, con `Decimal` para precios y `datetime` con zona horaria para los timestamps. La implementación concreta convierte los objetos de `market-data-client` a esos tipos dentro del módulo. Así se cumple la regla de AC-11 de que ningún otro módulo importe la librería. Además, el fake de AC-15 puede construir respuestas sin depender de ella, y Pyright strict no arrastra los tipos de la librería, que quizá no estén tipados (AC-8), al resto del código. Conviene mantener esos tipos mínimos, solo con los campos que el worker usa hoy, y ampliarlos cuando aparezca un caso de uso concreto.

## Resolved Decisions
<!-- Generated from Open Questions — settled answers that inform the plan. -->
- **¿Cuál es la organización de GitHub de `market-data-client` y a qué ref se fija en `uv add`?** — **`<org>` confirmada + tag de release (`@vX.Y.Z`)**: las actualizaciones quedan explícitas y legibles en `pyproject.toml`, y `uv.lock` igual fija el SHA, así que se cumplen AC-3 y NFR-1 sin el riesgo de la rama por defecto ni el mantenimiento manual de un SHA crudo.
- **Si el repo es privado, ¿cómo se autentica `uv sync` dentro del build de Docker?** — **Elijo la deploy key SSH vía `--mount=type=ssh` con URL `git+ssh://`.** Es la única opción que mantiene `uv sync --frozen` instalando desde Git y fijado por SHA en `uv.lock` (AC-3, AC-4, AC-9, NFR-1), y no deja tokens en la imagen ni en archivos versionados (NFR-2).
- **¿Cómo se instala `git` en la imagen del worker?** — **`apt-get install git` en la única stage actual**: es el cambio mínimo que cumple AC-9 y mantiene `uv sync --frozen` instalando desde Git. Como se eligió la deploy key SSH, también hay que instalar `openssh-client`, y conviene limpiar `/var/lib/apt/lists` para que la imagen no crezca de más.
- **¿Qué hace el worker con `market-data-client` al arrancar (AC-13/AC-14)?** — Al arrancar, el worker crea el cliente de `market-data-client` con los campos de `WorkerSettings` a través de la implementación concreta del `Protocol` (AC-11/AC-12). Después hace una única verificación liviana de conectividad (por ejemplo, autenticarse o pedir el estado del servicio, según lo que ofrezca la librería) y registra en el log que el cliente está listo. No se suscribe, no consulta precios ni persiste datos, porque el streaming y la persistencia quedan fuera de alcance. Si la creación o la verificación fallan, la excepción propia del worker se registra en el log y el proceso sale con código 1 (AC-14). Si todo sale bien, el worker queda en su loop actual hasta recibir SIGINT/SIGTERM, cierra el cliente con `close()` y sale con código 0 (AC-13). Así el fake del `Protocol` alcanza para testear ambos caminos sin red (AC-15).
- **¿Qué estilo de interfaz expone el `Protocol` de acceso a market data?** — 🔧 **Grep** `src/worker`worker/src/worker/__main__.py:3:import asyncio
- **¿Qué tipos devuelve el punto de acceso: los de la librería o unos propios del worker?** — Recomiendo que el punto de acceso devuelva **tipos propios del worker**: `dataclass(frozen=True, slots=True)` como `Quote`, definidos en el mismo módulo de AC-11 junto al `Protocol`, con `Decimal` para precios y `datetime` con zona horaria para los timestamps. La implementación concreta convierte los objetos de `market-data-client` a esos tipos dentro del módulo. Así se cumple la regla de AC-11 de que ningún otro módulo importe la librería. Además, el fake de AC-15 puede construir respuestas sin depender de ella, y Pyright strict no arrastra los tipos de la librería, que quizá no estén tipados (AC-8), al resto del código. Conviene mantener esos tipos mínimos, solo con los campos que el worker usa hoy, y ampliarlos cuando aparezca un caso de uso concreto.
