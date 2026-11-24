## Spec

Octo: `.octo/specs/<slug>/` (link) — o «sin spec» con el motivo.

## Qué cambia y por qué

## Checklist (§6 de CLAUDE.md)

- [ ] ¿Toda llamada al backend usa código generado por Orval? ¿Edité algo en `src/api/generated/`?
- [ ] ¿Respeté las reglas de dependencia entre carpetas y capas? ¿Hay imports entre pantallas?
- [ ] ¿Cada estado está en el lugar correcto (servidor / URL / formulario / local / Zustand)?
- [ ] ¿Las pantallas manejan los estados de carga, error y vacío?
- [ ] ¿Hay `any`, `!`, `as` injustificados, `@ts-ignore` o `console.log`? ¿Hay funciones Python sin anotar?
- [ ] ¿Las rutas nuevas tienen `operation_id`, `tags` y un esquema de respuesta de `app/schemas/` (anotación de retorno)?
- [ ] ¿Los precios, cantidades y montos son `Decimal` en el backend y `string` en el frontend? ¿Las fechas tienen zona horaria?
- [ ] ¿Agregué variables de entorno? ¿Están en `.env.example` con comentario?
- [ ] ¿Agregué dependencias nuevas? ¿Están justificadas?
- [ ] ¿Pasó todo lo de la §5?

## Contrato de la API

- [ ] No cambió el contrato
- [ ] Cambió: `backend/openapi.json` y `frontend/src/api/generated/` van en este mismo PR

## Capturas (si cambió la UI)

## Riesgo y rollback

- Riesgo:
- Cómo revertir:
