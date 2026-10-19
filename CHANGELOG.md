# Changelog de FARO Suite

Este historial registra cambios de la suite distribuida, no aprobaciones de proyectos. La versión del paquete es independiente de la versión del contrato de workspace.

## 1.3.0 — pendiente de publicación

### Cambios

- `faro-req-implementacion` pasa a llamarse `faro-req-desarrollo`: carpeta, nombre interno, catálogo, referencias y handoffs. Conserva el comportamiento y las precondiciones de desarrollo.
- Bootstrap compara también skills agregadas, retiradas y renombradas, y consulta el historial antes de reemplazar una instalación completa.
- Inicialización comprueba la coherencia de la suite antes de escribir el contrato de proyecto.
- Doctor valida las referencias locales y detecta `nextRoute` retiradas o desconocidas; no modifica el workspace.
- El validador del paquete comprueba referencias y changelog además de hashes e inventario.
- Los archivos distribuidos usan LF para que sus checksums no dependan de la conversión CRLF de Git en Windows.
- Desarrollo lee lineamientos comunes y por tecnología desde Markdown editables dentro de la skill. Incluye guías para .NET/C# (adaptadas de NZT) y Laravel, además de reglas de legibilidad, errores, configuración, cambios mínimos, refactorización y TDD.
- La validación local detecta referencias Markdown ausentes o vacías. Las personalizaciones de lineamientos no requieren editar `SKILL.md`; siguen siendo modificaciones locales que deben compararse y acordarse antes de actualizar la suite.

### Actualización desde 1.2.0

1. Obtener la release publicada y verificar versión, procedencia, inventario y checksums. No reutilizar el tag `v1.2.0` para este contenido.
2. Comparar la instalación existente y mostrar modificaciones locales, archivos eliminados y el renombre. Solicitar confirmación indicando el destino exacto.
3. Reemplazar todo el árbol `faro/`, conservando una copia recuperable hasta verificar el resultado. No superponer archivos: eso dejaría la carpeta retirada.
4. Actualizar el índice de skills o iniciar una sesión nueva según el agente.
5. Ejecutar doctor en cada workspace que se vaya a reanudar. Si `context/workflow.json.nextRoute` contiene el nombre anterior, solicitar autorización para sustituir únicamente ese valor por `faro-req-desarrollo`, preservando ID, versión, alcance, aprobaciones y tareas. Volver a ejecutar doctor antes de continuar.
6. No reinicializar proyectos, no reescribir documentos históricos ni cambiar `contractVersion`: el contrato sigue siendo `1.13.0`.

Una instalación nueva no requiere migrar workflows. La correspondencia consumida por herramientas está en `faro/references/suite-changelog.json`, que viaja con la suite y es la fuente de los renombres. No hay un alias ejecutable del nombre anterior.

Esta versión no está publicada por el solo hecho de modificar estos archivos. La instalación remota con procedencia verificada requiere publicar el commit y el nuevo tag `v1.3.0`.

## Mantenimiento de futuras releases

- Agregar una entrada al inicio de `suite-changelog.json` y una sección aquí; no reescribir entradas de releases publicadas.
- Sincronizar `manifest.json.version` y `suite-provenance.json.packageVersion/ref`. Registrar cada renombre en `renamedSkills`; los destinos deben existir o conducir por renombres posteriores a una skill vigente.
- Conservar la separación entre versión de paquete y contrato. Sólo cambiar el contrato si su estructura o política cambia realmente.
- Generar checksums con `python tools/update_checksums.py`. Usar `--normalize-line-endings` sólo al preparar una nueva release desde un checkout CRLF, nunca para ocultar una discrepancia de una release publicada o instalada.
- Ejecutar `python -B -m unittest discover -s tests -p 'test_*.py'`, `python tests/validate_package.py` y `python faro/scripts/verify-routing.py` antes de publicar. Verificar también una copia instalada con `--installed-at`.
- Publicar el nuevo tag únicamente después de las verificaciones. No mover ni reutilizar tags publicados.
