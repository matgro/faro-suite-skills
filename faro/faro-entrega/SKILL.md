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
- Antes de commit, push, PR o release, resolver versión y tag conforme a `references/versionado-y-tags.md`: proponer el incremento por impacto y preguntar en una sola confirmación si se actualiza la versión y se crea/publica el tag. No repetir decisiones explícitas ya autorizadas; una entrega sin versión/tag también requiere una decisión explícita.
- Si la acción crea una rama para un RM, usar `feature/<RM-ID>-<descripcion-kebab-case>` para incrementos funcionales. No usar el prefijo abreviado `feat/`.

## Procedimiento
1. Declarar preparación: validación, checks, cambios locales, migraciones, configuración/secretos por clave y riesgos. Para commit, push, PR o release, leer `references/versionado-y-tags.md`, inspeccionar versión y tags locales/remotos y confirmar las decisiones pendientes antes de modificar la versión o ejecutar la entrega. **Completo:** huecos visibles, versión y tag resueltos sin asumir autorización.
2. Para commit/PR, revisar diff por secretos, configuración local, generados y alcance; redactar el mensaje conforme a `## Mensajes de commit y PR`. **Completo:** sólo archivos autorizados y mensaje con título, descripción funcional y tareas asociadas.
3. Para release/deploy, verificar artefacto, ambiente, health checks, observabilidad, rollback y migraciones. **Completo:** no se reconstruye una versión distinta.
4. Ejecutar sólo la acción autorizada; registrar comando, referencia, resultado y evidencia del ambiente. Si se autorizó versionar y taguear, sincronizar metadatos e integridad, validar, crear el commit y el tag anotado sobre ese commit, publicar sólo las referencias autorizadas y verificar sus SHA remotos conforme a `references/versionado-y-tags.md`. **Completo:** salida verificable; un push de rama no se declara publicación del tag.
5. Si seguimiento está `REQUIRED`, publicar el resultado de cada operación externa autorizada (rama, commit, PR, release, despliegue o rollback) conforme a `../references/comment-format.md`, con la referencia durable resultante. Al completar el alcance autorizado, transicionar al estado remoto `DONE`; ante cancelación humana explícita, a `CANCELLED`. Si falla la sincronización, registrar el bloqueo real y no declarar la entrega cerrada.
6. Actualizar workflow y documentación operacional afectada. **Completo:** referencia y resultado reanudables.

## Mensajes de commit y PR

- Redactar el mensaje del commit en varias líneas: primera línea como título breve, línea en blanco, descripción funcional sintetizada y, debajo, las tareas asociadas.
- La descripción explica qué funcionalidad cambió, se agregó o se quitó, sin repetir el título. Usar una o dos oraciones; no incluir código, nombres de clases ni detalles internos de implementación.
- Colocar las referencias de tareas al final, separadas de la descripción por una línea en blanco, con formato `#<ID>` (por ejemplo, `#9999`). Si hay varias, incluir una por línea. Usar sólo tareas asociadas verificadas; no inventar IDs y, si no hay tareas asociadas, omitir ese bloque. No incluir estas referencias en el título.
- Preservar los saltos de línea al crear el commit: no concatenar título, descripción y tareas en una sola línea. El push publica el mensaje existente; no lo reemplaza ni duplica su título como descripción.
- Para un PR, usar la primera línea como título y el resto como descripción, conservando el resumen funcional y las tareas al final. Este formato no sustituye los comentarios de seguimiento de `../references/comment-format.md`.

Ejemplo de mensaje de commit (las tareas son ilustrativas):

```text
fix(sac): corregir identificación de solicitudes externas

Se agrega la identificación de la aplicación en las solicitudes a servicios externos.

#9999
#10000
```

## Invariantes
- Validación no es aceptación productiva; aceptación no es despliegue.
- Nunca imprimir secretos; documentar sólo nombres de llaves.
- Rollback de código no autoriza rollback destructivo de datos.
- Despliegue sin verificación se reporta como desplegado, no validado.

## Verificación
- [ ] Acción y ambiente fueron nombrados.
- [ ] Se confirmó si se actualiza versión y se crea/publica tag; el incremento responde al impacto y las referencias remotas autorizadas coinciden con el commit validado.
- [ ] Diff, checks y riesgos fueron revisados.
- [ ] El commit/PR separa título, descripción funcional breve y tareas asociadas verificadas, sin código ni nombres de clases.
- [ ] Evidencia posterior fue capturada si aplica.
- [ ] Workflow y documentación registran resultado real.
