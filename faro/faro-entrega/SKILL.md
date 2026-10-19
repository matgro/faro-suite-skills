---
name: faro-entrega
description: Use when FARO delivers a requested commit, PR, or deploy.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, delivery, git, release, deployment]
    related_skills: [faro, faro-req-validacion, faro-qa-ejecucion, faro-req-desarrollo]
---

# FARO — Entrega controlada

## Rol
Ejecuta acciones que sacan trabajo del directorio local: commit, branch, PR, release, despliegue o rollback. No implementa código ni convierte desarrollo en autorización implícita de salida.

## Precondiciones
- Acción explícita: commit, PR, release, despliegue o rollback.
- RM/BUG/TEC, versión y evidencia de validación identificados.
- Para despliegue, la autorización nombra el ambiente; producción nunca se infiere.
- Se leyeron reglas de repositorio, CI, despliegue, rollback y estado Git.
- Si la acción crea una rama para un RM, usar `feature/<RM-ID>-<descripcion-kebab-case>` para incrementos funcionales. No usar el prefijo abreviado `feat/`.

## Procedimiento
1. Declarar preparación: validación, checks, cambios locales, migraciones, configuración/secretos por clave y riesgos. **Completo:** huecos visibles.
2. Para commit/PR, revisar diff por secretos, configuración local, generados y alcance. **Completo:** sólo archivos autorizados.
3. Para release/deploy, verificar artefacto, ambiente, health checks, observabilidad, rollback y migraciones. **Completo:** no se reconstruye una versión distinta.
4. Ejecutar sólo la acción autorizada; registrar comando, referencia, resultado y evidencia del ambiente. **Completo:** salida verificable.
5. Si seguimiento está `REQUIRED`, comentar las referencias resultantes (rama, commit, PR, release o despliegue). Al completar el alcance autorizado, transicionar al estado remoto `DONE`; ante cancelación humana explícita, a `CANCELLED`. Si falla la sincronización, registrar el bloqueo real y no declarar la entrega cerrada.
6. Actualizar workflow y documentación operacional afectada. **Completo:** referencia y resultado reanudables.

## Invariantes
- Validación no es aceptación productiva; aceptación no es despliegue.
- Nunca imprimir secretos; documentar sólo nombres de llaves.
- Rollback de código no autoriza rollback destructivo de datos.
- Despliegue sin verificación se reporta como desplegado, no validado.

## Verificación
- [ ] Acción y ambiente fueron nombrados.
- [ ] Diff, checks y riesgos fueron revisados.
- [ ] Evidencia posterior fue capturada si aplica.
- [ ] Workflow y documentación registran resultado real.
