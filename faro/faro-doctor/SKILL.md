---
name: faro-doctor
description: Use when diagnosing an existing FARO workspace.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, doctor, diagnosis, workspace, governance]
    related_skills: [faro, faro-inicializacion, faro-arq-laravel, faro-arq-dotnet, faro-arq-mobile, faro-arq-generica, faro-arq-adr, faro-arq-rfc]
---

# FARO — Diagnóstico del espacio de trabajo

En cada interacción, leer y aplicar [Glosario de dominio](../references/domain-glossary.md) para consultar `context/glossary.md` si existe. Doctor permanece en sólo lectura: informar presencia, ausencias opcionales y discrepancias observadas, sin crear ni actualizar el glosario o su índice. El script informa presencia, no valida automáticamente las definiciones.

## Rol

Inspecciona un root y emite una clasificación contractual verificable sin inicializar, migrar, regenerar ni sobrescribir información. Es la respuesta obligatoria antes de inicializar o continuar cuando existe cualquier evidencia FARO. Un `AGENTS.md` ajeno sin bloque FARO se informa y preserva, pero por sí solo no acredita una instancia.

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

El diagnóstico siempre ejecuta las comprobaciones locales compartidas de `scripts/suite_validation.py`: nombres, carpetas, catálogo de migraciones, referencias y changelog distribuido. Para un contrato v2 inspecciona el schema completo de `workflow.json` además de `nextRoute`: campos exactos, tipos, `workItemRef`, `checkpoint` y ausencia de estado/backlog operativo. Una ruta retirada se muestra con su destino vigente y bloquea en modo estricto. Nunca ejecuta renombres ni altera aprobaciones.

La salida clasifica exactamente el workspace como `absent`, `current`, `legacy-migratable`, `mixed-ambiguous`, `future-unsupported` o `corrupt`. Sólo `current` íntegro supera `--strict`; la coherencia de la suite y el origen solicitado son gates adicionales independientes.

1. Fijar el root sin seguir un symlink y leer sólo los artefactos conocidos. `AGENTS.md` sin delimitadores y sin otra evidencia produce `absent`; un marcador parcial sí es evidencia corrupta. Leer la configuración v2 central y el catálogo de migraciones como normas de diagnóstico, nunca desde el manifiesto local. **Completo:** existencia y clasificación no dependen de un archivo ajeno homónimo.
2. Para `current`, exigir los cuatro directorios y siete archivos v2, regulares y sin symlinks; bloque FARO exactamente equivalente a la plantilla preservando el contenido externo; manifiesto/stats con campos, tipos, schemas y versiones coherentes; perfil v2; metadatos y tablas de ambos catálogos; helper `work_item_contract.py`; y workflow v2 exacto si existe. Validar el layout mediante el helper sin invocar operaciones mutantes. **Completo:** contrato, catálogos, unidades y continuidad concuerdan.
3. Para `legacy-migratable`, reconocer únicamente una versión origen declarada en `references/contract-migrations.json`, validar sus cinco artefactos y schema legacy en modo lectura y mostrar el comando del migrador sin `--apply`. Si coexisten versiones, catálogos/directorios v2, expedientes planos o workflow de otro schema, clasificar `mixed-ambiguous`; un JSON roto o contrato conocido incompleto es `corrupt`; una versión semántica mayor es `future-unsupported` y nunca se degrada. **Completo:** la recomendación no confunde reparación, inicialización y migración.
4. Verificar el origen Git de la suite con `--verify-suite-origin`: leer `references/suite-provenance.json`, resolver sólo su etiqueta remota inmutable, obtener temporalmente esa revisión y comparar el árbol `faro/` con `checksums.sha256` remoto. No aceptar una rama mutable, un SHA aportado por el ambiente ni un tag no resoluble. **Completo:** se informa repositorio, tag, commit resuelto y coincidencia byte a byte, o el bloqueo concreto.
5. Informar identidad, estado, fuentes indexadas, seguimiento/proveedor/DF, arquitectura registrada, workflow, glosario y bloqueos. Detectar evidencia raíz de .NET (`.sln`, `.csproj`, `global.json`) sin restaurar/build y recomendar `faro-arq-dotnet` para un v2 `new`/`initializing`; aplicar rutas equivalentes para Laravel, móvil u otro stack. No presentar una ausencia como inexistencia del proyecto. **Completo:** el reporte contesta qué existe y qué falta sin suposiciones.
6. Resolver sin escribir: `absent` → `faro-inicializacion`; `legacy-migratable` → revisar dry-run del migrador y pedir autorización separada para `--apply`; `mixed-ambiguous` → reconciliación humana antes de migrar; `future-unsupported` → suite compatible sin downgrade; `corrupt` → reparación evidenciada sin recreación ciega; `disabled` → detener; `current` íntegro → integración, arquitectura o ruta del pedido. **Completo:** una recomendación, ninguna acción automática.
7. Con `--check-external-skills`, leer `references/laravel-external-skills.json` y ejecutar solamente `hermes skills check <name>` para las capabilities declaradas. Informar instalada/actualizable/no verificable; no ejecutar `update`, `install` ni `--force`. Si hay actualización, recomendar el bootstrap FARO con autorización explícita para que la actualice y la audite. **Completo:** el estado externo se reporta sin modificar skills ni workspace.

## Formato mínimo del informe

- “Espacio FARO existente: sí/no” y root inspeccionado.
- “Clasificación del workspace” con uno de los seis valores cerrados.
- Matriz de versiones: paquete de suite, skill principal, inventario de versiones de skills, contrato esperado/instalado, paquete registrado en `stats.faro.version` y schema del workflow.
- Compatibilidad del contrato separado de la versión de paquete, coherencia local y ubicación de `references/suite-changelog.json`.
- El workflow se informa como checkpoint y schema, no como versión de release; las versiones de documentos se leen dentro de su expediente y no sustituyen suite ni contrato.
- `stats.faro.version` registra el paquete que materializó o actualizó el workspace: validar que sea semver e informar su diferencia con el paquete actual como evidencia, nunca como corrupción ni fallo de `--strict`.
- Rutas obsoletas/desconocidas y reemplazos propuestos. Para un renombre autorizado, cambiar sólo `nextRoute`, preservar el resto y volver a ejecutar doctor; nunca editar documentos históricos por búsqueda y reemplazo global.
- Repositorio, tag y commit de origen de la suite, más el resultado de checksums remotos.
- Lista de archivos requeridos: presente, ausente o inválido.
- Estado, proyecto, arquitectura, configuraciones de seguimiento/proveedor/DF y workflow.
- Faltantes, bloqueos y siguiente ruta recomendada.
- Para legacy migrable, comando de migración dry-run explícitamente marcado “no escribe”; nunca ejecutar `--apply` desde doctor.

## Invariantes

- Diagnosticar no concede permiso para reparar, inicializar, migrar, cambiar estado ni crear workflow.
- No borrar ni recrear JSON malformado; reportarlo tal como bloqueo.
- No revelar secretos ni leer archivos de entorno.
- La procedencia de release usa una etiqueta Git inmutable; una rama, la versión declarativa o el remoto local no prueban el origen del árbol instalado.
- Doctor es de solo lectura: comprobar actualizaciones no autoriza instalarlas ni aplicarlas.
- Un contrato existente pero incompleto sigue siendo existente: nunca se reemplaza silenciosamente.
- Doctor no crea locks, caches, catálogos, workflow ni directorios en el workspace; la igualdad byte a byte antes/después es una propiedad comprobable.

## Verificación

- [ ] El informe dice expresamente si el espacio ya existe.
- [ ] La clasificación usa exactamente el vocabulario cerrado y AGENTS ajeno solo no acredita FARO.
- [ ] Directorios/archivos, JSON, schemas/versiones, perfil, catálogos, helper y workflow fueron validados sin modificaciones.
- [ ] Nombres, carpetas, referencias, changelog y nextRoute fueron comprobados; las migraciones sólo se propusieron.
- [ ] La suite fue cotejada contra el tag remoto y sus checksums publicados.
- [ ] Se informó configuración de seguimiento/proveedor/DF y arquitectura sin inventar valores.
- [ ] .NET se detectó/enrutó por evidencia y no por preferencia.
- [ ] La recomendación no ejecuta una reparación ni una ruta posterior.
