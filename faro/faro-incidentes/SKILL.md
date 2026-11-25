---
name: faro-incidentes
description: Use when FARO records or investigates an incident.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, incidents, evidence, investigation, triage]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico, faro-int-jira, faro-int-azure-devops, systematic-debugging, incident-postmortem]
---

# FARO — Incidentes

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones. Las hipótesis causales de un INC no se convierten en definiciones confirmadas.

## Rol

Orquesta el registro, investigación, clasificación y cierre evidenciado de un incidente `INC`, sin presuponer un defecto. El expediente INC permanece separado de RM/BUG/TEC y conserva autorización, evidencia, cronología, impacto, conclusión y derivaciones; las capacidades externas revisadas aportan investigación técnica y revisión causal según [capacidades externas](references/capacidades-externas.md). No replica sus metodologías ni implementa una corrección. Con seguimiento `REQUIRED`, el gestor remoto es la fuente canónica del estado operativo; el expediente local no lo sustituye.

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
2. Buscar coincidencias por síntoma, entorno y evidencia; resolver por ID o fuente con `python -B <skills-root>/faro/faro-incidentes/scripts/incident_registry.py resolve --root <root> --id <INC-ID> --json` o `--source <fuente>`. Si `validate --json` informa un índice legacy, `validate` y `resolve` permanecen de sólo lectura y exponen cada fuente histórica como `LEGACY:<INC-ID>`; revisar primero `... upgrade --root <root> --json` y ejecutar luego `--apply` para migrarlo atómicamente, nunca editarlo a mano. Si es un caso nuevo, elegir una fuente estable, no secreta y sin pipes/saltos de línea; previsualizar `... reserve --root <root> --source <fuente> --scope <alcance> --json` y, tras revisar el resultado, repetir con `--apply`. El CLI crea bajo demanda `context/incidents/README.md` desde el asset, serializa la reserva con un lock de sistema liberable aun si el proceso termina y devuelve el mismo ID para la misma fuente incluso ante reintentos concurrentes; reutilizar esa fuente con un alcance diferente bloquea la operación. Nunca asignar un ID sin reserva serializada, calcular máximo+1 por fuera del CLI ni editar las filas de identidad a mano. **Completo:** coincidencia existente o reserva única demostrable, sin item remoto implícito.
3. Para una reserva nueva, crear exactamente `context/incidents/<INC-ID>-<slug>.md` desde `assets/incident.md`, conservar el encabezado `# <INC-ID> — ...` y no usar symlinks. Previsualizar `... register --root <root> --id <INC-ID> --source <fuente> --path context/incidents/<INC-ID>-<slug>.md --json`; repetir con `--apply` sólo si valida el archivo regular y consume la misma reserva. Ejecutar después `... validate --root <root>`. Los nombres no llevan versión ni se mueven por estar abiertos o cerrados; conservar historial in-place y agregar el índice a `context/README.md`. No crear esta estructura durante inicialización. **Completo:** expediente publicado, localizable e íntegro; reserva consumida atómicamente.
4. Registrar observado, esperado con fuente o pendiente, impacto y período realmente conocidos; sanitizar evidencia. Si seguimiento es `REQUIRED`, usar el adaptador configurado para vincular o crear el item neutral del INC conforme a `## Seguimiento`, registrar ID/URL/tipo y verificarlo por lectura. El CLI local no crea, modifica ni cierra items remotos. El estado, prioridad y asignación se consultan al gestor y no se copian como autoridad al expediente o índice. **Completo:** fuentes local/remota vinculadas y leídas, o bloqueo explícito.
5. Leer `../references/incident-external-skills.json` y `references/capacidades-externas.md`. Verificar procedencia, integridad, disponibilidad y escaneo permitido de la capacidad seleccionada antes de cargarla. Para investigación técnica usar `systematic-debugging` en fases 1–3, con su referencia `root-cause-tracing.md` cuando corresponda; detenerse antes de fase 4. Entregarle INC, fuentes, revisiones, alcance, permisos y salida requerida: hechos/evidencias, hipótesis contrastadas, causa sustentada o límites. Para post-mortem solicitado o proporcional a impacto/política del proyecto, usar `incident-postmortem` sobre evidencia ya reunida, sin forzarlo en cada reporte menor. **Completo:** la capacidad externa realizó su parte o se informó que esa etapa está bloqueada; no inventar su ejecución ni sustituirla silenciosamente por un diagnóstico propio.
6. Integrar resultados en el INC, sin duplicar la investigación en el BUG. Separar hechos observados, reportados, hipótesis y conclusiones; cada afirmación causal referencia evidencia. Registrar reproducciones realmente ejecutadas y lo que prueban: un mecanismo local no demuestra ocurrencia histórica ni versión desplegada. Mantener causas múltiples y factores contribuyentes si hay evidencia. No forzar cinco porqués, causa única, métricas, severidad, responsables, plazos ni acciones para completar una plantilla. **Completo:** causa y confianza no exceden la evidencia; desconocidos visibles.
7. Clasificar el resultado según `## Conclusión y derivación`. Una propuesta de corrección no es autorización. Crear o vincular BUG/RM/TEC sólo con autorización explícita de ese alcance, referencia al INC y esperado sustentado cuando sea BUG. El derivado tiene expediente e item remoto propios según su clase; mantener vínculos bidireccionales locales y remotos sin convertir el INC. Si aún no fue autorizado, registrar la propuesta sin reservar un BUG ficticio. **Completo:** decisión y siguiente ruta explícitas, incluso si no se requiere cambio de software.
8. Aplicar `## Cierre y autoridad de estado`, actualizar expediente, los campos de evidencia no operativa del índice y la continuidad de la unidad propia sin alterar ID, fuente o ruta fuera del CLI. Ejecutar nuevamente `incident_registry.py validate`. Si continúa la investigación, `nextRoute` es `faro-incidentes`; un handoff autorizado conserva el INC como fuente y apunta a la ruta de corrección, sin convertir aprobación de investigación en aprobación de implementación. Sincronizar hitos materiales conforme a `../references/comment-format.md` y verificar por lectura item, comentario, transición y relaciones afectados. **Completo:** se puede retomar el caso, el expediente conserva hechos y el gestor refleja el estado operativo real.

## Conclusión y derivación

| Resultado sustentado | Decisión / siguiente paso |
| --- | --- |
| Defecto propio: observado contradice esperado con fuente | Proponer BUG. Autorizado y con esperado documentado → `faro-req-analisis-tecnico`; si falta definición funcional → `faro-req-ingenieria` o DF según perfil. |
| Proveedor o dependencia externa | Referenciar contrato, respuesta y seguimiento externo; no crear BUG propio automáticamente. Un defecto propio al manejar esa respuesta puede generar un BUG separado si se demuestra y autoriza. |
| Comportamiento de negocio esperado | Citar la regla confirmada y cerrar sin BUG cuando corresponda. Si se pide otro comportamiento, derivar a RM/DF por la ruta funcional; no corregir una regla válida como si fuera un defecto. |
| Configuración, datos u operación | Proponer acción específica y pedir autorización de sus efectos. TEC sólo si el alcance realmente es mantenimiento sin cambio funcional; no usar TEC como permiso para operar. |
| Evidencia insuficiente o no reproducido | Conclusión no concluyente, evidencia faltante y siguiente comprobación; no equivale a «no es bug». No crear una corrección especulativa. |

Las clasificaciones pueden coexistir cuando hay causas combinadas; conservar sus evidencias y acciones por separado. `fix` describe la implementación/commit, no un tercer artefacto obligatorio junto a INC y BUG.

## Cierre y autoridad de estado

- El expediente registra eventos de apertura, inicio/reanudación de investigación, conclusión, cierre evidenciado y reapertura dentro de su cronología/historial; esos eventos no son un segundo estado operativo. Con `REQUIRED`, el estado actual se relee del item remoto. Con `OFF`, se informa expresamente que no existe estado remoto y la continuidad local no se presenta como sincronizada.
- Separar estado de investigación, conclusión y situación del impacto. Causa conocida no significa servicio recuperado; contención no significa corrección definitiva; BUG cerrado no cierra automáticamente el INC.
- Cerrar el expediente con conclusión sustentada, situación del impacto verificada y acciones pendientes enlazadas. Un cierre sin BUG es válido si se justifica con evidencia, por ejemplo regla de negocio correcta o causa externa resuelta. Ese evento no transiciona automáticamente el item remoto.
- Si persiste impacto activo o no verificado, no declarar el incidente resuelto ni cerrarlo por haber terminado el análisis. Mantenerlo abierto con el seguimiento correspondiente.
- Para archivar una investigación no concluyente, exigir decisión humana explícita y ausencia de impacto activo pendiente, dejando límites y condición de reapertura. No declararla «sin defecto».
- Solicitar `DONE` remoto sólo mediante la operación explícita de cierre del INC, después de releer el item y comprobar conclusión, impacto y acciones. Entrega, commit o cierre de un derivado no son esa operación. Releer después la transición antes de afirmar cierre remoto.
- Reabrir el mismo INC ante nueva evidencia del mismo caso, preservando conclusión previa e historial y usando una transición remota válida cuando `REQUIRED`. Una recurrencia distinta puede tener otro INC enlazado; no sobrescribir evidencia histórica.

## Seguimiento

- `OFF`: no crear tickets remotos ni afirmar un estado remoto. `REQUIRED`: el INC tiene item propio o recibido, tipo, workflow y relaciones verificados por el adaptador configurado; su estado operativo remoto es canónico. Exigir tipo neutral sólo para items nuevos; no asumir que existe un tipo «Incident» ni crear un «Bug» para una causa no confirmada. Si se requiere un alta nueva y falta un tipo neutral autorizado, pedir esa decisión y registrar el bloqueo.
- Importar una issue reportada como BUG no confirma su clasificación; preservar su ID, tipo y contenido sin reclasificarla automáticamente. Vincular el item recibido aunque sea de tipo Bug como seguimiento del INC, con su workflow verificado; no exigir otro item neutral ni bloquear sólo por su tipo. Crear un item neutral separado requiere decisión explícita y vínculo con el original, no una duplicación automática.
- INC y BUG/RM/TEC derivados mantienen IDs/URLs, expedientes y vínculos bidireccionales independientes. No duplicar un item recibido ni convertir el INC remoto en corrección silenciosamente; el derivado sólo se crea tras autorización y con el tipo mapeado.
- `DONE` del seguimiento del INC refleja cierre permitido del incidente, no finalización de todas las correcciones. No cerrar el item del INC por publicar el commit de un BUG derivado, ni cancelar un INC sólo porque la conclusión no fue un defecto.
- Antes de responder por estado o decidir cierre/reapertura, releer el item remoto. Si falla una escritura o readback REQUIRED, conservar evidencia local y `waitingOn`; no avanzar en la operación dependiente ni declarar estado o cierre remoto. Verificar por lectura el item, comentario, transición y vínculos afectados antes de afirmar éxito.

## Verificación

- [ ] INC único, separado y bajo demanda, sin interferir con trabajo activo ajeno.
- [ ] Reserva y registro resolvieron por el CLI, la fuente idempotente conserva un único ID y `validate` confirma índice/expediente sin symlinks.
- [ ] Capacidad externa identificada por procedencia, revisión, archivos requeridos y escaneo permitido; límites FARO transmitidos.
- [ ] Evidencias sin secretos/PII, hipótesis diferenciadas y conclusiones dentro del alcance probado.
- [ ] Derivación autorizada con expediente/item propios y vínculos bidireccionales, o cierre sin BUG justificado; no se cambió código ni se ejecutaron operaciones por inferencia.
- [ ] Investigación, impacto, corrección, entrega y cierre no se confundieron; seguimiento remoto y readback verificados si aplica.
