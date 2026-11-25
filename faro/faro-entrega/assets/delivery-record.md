---
schema_version: "1.0"
work_item_id: "<ID>"
artifact_type: "DELIVERY_EVIDENCE"
canonical_path: "context/requirements/work-items/<ID>/<ID>-entrega.md"
document_version: "0.1"
delivery_outcome: PENDING
---
# <ID> — Evidencia de entrega

## Alcance autorizado

- Operación solicitada: NO DEFINIDO.
- Fuente y fecha de autorización: NO DEFINIDO.
- Repositorio, componente y ambiente: NO DEFINIDO.
- Versión/tag y política aplicada: NO DEFINIDO.

## Operaciones verificadas

| Operación | Resultado | Referencia | Evidencia local | Fecha y zona |
| --- | --- | --- | --- | --- |

Resultados permitidos: `SATISFIED`, `FAILED`, `PENDING`. `delivery_outcome: SATISFIED` exige al menos una fila y que todas las operaciones registradas estén `SATISFIED`; cada fila referencia uno o más archivos regulares y no vacíos del expediente, separados por `;`.

## Historial de intentos

Conservar aquí, en orden cronológico, reintentos, fallos y reconciliaciones sin borrar las filas de `Operaciones verificadas` ni presentar un intento parcial como entrega satisfecha.

## Comprobación del artefacto

- Commit/SHA, tag, release o digest aplicable: NO DEFINIDO.
- Build o artefacto exacto desplegado: NO APLICA hasta verificar.
- Ambiente y versión efectiva comprobada: NO APLICA hasta verificar.
- Health checks, observabilidad y rollback: NO APLICA hasta verificar.

## Seguimiento externo

- Comentario o vínculo publicado: NO APLICA hasta verificar.
- Readback del recurso afectado y del item: NO APLICA hasta verificar.
- Bloqueo de sincronización, si existe: NO APLICA.

Este artefacto conserva resultados de entrega y sus reintentos; no representa el estado operativo del item, no acredita `DONE`, no autoriza otra operación y no sustituye `<ID>-cierre.json`.
