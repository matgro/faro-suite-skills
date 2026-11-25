---
name: faro-req-ingenieria
description: Use when FARO formalizes a functional software request.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, rm, traceability, analysis]
    related_skills: [faro, faro-req-analisis-tecnico, faro-req-desarrollo, faro-qa-ejecucion, faro-req-validacion, faro-ux, faro-cierre, faro-int-jira, faro-int-azure-devops]
---

# FARO — Ingeniería de requerimientos

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

Leer y aplicar [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md) antes de reservar, resolver o transferir una unidad.

## Overview

Convierte una solicitud informal en un RM trazable antes de implementar comportamiento. Cada RM, BUG o TEC vive en un expediente estable bajo `context/requirements/work-items/<ID>/`; el catálogo resuelve su ubicación y el gestor remoto conserva el estado operativo. La skill conserva fuentes, separa hechos confirmados/observados/derivados/propuestos y no inventa reglas.

## Contrato de expedientes

- `context/requirements/requirements-catalog.md` es el único catálogo de reserva y localización de RM/BUG/TEC. Puede conservar ID, tipo, ruta canónica, basename de `Documento principal`, referencia remota, relaciones y evidencia de reserva; nunca estado, prioridad ni asignación.
- La ruta canónica es `context/requirements/work-items/<ID>/`. Para una unidad nueva el primario es `<ID>.md`; una unidad migrada puede conservar un basename histórico indicado por `Documento principal`. Plan, tareas, QA, validación y cierre usan el mismo directorio e ID.
- Antes de leer o escribir un expediente existente, ejecutar `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json`. Antes del handoff, ejecutar `... validate --root <root> --strict`. No inferir rutas por búsqueda ni por nombre recordado.
- La existencia de `<ID>-cierre.json` indica un expediente congelado. El resolutor comprueba sus hashes; ninguna fase modifica un expediente congelado. Una corrección o evolución posterior reserva otro ID y registra `supersedes`, `follow_up_to` o la relación aplicable.
- `spec_maturity`, aprobación, baseline y veredictos son hechos propios de los artefactos. En el contrato v2, RM/BUG/TEC requieren seguimiento `REQUIRED` verificado; estado operativo, prioridad y asignación pertenecen al item remoto. Un workspace legado migrado con seguimiento `OFF` conserva su evidencia para diagnóstico, pero no crea, avanza, cierra ni congela expedientes hasta configurar y reconciliar un proveedor remoto.
- Para un expediente migrado ya publicado pero sin referencia remota, crear/importar y releer el item mediante el adaptador configurado; previsualizar y luego ejecutar `python -B <skills-root>/faro/scripts/work_item_contract.py link-external --root <root> --id <ID> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --apply --json`. El comando completa una referencia vacía de forma atómica y nunca sobrescribe otra distinta.

## When to Use

- Alta, modificación o eliminación de comportamiento, datos, permisos, integraciones o interfaz.
- Bug sin comportamiento esperado documentado.
- Cambio mixto que contiene una parte funcional.

No usar para consultas explicativas, bugs con comportamiento esperado documentado ni mantenimiento técnico que preserve el contrato observable; esas rutas se clasifican y documentan conforme al contrato.

Un pedido de investigar un síntoma o causa desconocida se deriva primero a `faro-incidentes`, sin abrir RM/BUG por anticipado. Una conclusión de negocio correcto sólo abre RM si el usuario pide cambiar ese comportamiento; conservar el INC como fuente, sin duplicar su investigación.

## Procedimiento

1. Leer `context/requirements/project-profile.md`, `references/process-contract.md`, `context/requirements/requirements-catalog.md` y fuentes pertinentes. Exigir `work_tracking.mode: REQUIRED`, proveedor configurado y credenciales/capacidad verificadas antes de reservar o materializar RM/BUG/TEC. Para un ID existente, resolverlo con el CLI central y detenerse si no coincide catálogo, directorio, primario o hashes de cierre. **Completo:** autoridad remota, configuración, ruta canónica y condición mutable/congelada son conocidas.
2. Preservar la solicitud y clasificar: consulta, RM, BUG, TEC o mixto. **Completo:** ninguna parte funcional se oculta como mantenimiento.
3. Para un RM nuevo, reservar de forma serializada con `python -B <skills-root>/faro/scripts/work_item_contract.py reserve --root <root> --kind RM --source <evidencia> --apply --json`. Con ese ID, usar el adaptador configurado `faro-int-jira` o `faro-int-azure-devops` para importar o crear el item remoto y releer proveedor, ID y URL; no inventar una API propia. Si falla, conservar la reserva y registrar `waitingOn`, sin materializar un expediente sin autoridad externa. **Completo:** reserva e identidad remota son únicas y reconciliables.
4. Crear `context/requirements/work-items/<RM-ID>/<RM-ID>.md` desde el asset elegido y previsualizar `register` sin `--apply`. Publicar con `python -B <skills-root>/faro/scripts/work_item_contract.py register --root <root> --id <RM-ID> --primary context/requirements/work-items/<RM-ID>/<RM-ID>.md --reservation-source <misma-evidencia> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --apply --json`; agregar `--related` cuando corresponda. `--primary` recibe la ruta completa relativa al root; el catálogo guarda sólo `<RM-ID>.md`. El helper consume la reserva sólo si carpeta, primario y front matter concuerdan. Si el remoto ya fue creado y la publicación falla, reconciliar ese mismo item; nunca crear otro. Para un expediente existente, usar exclusivamente `resolve` y sus campos `primaryDocument`/`primaryPath`, aunque el primario conserve un slug migrado. **Completo:** ID, directorio, primario, catálogo y remoto son únicos y estables.
5. Registrar SOL, SRC, RF, RN, RNF, RES, ACT, DAT, INT, VAL, CA y PD sólo cuando tengan evidencia o derivación necesaria. Para flujos, estados, decisiones o integraciones que ganarían claridad, incorporar un bloque Markdown/Mermaid en el mismo RM: debe ser legible sin renderizado, enlazar RF/RN/CA/PD existentes y no inventar comportamiento. Registrar además la matriz de impacto sobre conocimiento durable: DF/producto, arquitectura/ADR, operaciones y referencia. **Completo:** propuestas, bloqueos y promociones previstas quedan separados y trazables.
6. Ejecutar `references/quality-checklist.md`, asignar `spec_maturity: DRAFT`, `PENDING_DEFINITION` o `READY_FOR_REVIEW` y actualizar el catálogo sólo mediante el helper si cambió una referencia soportada. **Completo:** READY_FOR_REVIEW no contiene PD bloqueantes y no se confunde con estado operativo.
7. Registrar APPROVED únicamente con evidencia humana válida de una versión y alcance exactos; preservar baseline. **Completo:** la aprobación no es atribuida por el agente.
8. Registrar el item remoto como `SRC` y mantener proveedor, identificador/URL, proyecto y vínculo bidireccional en el primario y catálogo. Sincronizar el avance o bloqueo de definición mediante el adaptador configurado, releer la mutación y publicar una actualización concisa conforme a `../references/comment-format.md`. El Markdown no copia estado, prioridad ni asignación. Si la sincronización falla, bloquear el flujo. **Completo:** toda solicitud tiene trazabilidad remota y una única autoridad operacional.
9. Para planificar, transferir ID, ruta resuelta, versión y fuentes a `faro-req-analisis-tecnico`; crear o actualizar `context/workflow.json` cuando la solicitud quede activa, con `workItemRef`, `nextRoute` y sin duplicar el RM. Las versiones viven en front matter/control e historial interno: el expediente y sus archivos no incluyen `vN` ni se mueven por fase. Ejecutar `python -B <skills-root>/faro/scripts/work_item_contract.py validate --root <root> --strict` antes del handoff. No escribir código desde esta skill. **Completo:** el siguiente paso es explícito, reanudable y apunta al mismo expediente.

## Invariantes

- El código es comportamiento observado, no aprobación funcional.
- No inventar roles, estados, límites, validaciones, cálculos, mensajes o contratos.
- Una versión nueva no hereda aprobación de una anterior.
- Guardar artefactos; no depender de memoria conversacional.
- Un expediente congelado no se reabre ni edita. Un cambio posterior reserva otro ID y enlaza al anterior.
- Catálogo y workflow localizan; no sustituyen el primario ni el gestor remoto.

## Verification Checklist

- [ ] El RM y su nivel son proporcionales al alcance.
- [ ] Cada elemento normativo tiene fuente, derivación o PD.
- [ ] CA verificables no agregan comportamiento.
- [ ] PD bloqueantes están resueltos antes de READY_FOR_REVIEW.
- [ ] Aprobación, baseline y catálogo concuerdan cuando existen.
- [ ] El expediente resuelve por catálogo, no está congelado y `workItemRef` apunta a su ruta estable.
- [ ] Impactos de conocimiento durable están identificados sin presentar comportamiento futuro como vigente.
