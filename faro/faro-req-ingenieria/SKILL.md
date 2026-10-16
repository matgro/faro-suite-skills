---
name: faro-req-ingenieria
description: Use when FARO formalizes a functional software request.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, rm, traceability, analysis]
    related_skills: [faro, faro-req-analisis-tecnico, faro-req-implementacion, faro-qa-ejecucion, faro-req-validacion, faro-ux]
---

# FARO — Ingeniería de requerimientos

## Overview

Convierte una solicitud informal en un RM trazable antes de implementar comportamiento. Usa el contrato en `context/requirements/`, conserva fuentes, separa hechos confirmados/observados/derivados/propuestos y no inventa reglas.

## When to Use

- Alta, modificación o eliminación de comportamiento, datos, permisos, integraciones o interfaz.
- Bug sin comportamiento esperado documentado.
- Cambio mixto que contiene una parte funcional.

No usar para consultas explicativas, bugs con comportamiento esperado documentado ni mantenimiento técnico que preserve el contrato observable; esas rutas se clasifican y documentan conforme al contrato.

## Procedimiento

1. Leer `context/requirements/project-profile.md`, `references/process-contract.md`, catálogo y fuentes pertinentes. **Completo:** se conocen configuración, ID/rutas y evidencias accesibles.
2. Preservar la solicitud y clasificar: consulta, RM, BUG, TEC o mixto. **Completo:** ninguna parte funcional se oculta como mantenimiento.
3. Reservar ID según el perfil y elegir `rm-lite.md`, `rm-standard.md` o `rm-extended.md`. **Completo:** ID estable antes de referencias externas.
4. Registrar SOL, SRC, RF, RN, RNF, RES, ACT, DAT, INT, VAL, CA y PD sólo cuando tengan evidencia o derivación necesaria. **Completo:** las propuestas quedan separadas y los bloqueos tienen pregunta/impacto.
5. Ejecutar `references/quality-checklist.md`, asignar DRAFT, PENDING_DEFINITION o READY_FOR_REVIEW y actualizar catálogo. **Completo:** READY_FOR_REVIEW no contiene PD bloqueantes.
6. Registrar APPROVED únicamente con evidencia humana válida de una versión y alcance exactos; preservar baseline. **Completo:** la aprobación no es atribuida por el agente.
7. Si seguimiento está `REQUIRED`, importar el item como `SRC` o crearlo al crear el RM; registrar proveedor, identificador/URL, proyecto y el vínculo bidireccional. Sincronizar el hito con el estado remoto verificado y comentario de fase/versión. Si la sincronización falla, bloquear el flujo. **Completo:** toda solicitud tiene trazabilidad remota.
8. Para planificar, transferir RM/version/fuentes a `faro-req-analisis-tecnico`; crear o actualizar `context/workflow.json` cuando la solicitud quede activa, con `nextRoute` y sin duplicar el RM. Las versiones viven en frontmatter/control e historial interno: los artefactos estables no incluyen `vN` en su nombre y se actualizan in-place; no crear archivos paralelos por versión salvo archivado explícitamente solicitado. No escribir código desde esta skill. **Completo:** el siguiente paso es explícito y reanudable.

## Invariantes

- El código es comportamiento observado, no aprobación funcional.
- No inventar roles, estados, límites, validaciones, cálculos, mensajes o contratos.
- Una versión nueva no hereda aprobación de una anterior.
- Guardar artefactos; no depender de memoria conversacional.

## Verification Checklist

- [ ] El RM y su nivel son proporcionales al alcance.
- [ ] Cada elemento normativo tiene fuente, derivación o PD.
- [ ] CA verificables no agregan comportamiento.
- [ ] PD bloqueantes están resueltos antes de READY_FOR_REVIEW.
- [ ] Aprobación, baseline y catálogo concuerdan cuando existen.
