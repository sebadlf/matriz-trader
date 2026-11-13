🔧 **Bash**

```bash
cat .octo/specs/estado-actual-del-repo-la-ruta/bugfix.md; echo ----; cat .octo/specs/estado-actual-del-repo-la-ruta/plan.md | head -200
```<persisted-output>
Output too large (37.9KB). Full output saved to: /Users/sebadlf/.claude/projects/-Users-sebadlf-development-matriz-trader/6075fd41-abf5-4a5d-afe5-ab0283eba394/tool-results/bvg86x1kz.txt

Preview (first 2KB):
# Bugfix: `/orders` no permite ver, crear ni cancelar órdenes

> **Naturaleza del cambio.** Aunque se registra como bugfix, es funcionalidad faltante: la ruta
> `/orders` existe pero es un placeholder. Este documento fija el comportamiento actual verificado en
> el repo, el esperado y lo que no debe romperse. Las decisiones que el repo no resuelve quedan en
> [Preguntas 
… (truncated)🔧 **Bash**

```bash
sed -n 1,400p /Users/sebadlf/.claude/projects/-Users-sebadlf-development-matriz-trader/6075fd41-abf5-4a5d-afe5-ab0283eba394/tool-results/bvg86x1kz.txt | grep -E '^#|^- |^\| ' | head -150
```# Bugfix: `/orders` no permite ver, crear ni cancelar órdenes
## Evidencia del repo (verificada)
| Hecho | Fuente |
| `OrdersPage` solo renderiza `<Typography.Title level={2} data-testid="page-ordenes">Órdenes</Typography.Title>` | `frontend/src/pages/OrdersPage.tsx` |
| Los tests del layout dependen de `page-ordenes` y del ítem «Órdenes» | `frontend/src/layout/AppLayout.test.tsx` |
| El backend solo registra `health.router` (`GET /health`) | `backend/src/backend/main.py` |
| CORS del backend permite **solo `GET`** (`allow_methods=["GET"]`) | `backend/src/backend/main.py` |
| `matriz-client==0
… (truncated)🔧 **Bash**

```bash
git diff --stat; git diff backend/src/backend/main.py backend/pyproject.toml backend/Dockerfile .env.example backend/tests/test_settings.py frontend/src/layout/AppLayout.test.tsx | head -250
``` .env.example                           |  10 +-
 CLAUDE.md                              |  11 +-
 README.md                              |  24 +-
 backend/CLAUDE.md                      |  20 +-
 backend/Dockerfile                     |   2 +
 backend/pyproject.toml                 |   3 +
 backend/src/backend/main.py            |  10 +-
 backend/src/backend/settings.py        |  31 +-
 backend/tests/test_settings.py         |  48 ++-
 frontend/CLAUDE.md                     |  25 +-
 frontend/openapi.json                  | 522 +++++++++++++++++++++++++++++++++
 frontend/src/layout/AppLayout.
… (truncated)🔧 **Bash**

```bash
grep -nE '^(class|def|async def|@router|[A-Z_]+ =)|^    def ' broker/src/broker/matriz_gateway.py backend/src/backend/matriz.py backend/src/backend/trading.py backend/src/backend/settings.py backend/tests/fake_trading.py | head -80; grep -nE '^def test|^async def test' backend/tests/test_trading.py broker/tests/test_matriz_gateway.py | wc -l; grep -nE "^export|^  it\(|describe\(" frontend/src/pages/orders/*.ts frontend/src/pages/orders/*.tsx frontend/src/pages/OrdersPage.tsx | head -60; cat broker/pyproject.toml; head -30 broker/CLAUDE.md
```broker/src/broker/matriz_gateway.py:18:REDACTED = "***"
broker/src/broker/matriz_gateway.py:21:class GatewayError(Exception):
broker/src/broker/matriz_gateway.py:26:class MatrizCredentials:
broker/src/broker/matriz_gateway.py:33:class InstrumentRef:
broker/src/broker/matriz_gateway.py:39:class OrderRecord:
broker/src/broker/matriz_gateway.py:58:class NewOrder:
broker/src/broker/matriz_gateway.py:70:class OrderAck:
broker/src/broker/matriz_gateway.py:75:class MatrizGateway(Protocol):
broker/src/broker/matriz_gateway.py:78:    def connect(self) -> None:
broker/src/broker/matriz_gateway.py:82:   
… (truncated)🔧 **Bash**

```bash
sed -n 40,100p backend/src/backend/matriz.py; sed -n 119,160p backend/src/backend/trading.py; sed -n 1,80p frontend/src/pages/OrdersPage.tsx; git diff --cached --stat
```                # Si falla, propaga `GatewayError` y deja el caché como estaba.
                self._instruments = self._trading.list_instruments()
                self._fetched_at = now
            return list(self._instruments)


def build_trading(settings: BackendSettings) -> MatrizTrading | None:
    """Una instancia por proceso; no hace login (diferido al primer uso)."""
    credentials = settings.matriz_credentials
    return MatrizClientGateway(credentials) if credentials is not None else None


async def _gateway_error_handler(_request: Request, exc: Exception) -> JSONResponse:
    # 
… (truncated)## Overview

Se reemplazó el placeholder de `/orders` por una pantalla funcional para listar, crear y cancelar órdenes en Matriz. Para eso se agregó el paquete `matriz-broker`, que pasa a ser el único dueño de `matriz-client`, y se sumaron endpoints síncronos al backend para que la UI reciba los errores al momento.

## Changes

- **Broker (nuevo paquete `matriz-broker`):** `broker/src/broker/matriz_gateway.py` es el único módulo que importa `matriz_client`. Expone tipos propios del repo, define los protocolos `MatrizGateway` (sesión) y `MatrizTrading` (órdenes e instrumentos), y hace el login recién en el primer uso, una sola vez y protegido con lock. Los errores de Matriz se convierten en `GatewayError` con la contraseña oculta. El viejo `worker/src/worker/matriz_gateway.py` se eliminó.
- **Backend:** agrega `GET /accounts` (lee `MATRIZ_ACCOUNTS`), `GET /instruments` (en caché en memoria con TTL de 1 h), `GET /orders?account_id=`, `POST /orders` y `POST /orders/cancel`.
  - Códigos de error: `GatewayError` → 502; Matriz sin configurar → 503; cuenta que no está en `MATRIZ_ACCOUNTS` → 422.
  - CORS ahora permite `POST`.
  - Las credenciales de Matriz son opcionales, así que `/health` sigue respondiendo sin ellas.
- **Frontend:** `/orders` tiene un selector de cuenta, una tabla de órdenes con estados de carga, vacío y error, y el botón «Actualizar».
  - Se refresca cada 5 s solo mientras haya órdenes no finales.
  - «Cancelar» pide confirmación y la fila queda en `PENDING_CANCEL` hasta que la API informe un estado final.
  - El modal «Nueva orden» usa selects buscables de cuenta y activo. Si el tipo es LIMIT, el precio es obligatorio; si es MARKET, el precio se oculta y no se envía.
  - El título `page-ordenes` se mantiene.
- **Configuración e infra:** `MATRIZ_ACCOUNTS` está documentada en `.env.example` y la imagen del backend copia `broker/`.
- **Fuera de esta lista de archivos, `git diff` también muestra** cambios relacionados en `worker/*`, `pyproject.toml`, `uv.lock`, `frontend/openapi.json`, `frontend/src/test/setup.ts`, `scripts/check.sh`, `README.md` y los `CLAUDE.md`.

## Files

- `.octo/specs/estado-actual-del-repo-la-ruta/bugfix.md` — Requerimiento: comportamiento actual (CB), esperado (EB) e invariante (UB), con las decisiones abiertas ya resueltas.
- `.octo/specs/estado-actual-del-repo-la-ruta/plan.md` — Plan de implementación y tabla de archivos afectados.
- `.octo/specs/estado-actual-del-repo-la-ruta/tasks.md` — Avance de las tareas.
- `broker/pyproject.toml` — Nueva distribución `matriz-broker`. Es el único lugar donde se declara `matriz-client==0.3.0` (y la URL del wheel).
- `broker/src/broker/__init__.py` — Inicializa el paquete `broker`.
- `broker/src/broker/matriz_gateway.py` — Gateway único a Matriz: tipos, protocolos, `MatrizClientGateway` con login diferido, traducción de errores con secretos ocultos.
- `broker/tests/test_matriz_gateway.py` — Prueba con un `Client` falso el mapeo de modelos, los kwargs de `new_order`, el login diferido y el manejo de errores.
- `broker/CLAUDE.md` — Documenta que el acceso a Matriz pasa solo por este módulo y describe la API del gateway.
- `backend/pyproject.toml` — Agrega la dependencia `matriz-broker` y `pythonpath = ["tests"]` para el helper `fake_trading`.
- `backend/Dockerfile` — Copia `broker/` en las dos etapas de `uv sync`.
- `backend/src/backend/settings.py` — Agrega `matriz_base_url`, usuario y contraseña opcionales, y `MATRIZ_ACCOUNTS`. Las cuentas se recortan y se deduplican; las credenciales quedan en `None` si están incompletas.
- `backend/src/backend/matriz.py` — Crea el provider una vez por proceso, maneja `InstrumentCache` (TTL de 1 h), registra el handler de 502 y define las dependencias de FastAPI (503 y 422).
- `backend/src/backend/trading.py` — Router con los modelos Pydantic y los endpoints de cuentas, instrumentos y órdenes (listar, crear y cancelar). El listado sale ordenado por `transact_time` descendente.
- `backend/src/backend/main.py` — `create_app(settings, trading=None)` registra Matriz y el nuevo router, y CORS pasa a `GET`/`POST`.
- `backend/tests/fake_trading.py` — `FakeTrading` y `make_order` para testear sin red ni credenciales.
- `backend/tests/test_trading.py` — Tests de los endpoints: casos de éxito, validaciones 422, 502, 503 y caché de instrumentos.
- `backend/tests/test_settings.py` — Aísla las variables `MATRIZ_*` y prueba credenciales y cuentas.
- `.env.example` — La sección Matriz ahora cubre backend y worker, y agrega `MATRIZ_ACCOUNTS`.
- `frontend/src/pages/OrdersPage.tsx` — Selector de cuenta, tabla, polling condicional cada 5 s, cancelación con estado `PENDING_CANCEL` temporal y apertura del modal.
- `frontend/src/pages/OrdersPage.test.tsx` — Tests de integración de la página: carga, vacío, error y reintento, polling, y cancelación con éxito, error o descartada.
- `frontend/src/pages/orders/OrdersTable.tsx` — Tabla antd con las columnas de EB-2, «—» en campos vacíos y «Cancelar» con `Popconfirm`.
- `frontend/src/pages/orders/OrdersTable.test.tsx` — Tests de columnas, celdas vacías, cuándo se puede cancelar y la confirmación.
- `frontend/src/pages/orders/NewOrderModal.tsx` — Modal de alta: selects sin texto libre, precio según LIMIT o MARKET, validaciones y manejo de envío, error y éxito.
- `frontend/src/pages/orders/NewOrderModal.test.tsx` — Tests de los casos EB-18 a EB-33 (validación, Market vs Limit, error, éxito, doble envío).
- `frontend/src/pages/orders/orderStatus.ts` — Clasifica los estados en finales y no finales y define `isCancelable`, `hasNonFinal` y `effectiveStatus`.
- `frontend/src/pages/orders/orderStatus.test.ts` — Tests de esa clasificación y de los helpers.
- `frontend/src/pages/orders/format.ts` — `formatNumber` y `formatText` (con «—» para vacíos) y `describeApiError`, que arma el mensaje con el `detail` de la API.
- `frontend/src/pages/orders/format.test.ts` — Tests de formato y de los mensajes de error.
- `frontend/src/layout/AppLayout.test.tsx` — El test de `/orders` sigue verificando el título, pero ya no exige que no haya llamadas al backend. El de `/strategies` mantiene esa verificación.