---
name: faro-req-validacion
description: Use when FARO validates delivery against an approved RM.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, validation, evidence, delivery]
    related_skills: [faro, faro-arq-adr, faro-arq-rfc, faro-req-ingenieria, faro-req-analisis-tecnico, faro-qa-ejecucion, faro-cierre, faro-entrega]
---

# FARO — Validación contra requerimientos

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

Leer y aplicar [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md) antes de resolver la unidad o emitir el veredicto.

## Overview

Compara una entrega con la versión aprobada/autorizada, su plan, tareas, código y evidencia. Cada criterio termina CONFORME, NO_CONFORME o NO_VERIFICADO con evidencia específica.

El reporte canónico vive en `context/requirements/work-items/<ID>/<ID>-validacion.md`. Resolver antes con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json`; catálogo, `workflow.workItemRef` y todos los artefactos deben coincidir. Esta fase produce un veredicto y el inventario de conocimiento a promover; no congela ni cierra el expediente.

## When to Use

- Cerrar o revisar una implementación RM, BUG o TEC.
- Detectar cobertura incompleta, divergencia funcional o comportamiento adicional.

No aprobar RMs, autorizar merge/despliegue ni modificar código de producto desde esta skill.

El contrato v2 exige seguimiento `REQUIRED` verificado y referencia remota reconciliada. Un expediente legado con `OFF` puede inspeccionarse, pero no recibe un nuevo veredicto ni avanza a cierre.

## Procedimiento

Cuando haya extracción, traslado o sustitución de lógica, aplicar [Cierre verificable de refactorizaciones](../references/refactoring-completion.md). Contrastar consumidores, retiro/delegación, revisión independiente y evidencia de ejecución desde entradas reales. Un método nuevo sin uso o lógica anterior activa sin justificación produce NO_CONFORME; evidencia insuficiente produce NO_VERIFICADO. Ninguno permite VERIFIED aunque las pruebas existentes pasen.

1. Leer perfil/contrato, catálogo, entrada autorizada, baseline, plan, tareas, QA, revisión y entorno desde el expediente resuelto. Rechazar `<ID>-cierre.json`: un expediente congelado no se revalida ni edita. **Completo:** ruta, versión y alcance están identificados.
2. Comparar RF/RN/RNF/RES/CA con entradas de código relevantes, no sólo la pantalla principal. Cuando el alcance cite ADR/RFC, comprobar que el ADR aceptado esté enlazado y que no se haya validado una entrega dependiente de un RFC abierto. **Completo:** se registran conductas agregadas sin origen.
3. Ejecutar únicamente verificaciones pertinentes con comandos comprobados y sin usar producción sin autorización. **Completo:** no se reporta ejecución inexistente.
4. Completar `<ID>-validacion.md` desde `assets/validation-report.md`. `validated_primary_version` y `validated_primary_sha256` coinciden con la versión y bytes del primario, y la tabla `Resultado por criterio` contiene exactamente sus `CA-NNN`, sin extras ni faltantes; cada fila registra origen, esperado, método, observado y uno o más archivos regulares/no vacíos del expediente en `Evidencia local`, separados por `;`. Reconciliar exactamente una fila para `FUNCTIONAL`, `ARCHITECTURE`, `OPERATIONS` y `REFERENCE`: `INCORPORADO` declara una ruta root-relative bajo la autoridad durable del perfil, versión/baseline acreditada por metadata o `sha256:<digest>` y evidencia; `NO_APLICA` deja ruta/versión/evidencia en `—` y aporta justificación material. Mantener los gates equivalentes `impact_functional`, `impact_architecture`, `impact_operations` e `impact_reference` del front matter. La tabla `Decisión de entrega` coincide con `required_delivery_evidence`; `SATISFIED` enumera antes todas las `Operaciones de entrega requeridas` y exige que `<ID>-entrega.md` contenga exactamente esas operaciones, tipado y con evidencia; `NOT_APPLICABLE` exige tabla vacía y justificación. El CLI contrasta tablas, archivos y hashes: los campos planos no reemplazan evidencia. **Completo:** CA, promociones, versiones y entrega son verificables automáticamente.
5. Registrar `validation_outcome: VERIFIED` sólo si todos los CA del alcance están CONFORME y no hay divergencias materiales; usar evidencia QA cuando exista y distinguir su ausencia. Con `REQUIRED`, publicar el resultado y mantener el estado remoto de trabajo: VERIFIED no equivale a DONE. Si hay NO_CONFORME/NO_VERIFICADO, volver a la fase sustentada; si es VERIFIED, `nextRoute` es `faro-cierre`. Validar estrictamente el contrato antes del handoff. **Completo:** veredicto, conocimiento pendiente y siguiente ruta son inequívocos.

## Verification Checklist

- [ ] Código, plan, tareas y aprobación corresponden a la misma versión.
- [ ] Los NO_VERIFICADO explican su limitación.
- [ ] Los comandos listados se ejecutaron realmente.
- [ ] VERIFIED no se confunde con despliegue o aceptación productiva.
- [ ] Los cinco gates machine-readable coinciden con su evidencia; ningún `PENDING` se presenta como cerrable.
- [ ] El reporte pertenece al expediente resuelto y no existe marker de cierre.
- [ ] VERIFIED entrega a `faro-cierre`; no transicionó el item remoto a DONE ni congeló archivos.
