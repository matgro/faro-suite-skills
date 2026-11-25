---
name: faro-cierre
description: Use when FARO closes a verified work item.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, closure, work-items, knowledge, evidence]
    related_skills: [faro, faro-documentacion-funcional, faro-arq-adr, faro-req-validacion, faro-entrega, faro-int-jira, faro-int-azure-devops]
---

# FARO — Cierre de expediente

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar conocimiento sustentado sin alterar alcance, validación ni autorizaciones.

Leer y aplicar [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md) antes de promover, transicionar o congelar una unidad.

## Rol

Cierra un RM, BUG o TEC ya verificado: comprueba su expediente, promueve conocimiento aceptado a la documentación durable, reconcilia la entrega requerida, confirma el estado remoto y congela el registro histórico. No implementa código, no ejecuta QA, no convierte una validación parcial en conformidad y no realiza commit, PR, release o despliegue; esas acciones pertenecen a `faro-entrega`.

El expediente conserva para siempre `context/requirements/work-items/<ID>/`. Nunca se mueve a `active/` o `completed/`. El cierre canónico es `<ID>-cierre.json`, generado exclusivamente por el CLI central con hashes de todos los artefactos salvo sí mismo.

## Cuándo usar

- `faro-req-validacion` produjo `validation_outcome: VERIFIED` y entregó `nextRoute: faro-cierre`.
- Se reanuda un cierre bloqueado por promoción documental, entrega pendiente, sincronización remota o congelado incompleto.
- Se necesita comprobar si un expediente cerrado conserva integridad.

No usar para abandonar/cancelar una solicitud, corregir un expediente congelado ni cerrar sólo porque terminó una operación de entrega. Cancelación es estado del gestor y debe conservar su evidencia sin fabricar `VERIFIED`; un cambio posterior a un cierre reserva otro ID relacionado.

## Precondiciones

- Resolver con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json` y validar con `... validate --root <root> --strict`.
- Catálogo, `workflow.workItemRef`, primario y artefactos de fase apuntan al mismo ID y ruta.
- Existe `<ID>-validacion.md`; su tabla enumera exactamente todos los `CA-NNN` del primario, todos son `CONFORME`, cada uno enlaza evidencia local regular/no vacía, y `validated_primary_version` más `validated_primary_sha256` coinciden con la versión y bytes actuales del primario. `validation_outcome` es `VERIFIED` y no hay divergencia material.
- La validación contiene los cuatro impactos y `required_delivery_evidence`; pueden llegar `PENDING` para que cierre coordine su resolución, pero ningún gate pendiente permite previsualizar el cierre final, transicionar a `DONE` ni congelar.
- Toda acción externa requerida por el alcance —commit, PR, release, despliegue o rollback— tiene evidencia, o está explícitamente fuera del alcance. Una rama o push intermedio no cierra el work item si QA, validación o entrega final siguen pendientes.
- Cada destino durable aparece exactamente una vez: `INCORPORADO` exige ruta existente fuera del expediente, versión/baseline, trazabilidad al work item y evidencia; `NO_APLICA` exige justificación material y no declara ruta/versión ficticias.
- `required_delivery_evidence: SATISFIED` exige que `Operaciones de entrega requeridas` enumere exactamente el alcance y que `<ID>-entrega.md`, dentro del expediente, contenga el mismo conjunto sin faltantes: `work_item_id` coincidente, `artifact_type: DELIVERY_EVIDENCE`, `delivery_outcome: SATISFIED` y evidencia local por operación. Si la entrega no aplica, la tabla requerida queda vacía y `Decisión de entrega` justifica `NOT_APPLICABLE`.
- Seguimiento es `REQUIRED`; proveedor, ID/URL y mapeo `DONE` están verificados y reconciliados. Un expediente legado con `OFF` se bloquea hasta configurar su autoridad remota, preservando la evidencia histórica.

Si un expediente migrado ya publicado aún carece de referencia remota, no intentar compensarlo con flags de freeze. Crear/importar y releer el item mediante el adaptador configurado, previsualizar y aplicar `python -B <skills-root>/faro/scripts/work_item_contract.py link-external --root <root> --id <ID> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --apply --json`, y volver a validar. Una referencia existente diferente bloquea: no se sobrescribe.

Si ya existe `<ID>-cierre.json`, no escribir: `resolve` debe comprobar sus hashes y esta skill sólo informa cierre íntegro o corrupción. Si falta una precondición, registrar `waitingOn` en workflow y elegir un único handoff; no crear un marker parcial a mano.

## Promoción de conocimiento

1. Leer la matriz del primario y la sección `Promoción de conocimiento durable` de la validación. Comparar únicamente el delta validado con la documentación vigente; no promover propuestas, hallazgos fuera de alcance ni comportamiento no verificado.
2. Para `FUNCTIONAL` pendiente, entregar a `faro-documentacion-funcional`. La actualización crea una nueva baseline en el `Documento principal` que resuelve el catálogo para `context/requirements/functional/DF-<NNN>/`, registra el expediente origen y vuelve a `faro-cierre`; un basename migrado no se normaliza durante la promoción.
3. Para una decisión arquitectónica durable pendiente, usar `faro-arq-adr` y volver con el ADR aceptado enlazado. Un plan técnico no sustituye un ADR.
4. Para `OPERATIONS` o `REFERENCE`, actualizar sólo el documento durable y la sección exacta identificados por la validación, respetando sus instrucciones locales. Si no existe destino autorizado o falta definición humana, bloquear; no crear manuales, runbooks o contratos por intuición.
5. Un BUG puede usar `NO_APLICA` cuando restaura el contrato, sus pruebas quedan en código y no cambia conocimiento útil. La ausencia de impacto no se presume: se justifica por destino.

## Procedimiento de cierre

1. Resolver, validar y revisar Git/archivos del expediente. Confirmar que no apareció evidencia nueva después de la validación y que las promociones apuntan a versiones durables reales. **Completo:** el expediente es cerrable, no sólo implementado.
2. Si existe una promoción pendiente, actualizar validación/workflow con el handoff único y detenerse. Al volver con evidencia, actualizar el cuerpo y el gate correspondiente a `INCORPORATED` o `NOT_APPLICABLE`. Si falta una operación externa requerida, `nextRoute` es `faro-entrega`; al volver, verificar `<ID>-entrega.md`, registrar su evidencia y usar `required_delivery_evidence: SATISFIED`; usar `NOT_APPLICABLE` sólo con justificación. No congelar ni transicionar el item a `DONE` mientras algún gate esté `PENDING`. **Completo:** conocimiento y entrega preceden al cierre, y los cinco gates coinciden con evidencia verificable.
3. Previsualizar el marker sin escribir: `python -B <skills-root>/faro/scripts/work_item_contract.py freeze --root <root> --id <ID> --json`. El CLI relee CA, archivos de evidencia, promociones, versiones y entrega; revisar el inventario y hashes. La previsualización no afirma estado remoto ni ejecuta red. **Completo:** los gates locales exactos a congelar son conocidos.
4. Cargar como operación subordinada el adaptador configurado por el perfil: `faro-int-jira` o `faro-int-azure-devops`; no construir una API paralela. Usarlo para publicar un comentario conciso y transicionar el item remoto al estado mapeado como `DONE`. No fabricar un recibo local: el GET final lo ejecuta el CLI central con la configuración confirmada del perfil y credenciales del entorno. Si falla la transición, conservar el expediente mutable, registrar `waitingOn` y detenerse. **Completo:** la transición remota fue solicitada por el adaptador autorizado.
5. Generar el marker con `python -B <skills-root>/faro/scripts/work_item_contract.py freeze --root <root> --id <ID> --apply --json`. `--apply` exige perfil `REQUIRED`, credenciales `VERIFICADO`, mapeos de tipo/`DONE`, raíz del proveedor autorizada fuera del workspace y referencia completa en catálogo. El CLI vuelve a validar localmente antes de enviar credenciales, hace un GET HTTPS autenticado a Jira o Azure DevOps, deriva ID, tipo y estado desde la respuesta raw, conserva el body codificado y su hash, y genera por sí mismo los timestamps. Ya no acepta `--remote-state`, `--readback-at` ni `--readback-evidence`. Después relee otra vez los gates locales, escribe el marker schema 3 con fuente de reserva, `validationGate` y `remoteReadback`, y reconstruye su semántica offline desde primario, validación, evidencias y entrega. Ejecutar luego `resolve` y `validate --strict`; cualquier divergencia exige reconciliación, no reescritura silenciosa. **Completo:** expediente congelado con readback real e íntegro.
6. Limpiar la continuidad activa de `context/workflow.json` sólo después del congelado verificado, preservando otros campos ajenos. Informar ID, ruta, validación, promociones, referencias externas, timestamp y limitaciones reales. **Completo:** el chat no es necesario para reconstruir el cierre.

## Invariantes

- `VERIFIED`, entrega, `DONE` remoto y congelado son hechos distintos; el cierre exige todos los que correspondan al alcance.
- Promover conocimiento no copia planes, tareas o cronología a documentación durable: incorpora únicamente comportamiento vigente, decisiones, procedimientos o referencia útil.
- El catálogo conserva localización y referencia remota, nunca estado, prioridad o asignación.
- No existe cierre local bajo seguimiento `OFF`; reconciliar el item remoto es una precondición del marker.
- No agregar archivos, comentarios o correcciones dentro de un expediente congelado. Erratas, regresiones y evoluciones usan un sucesor con vínculo al ID anterior.
- No mover, borrar, renombrar ni recalcular hashes de un expediente cerrado para ocultar divergencias.
- Una transición remota exitosa no compensa un freeze fallido; reportar la discrepancia y reconciliarla explícitamente.

## Verificación

- [ ] El CLI resolvió catálogo, ruta, primario y referencia remota del mismo ID.
- [ ] Validación es VERIFIED y cada CA del alcance es CONFORME.
- [ ] Cada CA coincide con el primario, está CONFORME y enlaza evidencia local hasheada.
- [ ] Cada impacto durable está incorporado con ruta/versión/hash o tiene NO_APLICA justificado.
- [ ] Entregas requeridas están evidenciadas; operaciones parciales no se confundieron con cierre.
- [ ] `impact_*` no contiene `PENDING` y `required_delivery_evidence` es `SATISFIED` o `NOT_APPLICABLE`, en concordancia con el cuerpo.
- [ ] Si delivery es `SATISFIED`, `<ID>-entrega.md` identifica el mismo work item y declara `DELIVERY_EVIDENCE`.
- [ ] El estado remoto DONE fue confirmado por GET autenticado del CLI; no por strings aportados.
- [ ] `<ID>-cierre.json` fue generado por el CLI, excluye su propio hash y valida en modo strict.
- [ ] Workflow dejó de apuntar a la unidad cerrada y el expediente permaneció en su ruta estable.
