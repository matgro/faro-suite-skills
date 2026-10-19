# Contrato FARO de requerimientos

Versión: 1.0

## Prefijos estables

- `SOL`: solicitud; `SRC`: fuente; `OBJ`: objetivo; `RF`: requerimiento funcional; `RN`: regla de negocio; `RNF`: requisito no funcional; `RES`: restricción; `ACT`: actor; `DAT`: dato; `INT`: integración; `VAL`: validación; `CA`: criterio; `PD`: pendiente.
- Documento: `RM-0001`; correcciones documentadas: `BUG-0001`; mantenimiento sin cambio funcional: `TEC-0001`; tareas: `TASK-001`.
- Usar referencias completas, por ejemplo `RM-0001#RN-001`. No reutilizar IDs ni calcularlos por máximo+1 sin reserva serializada.

## Evidencia

Cada afirmación normativa debe ser CONFIRMADA con fuente localizable, OBSERVADA en código, DERIVADA necesariamente con origen o PROPUESTA separada. `NO DEFINIDO`, `NO APLICA` justificado y `NO REVISADO` son distintos. El código no prueba aprobación funcional.

## Estados

- RM: `DRAFT`, `PENDING_DEFINITION`, `READY_FOR_REVIEW`, `APPROVED`, `SUPERSEDED`.
- PD: `OPEN`, `RESOLVED`, `DEFERRED`.
- Entrega: `NOT_STARTED`, `IN_DEVELOPMENT`, `BLOCKED`, `IMPLEMENTED`, `VERIFIED`.
- Validación CA: `CONFORME`, `NO_CONFORME`, `NO_VERIFICADO`.

`APPROVED` exige evidencia humana de persona autorizada, versión exacta, alcance, fecha con zona y localizador. Una nueva versión no hereda aprobación. `VERIFIED` exige CA conformes y evidencia; no implica merge, despliegue ni aceptación productiva.

## Flujo

1. Clasificar solicitud: consulta, RM, BUG, TEC o combinación.
2. Cambios funcionales usan `faro-req-ingenieria`; BUG sólo restaura comportamiento con fuente; TEC justifica ausencia de cambio observable. Con seguimiento `REQUIRED`, cada solicitud se vincula a una issue o work item y se preserva como `SRC`; su estado registra avance operativo, pero no constituye aprobación FARO.
3. Un PD bloquea si puede cambiar resultado, datos, permisos, contratos, criterios o compatibilidad del alcance. No bajar su gravedad para avanzar.
4. Antes de código: RM/version inequívocos, CA verificables, PD bloqueantes resueltos, aprobación y autorización válidas, plan/tareas coherentes.
5. `faro-req-analisis-tecnico` crea plan y tareas; `faro-req-desarrollo` ejecuta sólo un plan autorizado y LISTO_PARA_DESARROLLO; `faro-qa-ejecucion` registra casos/evidencia y `faro-req-validacion` cierra contra CA. UI visible pasa antes por `faro-ux`; commit/PR/despliegue pasa por `faro-entrega`.

No aprobar, fusionar, desplegar ni ejecutar operaciones externas sólo porque exista un RM aprobado.
