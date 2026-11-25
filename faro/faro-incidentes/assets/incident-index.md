# Incidentes

Registro creado bajo demanda. Un incidente no confirma un defecto ni autoriza un fix.

## Registros

| ID | Expediente estable | Fuente de reserva serializada | Seguimiento remoto y último readback | Conclusión / impacto | Derivados y relaciones |
| --- | --- | --- | --- | --- | --- |

Con seguimiento `REQUIRED`, el gestor remoto es la fuente canónica del estado operativo. Este índice localiza expedientes y evidencia; no duplica estado, prioridad ni asignación. Con `OFF`, indicar expresamente que no existe seguimiento remoto.

## Reservas

| ID | Alcance | Fuente de reserva serializada |
| --- | --- | --- |

Reservar y publicar identidad únicamente mediante `scripts/incident_registry.py`: primero dry-run y luego `--apply`. La fuente estable permanece en el registro para que un reintento con el mismo alcance resuelva el mismo ID; un alcance incompatible se rechaza. El CLI serializa escrituras, rechaza duplicados/rutas inseguras y no crea items remotos. Un índice legacy puede leerse sin mutarlo y se migra sólo con `upgrade --apply`, identificando sus fuentes como `LEGACY:<INC-ID>`. No registrar aquí estado, prioridad, área, backlog, cola o asignación como autoridad local.
