---
name: faro-int-jira
description: Use when FARO configures and syncs required Jira work.
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, jira, integration, intake, synchronization]
    related_skills: [faro, faro-inicializacion, faro-doctor, faro-req-ingenieria, jira-rest-v3]
---

# FARO — Integración Jira

## Rol

`faro-int-jira` es el adaptador de gobernanza entre FARO y la capability externa `jira-rest-v3`. Configura Jira sólo por petición humana expresa, importa una issue como fuente `SRC` y, cuando `work_tracking.mode` es `REQUIRED` y su proveedor es `JIRA`, sincroniza el seguimiento operativo de la solicitud.

No sustituye el RM, la aprobación humana ni el análisis técnico. No implementa cambios de código.

## Cuándo usar

- Durante inicialización, después de que `faro-inicializacion` registre seguimiento `REQUIRED` y proveedor `JIRA` en el perfil.
- En un proyecto `available`, sólo si el usuario pide explícitamente agregar o configurar Jira.
- Cuando el usuario entrega una URL o clave Jira y el proyecto tiene Jira habilitado.

## Política y autorización

1. Leer el contrato FARO, `context/stats.json`, el perfil de requerimientos y el estado de integración. Confirmar que el proyecto está `available`, salvo configuración dentro de una inicialización. **Completo:** proyecto y política conocidos.
2. Durante una inicialización, verificar que `faro-inicializacion` ya registró la decisión `REQUIRED`, proveedor `JIRA`, URL y clave confirmadas —o su pendiente explícito— en el perfil; no repetir la consulta de bootstrap. Para un proyecto `available`, exigir petición explícita de agregar/configurar la integración y autorización humana antes de registrar o cambiar su política. **Completo:** decisión, URL y clave confirmadas, y fuente de autorización registradas sin secretos.
3. Registrar modo, proveedor, URL confirmada, clave del proyecto Jira, estado de credenciales y capacidades permitidas bajo `work_tracking` en `context/requirements/project-profile.md`. Con política `REQUIRED`, la URL y clave de proyecto son obligatorias antes de crear o importar solicitudes y se usan como fuentes de verdad para cada llamada; los valores no sensibles del entorno del agente sólo se aceptan si coinciden. Nunca registrar tokens, contraseñas, cookies, cabeceras Authorization ni contenido de `.env`. **Completo:** la configuración sólo contiene metadatos no sensibles y la URL/clave pertenecen inequívocamente al proyecto.
4. Con `REQUIRED`, localizar y verificar sin revelar valores las credenciales Jira disponibles para el agente, separadas de las credenciales de la aplicación, el acceso a la clave del proyecto del perfil y los estados/transiciones disponibles antes de procesar la primera solicitud. Las variables necesarias pueden leerse desde el entorno ya inyectado o desde cualquier `.env` global perteneciente a un agente, aunque no sea Hermes; FARO puede buscarlos en directorios de configuración de agentes fuera del workspace. Nunca buscar ni leer `.env` del workspace, de repositorios indexados ni de una aplicación. Usar los valores sólo para ejecutar la llamada autenticada y no imprimirlos, exportarlos ni persistirlos. Registrar en el perfil el mapeo real del proyecto: una equivalencia de pendiente (`Pendiente`, `Por hacer` u otro nombre confirmado) → `PENDING`; una de trabajo (`Haciendo` u otro nombre confirmado) → `DOING`; una de cierre (`Finalizado`, `Done` u otro nombre confirmado) → `DONE`. La equivalencia `CANCELLED` se registra si existe; si falta, sólo las cancelaciones quedan bloqueadas hasta que el workflow Jira la incorpore. Si falta PENDING, DOING o DONE, registrar el bloqueo y no simular sincronización. **Completo:** el mapeo se basa en el workflow real del proyecto.
5. Si no se encuentran credenciales Jira válidas en el entorno inyectado o en los `.env` globales de agentes, no consultar ni modificar Jira. Solicitar su configuración segura en el entorno de un agente, fuera del repositorio y del workspace, o aceptar URL, exportación o texto aportado por el usuario como fuente manual únicamente si la política no es `REQUIRED`. Nunca reutilizar credenciales de la aplicación. **Completo:** se buscaron sólo fuentes globales de agentes, sin exposición, persistencia ni llamada remota no autenticada.

## Trazabilidad Jira REQUIRED

1. Toda solicitud debe estar vinculada a una issue. Una issue recibida se registra como `SRC-JIRA-<KEY>` y se entrega a `faro-req-ingenieria`, salvo reportes que requieren investigar un síntoma/causa desconocida, que se entregan a `faro-incidentes` sin confirmar BUG por el tipo remoto. Una solicitud externa crea su issue al crear el RM; un INC crea o vincula su seguimiento según la regla siguiente.
   Para INC, exigir tipo neutral sólo para items nuevos y verificar el workflow real del proyecto; si falta ese mapeo para el alta, pedir la decisión, no inventar un tipo Incident ni usar Bug por defecto. Conservar el item recibido aunque sea de tipo Bug, con su ID, tipo y workflow verificados: su tipo remoto no confirma un defecto. No exigir otro item neutral ni duplicarlo/reclasificarlo automáticamente; crear un item neutral separado requiere decisión explícita y vínculo con el original. `REQUIRED` autoriza crear/vincular el item de investigación INC y sincronizar sus hitos, vínculos y transiciones verificadas. No autoriza crear el BUG derivado sin decisión explícita, reclasificar el item recibido ni modificar el esquema Jira. INC y corrección tienen vínculos bidireccionales; cerrar la corrección no cierra automáticamente el incidente. Verificar por lectura toda escritura y aplicar el criterio de cierre de `faro-incidentes` al item del INC.
2. El RM debe registrar clave, URL y proyecto Jira; Jira debe recibir el identificador del RM y los vínculos disponibles al repositorio, plan, rama, PR, evidencia de QA o entrega. No copiar adjuntos ni datos sensibles salvo petición y autorización explícitas.
3. Al iniciar la solicitud, transicionar a `Pendiente`/`Por hacer` o a `Haciendo`, según el workflow real. Durante definición, análisis técnico, UX, desarrollo, QA, validación y entrega, mantener `Haciendo` y añadir sólo las actualizaciones relevantes conforme a `../references/comment-format.md`: inicio/cierre de fase, unidad material completada o bloqueada, decisión o bloqueo, y referencia externa durable. Al completar el alcance autorizado, transicionar a `Finalizado`/`Done`. Sólo una cancelación humana explícita permite transicionar a `Cancelado`.
4. Si una sincronización obligatoria falla, no avanzar a la siguiente fase: registrar `waitingOn` con el error real. No exponer secretos ni ocultar el fallo.

## Límites permanentes

- `REQUIRED` autoriza únicamente crear la issue de un RM o del INC solicitado con tipo neutral confirmado, actualizar los vínculos configurados, añadir las actualizaciones relevantes definidas por la plantilla y transicionarla conforme a esta regla. No crear un BUG derivado sin autorización explícita.
- Asignar, editar prioridad/campos no configurados, adjuntar, borrar, registrar tiempos y gestionar sprints requieren autorización explícita independiente.
- Jira no equivale a aprobación funcional, QA ni validación FARO; el RM conserva esas fuentes de verdad.
- No exponer secretos, identificadores personales innecesarios ni información clínica en fuentes o reportes.

## Verificación

- [ ] Modo, autorización, proyecto y workflow Jira fueron comprobados.
- [ ] Credenciales globales de agentes permanecieron fuera de repositorios y artefactos FARO.
- [ ] Toda solicitud tiene issue, `SRC` y vínculo bidireccional con su RM.
- [ ] Cada hito o unidad material relevante dejó un estado o comentario Jira conciso y verificable.
- [ ] La issue quedó vinculada como fuente, no como aprobación implícita.
- [ ] Se indicó el siguiente handoff o el bloqueo real.
