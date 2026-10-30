# Notas — `matriz-client` 0.3.0 (T4)

Inspección realizada el 2026-10-30 sobre el wheel descargado en un directorio temporal aislado (`/tmp`), instalado en un venv descartable fuera del repo.

## Acceso: **público**

- `curl -sSL <url>` **sin credenciales** → HTTP `200` (redirige a `release-assets.githubusercontent.com`).
- URL: `https://github.com/gravity-quant/market-libs/releases/download/matriz-client-v0.3.0/matriz_client-0.3.0-py3-none-any.whl`
- SHA-256: `b44520777ef3ccaa7872036ca4a751b25615a13643c086fe5004af6f2c0351fd` (94 210 bytes).
- **Consecuencia:** no hace falta token de GitHub, `~/.netrc` ni Docker build secret. La URL se usa tal cual en `[tool.uv.sources]` (T5) y en los Dockerfiles (T10).

## Metadatos

| Campo | Valor |
|-------|-------|
| `Requires-Python` | `>=3.12` (compatible con 3.13) |
| Dependencias | `httpx>=0.27`, `python-dotenv>=1.0`, `tenacity>=9.1.0,<10`, `websocket-client>=1.8.0` |
| `py.typed` | **Sí** (`matriz_client/py.typed`, classifier `Typing :: Typed`) |
| API | MATBA ROFEX Primary API v1.21 (REST + WebSocket) |

**Pyright strict:** un probe que usa `Client(...)`, `login()`, `close()`, `AuthenticationError` y `MatrizClientError` da `0 errors` en modo `strict`. **No hace falta `stubs/matriz_client/__init__.pyi`**.

## Firma real

```python
from matriz_client import Client, AsyncClient, AuthenticationError, MatrizClientError, PrimaryAPIError

class Client:
    def __init__(
        self,
        *,                                  # todos keyword-only
        base_url: str | None = None,        # None → env PRIMARY_BASE_URL o "https://api.remarkets.primary.com.ar"
        username: str | None = None,        # None → env PRIMARY_USER o ""
        password: str | None = None,        # None → env PRIMARY_PASSWORD o ""
        token: str | None = None,
        token_expires_at: float | None = None,
        max_retries: int = 2,               # int >= 0; si no, ValueError
        http_client: httpx.Client | None = None,
        strict_decode: bool | None = None,
    ) -> None: ...
    def login(self) -> str: ...             # POST /auth/getToken → devuelve el token
    def close(self) -> None: ...            # cierra el httpx.Client; es idempotente
    def __enter__(self) -> Self: ...
    def __exit__(self, ...) -> None: ...    # llama a close()
```

`AsyncClient` tiene el mismo constructor (con `http_client: httpx.AsyncClient | None`), `async def login() -> str`, `async def aclose()` y `async with`.

### Conexión y cierre

- **El constructor no hace I/O.** Solo guarda el estado; el `httpx.Client` se crea lazy.
- **No existe `connect()`.** La forma de "conectar de verdad" (decisión resuelta: fail-fast) es llamar a **`login()`**, que valida las credenciales contra `POST /auth/getToken`. Si no se llama, el login ocurre solo en la primera request autenticada.
- **Cierre:** `close()` (sync) o `await aclose()` (async).
- **No hay parámetros obligatorios** a nivel de firma. Las credenciales se validan en `login()`: si `username` o `password` están vacíos, levanta `AuthenticationError("PRIMARY_USER and PRIMARY_PASSWORD must be set")`.
- **La cuenta (`account`) no forma parte del cliente.** Es un argumento por llamada (`new_order(account=...)`, `get_positions(account_name)`, etc.).
- El timeout por request es de 30 s (`_REQUEST_TIMEOUT`) y no se configura por constructor. Para acotarlo, se pasa un `http_client=httpx.Client(timeout=...)` propio.

### Errores observados en `login()`

| Situación | Excepción |
|-----------|-----------|
| Credenciales vacías | `matriz_client.AuthenticationError` (antes de cualquier I/O) |
| HTTP 401/403 | `matriz_client.AuthenticationError` |
| Otro 4xx/5xx | `matriz_client.PrimaryAPIError` |
| Respuesta sin `X-Auth-Token` | `matriz_client.AuthenticationError` |
| Host inalcanzable (probado contra `127.0.0.1:9`) | **`httpx.ConnectError`**, que **no** es subclase de `MatrizClientError` |

→ El gateway (T8) debe capturar `MatrizClientError` **y** `httpx.HTTPError` (o `httpx.TransportError`) para cumplir con "log ERROR + exit 1".

## Variables `MATRIZ_*` finales

| Variable | Obligatoria | Mapea a | Valor en `.env.example` |
|----------|-------------|---------|-------------------------|
| `MATRIZ_BASE_URL` | Sí | `Client(base_url=...)` | `https://api.remarkets.primary.com.ar` (sandbox reMarkets, default de la librería) |
| `MATRIZ_USERNAME` | Sí | `Client(username=...)` | `changeme` |
| `MATRIZ_PASSWORD` | Sí (`SecretStr`) | `Client(password=...)` | `changeme` |

- **`MATRIZ_ACCOUNT` se elimina:** el cliente no la recibe ni la necesita para inicializarse.
- **No se usan los nombres nativos `PRIMARY_*` de la librería.** El worker lee `MATRIZ_*` con `pydantic-settings` y los pasa **siempre explícitos** al constructor. Si se pasa `None`, la librería cae silenciosamente a `PRIMARY_*` del entorno.

## Pitfalls para T5/T8

1. **`load_dotenv()` al importar.** `matriz_client/_state.py` y `client.py` llaman a `load_dotenv()` en el import. `python-dotenv` busca `.env` subiendo desde el archivo de la librería (`.venv/lib/.../site-packages/matriz_client/`). Como `.venv` vive en la raíz del repo, **carga el `.env` raíz en `os.environ`** (sin sobrescribir) la primera vez que se importa `matriz_client`. En Docker no hay `.env`, así que no tiene efecto. En los unit tests del worker, `monkeypatch.delenv` debe aplicarse **después** de importar `matriz_client`, o los tests de settings tienen que construir `WorkerSettings(_env_file=None)` con el entorno ya limpio. Lo más simple es mantener el import de `matriz_client` solo en `matriz_gateway.py` y que los tests de settings y runner no importen ese módulo.
2. La librería adjunta un `NullHandler` + `RedactingFilter` a su logger `matriz_client` y no toca `logging.root`. Es compatible con el `basicConfig` del worker.
3. `Client` no es picklable ni copiable con `deepcopy` (levanta `NotImplementedError`), lo que no afecta el uso previsto.
4. El nombre de archivo del wheel importa: `uv pip install` rechaza un wheel renombrado (`mc.whl`). La URL de `[tool.uv.sources]` conserva el nombre canónico.

## Esqueleto sugerido para `MatrizClientGateway` (T8)

```python
import httpx
from matriz_client import Client, MatrizClientError

class MatrizClientGateway:
    def __init__(self, settings: WorkerSettings) -> None:
        self._client = Client(
            base_url=settings.matriz_base_url,
            username=settings.matriz_username,
            password=settings.matriz_password.get_secret_value(),
        )

    def connect(self) -> None:
        self._client.login()  # MatrizClientError | httpx.HTTPError si falla

    def close(self) -> None:
        self._client.close()
```
