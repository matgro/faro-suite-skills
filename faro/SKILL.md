---
name: faro
description: Use when user invokes FARO project routing.
version: 1.13.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, project, routing, governance, requirements]
    related_skills: [faro-inicializacion, faro-doctor, faro-arq-laravel, faro-arq-mobile, faro-arq-generica, faro-documentacion-funcional, faro-req-ingenieria, faro-req-analisis-tecnico, faro-req-implementacion, faro-qa-ejecucion, faro-req-validacion, faro-ux, faro-entrega, faro-int-jira, faro-int-azure-devops, azure-devops-rest-v7]
---

# FARO — Orquestador de proyecto

## Rol

`faro` es el único punto de entrada y router de FARO. No crea ni repara contratos por sí mismo: `faro-inicializacion` materializa un workspace nuevo y `faro-doctor` diagnostica uno existente. FARO tampoco formaliza requisitos, diseña, implementa, prueba, valida ni despliega; identifica estado y carga exactamente una skill `faro-*` especializada. `azure-devops-rest-v7` es capability técnica del adaptador `faro-int-azure-devops`, no una ruta de ciclo de vida directa.

El contrato persistente del workspace vive en `AGENTS.md`, `context/faro-workspace.json`, `context/stats.json`, `context/README.md`, `context/requirements/project-profile.md` y, sólo para continuidad activa, `context/workflow.json`. `templates/faro-workspace-config.json` es la política estructural canónica y central: declara los archivos/directorios requeridos y las plantillas aprobadas. `context/faro-workspace.json` es únicamente un manifiesto local de versión y artefactos instalados; no puede redefinir la política FARO. La lógica de inicialización, ruteo, Jira, autorización y entrega vive exclusivamente en `faro` y las skills `faro-*`.

## Activación

Usar cuando el usuario diga `usa faro-<nombre>`, pida inicializar, reanudar, diagnosticar/revisar estado o realizar trabajo gobernado por FARO, o cuando exista el bloque `FARO:START` en `AGENTS.md`.

No tomar control de un directorio ajeno sin invocación FARO explícita.

## Regla de root

El root coordinador es siempre el directorio de trabajo actual de la sesión. Se crean o actualizan contratos FARO sólo allí; una ruta aportada como código, documentación o evidencia se registra en el índice y no recibe escrituras FARO. Cambiar el root exige una instrucción humana explícita.

## Detección de workspace e inicialización

1. Antes de enrutar, fijar root y comprobar existencia de `AGENTS.md`, bloque `FARO:START`/`FARO:END`, `context/faro-workspace.json`, `context/stats.json`, `context/README.md`, perfil y workflow opcional. Después pueden inspeccionarse fuentes externas aportadas. **Completo:** se conoce si el workspace es ausente, existente completo o existente parcial.
2. Ante “inicializa/prepara con FARO”: si no hay bloque FARO ni artefacto FARO, cargar `faro-inicializacion`. Si existe cualquiera de ellos —incluso incompleto, en `new` o `initializing`— cargar `faro-doctor`, informar que el espacio ya existe y mostrar su estado; no reinicializar ni reparar sin una autorización posterior explícita. **Completo:** una inicialización repetida nunca sobrescribe información.
3. Para pedidos no inicializadores con contrato existente, validar JSON y leer configuración, índice, estado, perfil y workflow. Un JSON malformado se informa y se enruta a `faro-doctor`; no se descarta ni se reemplaza. **Completo:** versión/estado/configuración son conocidos antes de cargar otra skill.
4. Si `state` es `disabled`, detener FARO. Si el contrato existe y `state` es `new` o `initializing`, seguir la ruta de arquitectura aplicable o el adaptador de seguimiento confirmado cuando `work_tracking.mode` sea `REQUIRED`; no recibir SOL/RM/BUG/TEC. **Completo:** no hay intake antes de `available`.
5. Comparar la versión instalada con la configuración canónica. Una configuración anterior puede ser diagnosticada y migrada sólo bajo autorización explícita; una posterior nunca se degrada. **Completo:** el contrato es versionado y no se inventa una migración.

## Contrato inicial administrado

`faro-inicializacion` crea y mantiene únicamente las rutas declaradas por `templates/faro-workspace-config.json`:

| Ruta | Propósito |
| --- | --- |
| `AGENTS.md` | Manifiesto mínimo de la instancia; conserva contenido externo y administra sólo `<!-- FARO:START -->` / `<!-- FARO:END -->` desde `templates/AGENTS.md`. No replica política global. |
| `context/faro-workspace.json` | Manifiesto local con versión, origen del contrato y artefactos instalados; la política se lee centralmente desde `templates/faro-workspace-config.json`. |
| `context/stats.json` | Identidad, versión, repositorios y estado del proyecto. |
| `context/README.md` | Índice de código, documentación y fuentes. |
| `context/requirements/project-profile.md` | Decisiones de seguimiento, proveedor y documentación funcional, sin secretos. |
| `context/workflow.json` | Sólo continuidad de una unidad activa; no duplica RM, planes ni tareas. |

Durante inicialización se formula una sola consulta agrupada para identidad/tipo/fuentes que no puedan observarse, seguimiento de trabajo (`OFF`/`REQUIRED`), proveedor (`JIRA`/`AZURE_DEVOPS`) y documentación funcional (`HABILITADA`/`DESHABILITADA`). Con Jira `REQUIRED`, se proponen `https://matgro.atlassian.net` y `LPK`. Con Azure DevOps `REQUIRED`, se pide URL de organización, proyecto, área y equipo; una URL de proyecto aportada puede descomponerse como propuesta, pero cada valor se confirma. Un proyecto queda `initializing` hasta que una skill de arquitectura registre evidencia y habilite `available`.

## Tabla de ruteo

| Señal y precondición | Cargar | Salida / siguiente ruta |
| --- | --- | --- |
| Pedido explícito de inicializar; no hay bloque ni artefactos FARO | `faro-inicializacion` | Contrato versionado en `initializing`, decisiones registradas y handoff único. |
| Pedido explícito de inicializar; existe bloque o cualquier artefacto FARO | `faro-doctor` | “Espacio existente”, estado, integridad y recomendación sin escribir. |
| Pedido de diagnóstico/estado/salud FARO | `faro-doctor` | Estado verificable, faltantes y recomendación sin crear artefactos. |
| Contrato existente incompleto, inválido o versiones incompatibles | `faro-doctor` | Bloqueo y propuesta de reparación con autorización explícita. |
| Estado `new`/`initializing`, seguimiento `REQUIRED`, proveedor `JIRA` | `faro-int-jira` | Proyecto/workflow Jira verificados sin secretos; volver a arquitectura. |
| Estado `new`/`initializing`, seguimiento `REQUIRED`, proveedor `AZURE_DEVOPS` | `faro-int-azure-devops` | Organización, proyecto, configuraciones remotas y workflow Azure DevOps verificados sin secretos; volver a arquitectura. |
| Estado `new`/`initializing`, Laravel/API confirmado | `faro-arq-laravel` | Arquitectura evidenciada; completar disponibilidad. |
| Estado `new`/`initializing`, proyecto móvil confirmado | `faro-arq-mobile` | Arquitectura evidenciada; completar disponibilidad. |
| Estado `new`/`initializing`, stack confirmado distinto | `faro-arq-generica` | Arquitectura mínima basada en evidencia; completar disponibilidad. |
| `available`; agregar/configurar Jira explícitamente | `faro-int-jira` | Integración autorizada o issue enlazada como `SRC`. |
| `available`; agregar/configurar Azure DevOps / Visual Studio explícitamente | `faro-int-azure-devops` | Integración autorizada o work item enlazado como `SRC`. |
| `available`; perfil DF `HABILITADA`; solicitud funcional/cambio/BUG sin esperado o DF | `faro-documentacion-funcional` | DF identificado/creado; si hay cambio, siguiente ruta `faro-req-ingenieria`. |
| `available`; solicitud funcional/cambio/BUG sin esperado; DF no habilitada | `faro-req-ingenieria` | RM/BUG/TEC trazable, versión y estado de definición. |
| RM/BUG/TEC requiere aclarar, cambiar alcance o resolver PD | `faro-req-ingenieria` | Artefacto funcional actualizado. |
| RM/BUG/TEC autorizado; impacto, plan o tareas | `faro-req-analisis-tecnico` | Plan/tareas contra código, estado técnico. |
| Plan `LISTO_PARA_DESARROLLO`; autorización exacta; implementar | `faro-req-implementacion` | Incremento implementado, tareas/evidencia actualizadas. |
| Incremento construido; QA, casos, reproducción o pruebas | `faro-qa-ejecucion` | Casos, evidencia, BUGs y cobertura ejecutada. |
| Comparar entrega con RM/BUG/TEC autorizado | `faro-req-validacion` | Informe CONFORME/NO_CONFORME/NO_VERIFICADO. |
| RF/CA afectan pantalla, flujo, navegación o estados visibles | `faro-ux` | Diseño proporcional y catálogo frontend respetado. |
| Commit, PR, release, despliegue o rollback explícito | `faro-entrega` | Acción de salida explícitamente autorizada. |
| Consulta sin cambio de artefacto en `available` | Responder desde el contrato | Sin creación artificial de flujo. |

## Continuidad e invariantes

- Cargar una sola skill especialista por petición; sólo otra especialista puede ordenar el siguiente handoff o el usuario cambiar de fase.
- La configuración canónica central, no los archivos de proyecto, define la política FARO y las rutas permitidas.
- El manifiesto local sólo acredita versión/origen/artefactos instalados; no puede autorizar ni desautorizar una ruta.
- Las decisiones específicas del proyecto (seguimiento, proveedor, URL, proyecto, área, clave y mapeos) viven en `project-profile.md`, sin secretos.
- `workflow.json` no sustituye `context/requirements/`: RM, plan y validación conservan sus propias fuentes de verdad.
- Una unidad tiene `todo`, `doing`, `done` o `dropped`; máximo una `doing`.
- `authorization.status` señala versión y alcance autorizados; otra versión no habilita trabajo.
- El código observado no sustituye una decisión funcional.
- Una skill instalada no autoriza su uso: arquitectura, contrato y artefacto activo deciden.
- No inventar stack, comandos, roles, reglas, endpoints, tablas ni validaciones.
- Despliegue requiere ambiente y autorización explícitos.

## Verificación

- [ ] Root, presencia del workspace y estado fueron leídos antes de enrutar.
- [ ] Un pedido repetido de inicialización fue enviado a `faro-doctor`, no a escritura.
- [ ] La configuración versionada declara cada archivo creado o comprobado.
- [ ] El estado permite la ruta elegida.
- [ ] La única skill cargada corresponde a una fila de la tabla.
- [ ] La autorización/versiones coinciden antes de análisis técnico, implementación, QA o entrega.
- [ ] El bloque FARO y JSON conservan información no administrada.
