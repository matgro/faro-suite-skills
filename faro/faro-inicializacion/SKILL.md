---
name: faro-inicializacion
description: Use when initializing a FARO workspace contract.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, initialization, bootstrap, workspace, governance]
    related_skills: [faro, faro-doctor, faro-bootstrap-laravel, faro-bootstrap-dotnet, faro-arq-laravel, faro-arq-dotnet, faro-arq-mobile, faro-arq-generica, faro-int-jira, faro-int-azure-devops]
---

# FARO — Inicialización de espacio de trabajo

En cada interacción, leer y aplicar [Glosario de dominio](../references/domain-glossary.md) para `context/glossary.md`. No crearlo vacío: sólo después de materializar el contrato y con conocimiento sustentado; indexarlo sin modificar los artefactos obligatorios del manifiesto.

## Rol

Crea el contrato persistente y configurable de FARO en el root coordinador. Esta skill no formaliza solicitudes ni declara el proyecto `available`: deja un espacio inicializado, verificable y listo para que la ruta de arquitectura reúna evidencia.

La configuración canónica esperada para cada versión está en `faro/templates/faro-workspace-config.json`. Es la fuente que define los directorios, archivos obligatorios, archivos condicionales, estados admitidos y plantillas autorizadas. No inventar variantes de archivos ni contenido de contrato fuera de esas plantillas.

## Cuándo usar

- `faro-doctor` clasificó el root exactamente como `absent` durante un pedido de inicialización.
- El usuario pide preparar un directorio para trabajo gobernado por FARO y no existe un espacio FARO válido.

No usar cuando el doctor clasifica `current`, `legacy-migratable`, `mixed-ambiguous`, `future-unsupported` o `corrupt`: el contrato existente se continúa, migra o repara por su ruta explícita, nunca se sobrescribe ni reinicializa. Un `AGENTS.md` ajeno sin delimitadores FARO no acredita un contrato y se preserva íntegro.

## Entradas y límites

- El root coordinador es el directorio de trabajo actual; rutas externas aportadas son fuentes de evidencia y no reciben escrituras FARO.
- Leer `faro/templates/faro-workspace-config.json` antes de crear archivos. Crear únicamente las rutas que declara.
- Para `AGENTS.md`, preservar byte a byte todo contenido ajeno y agregar exactamente el bloque `<!-- FARO:START -->` / `<!-- FARO:END -->` de `templates/AGENTS.md`. Si ya hay cualquier delimitador FARO, detenerse y volver a doctor; inicialización no reemplaza bloques. Si el archivo no existe, crearlo desde la plantilla estándar.
- No leer ni copiar secretos desde el `.env` del workspace ni incorporarlos a artefactos FARO. Esta ruta no necesita credenciales; una integración posterior puede localizar y consumir las variables necesarias desde el entorno ya inyectado o desde cualquier `.env` global perteneciente a un agente, aunque no sea Hermes, siempre fuera del workspace y de repositorios indexados. No imprimir, exportar ni persistir sus valores.
- No procesar SOL/RM/BUG/TEC durante esta ruta.

## Procedimiento

Antes de crear o reparar archivos, ejecutar con el intérprete Python disponible `python -B <skills-root>/faro/scripts/suite_validation.py` y exigir código 0. Comprueba nombres/carpetas, catálogo, referencias y `references/suite-changelog.json`. Una suite mezclada o incompleta se corrige mediante bootstrap con comparación y confirmación, no regenerando el workspace. La versión del paquete en `suite-provenance.json` es independiente de `contractVersion`; consultar el changelog para actualizaciones, sin copiar la versión del paquete al contrato ni migrar rutas automáticamente.

1. Fijar el root actual y ejecutar doctor en sólo lectura. Continuar únicamente con clasificación `absent`; `AGENTS.md` ajeno por sí solo sigue siendo `absent`, pero cualquier manifiesto, estado, perfil, catálogo o delimitador FARO parcial exige detenerse. No tratar `legacy-migratable`, `mixed-ambiguous`, `future-unsupported` o `corrupt` como un root vacío ni invocar el migrador desde esta skill. **Completo:** la ausencia quedó demostrada sin escribir.
2. Formular una sola consulta agrupada con las decisiones necesarias: identidad del proyecto si no es verificable, tipo de proyecto (existente, nuevo u otro), stack, repositorios/fuentes a indexar si se observan, seguimiento (`OFF` o `REQUIRED`), proveedor (`JIRA` o `AZURE_DEVOPS`) y documentación funcional (`HABILITADA` o `DESHABILITADA`). Para Jira `REQUIRED`, proponer `https://matgro.atlassian.net` y `LPK`. Para Azure DevOps `REQUIRED`, pedir URL de organización, proyecto, área y equipo; si se aporta una URL de proyecto, proponer su descomposición para confirmación. **Completo:** cada decisión queda confirmada o marcada `PENDIENTE`; no se inventa una política.
3. Si el proyecto se declaró Laravel/API `nuevo` y aún no existe `composer.json`, no escribir el contrato: exigir root vacío, destino confirmado y autorización explícita, y entregar `faro-bootstrap-laravel`. Si el proyecto se declaró .NET/C# `nuevo` y aún no existe `.sln` ni `.csproj`, aplicar la misma regla y entregar `faro-bootstrap-dotnet`; éste exige una plantilla `dotnet new` confirmada. Si los scaffolds ya existen, continuar sin repetirlos. **Completo:** el scaffold técnico ocurre antes de `AGENTS.md` y `context/`, por lo que Composer y `dotnet new` reciben un destino vacío.
4. Leer la configuración canónica central y materializar `context/` como parte de sus cuatro directorios requeridos: `context/`, `context/requirements/`, `context/requirements/functional/` y `context/requirements/work-items/`. Crear los siete archivos obligatorios desde sus fuentes declaradas: `AGENTS.md`, `context/faro-workspace.json`, `context/stats.json`, `context/README.md`, `context/requirements/project-profile.md`, `context/requirements/requirements-catalog.md` y `context/requirements/functional-documents-catalog.md`. El manifiesto local sólo declara versión, origen y esos siete artefactos; no copia política. Reemplazar marcadores sólo con hechos o respuestas humanas y conservar `PENDIENTE`/`null` cuando falte una decisión. No crear unidades, documentos funcionales, incidentes, reservas, `workflow.json` ni un registro de migración. **Completo:** estructura v2 vacía, catálogos canónicos y contenido ajeno de AGENTS preservado.
5. Registrar en `stats.json` `schemaVersion: 2` y `contractVersion` desde la configuración contractual central, pero `faro.version` desde `references/suite-provenance.json`: versión del paquete y versión del contrato son autoridades independientes aunque hoy coincidan. Registrar fecha UTC ISO-8601 con zona y exactamente `state: initializing`. El índice incluye el root y sólo fuentes confirmadas. Escribir respuestas confirmadas en el perfil, manteniendo en `null` todo tipo remoto, workflow, campo, actividad, estimación o asignación que no haya sido observado y confirmado; inicializar no acredita defaults de Jira/Azure DevOps. Con seguimiento `REQUIRED`, entregar el adaptador del proveedor para descubrir y verificar su configuración. Si está `OFF` o pendiente, elegir una ruta única por evidencia: Laravel/API con `composer.json` → `faro-arq-laravel`; .NET/C# con `.sln`, `.csproj` o `global.json` → `faro-arq-dotnet`; móvil → `faro-arq-mobile`; otro stack confirmado → `faro-arq-generica`. **Completo:** estado, índice, catálogos, manifiesto y perfil concuerdan sin inventar configuración remota.
6. Ejecutar `python -B <skills-root>/faro/faro-doctor/scripts/doctor.py --root <root> --strict` antes de cerrar y exigir código 0. Esta comprobación local incluye coherencia de la suite y de `nextRoute` si hay workflow; no acredita procedencia remota, para la que se usa además `--verify-suite-origin`. No marcar `available`; esa transición pertenece a la arquitectura. **Completo:** el reporte identifica archivos creados/preservados, decisiones pendientes y handoff.

## Invariantes

- `faro/templates/faro-workspace-config.json` es la política estructural central; `context/faro-workspace.json` sólo acredita la versión, origen y artefactos materializados.
- El template de `AGENTS.md` es la única fuente del bloque FARO estándar; el contenido externo no se borra.
- `workflow.json` no se crea por defecto: sólo para una unidad activa que requiera continuidad.
- Inicialización no crea RM/BUG/TEC/DF/INC, reservas, expedientes ni `context/faro-migration-v2.json`; tampoco convierte layouts legacy.
- Una inicialización incompleta permanece en `initializing`; nunca se usa `available` como sustituto de decisiones o arquitectura pendientes.
- La configuración de seguimiento conserva sólo metadatos no secretos; los PAT de Azure DevOps viven fuera del perfil y pueden residir en el entorno o `.env` global de cualquier agente fuera del workspace.

## Verificación

- [ ] La configuración canónica fue leída y su versión quedó registrada en el workspace.
- [ ] La suite pasó la validación local antes de escribir; versión de paquete y contrato no se confundieron.
- [ ] Existen los cuatro directorios y siete archivos obligatorios declarados, incluidos ambos catálogos vacíos.
- [ ] El bloque FARO de `AGENTS.md` se originó en la plantilla y el contenido ajeno fue preservado.
- [ ] `stats.json`, `faro-workspace.json`, índice y perfil son válidos y consistentes.
- [ ] No se creó workflow, unidad, incidente ni registro de migración, y ningún default remoto no verificado quedó acreditado.
- [ ] Seguimiento, proveedor y documentación funcional están confirmados o explícitamente pendientes.
- [ ] El estado sigue siendo `initializing` hasta que arquitectura complete su evidencia.
- [ ] Se indicó un único handoff o bloqueo real.
