---
name: faro-entrega
description: Use when FARO delivers a requested commit, PR, or deploy.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, delivery, git, release, deployment]
    related_skills: [faro, faro-req-validacion, faro-qa-ejecucion, faro-req-desarrollo, faro-cierre]
---

# FARO — Entrega controlada

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

## Rol
Ejecuta acciones que sacan trabajo del directorio local: commit, branch, push, PR, release, despliegue o rollback. No implementa código ni convierte desarrollo en autorización implícita de salida. Entrega y cierre son operaciones independientes: una referencia Git, PR, release o despliegue aporta evidencia, pero nunca marca por sí misma el RM/BUG/TEC remoto como `DONE`.

## Precondiciones

- Resolver el expediente con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json` y validar el contrato. Catálogo, `workflow.workItemRef`, primario y referencia remota deben señalar el mismo RM/BUG/TEC. Si el helper informa un expediente congelado, no ejecutar ni escribir dentro de él: una operación posterior requiere un sucesor enlazado o un INC nuevo según su naturaleza.
- Para una aplicación, leer [Versionado de aplicaciones](../references/application-versioning.md) y su política por componente en `context/requirements/project-profile.md`. Resolver fuente, derivados, modo de decisión y permisos. Entrega actualiza valores de mecanismos existentes, no implementa lectores ni pipelines; si faltan, derivar a análisis/desarrollo autorizado. No incrementar por cada commit ni por reintentos/promociones; comprobar artefacto y versión efectiva al desplegar.
- Acción explícita: commit, PR, release, despliegue o rollback.
- RM/BUG/TEC, versión y evidencia de validación identificados.
- Con seguimiento `REQUIRED`, item remoto, tipo, estado actual y relaciones relevantes releídos; el gestor conserva la autoridad del estado operativo.
- Para despliegue, la autorización nombra el ambiente; producción nunca se infiere.
- Se leyeron reglas de repositorio, CI, despliegue, rollback y estado Git.
- Antes de commit, push, PR o release, resolver versión y tag conforme a `references/versionado-y-tags.md`: proponer el incremento por impacto y preguntar en una sola confirmación si se actualiza la versión y se crea/publica el tag. No repetir decisiones explícitas ya autorizadas; una entrega sin versión/tag también requiere una decisión explícita.
  Una política AUTOMATICA previamente aprobada puede cubrir esa decisión dentro de sus límites; no autoriza otras operaciones o ambientes y no sustituye la verificación de versión/artefacto.
- Si la acción crea una rama, respetar primero la convención observada del repositorio. Si no existe una y la unidad es RM, BUG o TEC, usar `feature/<ID>-<descripcion-kebab-case>` con el prefijo real del ID. No usar `feat/` como sustitución implícita.

## Procedimiento
1. Declarar preparación: validación, checks, cambios locales, migraciones, configuración/secretos por clave y riesgos. Para commit, push, PR o release, leer `references/versionado-y-tags.md`, inspeccionar versión y tags locales/remotos y confirmar las decisiones pendientes antes de modificar la versión o ejecutar la entrega. **Completo:** huecos visibles, versión y tag resueltos sin asumir autorización.
2. Para commit/PR, revisar diff por secretos, configuración local, generados y alcance; redactar el mensaje conforme a `## Mensajes de commit y PR`. **Completo:** sólo archivos autorizados y mensaje con título, descripción funcional y tareas asociadas.
3. Para release/deploy, verificar artefacto, ambiente, health checks, observabilidad, rollback y migraciones. **Completo:** no se reconstruye una versión distinta.
4. Ejecutar sólo la acción autorizada; crear o actualizar `<ID>-entrega.md` dentro del expediente resuelto usando `assets/delivery-record.md`, y registrar operación, autorización, comando sin secretos, referencia, resultado, evidencia y ambiente. Si se autorizó versionar y taguear, sincronizar metadatos e integridad, validar, crear el commit y el tag anotado sobre ese commit, publicar sólo las referencias autorizadas y verificar sus SHA remotos conforme a `references/versionado-y-tags.md`. Cada reintento se agrega al historial del mismo artefacto; no se crea otro expediente ni se sobrescribe evidencia previa. **Completo:** salida verificable; un push de rama no se declara publicación del tag.
5. Registrar cada operación en `Operaciones verificadas` con resultado, referencia, fecha con zona y uno o más archivos regulares/no vacíos del expediente en `Evidencia local`, separados por `;`. Usar `delivery_outcome: SATISFIED` sólo cuando todas las operaciones requeridas estén `SATISFIED`; un intento fallido o pendiente conserva otro outcome. Si seguimiento está `REQUIRED`, publicar el resultado real conforme a `../references/comment-format.md`. Releer después el comentario/vínculo y el item. Mantener el estado operativo de trabajo: no solicitar `DONE` ni `CANCELLED` desde esta skill. Si falla la sincronización o readback, registrar el bloqueo y reportar por separado entrega y seguimiento.
6. Actualizar workflow y la documentación operacional durable afectada con referencias verificadas, sin copiar el plan ni usar el runbook como cronología de la entrega. Entregar el control a la operación de cierre cuando se solicite, sin ejecutarla ni anticipar su resultado. **Completo:** `<ID>-entrega.md` hace reanudable el resultado; el item todavía no fue cerrado por inferencia.

## Entrega no es cierre

- Crear rama, commit o tag, hacer push, abrir/fusionar PR, publicar release, desplegar o ejecutar rollback no equivale a completar la unidad de trabajo.
- Una entrega exitosa puede ser entrada del cierre sólo después de que los gates FARO aplicables —validación, evidencia, pendientes y decisión sobre documentación durable— estén satisfechos. Esta skill registra evidencia; no los reinterpreta.
- `DONE` requiere una operación explícita de cierre sobre el item remoto, con estado leído antes y después. `CANCELLED` requiere cancelación humana explícita. Ninguna de las dos transiciones se deriva de un comentario de entrega.
- Si una operación externa tiene éxito y la sincronización falla, conservar ambas verdades: entrega realizada y seguimiento bloqueado. No repetir ni revertir automáticamente la operación para obtener un estado remoto verde.
- Si despliegue o verificación posterior falla, registrar el resultado y volver a la fase correspondiente; no cerrar, reabrir ni cancelar automáticamente el work item.

## Mensajes de commit y PR

- Redactar el mensaje del commit en varias líneas: primera línea como título breve, línea en blanco, descripción funcional sintetizada y, debajo, las tareas asociadas.
- La descripción explica qué funcionalidad cambió, se agregó o se quitó, sin repetir el título. Usar una o dos oraciones; no incluir código, nombres de clases ni detalles internos de implementación.
- Colocar las referencias de tareas al final, separadas de la descripción por una línea en blanco, con formato `#<ID>` (por ejemplo, `#9999`). Si hay varias, incluir una por línea. Usar sólo tareas asociadas verificadas; no inventar IDs y, si no hay tareas asociadas, omitir ese bloque. No incluir estas referencias en el título.
- Preservar los saltos de línea al crear el commit: no concatenar título, descripción y tareas en una sola línea. El push publica el mensaje existente; no lo reemplaza ni duplica su título como descripción.
- Para un PR, usar la primera línea como título y el resto como descripción, conservando el resumen funcional y las tareas al final. Este formato no sustituye los comentarios de seguimiento de `../references/comment-format.md`.

Ejemplo de mensaje de commit (las tareas son ilustrativas):

```text
fix(sac): corregir identificación de solicitudes externas

Se agrega la identificación de la aplicación en las solicitudes a servicios externos.

#9999
#10000
```

## Invariantes
- Validación no es aceptación productiva; aceptación no es despliegue.
- Entrega no es cierre; push, PR, merge, release, tag, deploy o rollback no implican `DONE`.
- Nunca imprimir secretos; documentar sólo nombres de llaves.
- Rollback de código no autoriza rollback destructivo de datos.
- Despliegue sin verificación se reporta como desplegado, no validado.

## Verificación
- [ ] Acción y ambiente fueron nombrados.
- [ ] Se confirmó si se actualiza versión y se crea/publica tag; el incremento responde al impacto y las referencias remotas autorizadas coinciden con el commit validado.
- [ ] Diff, checks y riesgos fueron revisados.
- [ ] El commit/PR separa título, descripción funcional breve y tareas asociadas verificadas, sin código ni nombres de clases.
- [ ] Evidencia posterior fue capturada si aplica.
- [ ] La versión del producto, su fuente, derivados, SHA y artefacto corresponden a la entrega acordada; reintentos/promociones no incrementaron otra vez. El resultado distingue tag, build, despliegue y versión efectiva comprobada, o su limitación explícita.
- [ ] Comentarios/vínculos remotos fueron releídos; el item no se cerró ni canceló desde entrega.
- [ ] El expediente fue resuelto por el helper, no estaba congelado y `<ID>-entrega.md` conserva el resultado real y sus reintentos.
- [ ] Workflow y documentación durable registran sólo continuidad o conocimiento vigente, sin declarar la unidad completa.
