# Formato de actualizaciones de seguimiento

Las actualizaciones remotas son una bitácora breve para retomar trabajo, no un transcript de la sesión ni un reporte de entrega. No llevan el prefijo `FARO`, ni repiten autor, fecha, estado remoto, comandos, hashes, conteos de pruebas, rutas locales o antecedentes ya vinculados.

## Cuándo publicar

Publicar un comentario sólo cuando deja un hecho útil para una sesión posterior:

- comienza o termina una fase;
- una unidad material de implementación queda completada, bloqueada o se revierte;
- cambia el alcance, una decisión, una autorización, una dependencia o `waitingOn`;
- una operación externa autorizada produce una referencia durable: rama, commit, PR, release o despliegue;
- QA o validación produce un resultado que modifica el siguiente paso.

Durante implementación, publicar un comentario por cada unidad material terminada o bloqueada. No publicar por lecturas, comandos, archivos modificados, intentos intermedios, cada prueba individual ni cada herramienta usada. Si una unidad termina en la misma sesión y no deja una decisión, bloqueo ni referencia durable, resumirla en el comentario de cierre de su tarea inmediata.

## Plantilla

Usar como máximo cuatro líneas, omitiendo las opcionales:

```text
<Fase> · <acción o unidad> — <COMPLETADA | BLOQUEADA | EN CURSO>
<resultado verificable, en una oración>
Evidencia: <enlace o referencia durable>.
Siguiente: <acción, fase o bloqueo>.
```

- `Evidencia` sólo se incluye si existe una referencia útil.
- `Siguiente` se incluye cuando cambia el handoff; para un bloqueo, indica el requisito para reanudar.
- Una excepción relevante se expresa en el resultado sin reproducir logs: `Pruebas del alcance correctas; persiste un fallo basal ajeno en la evidencia enlazada.`
- El comentario no afirma aprobación, validación funcional, merge ni despliegue si no ocurrieron.

## Ejemplos

```text
Desarrollo · TASK-002 — COMPLETADA
Se resolvió el nodo antes de persistir el registro y se cubrió el rechazo sin efectos.
Evidencia: rama feature/RM-0002-resolucion-nodo-almacen-cygnus.
Siguiente: TASK-003.
```

```text
QA · ejecución de CA-04 — BLOQUEADA
Falta autorización para usar los datos de prueba requeridos.
Siguiente: confirmar datos aislados y reanudar CA-04.
```

```text
Entrega · push — COMPLETADA
La rama autorizada quedó publicada y coincide con la referencia remota.
Evidencia: commit db5589921ad5cd6e3b7ce9a65b65085ed5935b78.
Siguiente: QA y validación funcional.
```
