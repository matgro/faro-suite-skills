---
schema_version: "1.0"
work_item_id: "<BUG-ID / TEC-ID>"
artifact_type: "BUG_ASSESSMENT_OR_TECHNICAL_MAINTENANCE"
canonical_path: "context/requirements/work-items/<ID>/<ID>.md"
document_version: "0.1"
assessment_maturity: DRAFT
external_work_item: {provider: null, id: null, url: null}
relationships: []
---
# <BUG-ID / TEC-ID> — <Título>

## Control y clasificación
- Tipo BUG/TEC, madurez de evaluación, proyecto, solicitante, autorización, repositorio/revisión y fecha: NO DEFINIDO.
- Solicitud, alcance, justificación de no abrir RM y referencia RM/regla: NO DEFINIDO.
- Incidente de origen (INC, registro y seguimiento), si existe: NO APLICA hasta verificar. Referenciar evidencia y conclusión sin duplicar la investigación; su autorización no autoriza esta corrección.
- Estado, prioridad y asignación pertenecen a `external_work_item` cuando el seguimiento es `REQUIRED`; no se duplican aquí.

## BUG
- Comportamiento esperado con fuente, actual observado, reproducción, entorno y evidencia: NO DEFINIDO.

## TEC
- Objetivo técnico, contratos observables preservados, restricciones y evidencia de no cambio funcional: NO DEFINIDO.

## Corrección o mantenimiento autorizado
- Cambios, riesgos, límites, RM abierto si aparece cambio funcional y referencia al plan/tareas: NO DEFINIDO.

## Criterios u objetivos verificables

### CA-001 — <Resultado verificable>
- Origen: NO DEFINIDO
- Resultado esperado: NO DEFINIDO
- Método previsto: NO DEFINIDO

## Impacto en conocimiento durable
| Destino | Delta autorizado | Resolución requerida | Fuente / autorización |
|---|---|---|---|
| FUNCTIONAL | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| ARCHITECTURE | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| OPERATIONS | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| REFERENCE | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |

Destinos: `FUNCTIONAL`, `ARCHITECTURE`, `OPERATIONS`, `REFERENCE`. Un BUG puede declarar `NO_APLICA` cuando las pruebas de regresión conservan todo el conocimiento útil y no cambia documentación durable.

## Operaciones de entrega requeridas
| Operación | Origen del alcance |
|---|---|

Mantener vacía sólo si el alcance autorizado no exige commit, PR, release, deploy ni otra operación externa.

## Evidencia de resultado
- QA, validación y límites: NO DEFINIDO. El cierre definitivo vive en `<ID>-cierre.json` y sólo lo genera `faro-cierre`.

No declarar restauración sin comparar la fuente esperada. Si falta comportamiento esperado, volver a FARO ingeniería de requerimientos.
