# Contrato FARO de requerimientos

Versión: 2.0

## Prefijos estables

- `SOL`: solicitud; `SRC`: fuente; `OBJ`: objetivo; `RF`: requerimiento funcional; `RN`: regla de negocio; `RNF`: requisito no funcional; `RES`: restricción; `ACT`: actor; `DAT`: dato; `INT`: integración; `VAL`: validación; `CA`: criterio; `PD`: pendiente.
- Documento: `RM-0001`; correcciones documentadas: `BUG-0001`; mantenimiento sin cambio funcional: `TEC-0001`; tareas: `TASK-001`.
- Investigación de síntoma sin defecto confirmado: `INC-0001`, bajo `context/incidents/` y gobernada por `faro-incidentes`. No es un RM ni una autorización de fix; BUG/RM/TEC derivados enlazan al INC sin duplicar evidencia.
- Usar referencias completas, por ejemplo `RM-0001#RN-001`. No reutilizar IDs ni calcularlos por máximo+1 sin reserva serializada.

## Persistencia de expedientes

- El catálogo canónico es `context/requirements/requirements-catalog.md`. Reserva y localiza; no guarda estado, prioridad ni asignación.
- Cada RM/BUG/TEC vive en `context/requirements/work-items/<ID>/`. Las unidades nuevas usan `<ID>.md`; una migrada puede conservar el basename histórico declarado como `Documento principal` en el catálogo. Los archivos de fase conservan el mismo ID y directorio durante toda su vida; no existen carpetas `active`/`completed`.
- Resolver con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json` y validar antes de cada handoff. Una ruta aportada por chat o workflow no sustituye el catálogo.
- `<ID>-cierre.json` congela el expediente y contiene hashes de todos sus artefactos salvo sí mismo. Cualquier diferencia bloquea. Un cambio posterior crea otro expediente y enlaza al anterior.

## Evidencia

Cada afirmación normativa debe ser CONFIRMADA con fuente localizable, OBSERVADA en código, DERIVADA necesariamente con origen o PROPUESTA separada. `NO DEFINIDO`, `NO APLICA` justificado y `NO REVISADO` son distintos. El código no prueba aprobación funcional.

## Madurez, resultados y estado operacional

- Madurez de especificación RM: `DRAFT`, `PENDING_DEFINITION`, `READY_FOR_REVIEW`, `APPROVED`, `SUPERSEDED`.
- PD: `OPEN`, `RESOLVED`, `DEFERRED`.
- Preparación técnica: `PRELIMINAR`, `BLOQUEADO`, `LISTO_PARA_DESARROLLO`.
- Resultado de caso QA: `PENDING`, `PASSED`, `FAILED`, `BLOCKED`.
- Validación CA: `CONFORME`, `NO_CONFORME`, `NO_VERIFICADO`.

Estos valores describen madurez o evidencia del artefacto, no el avance operativo del item. Con seguimiento `REQUIRED`, el proveedor remoto es autoridad de estado, prioridad y asignación; Markdown, catálogo y workflow no los copian. `APPROVED` exige evidencia humana de persona autorizada, versión exacta, alcance, fecha con zona y localizador. Una nueva versión no hereda aprobación. `VERIFIED` exige CA conformes y evidencia; no implica merge, despliegue, aceptación productiva ni cierre.

El contrato v2 sólo crea y avanza RM/BUG/TEC con seguimiento `REQUIRED` verificado. Un legado migrado con `OFF` permanece legible y diagnosticable, pero no recibe escrituras de ciclo de vida ni congelado hasta reconciliarse con un item remoto.

## Flujo

1. Clasificar solicitud: consulta, RM, BUG, TEC o combinación.
   Si se solicita registrar o investigar un síntoma con causa desconocida, usar `faro-incidentes` antes de clasificarlo como BUG. Un esperado faltante se investiga como pendiente, no obliga por sí solo a crear un RM. Un BUG conocido con esperado documentado conserva el circuito directo.
2. Cambios funcionales usan `faro-req-ingenieria`; BUG sólo restaura comportamiento con fuente; TEC justifica ausencia de cambio observable. Reservar su ID y expediente antes de referencias externas. Con seguimiento `REQUIRED`, cada solicitud se vincula a una issue o work item y se preserva como `SRC`; su estado registra avance operativo, pero no constituye aprobación FARO.
3. Un PD bloquea si puede cambiar resultado, datos, permisos, contratos, criterios o compatibilidad del alcance. No bajar su gravedad para avanzar.
4. Antes de código: RM/version inequívocos, CA verificables, PD bloqueantes resueltos, aprobación y autorización válidas, plan/tareas coherentes.
5. `faro-req-analisis-tecnico` crea plan y tareas dentro del expediente; `faro-req-desarrollo` ejecuta sólo un plan autorizado y LISTO_PARA_DESARROLLO; `faro-qa-ejecucion` registra casos/evidencia y `faro-req-validacion` produce el veredicto contra CA. UI visible pasa antes por `faro-ux`; commit/PR/despliegue pasa por `faro-entrega`.
6. `faro-cierre` comprueba resultado `VERIFIED`, promociones de conocimiento durable, entrega requerida y sincronización remota antes de generar `<ID>-cierre.json`. El expediente se congela en su ruta; no se mueve ni se reabre.

No aprobar, fusionar, desplegar ni ejecutar operaciones externas sólo porque exista un RM aprobado.
