---
name: faro-incidentes
description: Use when FARO records or investigates an incident.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, incidents, evidence, investigation, triage]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico, faro-int-jira, faro-int-azure-devops, systematic-debugging, incident-postmortem]
---

# FARO — Incidentes

## Rol

Orquesta el registro, investigación, clasificación y cierre de un incidente `INC`, sin presuponer un defecto. FARO conserva autorización, evidencia, continuidad y derivación; las capacidades externas revisadas aportan investigación técnica y revisión causal según [capacidades externas](references/capacidades-externas.md). No replica sus metodologías ni implementa una corrección.

## Cuándo usar

- Registrar o investigar un error reportado, comportamiento inesperado o problema de proveedor cuya causa no está confirmada.
- Reanudar un INC, revisar su evidencia o concluir si requiere BUG, RM, TEC o ninguna corrección de software.
- Un BUG con esperado documentado y un fallo de QA contra CA conocidos conservan sus rutas existentes; no exigir un INC artificial para cada BUG.

## Precondiciones

- Workspace FARO `available`, root, perfil y fuentes identificados; no crear artefactos en repositorios externos indexados.
- Pedido de registrar/investigar un incidente concreto. Una consulta general sobre el proceso no crea un INC.
- Alcance de investigación autorizado; entorno, datos y efectos de reproducciones conocidos antes de ejecutar. Registrar no autoriza instrumentación, cambios de aplicación, acciones comerciales, rollback ni despliegue.

## Procedimiento

1. Leer contrato, perfil, índice, workflow y registros relacionados. Preservar una unidad activa ajena: no reemplazar `workflow.json` sin decisión humana sobre el cambio de foco. **Completo:** contexto y permisos conocidos.
2. Buscar coincidencias por síntoma, entorno y evidencia; vincular un INC existente si es el mismo caso. Reservar `INC-0001` con el mecanismo serializado del proyecto, considerando registros y reservas, sin reutilizar IDs ni calcular máximo+1 sin reserva serializada. Crear bajo demanda `context/incidents/README.md` desde `assets/incident-index.md` y `context/incidents/INC-0001-<slug>.md` desde `assets/incident.md`. Los nombres no llevan versión; conservar historial in-place y agregar el índice a `context/README.md`. No crear esta estructura durante inicialización. **Completo:** registro único localizable, síntoma preservado sin etiquetarlo BUG.
3. Registrar observado, esperado con fuente o pendiente, impacto y período realmente conocidos; sanitizar evidencia. Si seguimiento es `REQUIRED`, usar el adaptador configurado para vincular o crear el item del INC conforme a `## Seguimiento`; no simular sincronización. **Completo:** fuente local y remota vinculadas o bloqueo explícito.
4. Leer `../references/incident-external-skills.json` y `references/capacidades-externas.md`. Verificar procedencia, integridad, disponibilidad y escaneo permitido de la capacidad seleccionada antes de cargarla. Para investigación técnica usar `systematic-debugging` en fases 1–3, con su referencia `root-cause-tracing.md` cuando corresponda; detenerse antes de fase 4. Entregarle INC, fuentes, revisiones, alcance, permisos y salida requerida: hechos/evidencias, hipótesis contrastadas, causa sustentada o límites. Para post-mortem solicitado o proporcional a impacto/política del proyecto, usar `incident-postmortem` sobre evidencia ya reunida, sin forzarlo en cada reporte menor. **Completo:** la capacidad externa realizó su parte o se informó que esa etapa está bloqueada; no inventar su ejecución ni sustituirla silenciosamente por un diagnóstico propio.
5. Integrar resultados en el INC, sin duplicar la investigación en el BUG. Separar hechos observados, reportados, hipótesis y conclusiones; cada afirmación causal referencia evidencia. Registrar reproducciones realmente ejecutadas y lo que prueban: un mecanismo local no demuestra ocurrencia histórica ni versión desplegada. Mantener causas múltiples y factores contribuyentes si hay evidencia. No forzar cinco porqués, causa única, métricas, severidad, responsables, plazos ni acciones para completar una plantilla. **Completo:** causa y confianza no exceden la evidencia; desconocidos visibles.
6. Clasificar el resultado según `## Conclusión y derivación`. Una propuesta de corrección no es autorización. Crear o vincular BUG/RM/TEC sólo con autorización explícita de ese alcance, referencia al INC y esperado sustentado cuando sea BUG. Si aún no fue autorizada, registrar la propuesta sin reservar un BUG ficticio. **Completo:** decisión y siguiente ruta explícitas, incluso si no se requiere cambio de software.
7. Aplicar `## Cierre`, actualizar registro, índice y continuidad de la unidad propia. Si continúa la investigación, `nextRoute` es `faro-incidentes`; un handoff autorizado conserva el INC como fuente y apunta a la ruta de corrección, sin convertir aprobación de investigación en aprobación de implementación. Sincronizar hitos materiales conforme a `../references/comment-format.md` y verificar por lectura toda escritura remota. **Completo:** se puede retomar el caso y se conoce qué terminó y qué sigue pendiente.

## Conclusión y derivación

| Resultado sustentado | Decisión / siguiente paso |
| --- | --- |
| Defecto propio: observado contradice esperado con fuente | Proponer BUG. Autorizado y con esperado documentado → `faro-req-analisis-tecnico`; si falta definición funcional → `faro-req-ingenieria` o DF según perfil. |
| Proveedor o dependencia externa | Referenciar contrato, respuesta y seguimiento externo; no crear BUG propio automáticamente. Un defecto propio al manejar esa respuesta puede generar un BUG separado si se demuestra y autoriza. |
| Comportamiento de negocio esperado | Citar la regla confirmada y cerrar sin BUG cuando corresponda. Si se pide otro comportamiento, derivar a RM/DF por la ruta funcional; no corregir una regla válida como si fuera un defecto. |
| Configuración, datos u operación | Proponer acción específica y pedir autorización de sus efectos. TEC sólo si el alcance realmente es mantenimiento sin cambio funcional; no usar TEC como permiso para operar. |
| Evidencia insuficiente o no reproducido | Conclusión no concluyente, evidencia faltante y siguiente comprobación; no equivale a «no es bug». No crear una corrección especulativa. |

Las clasificaciones pueden coexistir cuando hay causas combinadas; conservar sus evidencias y acciones por separado. `fix` describe la implementación/commit, no un tercer artefacto obligatorio junto a INC y BUG.

## Cierre

- Estados del registro: `ABIERTO`, `EN_INVESTIGACION`, `CERRADO`. Un bloqueo se expresa en pendientes y `waitingOn`, no como una causa inventada.
- Separar estado de investigación, conclusión y situación del impacto. Causa conocida no significa servicio recuperado; contención no significa corrección definitiva; BUG cerrado no cierra automáticamente el INC.
- Cerrar con conclusión sustentada, situación del impacto verificada y acciones pendientes enlazadas. Un cierre sin BUG es válido si se justifica con evidencia, por ejemplo regla de negocio correcta o causa externa resuelta.
- Si persiste impacto activo o no verificado, no declarar el incidente resuelto ni cerrarlo por haber terminado el análisis. Mantenerlo abierto con el seguimiento correspondiente.
- Para archivar una investigación no concluyente, exigir decisión humana explícita y ausencia de impacto activo pendiente, dejando límites y condición de reapertura. No declararla «sin defecto».
- Reabrir el mismo INC ante nueva evidencia del mismo caso, preservando conclusión previa e historial. Una recurrencia distinta puede tener otro INC enlazado; no sobrescribir evidencia histórica.

## Seguimiento

- `OFF`: no crear tickets remotos. `REQUIRED`: el INC tiene item propio o recibido, tipo y transiciones verificados por el adaptador configurado. Exigir tipo neutral sólo para items nuevos; no asumir que existe un tipo «Incident» ni crear un «Bug» para una causa no confirmada. Si se requiere un alta nueva y falta un tipo neutral autorizado, pedir esa decisión y registrar el bloqueo.
- Importar una issue reportada como BUG no confirma su clasificación; preservar su ID, tipo y contenido sin reclasificarla automáticamente. Vincular el item recibido aunque sea de tipo Bug como seguimiento del INC, con su workflow verificado; no exigir otro item neutral ni bloquear sólo por su tipo. Crear un item neutral separado requiere decisión explícita y vínculo con el original, no una duplicación automática.
- INC y BUG derivados mantienen IDs/URLs y vínculos bidireccionales independientes. No duplicar un item recibido ni convertir el INC remoto en BUG silenciosamente; el BUG sólo se crea tras autorización.
- `DONE` del seguimiento del INC refleja cierre permitido del incidente, no finalización de todas las correcciones. No cerrar el item del INC por publicar el commit de un BUG derivado, ni cancelar un INC sólo porque la conclusión no fue un defecto.
- Si falla una escritura REQUIRED, conservar evidencia local y `waitingOn`; no avanzar de fase ni declarar el cierre remoto. Verificar por lectura el item, comentario y vínculos afectados antes de afirmar éxito.

## Verificación

- [ ] INC único y bajo demanda, sin interferir con trabajo activo ajeno.
- [ ] Capacidad externa identificada por procedencia, revisión, archivos requeridos y escaneo permitido; límites FARO transmitidos.
- [ ] Evidencias sin secretos/PII, hipótesis diferenciadas y conclusiones dentro del alcance probado.
- [ ] Derivación autorizada o cierre sin BUG justificado; no se cambió código ni se ejecutaron operaciones por inferencia.
- [ ] Investigación, impacto y corrección no se confundieron; seguimiento remoto verificado si aplica.
