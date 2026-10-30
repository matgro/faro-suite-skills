# <INC-ID> — <Título del síntoma>

## Control

- Estado: <ABIERTO | EN_INVESTIGACION | CERRADO>.
- Versión del registro: <versión>.
- Solicitud y autorización de investigación: <fuente, alcance y límites>.
- Proyecto, entorno y servicios afectados: <confirmados o pendientes>.
- Seguimiento: <OFF o proveedor, ID y URL verificados>.
- Relacionados: <INC/BUG/RM/TEC o ninguno>.

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

| Acción propuesta | Decisión / autorización | INC/BUG/RM/TEC o seguimiento externo | Verificación / pendiente |
| --- | --- | --- | --- |

Investigar no autoriza corregir. No inventar IDs, responsables ni fechas; registrar compromisos sólo si se confirmaron. El BUG referencia esta investigación sin duplicarla.

## Cierre o continuidad

- Resultado de investigación: <conclusión y fuente>.
- Impacto al cierre: <evidencia de resolución/ausencia de impacto pendiente o continuar abierto>.
- Motivo de cierre sin BUG, si aplica: <justificación sustentada>.
- Decisión humana de archivo no concluyente, si aplica: <fuente o no autorizado>.
- Acciones abiertas y siguiente paso: <referencias y pendientes>.
- Condición de reapertura: <nueva evidencia o recurrencia del mismo caso>.

## Historial

| Versión / fecha con zona | Cambio y motivo | Evidencia / autorización |
| --- | --- | --- |
