🔧 **Read** `necesito-que-se-expongan-en-el/requirements.md`1	# Requirements: variables de configuración de `market-data-client` y `matriz-client` en el `.env`
2	
3	## Introduction
4	
5	El backend depende de dos librerías internas (`backend/pyproject.toml`): `market-data-client` (v0.7.1) y `matriz-client` (v0.4.0). Ambas leen su configuración de variables de entorno, pero hoy ninguna de esas variables figura en `.env.example` ni en `Settings` (`backend/app/core/config.py`). Quien levanta el proyecto no tiene forma de saber qué variables hacen falta, y el backend no puede validarlas al arrancar.
6	
7	Variables que leen las librerías (relevadas del códig
… (truncated)🔧 **Read** `necesito-que-se-expongan-en-el/plan.md`1	# Plan: variables de configuración de `market-data-client` y `matriz-client` en el `.env`
2	
3	> Exponer las ocho variables de `matriz-client` y `market-data-client` en `.env.example` y en `Settings`, con las credenciales obligatorias, URLs validadas, secretos enmascarados y el host efectivo en el log. Appetite: S. Risk: medium.
4	
5	## Approach
6	
7	```mermaid
8	flowchart LR
9	  A[".env de la raíz / entorno"] --> B["Settings: 8 campos planos (str, SecretStr, HttpUrl)"]
10	  B --> C["load_settings(): exit 1 nombrando variables, sin input_value"]
11	  B --> D["lifespan: log external_endpoints
… (truncated)🔧 **Bash**

```bash
git diff -- .env.example .github/workflows/ci.yml README.md backend/CLAUDE.md backend/app backend/tests
```diff --git a/.env.example b/.env.example
index 5eb05de..5aae993 100644
--- a/.env.example
+++ b/.env.example
@@ -28,6 +28,26 @@ BACKEND_PORT=8000
 # Nivel de log de uvicorn: critical | error | warning | info | debug.
 LOG_LEVEL=info
 
+# --- matriz-client (API de Primary / Matriz) ---
+# Usuario de la API de Primary. Obligatoria: el backend no arranca sin ella.
+PRIMARY_USER=change-me-user
+# Contraseña de ese usuario. Obligatoria y secreta: nunca la commitees.
+PRIMARY_PASSWORD=change-me-local-only
+# URL base de la API de Primary. Opcional; default de la librería: https://api.remarkets.prima
… (truncated)## Resumen

El backend ahora lee las 8 variables de entorno que usan `matriz-client` y `market-data-client`. Están documentadas en `.env.example`, tipadas y validadas en `Settings`, y los secretos quedan ocultos en `repr()`, en los logs y en stderr. El cambio no crea los clientes ni agrega endpoints: solo prepara la configuración en un único lugar y hace que un `.env` incompleto o mal formado falle al arrancar.

## Cambios

- **Configuración (`Settings`)**:
  - Se agregaron 8 campos con los mismos nombres que leen las librerías.
  - Las 6 credenciales son obligatorias y no pueden estar vacías ni tener solo espacios (`NonEmptyStr`, `_secret_not_blank`). `PRIMARY_PASSWORD` y `MARKET_DATA_CLIENT_SECRET` son `SecretStr`.
  - Las 3 URLs se validan como `HttpUrl`. `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL` tienen como default los entornos de prueba de cada librería (reMarkets y market data develop).
- **Errores sin secretos**: `load_settings()` ya no vuelca `str(exc)`, que puede incluir la entrada completa con los secretos. Ahora imprime una línea `VARIABLE: mensaje` por error, usa `include_input=False` y sale con `raise SystemExit(1) from None`.
- **Log al arrancar**: el `lifespan` registra el evento `external_endpoints` con los hosts contra los que opera el backend. Solo los hosts: nunca el usuario, los secretos ni la URL completa.
- **Tests y CI**:
  - `conftest.py` define credenciales ficticias y borra las dos `*_BASE_URL` del entorno para que rijan los defaults.
  - Se agregaron tests para AC-1 a AC-10 y para el log de hosts.
  - El job `migrations` de CI define credenciales ficticias, porque Alembic llama a `load_settings()`.
- **Documentación**: `.env.example` (8 variables comentadas, con valores `change-me-*` en lugar de secretos), `README.md` y `backend/CLAUDE.md`.
- **Docker Compose**: no se modificó. El `env_file: .env` existente ya le pasa las variables al backend (AC-11).

## Archivos

- `.env.example` — nuevas secciones `matriz-client` y `market-data-client` con las 8 variables. Cada una tiene un comentario en español que dice si es obligatoria u opcional y cuál es su default. Los secretos usan `change-me-local-only`.
- `backend/app/core/config.py` — 8 campos nuevos en `Settings`, las constantes `PRIMARY_BASE_URL_DEFAULT` y `MARKET_DATA_BASE_URL_DEFAULT`, el tipo `NonEmptyStr`, el validador `_secret_not_blank` y los helpers `_errors` / `_format_errors`, que arman el mensaje de stderr sin incluir los valores de entrada.
- `backend/app/main.py` — el `lifespan` loguea `external_endpoints` con `primary_host`, `market_data_host` y `market_data_auth_host`.
- `backend/tests/conftest.py` — `TEST_CREDENTIALS` y fixture `test_env` que las define y borra `PRIMARY_BASE_URL` y `MARKET_DATA_BASE_URL`, para que los tests no dependan del `.env` local.
- `backend/tests/test_deps.py` — `test_lifespan_logs_external_hosts`: verifica los tres hosts en el log JSON y que no aparezcan las credenciales.
- `.github/workflows/ci.yml` — job `migrations`: 6 credenciales ficticias en `env:`.
- `README.md` — explica qué credenciales exige el backend, qué pasa si falta alguna y los defaults de las URLs base.
- `backend/CLAUDE.md` — documenta que `test_env` define `TEST_CREDENTIALS` y cómo aislar los tests del `.env` local.
- `.octo/specs/necesito-que-se-expongan-en-el/requirements.md` — requisitos (US-1 a US-4, AC-1 a AC-12) y decisiones tomadas.
- `.octo/specs/necesito-que-se-expongan-en-el/plan.md` — plan: diseño de `Settings`, riesgos, tabla de verificación por AC y waves de tareas.
- `.octo/specs/necesito-que-se-expongan-en-el/tasks.md` — lista de tareas marcadas como completadas.

`backend/tests/test_config.py` no figura en la lista de 11 archivos, pero `git diff` muestra que este spec agregó ahí los tests de AC-1 a AC-10. Cubren el contenido de `.env.example`, la carga desde el `.env` y desde el entorno, los defaults, URLs inválidas, credenciales faltantes o vacías, el enmascarado en `repr` y en structlog, y que stderr no muestre secretos.

**Pendiente:** AC-8 sigue escrito para credenciales opcionales («el backend arranca igual y `/api/health` responde `200`»). La implementación sigue las decisiones tomadas en el spec: el backend sale con `1` si falta una credencial o está vacía. Conviene corregir AC-8 en `requirements.md` para que coincida.