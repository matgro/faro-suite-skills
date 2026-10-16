---
name: faro-inicializacion
description: Use when initializing a FARO workspace contract.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, initialization, bootstrap, workspace, governance]
    related_skills: [faro, faro-doctor, faro-arq-laravel, faro-arq-mobile, faro-arq-generica, faro-int-jira, faro-int-azure-devops]
---

# FARO — Inicialización de espacio de trabajo

## Rol

Crea el contrato persistente y configurable de FARO en el root coordinador. Esta skill no formaliza solicitudes ni declara el proyecto `available`: deja un espacio inicializado, verificable y listo para que la ruta de arquitectura reúna evidencia.

La configuración canónica esperada para cada versión está en `faro/templates/faro-workspace-config.json`. Es la fuente que define los directorios, archivos obligatorios, archivos condicionales, estados admitidos y plantillas autorizadas. No inventar variantes de archivos ni contenido de contrato fuera de esas plantillas.

## Cuándo usar

- `faro` detecta ausencia de contrato FARO o `state` igual a `new`/`initializing` durante un pedido de inicialización.
- El usuario pide preparar un directorio para trabajo gobernado por FARO y no existe un espacio FARO válido.
- Un diagnóstico reporta contrato incompleto y el usuario autoriza explícitamente repararlo o inicializarlo.

No usar cuando el contrato ya existe: `faro` debe enrutar a `faro-doctor`, que informa sin sobrescribir ni reinicializar.

## Entradas y límites

- El root coordinador es el directorio de trabajo actual; rutas externas aportadas son fuentes de evidencia y no reciben escrituras FARO.
- Leer `faro/templates/faro-workspace-config.json` antes de crear archivos. Crear únicamente las rutas que declara.
- Para `AGENTS.md`, preservar todo contenido ajeno y crear o reemplazar sólo el bloque `<!-- FARO:START -->` / `<!-- FARO:END -->` con `templates/AGENTS.md`. Si el archivo no existe, crearlo desde esa plantilla estándar.
- No leer secretos ni copiar `.env`; las credenciales se mantienen fuera de los artefactos FARO.
- No procesar SOL/RM/BUG/TEC durante esta ruta.

## Procedimiento

1. Fijar el root actual, inspeccionar `AGENTS.md`, `context/`, manifest/lockfiles, Git e instrucciones locales; identificar si hay un contrato FARO parcial. Si ya existe un contrato con configuración suficiente, detener la inicialización y entregar la ruta `faro-doctor`. **Completo:** se distinguió ausencia, parcialidad y contrato existente sin escribir sobre éste.
2. Leer la configuración canónica central y materializar `context/`, `context/requirements/`, `AGENTS.md`, `context/faro-workspace.json`, `context/stats.json`, `context/README.md` y `context/requirements/project-profile.md` desde sus plantillas. `context/faro-workspace.json` se crea desde `templates/faro-workspace-manifest.json`: sólo declara versión, origen y artefactos instalados; no copia ni redefine la política central. Reemplazar marcadores sólo con hechos observados o respuestas humanas; conservar `PENDIENTE` cuando falte una decisión. **Completo:** todos los archivos obligatorios existen y el manifiesto local apunta a la configuración canónica.
3. Registrar en `stats.json` `faro.version` y `contractVersion` equivalentes a la configuración central; establecer `state: initializing`, salvo que esté explícitamente `disabled`. El índice debe incluir el root, repositorios/fuentes conocidas o indicar pendientes sin afirmar evidencia inexistente. **Completo:** estado, índice y manifiesto se refieren al mismo root y versión.
4. Formular una sola consulta agrupada con las decisiones necesarias: identidad del proyecto si no es verificable, tipo de proyecto (existente, nuevo u otro), repositorios/fuentes a indexar si no se observan, seguimiento (`OFF` o `REQUIRED`), proveedor (`JIRA` o `AZURE_DEVOPS`) y documentación funcional (`HABILITADA` o `DESHABILITADA`). Para Jira `REQUIRED`, proponer `https://matgro.atlassian.net` y `LPK`. Para Azure DevOps `REQUIRED`, pedir URL de organización, proyecto, área y equipo; si se aporta una URL de proyecto, proponer su descomposición para confirmación. **Completo:** cada decisión queda confirmada o marcada `PENDIENTE`; no se inventa una política.
5. Escribir las respuestas confirmadas en `project-profile.md`; con seguimiento `REQUIRED`, entregar `faro-int-jira` o `faro-int-azure-devops` según proveedor para validar credenciales separadas, configuraciones remotas y workflow real. Si está `OFF` o pendiente, elegir una sola ruta de arquitectura con evidencia: Laravel/API → `faro-arq-laravel`; móvil → `faro-arq-mobile`; otro stack confirmado → `faro-arq-generica`. **Completo:** existe una única siguiente ruta basada en evidencia o un bloqueo con su decisión pendiente.
6. Ejecutar `faro-doctor/scripts/doctor.py --root <root>` o las mismas comprobaciones antes de cerrar. No marcar `available`; esa transición pertenece a la arquitectura. **Completo:** el reporte identifica archivos creados/preservados, decisiones pendientes y handoff.

## Invariantes

- `faro/templates/faro-workspace-config.json` es la política estructural central; `context/faro-workspace.json` sólo acredita la versión, origen y artefactos materializados.
- El template de `AGENTS.md` es la única fuente del bloque FARO estándar; el contenido externo no se borra.
- `workflow.json` no se crea por defecto: sólo para una unidad activa que requiera continuidad.
- Una inicialización incompleta permanece en `initializing`; nunca se usa `available` como sustituto de decisiones o arquitectura pendientes.
- La configuración de seguimiento conserva sólo metadatos no secretos; los PAT de Azure DevOps viven fuera del perfil.

## Verificación

- [ ] La configuración canónica fue leída y su versión quedó registrada en el workspace.
- [ ] Existen todos los directorios y archivos obligatorios declarados.
- [ ] El bloque FARO de `AGENTS.md` se originó en la plantilla y el contenido ajeno fue preservado.
- [ ] `stats.json`, `faro-workspace.json`, índice y perfil son válidos y consistentes.
- [ ] Seguimiento, proveedor y documentación funcional están confirmados o explícitamente pendientes.
- [ ] El estado sigue siendo `initializing` hasta que arquitectura complete su evidencia.
- [ ] Se indicó un único handoff o bloqueo real.
