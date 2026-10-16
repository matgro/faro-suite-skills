---
name: faro-int-azure-devops
description: Use when FARO configures Azure DevOps work tracking.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, azure-devops, visualstudio, integration, synchronization]
    related_skills: [faro, faro-inicializacion, faro-doctor, faro-req-ingenieria, azure-devops-rest-v7]
---

# FARO — Integración Azure DevOps / Visual Studio

## Rol

`faro-int-azure-devops` es el adaptador de gobernanza entre FARO y `azure-devops-rest-v7`. Configura Azure DevOps sólo por petición humana expresa, importa un work item como fuente `SRC` y, con política `REQUIRED`, sincroniza el seguimiento operativo de la solicitud.

La URL hospedada en `*.visualstudio.com` y `dev.azure.com` identifica el mismo proveedor; se conserva la URL confirmada sin transformarla. No sustituye el RM, aprobación humana, análisis técnico ni implementación.

## Cuándo usar

- Durante inicialización después de confirmar `work_tracking.mode: REQUIRED` y `provider: AZURE_DEVOPS`.
- En un proyecto `available`, sólo cuando el usuario pide agregar o configurar Azure DevOps.
- Cuando el usuario aporta una URL Azure DevOps/Visual Studio y el perfil habilita este proveedor.

## Configuración y autorización

1. Leer el contrato FARO, `context/stats.json`, el perfil y el workflow. Confirmar `available`, salvo dentro de una inicialización. **Completo:** estado y política conocidos.
2. Registrar sólo metadatos en `project-profile.md`: proveedor, URL de organización, proyecto, área, equipo, iteración por defecto, tipo de item, campo/valor de actividad, campo/valor de estimación de tarea, asignado por defecto, estado de credenciales y capacidades autorizadas. No registrar PAT, contraseñas, cookies ni cabeceras. **Completo:** los valores específicos del proyecto son verificables y no sensibles.
3. El PAT permanece fuera del repositorio como `AZDO_PAT`; `AZDO_ORGANIZATION_URL`, `AZDO_DEFAULT_PROJECT`, `AZDO_DEFAULT_AREA_PATH`, `AZDO_DEFAULT_TEAM` y `AZDO_DEFAULT_ASSIGNED_TO` son opcionales, sólo se aceptan si coinciden con el perfil. Si falta PAT, no consultar ni modificar Azure DevOps. **Completo:** no hubo lectura de `.env` ni reutilización de credenciales de la aplicación.
4. Con modo `REQUIRED`, ejecutar una lectura autenticada contra la organización y consultar los tipos de work item, áreas, iteraciones del equipo y campos del tipo configurado. Registrar los valores reales elegidos y el mapeo operacional `PENDING`, `DOING`, `DONE` y, si existe, `CANCELLED`. **Completo:** configuración y workflow provienen del proyecto remoto real.
5. Para crear un `Task`, confirmar que el campo de estimación configurado está disponible. Si no se provee estimación, usar `1`; no crear la tarea si ese campo no es editable o no acepta el valor. **Completo:** toda tarea creada tiene estimación explícita.
6. Actividad, iteración y asignado son configurables. Si el valor solicitado no coincide con los valores ya validados, consultar Azure DevOps antes de crear o actualizar: actividad en los campos del work item type, iteraciones en el equipo y usuario en las identidades accesibles. No inventar valores ni sustituirlos silenciosamente. **Completo:** cada valor aplicado existe y es compatible con el proyecto.

## Trazabilidad REQUIRED

1. Toda solicitud se vincula a un work item. Un item recibido se registra como `SRC-AZDO-<ID>` y se entrega a `faro-req-ingenieria`; una solicitud externa crea su item al crear el RM.
2. El RM registra ID, URL, organización, proyecto y área; Azure DevOps recibe el identificador del RM y vínculos disponibles a repositorio, plan, rama, PR, QA o entrega. No copiar adjuntos ni datos sensibles sin autorización explícita.
3. Al iniciar, mover el item al estado remoto que mapea a `PENDING` o `DOING`. Durante definición, análisis, UX, desarrollo, QA, validación y entrega, mantener el estado de trabajo y añadir un comentario de hito con fase FARO, versión y vínculos. Al completar el alcance autorizado, mover a `DONE`. Sólo una cancelación humana explícita permite `CANCELLED`.
4. Si una sincronización obligatoria falla, registrar `waitingOn` con el error real y no avanzar de fase.

## Límites permanentes

- `REQUIRED` autoriza crear el item de un RM, actualizar vínculos configurados, añadir comentarios de hito y cambiar su estado conforme al mapeo verificado.
- Asignar o cambiar el asignado, área, iteración, actividad, estimación, prioridad, adjuntos, borrado, tiempo o sprints requiere autorización explícita independiente, incluso si existen valores por defecto configurados.
- Azure DevOps no equivale a aprobación funcional, QA ni validación FARO.
- No exponer secretos, identificadores personales innecesarios ni datos sensibles.

## Verificación

- [ ] Proveedor, organización, proyecto, área y workflow fueron comprobados.
- [ ] PAT y demás credenciales permanecieron fuera del repositorio y de los artefactos FARO.
- [ ] Tipos, actividades, iteraciones y asignados provienen de consultas remotas verificables.
- [ ] Cada `Task` creada tiene su estimación explícita; el valor omitido fue `1`.
- [ ] Toda solicitud tiene work item, `SRC` y vínculo bidireccional con su RM.
- [ ] Cada hito relevante dejó estado o comentario remoto verificable.
