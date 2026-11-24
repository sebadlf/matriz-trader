---
inclusion: always
description: Product purpose, target users, and goals.
---

# Product

`matriz-trader` es un cliente de trading **manual asistido y algorítmico** sobre Matriz, construido con las librerías internas `market-data-client` y `matriz-client` (`gravity-quant/market-libs`). Hoy es un esqueleto: solo expone `GET /api/health` y una pantalla de inicio.

- **Purpose**: operar en Matriz desde una interfaz propia, con datos de mercado en tiempo real, envío de órdenes manuales con asistencia (confirmación, controles de riesgo) y ejecución de estrategias algorítmicas sobre la misma infraestructura de órdenes.
- **Target users**: dos perfiles que comparten la misma infraestructura de órdenes.
  - Trader manual: arma y envía órdenes desde la UI y necesita confirmaciones claras, números bien formateados y protección contra errores (doble envío, precio o cantidad equivocados).
  - Operador de estrategias: configura y supervisa estrategias algorítmicas, y necesita límites de riesgo, kill switch y trazabilidad de cada orden de punta a punta (`correlation_id`).
- **Key goals**: seguridad operativa, gates automáticos y trazabilidad.
  - Que un error de software no se convierta en una orden incorrecta o duplicada: `Decimal` para precios y cantidades, fechas en UTC, idempotencia por `client_order_id`, controles de riesgo previos al envío, kill switch persistido y auditoría de solo inserción (`backend/CLAUDE.md` §8).
  - Que el código, escrito mayormente por agentes de IA, pase gates automáticos idénticos en el agente, en el commit y en CI (`scripts/gate.sh`).
  - Errores tipados y logs estructurados que permitan seguir una orden desde la UI hasta Matriz.
- **Non-goals** (por ahora):
  - Despliegue continuo, staging y observabilidad en producción (OpenTelemetry).
  - Herramientas de calidad SaaS o pagas: todo es OSS o gratuito.
  - Ser un cliente genérico multi-broker: el objetivo es Matriz.
