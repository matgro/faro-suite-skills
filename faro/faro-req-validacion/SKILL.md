---
name: faro-req-validacion
description: Use when FARO validates delivery against an approved RM.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, requirements, validation, evidence, delivery]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico, faro-qa-ejecucion, faro-entrega]
---

# FARO — Validación contra requerimientos

## Overview

Compara una entrega con la versión aprobada/autorizada, su plan, tareas, código y evidencia. Cada criterio termina CONFORME, NO_CONFORME o NO_VERIFICADO con evidencia específica.

## When to Use

- Cerrar o revisar una implementación RM, BUG o TEC.
- Detectar cobertura incompleta, divergencia funcional o comportamiento adicional.

No aprobar RMs, autorizar merge/despliegue ni modificar código de producto desde esta skill.

## Procedimiento

1. Leer perfil/contrato, entrada autorizada, baseline, plan, tareas, revisión y entorno. **Completo:** versión y alcance están identificados.
2. Comparar RF/RN/RNF/RES/CA con entradas de código relevantes, no sólo la pantalla principal. **Completo:** se registran conductas agregadas sin origen.
3. Ejecutar únicamente verificaciones pertinentes con comandos comprobados y sin usar producción sin autorización. **Completo:** no se reporta ejecución inexistente.
4. Completar `assets/validation-report.md` por CA, cobertura, ejecuciones, hallazgos y límites. **Completo:** cada CA tiene estado y evidencia.
5. Marcar VERIFIED sólo si todos los CA del alcance están CONFORME y no hay divergencias materiales; usar evidencia de `faro-qa-ejecucion` cuando exista y distinguir explícitamente su ausencia. Si Jira está `REQUIRED`, comentar el resultado y mantener `Haciendo` hasta el cierre operativo; si falla, bloquear el flujo. Actualizar workflow con la siguiente ruta. **Completo:** los hallazgos regresan al flujo funcional o de desarrollo adecuado.

## Verification Checklist

- [ ] Código, plan, tareas y aprobación corresponden a la misma versión.
- [ ] Los NO_VERIFICADO explican su limitación.
- [ ] Los comandos listados se ejecutaron realmente.
- [ ] VERIFIED no se confunde con despliegue o aceptación productiva.
