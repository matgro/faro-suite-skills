---
name: faro-req-analisis-tecnico
description: Use when FARO plans an approved RM against real code.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, technical-analysis, planning, tasks]
    related_skills: [faro, faro-arq-adr, faro-arq-rfc, faro-req-ingenieria, faro-req-desarrollo, faro-req-validacion, faro-cierre, faro-int-jira, faro-int-azure-devops]
---

# FARO — Análisis técnico de requerimientos

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

Leer y aplicar [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md) antes de resolver o escribir un expediente.

## Overview

Contrasta un RM, BUG o TEC con el repositorio y crea un plan técnico y tareas trazables. Las decisiones de negocio faltantes regresan al RM; esta skill no implementa código.

## Expediente activo

Para un ID publicado, resolver con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json`. El primario, plan y tareas viven en el directorio devuelto; no aceptar una ruta inferida ni escribir fuera de él. Si existe `<ID>-cierre.json`, detenerse: un seguimiento posterior requiere otro ID enlazado. Un BUG/TEC nuevo todavía no puede resolverse: primero completa el alta transaccional del paso 1. El catálogo y `workflow.workItemRef` localizan, pero no copian estado, prioridad ni asignación del gestor remoto.

El perfil debe declarar seguimiento `REQUIRED` verificado y el catálogo debe contener referencia remota. Un expediente legado con `OFF` se diagnostica sin escribir hasta configurar el proveedor, crear/importar y releer su item mediante el adaptador y completar la referencia vacía con `python -B <skills-root>/faro/scripts/work_item_contract.py link-external --root <root> --id <ID> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --apply --json`. Nunca sobrescribir una referencia distinta ni crear un segundo item para reconciliar.

## When to Use

- Preparar desarrollo de un RM aprobado.
- Evaluar impacto o actualizar un plan tras cambiar una versión funcional.
- Planificar BUG documentado o mantenimiento TEC.

## Procedimiento

Para refactorizaciones, leer [Cierre verificable de refactorizaciones](../references/refactoring-completion.md) y completar en el plan consumidores antes/después, retiro o delegación, compatibilidad, pruebas desde entradas reales y revisión independiente. No planificar una extracción como mera creación de una clase o método; la tarea incluye conectar y retirar dentro del alcance autorizado.

1. Leer perfil, contrato, catálogo, entrada y autorización. Para un ID ya publicado, ejecutar `resolve`. Para un BUG/TEC nuevo ya clasificado y autorizado, sustituir `<TIPO>` por `BUG` o `TEC` y reservar con `python -B <skills-root>/faro/scripts/work_item_contract.py reserve --root <root> --kind <TIPO> --source <evidencia> --apply --json`; usar el adaptador Jira/Azure configurado para crear/importar y releer el item remoto; crear `<ID>/<ID>.md` desde `assets/maintenance-record.md`; previsualizar `register` y publicar con `python -B <skills-root>/faro/scripts/work_item_contract.py register --root <root> --id <ID> --primary context/requirements/work-items/<ID>/<ID>.md --reservation-source <misma-evidencia> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --related <origen> --apply --json`. `--primary` recibe la ruta completa para validarla y el catálogo guarda sólo el basename `Documento principal`; `resolve --json` devuelve ambos como `primaryDocument` y `primaryPath`. Luego ejecutar `validate --strict` y `resolve`. Si la creación remota tuvo éxito pero `register` falló, conservar ID/evidencia y reconciliar ese mismo item, sin repetir la creación. **Completo:** ruta, referencia remota y mutabilidad están identificadas antes de planificar.
2. Leer instrucciones del repositorio, documento/version de entrada y estado Git sin pisar trabajo ajeno. Inspeccionar arquitectura, entradas, modelos, contratos, dependencias y pruebas relevantes. **Completo:** hechos observados se distinguen de rutas propuestas.
3. Mapear RF/RN/RNF/RES a componentes reales y detectar contradicciones/duplicación. **Completo:** ninguna regla se cambia para acomodar el código.
4. Si una decisión técnica es costosa de revertir, restringe opciones futuras o fue controvertida, registrar una decisión humana ya tomada con `faro-arq-adr`. Si además necesita acuerdo de personas fuera de la conversación y hay alternativas reales, abrir `faro-arq-rfc` antes; ningún trabajo dependiente queda listo para desarrollo mientras el RFC esté `open`. Las decisiones funcionales faltantes regresan a `faro-req-ingenieria`. **Completo:** decisión, aprobación y bloqueo se distinguen.
5. Crear o actualizar `<ID>-plan-tecnico.md` desde `assets/technical-plan.md` y `<ID>-tareas.md` desde `assets/tasks.md` dentro del expediente resuelto. Usar siempre el primario devuelto por el helper, aunque tenga basename migrado. Conservar el INC sólo como relación/evidencia. Cuando la relación entre componentes, contratos o integraciones no se entienda con la tabla, añadir Mermaid dentro del plan. Versiones, baseline e historial pertenecen dentro del documento; no duplicar archivos ni mover el expediente por fase. **Completo:** cada artefacto comparte ID/ruta y cada tarea apunta a alcance o justificación y verificación.
6. Registrar `plan_readiness: PRELIMINAR`, `BLOQUEADO` o `LISTO_PARA_DESARROLLO` según contrato, bloqueos y evidencia. Es un gate técnico, no el estado del work item. **Completo:** aprobación, revisión y readiness concuerdan sin duplicar el gestor.
7. Sincronizar avance o bloqueo del análisis mediante el adaptador configurado y una actualización concisa conforme a `../references/comment-format.md`, con enlace al plan cuando exista; releer la mutación y mantener el estado operativo sólo en el proveedor. Si falla, bloquear el flujo.
8. Actualizar el catálogo sólo mediante el helper cuando cambie una referencia soportada, y `context/workflow.json` con el mismo `workItemRef`: `nextRoute` es `faro-req-desarrollo` sólo si versión y autorización coinciden y no hay RFC abierto dependiente. Ejecutar la validación estricta del contrato de work items antes del handoff. **Completo:** primario, plan, tareas, workflow y traspaso apuntan al mismo expediente y versión.

## Invariantes

- Un análisis previo a aprobación es PRELIMINAR, no autorización de implementación.
- No asumir endpoints, tablas, clases, versiones o comandos.
- BUG requiere comportamiento esperado documentado; TEC requiere preservar contrato observable.
- Plan readiness, hallazgos y evidencia no reemplazan el estado remoto.
- Un expediente congelado es inmutable; una corrección posterior crea un sucesor relacionado.

## Verification Checklist

- [ ] Revisión del repositorio y cambios locales quedaron registrados.
- [ ] Todo diseño propuesto respeta un elemento de entrada o justificación técnica.
- [ ] Decisiones funcionales no resueltas volvieron a `faro-req-ingenieria`.
- [ ] Plan, tareas y verificación pertenecen a la misma versión.
- [ ] Todos los artefactos pertenecen al directorio resuelto y el expediente no está congelado.
