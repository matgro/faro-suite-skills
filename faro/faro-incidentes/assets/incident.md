# <INC-ID> — <Título del síntoma>

## Control y seguimiento

- Versión del registro: <versión>.
- Solicitud y autorización de investigación: <fuente, alcance y límites>.
- Proyecto, entorno y servicios afectados: <confirmados o pendientes>.
- Seguimiento: <OFF o proveedor, ID, URL y tipo verificados>.
- Último readback remoto: <fecha/zona, estado y relaciones observados, o no aplica>. Es evidencia fechada, no una fuente local alternativa del estado operativo.
- Relacionados: <INC/BUG/RM/TEC, expedientes e items remotos independientes, o ninguno>.

Con seguimiento `REQUIRED`, consultar el estado operativo vigente en el gestor; no mantener aquí una copia mutable de estado, prioridad o asignación. Con `OFF`, indicar que no existe estado remoto.

## Reporte e impacto

- Síntoma reportado y fuente: <qué ocurrió, quién/qué lo reporta sin datos personales innecesarios>.
- Esperado y fuente: <regla/contrato/DF o pendiente de confirmar>.
- Observado: <hechos; no usar el código actual como aprobación funcional>.
- Período y zona horaria: <confirmados o desconocidos>.
- Impacto: <servicios/operaciones afectados, medición y fuente o no disponible>.
- Situación actual del impacto: <hechos, verificación y pendientes; no asumir recuperación>.

## Evidencias

| Ref | Fuente / localizador seguro | Revisión, entorno o período | Hecho respaldado | Límites |
| --- | --- | --- | --- | --- |

No copiar secretos, PII ni payloads productivos sensibles. Preservar referencias accesibles y datos sanitizados.

## Cronología

| Fecha/hora y zona | Evento | Evidencia |
| --- | --- | --- |

No inventar horas ni completar huecos por inferencia. Mantener zona de origen y conversión verificable cuando corresponda.

## Investigación

- Capacidad externa utilizada: <nombre, origen, commit, integridad/escaneo o bloqueo>.
- Repositorios y revisiones inspeccionadas: <HEAD, cambios locales y límites sobre versión desplegada>.
- Alcance ejecutado: <lecturas y pruebas autorizadas; no realizadas se identifican como pendientes>.

| Hipótesis | Comprobación autorizada | Evidencia y resultado | Conclusión / límites |
| --- | --- | --- | --- |

## Causa y conclusión

- Resultado: <defecto propio / proveedor / comportamiento esperado / configuración-datos-operación / no concluyente; combinaciones justificadas>.
- Causa sustentada y evidencias: <conocida, probable o no determinada; no forzar una causa>.
- Factores contribuyentes: <con fuente o no determinados>.
- Hipótesis descartadas y por qué: <referencias>.
- Límites y evidencia faltante: <pendientes concretos>.

## Decisión y acciones derivadas

| Acción propuesta | Decisión / autorización | Expediente derivado | Item remoto y relación bidireccional | Verificación / pendiente |
| --- | --- | --- | --- | --- |

Investigar no autoriza corregir. No inventar IDs, responsables ni fechas; registrar compromisos sólo si se confirmaron. El BUG referencia esta investigación sin duplicarla.

## Cierre o continuidad

- Resultado de investigación: <conclusión y fuente>.
- Impacto al cierre: <evidencia de resolución/ausencia de impacto pendiente o continuar abierto>.
- Motivo de cierre sin BUG, si aplica: <justificación sustentada>.
- Decisión humana de archivo no concluyente, si aplica: <fuente o no autorizado>.
- Acciones abiertas y siguiente paso: <referencias y pendientes>.
- Condición de reapertura: <nueva evidencia o recurrencia del mismo caso>.
- Cierre remoto, si `REQUIRED`: <operación explícita, estado leído antes/después y evidencia; no inferir por entrega o cierre de un derivado>.

## Historial de eventos del expediente

| Versión / fecha con zona | Evento: apertura, investigación, conclusión, cierre evidenciado o reapertura | Cambio y motivo | Evidencia / autorización |
| --- | --- | --- | --- |
