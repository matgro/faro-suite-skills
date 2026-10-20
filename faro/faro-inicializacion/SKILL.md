---
name: faro-inicializacion
description: Use when initializing a FARO workspace contract.
version: 1.3.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, initialization, bootstrap, workspace, governance]
    related_skills: [faro, faro-doctor, faro-bootstrap-laravel, faro-arq-laravel, faro-arq-mobile, faro-arq-generica, faro-int-jira, faro-int-azure-devops]
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
- No leer ni copiar secretos desde el `.env` del workspace ni incorporarlos a artefactos FARO. Esta ruta no necesita credenciales; una integración posterior puede localizar y consumir las variables necesarias desde el entorno ya inyectado o desde cualquier `.env` global perteneciente a un agente, aunque no sea Hermes, siempre fuera del workspace y de repositorios indexados. No imprimir, exportar ni persistir sus valores.
- No procesar SOL/RM/BUG/TEC durante esta ruta.

## Procedimiento

Antes de crear o reparar archivos, ejecutar con el intérprete Python disponible `python -B <skills-root>/faro/scripts/suite_validation.py` y exigir código 0. Comprueba nombres/carpetas, catálogo, referencias y `references/suite-changelog.json`. Una suite mezclada o incompleta se corrige mediante bootstrap con comparación y confirmación, no regenerando el workspace. La versión del paquete en `suite-provenance.json` es independiente de `contractVersion`; consultar el changelog para actualizaciones, sin copiar la versión del paquete al contrato ni migrar rutas automáticamente.

1. Fijar el root actual, inspeccionar `AGENTS.md`, `context/`, manifest/lockfiles, Git e instrucciones locales; identificar si hay un contrato FARO parcial. Si ya existe un contrato con configuración suficiente, detener la inicialización y entregar la ruta `faro-doctor`. **Completo:** se distinguió ausencia, parcialidad y contrato existente sin escribir sobre éste.
2. Formular una sola consulta agrupada con las decisiones necesarias: identidad del proyecto si no es verificable, tipo de proyecto (existente, nuevo u otro), stack, repositorios/fuentes a indexar si se observan, seguimiento (`OFF` o `REQUIRED`), proveedor (`JIRA` o `AZURE_DEVOPS`) y documentación funcional (`HABILITADA` o `DESHABILITADA`). Para Jira `REQUIRED`, proponer `https://matgro.atlassian.net` y `LPK`. Para Azure DevOps `REQUIRED`, pedir URL de organización, proyecto, área y equipo; si se aporta una URL de proyecto, proponer su descomposición para confirmación. **Completo:** cada decisión queda confirmada o marcada `PENDIENTE`; no se inventa una política.
3. Si el proyecto se declaró Laravel/API `nuevo` y aún no existe `composer.json`, no escribir el contrato: exigir root vacío, destino confirmado y autorización explícita, y entregar `faro-bootstrap-laravel`. Si el scaffold Laravel ya existe, continuar sin repetirlo. **Completo:** el scaffold técnico ocurre antes de `AGENTS.md` y `context/`, por lo que Composer recibe un destino vacío.
4. Leer la configuración canónica central y materializar `context/`, `context/requirements/`, `AGENTS.md`, `context/faro-workspace.json`, `context/stats.json`, `context/README.md` y `context/requirements/project-profile.md` desde sus plantillas. `context/faro-workspace.json` se crea desde `templates/faro-workspace-manifest.json`: sólo declara versión, origen y artefactos instalados; no copia ni redefine la política central. Reemplazar marcadores sólo con hechos observados o respuestas humanas; conservar `PENDIENTE` cuando falte una decisión. **Completo:** todos los archivos obligatorios existen y el manifiesto local apunta a la configuración canónica.
5. Registrar en `stats.json` `faro.version` y `contractVersion` equivalentes a la configuración central; establecer `state: initializing`, salvo que esté explícitamente `disabled`. El índice debe incluir el root, repositorios/fuentes conocidas o indicar pendientes sin afirmar evidencia inexistente. Escribir las respuestas confirmadas en `project-profile.md`; con seguimiento `REQUIRED`, entregar `faro-int-jira` o `faro-int-azure-devops` según proveedor para validar credenciales globales disponibles para algún agente, configuraciones remotas y workflow real. Si está `OFF` o pendiente, elegir una sola ruta de arquitectura con evidencia: Laravel/API con `composer.json` → `faro-arq-laravel`; móvil → `faro-arq-mobile`; otro stack confirmado → `faro-arq-generica`. **Completo:** estado, índice y manifiesto se refieren al mismo root y versión, y existe una única siguiente ruta basada en evidencia o un bloqueo con su decisión pendiente.
6. Ejecutar `python -B <skills-root>/faro/faro-doctor/scripts/doctor.py --root <root> --strict` antes de cerrar y exigir código 0. Esta comprobación local incluye coherencia de la suite y de `nextRoute` si hay workflow; no acredita procedencia remota, para la que se usa además `--verify-suite-origin`. No marcar `available`; esa transición pertenece a la arquitectura. **Completo:** el reporte identifica archivos creados/preservados, decisiones pendientes y handoff.

## Invariantes

- `faro/templates/faro-workspace-config.json` es la política estructural central; `context/faro-workspace.json` sólo acredita la versión, origen y artefactos materializados.
- El template de `AGENTS.md` es la única fuente del bloque FARO estándar; el contenido externo no se borra.
- `workflow.json` no se crea por defecto: sólo para una unidad activa que requiera continuidad.
- Una inicialización incompleta permanece en `initializing`; nunca se usa `available` como sustituto de decisiones o arquitectura pendientes.
- La configuración de seguimiento conserva sólo metadatos no secretos; los PAT de Azure DevOps viven fuera del perfil y pueden residir en el entorno o `.env` global de cualquier agente fuera del workspace.

## Verificación

- [ ] La configuración canónica fue leída y su versión quedó registrada en el workspace.
- [ ] La suite pasó la validación local antes de escribir; versión de paquete y contrato no se confundieron.
- [ ] Existen todos los directorios y archivos obligatorios declarados.
- [ ] El bloque FARO de `AGENTS.md` se originó en la plantilla y el contenido ajeno fue preservado.
- [ ] `stats.json`, `faro-workspace.json`, índice y perfil son válidos y consistentes.
- [ ] Seguimiento, proveedor y documentación funcional están confirmados o explícitamente pendientes.
- [ ] El estado sigue siendo `initializing` hasta que arquitectura complete su evidencia.
- [ ] Se indicó un único handoff o bloqueo real.
