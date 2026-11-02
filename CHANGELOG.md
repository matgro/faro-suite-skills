# Changelog de FARO Suite

Este historial registra cambios de la suite distribuida, no aprobaciones de proyectos. La versión del paquete es independiente de la versión del contrato de workspace.

## 1.8.0 — 2026-11-02

- Incorpora versionado de aplicaciones por componente: arquitectura descubre fuente/lectores, desarrollo prepara mecanismos autorizados y entrega actualiza valores existentes con evidencia del artefacto y de la versión efectiva.
- Propone para Laravel una versión literal en `config/app.php`, consumida mediante `config('app.version')`, sin usar `.env`. En .NET/Blazor respeta propiedades de build y assemblies; en otros stacks requiere evidencia del mecanismo nativo.
- Añade política opcional al perfil, confirmación por entrega o automatización explícita con límites, un único escritor e idempotencia: reintentos/promociones no incrementan y rollback recupera el artefacto anterior.
- Actualiza la guía completa de FARO con versionado de aplicaciones y los cambios de 1.7.0: glosario transversal, cierre de refactorizaciones y visuales Markdown/Mermaid. La publicación no instala ni modifica aplicaciones.

### Actualización desde 1.7.0

1. Obtener `v1.8.0`, verificar procedencia, inventario y checksums; comparar y confirmar el reemplazo completo de `faro/`.
2. No requiere reinicializar workspaces ni cambiar el contrato `1.13.0`. Completar la política por componente antes de su primera entrega versionada.
3. Los mecanismos faltantes requieren desarrollo autorizado; publicar FARO no modifica las aplicaciones ni autoriza sus despliegues.

## 1.7.0 — 2026-11-02

### Cambios

- Exige cierre verificable de refactorizaciones: consumidores conectados, retiro/delegación de lógica sustituida, pruebas desde entradas reales y revisión independiente. Integra apoyos externos condicionados sin instalación automática ni nuevas rutas; Laravel incorpora análisis `lc:dead-code` de sólo lectura. Un método nuevo sin uso no acredita una extracción terminada.

- Añade un glosario de dominio opcional por workspace en `context/glossary.md`, consultado en cada interacción y mantenido sólo con evidencia y permiso documental. Distingue definiciones confirmadas, observaciones, pendientes y conflictos; conserva fuentes, ámbito, alias e historial sin generar RM ni seguimiento remoto artificial.
- Integra la política transversal en router y especialistas, incluidos incidentes, la plantilla genérica, el diagnóstico de presencia y pruebas de compatibilidad con espacios existentes.
- Añade diagramas opcionales Markdown/Mermaid dentro de DF, RM y planes técnicos: flujos, estados, secuencias y navegación trazables, sin documentos visuales paralelos.
- Integra todas las capacidades publicadas hasta 1.6.1, incluidos incidentes, lineamientos .NET/Blazor, estructura RFC y guía de flujos.

### Actualización desde 1.6.1

1. Obtener `v1.7.0`, verificar procedencia, inventario y checksums; comparar y confirmar el reemplazo completo de `faro/`.
2. No requiere reinicializar workspaces ni cambiar el contrato `1.13.0`. El glosario se crea bajo demanda con evidencia.
3. La publicación no instala capabilities externas ni modifica instalaciones del agente; su uso exige disponibilidad, procedencia y auditoría.

## 1.6.1

### Cambios

- Publica `docs/flujo-faro/README.md` como mapa central del router y cinco capítulos con árboles de decisión para instalación/inicio/doctor, arquitectura/ADR/RFC, solicitudes/desarrollo/QA/validación, incidentes e integraciones/entrega.
- Explica qué observa, qué pregunta, a quién deriva, qué produce y qué bloquea cada ruta, con fuentes y límites de los scripts reales. Incluye 23 diagramas Mermaid y comprobaciones de cobertura del inventario, enlaces y secciones.
- La guía conserva la revisión fuente de FARO 1.6.0 que describe; esta publicación sólo añade documentación, pruebas y metadatos de release. No cambia el comportamiento, las versiones individuales de skills ni el contrato de workspace.

### Actualización desde 1.6.0

1. Consultar la guía en el repositorio bajo el tag `v1.6.1`; `docs/` no se copia al instalar el árbol runtime `faro/`.
2. Si se actualiza la instalación, verificar procedencia, inventario y checksums, comparar el destino y confirmar el reemplazo completo como siempre.
3. No requiere migrar ni reinicializar workspaces, instalar nuevas dependencias externas ni modificar su `contractVersion`.

## 1.6.0

### Cambios

- Añade `faro-incidentes` como orquestador de registro INC, evidencia, investigación y conclusión independiente de una corrección BUG/RM/TEC. Admite cierre sin BUG sustentado y resultado no concluyente sin fingir recuperación.
- Delega investigación y post-mortem en capacidades externas revisadas de `obra/superpowers` y `github/awesome-copilot`, fijadas por commit e integridad; no las instala ni reemplaza skills locales implícitamente.
- Integra ruteo, plantillas bajo demanda, trazabilidad Jira/Azure DevOps y controles de disponibilidad externa. No exige migración de contratos ni crea incidentes artificiales para cada fallo de QA conocido.
- Conserva el item recibido aunque su tipo sea Bug sin confirmar el defecto ni duplicarlo; exige un tipo neutral sólo para altas nuevas de incidentes.
- Establece confirmación previa de versión y tag al entregar, criterio SemVer por impacto, creación de tags anotados y verificación de las referencias remotas autorizadas.

### Actualización desde 1.5.3 o 1.5.4

1. Obtener el tag `v1.6.0` publicado y verificar versión, procedencia, inventario y checksums. Incluye el formato de mensajes documentado en 1.5.4.
2. Comparar la instalación existente y solicitar confirmación antes de reemplazar el árbol completo `faro/`.
3. Confirmar por separado la instalación/reemplazo de las capacidades externas de incidentes y auditar revisión, archivos auxiliares y licencia. Un nombre coincidente no autoriza reemplazar una skill local.
4. No requiere migrar workspaces ni modificar su `contractVersion`; los registros INC se crean bajo demanda. La instalación de dependencias externas no se acredita con la sola publicación del tag de FARO.

## 1.5.4 — pendiente de publicación

### Cambios

- Define mensajes de commit con título en la primera línea, descripción funcional de una o dos oraciones y tareas asociadas al final, separadas por líneas en blanco.
- La descripción explica qué funcionalidad cambió, se agregó o se quitó, sin repetir el título ni incluir código, nombres de clases o detalles internos.
- Las tareas verificadas se indican como `#<ID>`, una por línea y fuera del título; si no hay tareas asociadas, se omite el bloque.
- Aplica la misma separación al título y la descripción de PR e incorpora pruebas de contrato del formato.

### Actualización desde 1.5.3

1. Obtener la release publicada y verificar versión, procedencia, inventario y checksums.
2. Comparar la instalación existente y solicitar confirmación antes de reemplazar el árbol completo `faro/`.
3. No requiere migrar workspaces, modificar su `contractVersion` ni reescribir commits o PR existentes.

## 1.5.3 — pendiente de publicación

### Cambios

- Extiende los lineamientos generales .NET/C# para incorporar operaciones en las clases y archivos existentes, reutilizando métodos y dependencias antes de agregar otros.
- No permite fragmentar clases en archivos como `Repository.Queries.cs`, `Repository.Resend.cs` o `Service.Commands.cs` por preferencia de organización o longitud del archivo: exige convención explícita del componente o autorización humana.
- Mantiene las excepciones de código generado y parciales exigidos por el framework. No autoriza consolidar archivos preexistentes ni crear repositorios paralelos o auxiliares sólo para ubicar el código nuevo fuera de su responsable.

### Actualización desde 1.5.2

1. Obtener la release publicada y verificar versión, procedencia, inventario y checksums.
2. Comparar la instalación existente y solicitar confirmación antes de reemplazar el árbol completo `faro/`.
3. No requiere migrar workspaces, modificar su `contractVersion` ni reorganizar código existente.

## 1.5.2 — pendiente de publicación

### Cambios

- Actualiza el template RFC con tabla de metadatos y secciones de resumen, problema, contexto, alcance, fuera de alcance, opciones evaluadas, decisión/estado actual, consecuencias, plan de acción, riesgos y mitigaciones, preguntas abiertas y referencias.
- Cada alternativa tiene descripción, pros y contras; el plan de acción y los riesgos usan tablas.
- Conserva los estados `open|accepted|rejected|withdrawn`, la trazabilidad y el hecho, restricción y evidencia del problema. Mantiene la ventana de comentarios y las posiciones atribuibles dentro de «Decisión / Estado actual».
- Añade pruebas de contrato para la estructura y la ausencia de contenido específico del ejemplo.
- Incorpora lineamientos Blazor adaptados de NZT como referencia editable de `faro-req-desarrollo`, complementaria a los comunes y .NET: componentes, formularios, modos de renderizado, prerenderizado, seguridad y rendimiento. No agrega rutas, dependencias ni migraciones; conserva procedencia y licencia MIT de la fuente.

### Actualización desde 1.5.1

1. Obtener la release publicada y verificar versión, procedencia, inventario y checksums.
2. Comparar la instalación existente y solicitar confirmación antes de reemplazar el árbol completo `faro/`.
3. No requiere migrar workspaces, modificar su `contractVersion` ni reescribir RFC existentes.


## 1.5.1 — pendiente de publicación

### Cambios

- Estandariza las actualizaciones remotas de Jira y Azure DevOps como bitácoras breves y útiles: sólo inicio/cierre de fase, unidades materiales, decisiones, bloqueos y referencias externas durables.
- Añade `faro/references/comment-format.md` con una plantilla común para desarrollo, QA, validación y entrega, sin transcripciones de comandos, archivos o pruebas intermedias.


### Actualización desde 1.5.0

1. Obtener la release publicada y verificar versión, procedencia, inventario y checksums.
2. Comparar la instalación existente y solicitar confirmación antes de reemplazar el árbol completo `faro/`.
3. Reiniciar la sesión o refrescar el índice de skills según el agente. No requiere migrar workspaces ni modificar su `contractVersion`.

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
