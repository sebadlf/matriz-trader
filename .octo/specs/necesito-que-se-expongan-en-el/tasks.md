# Tasks — Necesito que se expongan en el

### Wave 1
- [x] T1 @docs-expert: agregar las secciones `matriz-client` y `market-data-client` a `.env.example` con las 8 variables, comentarios en español y placeholders no secretos, y mencionarlas en `README.md:59` — _outcome: `.env.example` lista las 8 variables comentadas con defaults de reMarkets/develop y valores `change-me-*` (AC-1, AC-2, AC-3, AC-4)_
- [x] T2 @backend-expert: agregar los 8 campos, `NonEmptyStr`, `_secret_not_blank`, las constantes de default y `_format_errors` a `backend/app/core/config.py`; definir las 6 credenciales falsas en `test_env` de `backend/tests/conftest.py` y actualizar `backend/CLAUDE.md:99` — _outcome: `Settings` expone los 8 campos tipados, `load_settings()` sale con `1` nombrando la variable sin volcar `input_value`, y la suite existente pasa sin `.env` (AC-5, AC-6, AC-7, AC-8, AC-9, AC-10, AC-12)_
- [x] T3: agregar las 6 credenciales ficticias al `env:` del job `migrations` en `.github/workflows/ci.yml:163` — _outcome: `alembic upgrade head --sql` del job `migrations` valida `Settings` sin `.env`; actionlint y zizmor pasan (AC-12)_

### Wave 2 (depends on T1, T2)
- [x] T4 @test-generator: agregar a `backend/tests/test_config.py` los tests de la tabla de Verification (carga, defaults, URLs inválidas, credenciales faltantes y vacías, enmascarado en `repr` y structlog, stderr sin secretos, contenido de `.env.example`) — _outcome: cada AC-1 a AC-10 tiene al menos un test que falla si se rompe el comportamiento y la cobertura del backend sigue ≥ 85 % (AC-1, AC-2, AC-3, AC-4, AC-5, AC-6, AC-7, AC-8, AC-9, AC-10)_
- [x] T5 @backend-expert: loguear `external_endpoints` con los hosts efectivos en el `lifespan` de `backend/app/main.py` y agregar `test_lifespan_logs_external_hosts` en `backend/tests/test_deps.py` — _outcome: al arrancar se ve en el log contra qué hosts opera el backend, sin secretos (AC-9)_

### Wave 3 (depends on T3, T4, T5)
- [x] T6: correr `scripts/gate.sh changed full` sin `.env` en la raíz y `docker compose -f docker-compose.dev.yml config backend` / `-f docker-compose.prod.yml config backend` con un `.env` de prueba — _outcome: el gate sale con `0` y ambos compose muestran las 8 variables en el `environment` del backend (AC-11, AC-12)_
