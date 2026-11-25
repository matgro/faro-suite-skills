---
schema_version: "1.0"
work_item_id: "<RM-ID / BUG-ID / TEC-ID>"
artifact_type: "VALIDATION_REPORT"
canonical_path: "context/requirements/work-items/<ID>/<ID>-validacion.md"
document_version: "0.1"
validated_primary_version: PENDING
validated_primary_sha256: PENDING
validation_outcome: PENDING
impact_functional: PENDING
impact_architecture: PENDING
impact_operations: PENDING
impact_reference: PENDING
required_delivery_evidence: PENDING
---
# Reporte de validación — <RM-ID / BUG-ID / TEC-ID>

## Control de evidencia
- Fecha/responsable, entrada/version, baseline/aprobación, plan/tareas, revisión, entorno, datos y alcance: NO DEFINIDO.

## Resultado por criterio
| CA | Origen | Resultado esperado | Método | Resultado observado | Evidencia local | Estado |
|---|---|---|---|---|---|---|

Estados: CONFORME, NO_CONFORME, NO_VERIFICADO.

## Ejecuciones verificadas
| Ejecución | Entorno | Resultado | Evidencia local | Fecha y zona |
|---|---|---|---|---|

Cada fila usada para cerrar debe estar `SATISFIED`, apuntar a evidencia local regular/no vacía y tener fecha ISO-8601 no futura.

## Hallazgos de validación
| Hallazgo | Tipo | Descripción | Elementos | Evidencia local | Acción | Bloquea |
|---|---|---|---|---|---|---|

Un hallazgo con `Bloquea` distinto de `NO` impide `VERIFIED` y congelado.

## Límites y conclusión

### Refactorizaciones (si aplica)
| Origen → destino | Consumidor real comprobado | Retiro o delegación y compatibilidad | Entrada ejecutada y evidencia | Revisor y revisión inspeccionada | Resultado |
|---|---|---|---|---|---|

- Método nuevo sin uso o lógica sustituida activa sin justificación: NO_CONFORME. Integración/equivalencia sin evidencia: NO_VERIFICADO. Pruebas verdes de la ruta vieja no acreditan el refactor.
- No inspeccionado, pruebas no ejecutadas, accesos faltantes y decisiones funcionales: NO DEFINIDO.
- Totales CONFORME/NO_CONFORME/NO_VERIFICADO, `validation_outcome` y siguientes acciones: NO DEFINIDO.

## Promoción de conocimiento durable
| Destino | Delta validado | Resultado | Ruta durable | Versión / baseline | Evidencia | Justificación |
|---|---|---|---|---|---|---|

Destinos: `FUNCTIONAL`, `ARCHITECTURE`, `OPERATIONS`, `REFERENCE`. Resultados: `PENDIENTE_PROMOCION`, `INCORPORADO`, `NO_APLICA` justificado. Toda promoción pendiente bloquea `faro-cierre`.

Para `INCORPORADO`, la ruta debe ser root-relative, existir fuera del expediente, trazar el work item y la versión/baseline debe coincidir con la fuente durable; `Evidencia` enumera uno o más archivos del expediente separados por `;`, y FARO captura todos sus SHA-256. La resolución y el delta deben coincidir con `Impacto en conocimiento durable` del primario. Para `NO_APLICA`, ruta, versión y evidencia usan `—`, la autoridad primaria debe permitirlo y la justificación material es obligatoria.

## Operaciones de entrega requeridas
| Operación | Origen del alcance |
|---|---|

Con `SATISFIED`, enumerar exactamente todas las operaciones externas exigidas —por ejemplo commit, PR, release o deploy— usando el mismo nombre que tendrá cada fila de `<ID>-entrega.md`. Con `NOT_APPLICABLE`, la tabla permanece vacía.

## Decisión de entrega
| Resultado | Justificación |
|---|---|

Resultados: `SATISFIED` cuando existe `<ID>-entrega.md` con operaciones y evidencia local verificables; `NOT_APPLICABLE` sólo con justificación material.

Los gates del front matter reflejan estas tablas: cada `impact_*` usa `PENDING`, `INCORPORATED` o `NOT_APPLICABLE`; `required_delivery_evidence` usa `PENDING`, `SATISFIED` o `NOT_APPLICABLE`. `validated_primary_version` y `validated_primary_sha256` identifican exactamente la versión y bytes validados. El CLI contrasta los campos con las filas, archivos y hashes; el front matter por sí solo no acredita cierre. `PENDING` permite entregar a cierre para completar la promoción o entrega, pero impide congelar.

VERIFIED requiere todos los CA conformes y sin divergencias materiales; no implica despliegue, aceptación productiva, cierre remoto ni congelado del expediente.
