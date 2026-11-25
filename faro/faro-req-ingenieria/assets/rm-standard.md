---
schema_version: "1.0"
work_item_id: "<RM-ID>"
artifact_type: "REQUIREMENT_SPEC"
canonical_path: "context/requirements/work-items/<RM-ID>/<RM-ID>.md"
title: "<Título>"
document_version: "0.1"
level: "STANDARD"
spec_maturity: DRAFT
project: "NO DEFINIDO"
requester: "NO DEFINIDO"
created_at: "NO DEFINIDO"
updated_at: "NO DEFINIDO"
approval: {approved_version: null, approved_by: null, approved_at: null, evidence: null}
external_work_item: {provider: null, id: null, url: null}
relationships: []
---
# <RM-ID> — <Título>

## Solicitud, fuentes y alcance
- SOL-001, objetivo, incluidos, exclusiones y dependencias: NO DEFINIDO.
| SRC | Tipo/autoridad | Localizador/versión | Consulta | Hecho |
|---|---|---|---|---|

## Actores, RF y RN
| ACT | Actor/responsabilidad confirmada | Fuente |
|---|---|---|

### RF-001 — <Título>
- Actor/disparador, precondiciones, resultado, fuente, relaciones y CA: NO DEFINIDO.
### RN-001 — <Título>
- Condición, consecuencia, excepciones, vigencia y RF afectados: NO DEFINIDO.

## RNF, restricciones, validaciones, datos e integraciones
| ID | Enunciado/contrato | Condición o medida | Fuente | CA/PD |
|---|---|---|---|---|

## Flujo, criterios, impacto y pendientes
| Paso | Actor | Acción/condición | Resultado | Fuente/elemento |
|---|---|---|---|---|

### Visuales en Markdown/Mermaid (cuando apliquen)
- Propósito, aplicabilidad y trazabilidad RF/RN/CA/PD: NO DEFINIDO.
- El bloque se lee como texto en un README y no agrega comportamiento fuera del RM.
```mermaid
flowchart TD
    A[RF-XXX: disparador] --> B{RN-XXX: condición}
    B -->|Cumple| C[CA-XXX: resultado]
    B -->|No cumple| D[PD-XXX o excepción documentada]
```

### CA-001 — <Título>
- Origen: NO DEFINIDO
- Resultado esperado: NO DEFINIDO
- Método previsto: NO DEFINIDO
### PD-001 — <Pregunta>
- Motivo, afectados, fase, bloqueo, estado OPEN, respuesta y evidencia: NO DEFINIDO.

## Impacto en conocimiento durable
| Destino | Delta autorizado | Resolución requerida | Fuente / autorización |
|---|---|---|---|
| FUNCTIONAL | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| ARCHITECTURE | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| OPERATIONS | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |
| REFERENCE | NO DEFINIDO | INCORPORAR / NO_APLICA | NO DEFINIDO |

Destinos: `FUNCTIONAL`, `ARCHITECTURE`, `OPERATIONS`, `REFERENCE`. La promoción permanece `PENDIENTE` hasta que `faro-cierre` comprueba `INCORPORADO` o `NO_APLICA` justificado.

## Operaciones de entrega requeridas
| Operación | Origen del alcance |
|---|---|

Mantener vacía sólo si el alcance autorizado no exige commit, PR, release, deploy ni otra operación externa.

## Propuestas, trazabilidad y aprobación
- Propuestas separadas: NO DEFINIDO.
- Relacionar SOL/SRC → RF/RN/DAT/INT → CA.
- Calidad, versión, persona autorizada, evidencia/baseline e impacto frente a versión previa: NO DEFINIDO.
- Estado, prioridad y asignación se consultan en `external_work_item` cuando el seguimiento es `REQUIRED`; no se duplican aquí.
