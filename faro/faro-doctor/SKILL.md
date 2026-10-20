---
name: faro-doctor
description: Use when diagnosing an existing FARO workspace.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, doctor, diagnosis, workspace, governance]
    related_skills: [faro, faro-inicializacion, faro-arq-laravel, faro-arq-dotnet, faro-arq-mobile, faro-arq-generica, faro-arq-adr, faro-arq-rfc]
---

# FARO — Diagnóstico del espacio de trabajo

## Rol

Inspecciona un espacio FARO existente y muestra un estado verificable sin inicializarlo, regenerarlo ni sobrescribir información. Es la respuesta obligatoria a un pedido de inicialización cuando el contrato FARO ya existe: informa que el espacio ya está presente, su estado y la acción de recuperación o continuación aplicable.

## Cuándo usar

- El usuario pide inicializar y existe un bloque `FARO:START`/`FARO:END` o artefactos FARO en el root actual.
- Se pide revisar salud, existencia, versión, integridad o estado de un espacio FARO.
- `faro-inicializacion` necesita comprobar su resultado antes de cerrar.

No usar para crear ni reparar por iniciativa propia. Si encuentra faltantes, los informa y propone `faro-inicializacion` sólo cuando el usuario autorice reparación.

## Ejecución

Ejecutar de forma sólo lectura desde cualquier ubicación:

```bash
python3 -B <skills-root>/faro/faro-doctor/scripts/doctor.py --root "$PWD" --verify-suite-origin --strict
```

`--verify-suite-origin` es obligatorio para un diagnóstico completo: resuelve la etiqueta Git inmutable declarada por la suite, obtiene esa revisión temporalmente y compara cada archivo instalado con sus checksums publicados. Requiere `git` y conectividad al remoto; un tag ausente, remoto inaccesible o árbol distinto es un bloqueo real. Usar `--strict` para que faltantes, JSON inválidos o una verificación de origen solicitada que falle devuelvan código distinto de cero. El script no repara ni crea archivos en el workspace; el procedimiento interpreta el resultado y define el handoff.

## Comprobaciones

El diagnóstico siempre ejecuta las comprobaciones locales compartidas de `scripts/suite_validation.py`: nombres, carpetas, catálogo, referencias y changelog distribuido. Inspecciona `workflow.nextRoute` aunque la versión del contrato coincida. Una ruta retirada se muestra con su destino vigente y bloquea en modo estricto; una ruta desconocida o JSON inválido también bloquea. Nunca ejecuta el renombre ni altera aprobaciones.

1. Fijar el root actual y leer `AGENTS.md`, el manifiesto `context/faro-workspace.json`, `context/stats.json`, `context/README.md`, `context/requirements/project-profile.md` y `context/workflow.json` si existe. Leer `faro/templates/faro-workspace-config.json` como norma central de versión y estructura. El manifiesto local sólo debe declarar versión, origen del contrato y artefactos instalados; no se interpreta como política. **Completo:** cada archivo se clasifica como presente, ausente, inválido o no aplicable.
2. Confirmar que `AGENTS.md` posee exactamente un bloque FARO delimitado y que corresponde a la plantilla estándar sin evaluar ni alterar contenido externo. Confirmar que las rutas obligatorias declaradas por la configuración existen. **Completo:** el informe separa contrato estándar, contenido ajeno y faltantes.
3. Validar JSON y coherencia: `schemaVersion`, `contractVersion`, `faro.version`, `project`, `state`, `updatedAt` y rutas. La versión instalada se compara con la versión esperada de la configuración; una versión posterior no se degrada. **Completo:** incompatibilidades y JSON malformados se informan textualmente.
4. Verificar el origen Git de la suite con `--verify-suite-origin`: leer `references/suite-provenance.json`, resolver sólo su etiqueta remota inmutable, obtener temporalmente esa revisión y comparar el árbol `faro/` con `checksums.sha256` remoto. No aceptar una rama mutable, un SHA aportado por el ambiente ni un tag no resoluble. **Completo:** se informa repositorio, tag, commit resuelto y coincidencia byte a byte, o el bloqueo concreto.
5. Informar identidad, estado (`new`, `initializing`, `available` o `disabled`), repositorios/fuentes indexados, decisiones de seguimiento/proveedor/DF, arquitectura registrada, workflow activo y bloqueos. No presentar una ausencia como evidencia de inexistencia en el proyecto; usar “no indexado” o “no encontrado en el contrato”. **Completo:** el reporte contesta qué existe y qué falta sin suposiciones.
6. Resolver la recomendación sin escribir: `disabled` → detener; suite mezclada/incompleta u origen no verificable → revisar publicación/procedencia y actualizar la suite mediante bootstrap con confirmación, sin reinicializar el workspace; ruta de workflow retirada/desconocida → consultar changelog y pedir autorización para la corrección puntual; contrato incompleto/corrupto → reparación autorizada; `new`/`initializing` íntegro → ruta de arquitectura evidenciada; `available` → seguir la ruta FARO correspondiente al pedido. Ante JSON de workflow malformado, no recrearlo ni proponer una sustitución ciega. **Completo:** se informa una recomendación, no una acción automática.
7. Con `--check-external-skills`, leer `references/laravel-external-skills.json` y ejecutar solamente `hermes skills check <name>` para las capabilities declaradas. Informar instalada/actualizable/no verificable; no ejecutar `update`, `install` ni `--force`. Si hay actualización, recomendar el bootstrap FARO con autorización explícita para que la actualice y la audite. **Completo:** el estado externo se reporta sin modificar skills ni workspace.

## Formato mínimo del informe

- “Espacio FARO existente: sí/no” y root inspeccionado.
- Versión esperada / instalada y compatibilidad.
- Versión de paquete separada del contrato, coherencia local y ubicación de `references/suite-changelog.json`.
- Rutas obsoletas/desconocidas y reemplazos propuestos. Para un renombre autorizado, cambiar sólo `nextRoute`, preservar el resto y volver a ejecutar doctor; nunca editar documentos históricos por búsqueda y reemplazo global.
- Repositorio, tag y commit de origen de la suite, más el resultado de checksums remotos.
- Lista de archivos requeridos: presente, ausente o inválido.
- Estado, proyecto, arquitectura, configuraciones de seguimiento/proveedor/DF y workflow.
- Faltantes, bloqueos y siguiente ruta recomendada.

## Invariantes

- Diagnosticar no concede permiso para reparar, inicializar, migrar, cambiar estado ni crear workflow.
- No borrar ni recrear JSON malformado; reportarlo tal como bloqueo.
- No revelar secretos ni leer archivos de entorno.
- La procedencia de release usa una etiqueta Git inmutable; una rama, la versión declarativa o el remoto local no prueban el origen del árbol instalado.
- Doctor es de solo lectura: comprobar actualizaciones no autoriza instalarlas ni aplicarlas.
- Un contrato existente pero incompleto sigue siendo existente: nunca se reemplaza silenciosamente.

## Verificación

- [ ] El informe dice expresamente si el espacio ya existe.
- [ ] Cada requisito de la configuración versionada fue comprobado.
- [ ] JSON, versiones y estado fueron validados sin modificaciones.
- [ ] Nombres, carpetas, referencias, changelog y nextRoute fueron comprobados; las migraciones sólo se propusieron.
- [ ] La suite fue cotejada contra el tag remoto y sus checksums publicados.
- [ ] Se informó configuración de seguimiento/proveedor/DF y arquitectura sin inventar valores.
- [ ] La recomendación no ejecuta una reparación ni una ruta posterior.
