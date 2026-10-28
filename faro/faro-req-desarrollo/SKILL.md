---
name: faro-req-desarrollo
description: Use when FARO develops an approved requirement plan.
version: 1.1.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, development, requirements, code, verification]
    related_skills: [faro, faro-req-analisis-tecnico, faro-qa-ejecucion, faro-req-validacion, faro-ux]
---

# FARO — Desarrollo de requerimientos

## Rol
Implementa una unidad autorizada de un RM, BUG o TEC con plan técnico `LISTO_PARA_DESARROLLO`. No redefine comportamiento funcional, no acepta la entrega, no realiza QA de aplicación ni hace commit, PR o despliegue sin la ruta `faro-entrega`.

## Precondiciones
- FARO está `available`.
- La entrada identifica ID, versión, alcance y autorización humana vigente.
- Plan y tareas pertenecen a la misma versión y están `LISTO_PARA_DESARROLLO`.
- Se leyeron `AGENTS.md`, arquitectura, instrucciones del repositorio, Git y tarea activa.
- Se revisó `context/decisions/adr/README.md` si existe y los ADRs relevantes a la tarea; sus IDs o la ausencia del catálogo quedarán en la evidencia.
- Se identificó la tecnología del componente y se leyeron los archivos de lineamientos aplicables, según la sección siguiente.
- No hay RFC abierto cuya decisión afecte la tarea; si existe, `waitingOn` identifica el RFC y su bloqueo.
- Antes de editar código, la rama activa debe cumplir `feature/<RM-ID>-<descripcion-kebab-case>`. Si no existe, crearla desde la base autorizada antes de modificar archivos. Si hay cambios no atribuibles a la unidad, bloquear y pedir decisión.

Si una precondición falla, actualizar `context/workflow.json` con `waitingOn`, no modificar código y devolver la ruta a `faro`, `faro-req-ingenieria` o `faro-req-analisis-tecnico`.

## Lineamientos de desarrollo

Las reglas de código viven en archivos Markdown dentro de esta misma skill, no en el workspace ni en una instalación externa:

- Leer siempre [Lineamientos comunes](references/lineamientos-comunes.md).
- Para .NET/C#, leer además [Lineamientos .NET](references/lineamientos-dotnet.md).
- Para componentes Blazor, leer además de los comunes y .NET los [Lineamientos Blazor](references/lineamientos-blazor.md); aplicar sólo las secciones del modo de renderizado y de la tarea evidenciados.
- Para Laravel, leer además [Lineamientos Laravel](references/lineamientos-laravel.md).

Elegir por evidencia del componente que se va a modificar: arquitectura y archivos de proyecto `.csproj`/configuración de SDK para .NET; componentes `.razor`, arranque, servicios y configuración de renderizado para Blazor; `composer.json`, `composer.lock` y uso de Laravel para Laravel. Un backend .NET, Razor Pages o MVC no activa por sí solo la guía Blazor. No elegir sólo por extensión ni asumir una tecnología por el nombre del repositorio. En un workspace mixto, aplicar a cada componente sus propias reglas; para otra tecnología, usar los comunes y las instrucciones locales, indicando que no hay guía específica. Si falta evidencia necesaria, aclararla antes de editar.

Leer los archivos aplicables antes de cada unidad de desarrollo; no sustituirlos por una copia resumida en esta skill ni por valores recordados. Si falta o está vacío alguno de los seleccionados, bloquear e informar la ruta, sin inventar sus reglas. Registrar en la evidencia existente de la tarea qué archivos se usaron y las excepciones acordadas; no crear otro contrato ni nuevos estados.

Las instrucciones explícitas del repositorio y la arquitectura aprobada prevalecen sobre estos valores por defecto; las reglas tecnológicas especializan las comunes. Ningún lineamiento modifica el RM, sus autorizaciones o las restricciones de seguridad. Si hay una contradicción no resoluble, volver al análisis técnico o a la definición funcional antes de cambiar código.

El usuario puede editar las reglas directamente en esos archivos sin tocar `SKILL.md`; el agente sólo las cambia por pedido explícito, nunca para eludirlas. Son cambios locales visibles en la comparación de una actualización y en la verificación de hashes: no afirmar integridad de release idéntica ni regenerar checksums de una instalación para ocultarlos. Antes de reemplazar la suite, mostrar las personalizaciones y acordar su conservación o reaplicación; nunca descartarlas silenciosamente.

## Procedimiento
1. Confirmar la unidad en el plan y marcarla `doing` en workflow. Si seguimiento está `REQUIRED`, transicionar el item al estado remoto de trabajo y registrar una actualización concisa conforme a `../references/comment-format.md` cuando la unidad permanezca abierta entre sesiones; si falla, bloquear antes de editar código. **Completo:** unidad, versión, autorización y seguimiento trazables.
2. Inspeccionar implementaciones, consumidores, pruebas, convenciones locales y ADRs relevantes; comparar el cambio propuesto con decisiones `accepted`, `deprecated` o `superseded` que puedan afectarlo. Registrar los ADRs revisados en la evidencia. Si el cambio contradice un ADR aceptado, no editar: volver a `faro-req-analisis-tecnico` para justificar un nuevo ADR o superceder el existente. **Completo:** fuentes de reglas explícitas, memoria arquitectónica revisada y reutilización o ruta nueva justificada.
3. Si existe interfaz, cargar `faro-ux` antes de modificar pantallas y aplicar la guía tecnológica correspondiente. **Completo:** catálogo, dominio y markup único respetados.
4. Implementar sólo el alcance de la tarea, siguiendo las reglas de código y la disciplina de pruebas definidas en los archivos leídos. Mantener contratos salvo orden explícita del RM; acordar y registrar las excepciones que esos lineamientos requieran. **Completo:** no hay alcance adicional ni rutas paralelas y la evidencia demuestra la disciplina aplicada o su excepción autorizada.
5. Ejecutar las pruebas relevantes y los checks existentes, revisando el diff contra los lineamientos seleccionados. **Completo:** resultados reales, excepciones o bloqueo registrados; no se confunden compilación y pruebas.
6. Actualizar tareas, fuentes técnicas afectadas y workflow: `done`, evidencia y `nextRoute`. Si seguimiento está `REQUIRED`, publicar una actualización por cada unidad material completada o bloqueada, usando `../references/comment-format.md`; no comentar comandos, archivos, intentos ni pruebas intermedias. **Completo:** reanudable sin chat y con trazabilidad remota útil.
7. Detenerse y reportar cambios, comprobaciones, límites y siguiente ruta. QA de aplicación se enruta a `faro-qa-ejecucion`.

## Invariantes
- El plan técnico guía el cómo; el RM autorizado guía el qué.
- Un fallo derivado del cambio se corrige dentro de la unidad; ambigüedad funcional vuelve a `faro-req-ingenieria`.
- No declarar conformidad funcional; pertenece a `faro-req-validacion`.
- No implementar trabajo dependiente de un RFC abierto; un RFC aceptado se consulta mediante su ADR enlazado.
- No contradecir un ADR aceptado ni reabrir una alternativa descartada sin análisis y ADR sucesor explícitos.
- No tratar compilación o inspección como prueba ejecutada.
- No exponer secretos ni usar producción sin autorización.

## Verificación
- [ ] ID, versión, autorización y tarea coinciden.
- [ ] Se leyó código vecino, consumidores y pruebas.
- [ ] Se revisaron ADRs relevantes o se registró que no existe catálogo; no hay contradicción sin ADR sucesor.
- [ ] Se leyeron los lineamientos comunes y los del stack evidenciado; reglas y excepciones quedaron trazables sin modificar el alcance.
- [ ] UI revisó catálogo local cuando aplica.
- [ ] Pruebas ejecutadas o bloqueo evidenciado.
- [ ] Tarea/workflow registran resultado y siguiente ruta.
- [ ] No hubo entrega ni aceptación implícitas.
