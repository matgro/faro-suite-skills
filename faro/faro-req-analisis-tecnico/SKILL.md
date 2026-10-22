---
name: faro-req-analisis-tecnico
description: Use when FARO plans an approved RM against real code.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, technical-analysis, planning, tasks]
    related_skills: [faro, faro-arq-adr, faro-arq-rfc, faro-req-ingenieria, faro-req-desarrollo, faro-req-validacion]
---

# FARO — Análisis técnico de requerimientos

## Overview

Contrasta un RM, BUG o TEC con el repositorio y crea un plan técnico y tareas trazables. Las decisiones de negocio faltantes regresan al RM; esta skill no implementa código.

## When to Use

- Preparar desarrollo de un RM aprobado.
- Evaluar impacto o actualizar un plan tras cambiar una versión funcional.
- Planificar BUG documentado o mantenimiento TEC.

## Procedimiento

1. Leer perfil, contrato, instrucciones del repositorio, documento/version de entrada, autorización y estado Git. **Completo:** no se pisa trabajo ajeno y la base está identificada.
2. Inspeccionar arquitectura, entradas, modelos, contratos, dependencias y pruebas relevantes. **Completo:** hechos observados se distinguen de rutas propuestas.
3. Mapear RF/RN/RNF/RES a componentes reales y detectar contradicciones/duplicación. **Completo:** ninguna regla se cambia para acomodar el código.
4. Si una decisión técnica es costosa de revertir, restringe opciones futuras o fue controvertida, registrar una decisión humana ya tomada con `faro-arq-adr`. Si además necesita acuerdo de personas fuera de la conversación y hay alternativas reales, abrir `faro-arq-rfc` antes; ningún trabajo dependiente queda listo para desarrollo mientras el RFC esté `open`. Las decisiones funcionales faltantes regresan a `faro-req-ingenieria`. **Completo:** decisión, aprobación y bloqueo se distinguen.
5. Crear o actualizar el plan desde `assets/technical-plan.md` y tareas desde `assets/tasks.md`; para BUG/TEC usar `assets/maintenance-record.md`. Usar nombres estables sin versión, por ejemplo `<RM-ID>-plan-tecnico.md` y `<RM-ID>-tareas.md`: versión, baseline e historial pertenecen dentro del documento. No duplicar archivos por cada versión salvo archivado explícitamente solicitado. **Completo:** cada tarea apunta a alcance funcional o justificación técnica y verificación.
6. Marcar PRELIMINAR, BLOQUEADO o LISTO_PARA_DESARROLLO según contrato, bloqueos y evidencia. **Completo:** la aprobación y la revisión citada concuerdan.
7. Si seguimiento está `REQUIRED`, sincronizar el cierre o bloqueo del análisis con una actualización concisa conforme a `../references/comment-format.md`, con enlace al plan cuando exista; mantener el estado de trabajo o transicionar conforme al workflow remoto verificado. Si la sincronización falla, bloquear el flujo.
8. Actualizar catálogo/handoff y `context/workflow.json` cuando exista: `nextRoute` es `faro-req-desarrollo` sólo si la versión y autorización coinciden y no hay RFC abierto dependiente. **Completo:** plan, tareas, workflow y traspaso apuntan a la misma versión.

## Invariantes

- Un análisis previo a aprobación es PRELIMINAR, no autorización de implementación.
- No asumir endpoints, tablas, clases, versiones o comandos.
- BUG requiere comportamiento esperado documentado; TEC requiere preservar contrato observable.

## Verification Checklist

- [ ] Revisión del repositorio y cambios locales quedaron registrados.
- [ ] Todo diseño propuesto respeta un elemento de entrada o justificación técnica.
- [ ] Decisiones funcionales no resueltas volvieron a `faro-req-ingenieria`.
- [ ] Plan, tareas y verificación pertenecen a la misma versión.
