# CLAUDE.md — model

Modelo de datos compartido por `backend` y `worker` (`matriz-model`, paquete `model`). PostgreSQL vía psycopg 3.

## API pública (`import model`)

- `Base` — `DeclarativeBase` con naming convention de constraints. Los modelos usan solo `Mapped[]` y `mapped_column()`, sin plugins.
- `create_engine_from_url(url)`, `get_engine()` (singleton con `DATABASE_URL`), `get_sessionmaker(engine)`.
- `DatabaseSettings`, `root_env_file()` (busca el `.env` raíz), `missing_env_vars(exc)`.

## Comandos

Desde la raíz del repo:

```bash
docker compose up postgres
uv run alembic -c model/alembic.ini upgrade head     # migraciones: siempre manuales
```

Desde `model/`:

```bash
uv run pytest                 # sin Postgres: solo inspecciona metadata y el dialecto
```

Alembic toma la URL de `DATABASE_URL` (`migrations/env.py`) y `target_metadata = Base.metadata`. Los modelos nuevos tienen que importarse donde `Base.metadata` los vea antes de autogenerar.
