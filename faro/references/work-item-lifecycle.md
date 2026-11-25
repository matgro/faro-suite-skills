# Expedientes y conocimiento duradero

## Autoridad

FARO separa el trabajo que cambia el producto del conocimiento vigente del producto.

| Información | Fuente canónica |
| --- | --- |
| Estado operativo, prioridad, asignación, iteración y cola global | Jira o Azure DevOps configurado en el perfil |
| Solicitud, diagnóstico y alcance autorizado | Documento principal del expediente |
| Plan, tareas y evidencia de ejecución | Archivos del mismo expediente |
| Resultado de QA y validación | Reportes del mismo expediente |
| Comportamiento vigente | DF baselineado y documentación de producto indexada |
| Decisión técnica duradera | Arquitectura y ADR |
| Operación vigente | Runbook o documentación operativa indexada |
| Contrato o referencia vigente | Referencia/API/glosario indexado |
| Continuidad temporal | `context/workflow.json`, sólo como puntero y checkpoint |

Los campos locales de madurez o resultado —por ejemplo `spec_maturity`, `assessment_maturity`, `plan_readiness`, resultados de casos y veredicto de validación— son evidencia documental. No deben llamarse ni utilizarse como el estado operativo del item remoto.

## Rutas estables

```text
context/requirements/
├── project-profile.md
├── requirements-catalog.md
├── functional-documents-catalog.md
├── functional/
│   └── DF-001/
│       ├── DF-001.md
│       └── DF-001-investigacion-interna.md
└── work-items/
    ├── RM-0001/
    │   ├── RM-0001.md
    │   ├── RM-0001-plan-tecnico.md
    │   ├── RM-0001-tareas.md
    │   ├── RM-0001-qa.md
    │   ├── RM-0001-validacion.md
    │   └── RM-0001-entrega.md
    ├── BUG-0001/
    └── TEC-0001/
```

Los ejemplos muestran los nombres de una unidad nueva. Los expedientes y DF migrados pueden conservar un basename histórico con slug dentro de su carpeta; la columna `Documento principal` del catálogo y el helper central determinan cuál es el primario. No renombrarlo por heurística. No crear `active/` ni `completed/`, no mover una unidad cuando cambia su estado y no resolver rutas por una búsqueda global si existe catálogo.

`context/incidents/` sigue separado: una investigación INC puede producir un BUG, pero no es su expediente ni comparte automáticamente su cierre.

## Reserva y localización

Todas las skills usan `scripts/work_item_contract.py` para validar, reservar, localizar y comprobar expedientes. La reserva se serializa; el casing se compara para detectar colisiones, pero nunca se normaliza silenciosamente: `DF-NNN`, `RM-NNNN`, `BUG-NNNN` y `TEC-NNNN` son obligatoriamente mayúsculos. El catálogo conserva ID, tipo, ruta, documento principal, referencia remota, relaciones y la fuente de reserva aun después de publicar; un reintento con la misma fuente resuelve el mismo ID. RM/BUG/TEC comparten un namespace de fuente: reintentar el mismo intake con otra clasificación bloquea en vez de duplicarlo. DF usa su namespace documental separado. No contiene estado, prioridad, asignado ni sprint.

Una colisión, un ID duplicado entre layouts, una ruta fuera del root, una carpeta cuyo nombre no coincide con el front matter o un catálogo ambiguo bloquean la escritura. No corregirlos por máximo+1, renumeración o heurística.

Un expediente migrado ya publicado que conserva vacíos proveedor, ID y URL remotos sólo se reconcilia después de crear o importar y releer el mismo item mediante el adaptador configurado. `scripts/work_item_contract.py link-external` puede completar ese triple vacío de forma atómica; nunca sobrescribe una referencia existente, parcial o diferente. Hasta reconciliarla, el expediente permanece sólo diagnosticable y no avanza ni se congela.

## Ciclo

1. Ingeniería reserva un ID, crea o enlaza el item remoto y materializa un único expediente. Si el seguimiento no está `REQUIRED` y verificado, se detiene antes de crear RM/BUG/TEC.
2. Análisis, desarrollo, QA, validación y entrega resuelven ese mismo expediente. Cada fase escribe su evidencia específica; el gestor conserva el estado operativo.
3. Validación compara la versión autorizada y registra por CA `CONFORME`, `NO_CONFORME` o `NO_VERIFICADO`. Sólo emite el veredicto global `VERIFIED` cuando todos los CA del alcance están conformes y no hay divergencias materiales; únicamente ese veredicto pasa al cierre.
4. Cierre resuelve una matriz explícita de impacto duradero: producto/DF, arquitectura/ADR, operación/runbook y referencia/API/glosario. Cada fila apunta a una actualización verificada o justifica `NO_APLICA`.
5. Después de consolidar conocimiento y comprobar que las operaciones externas enumeradas coinciden exactamente con la entrega, cierre solicita la transición remota a `DONE`. El CLI central valida primero CA, hash del primario, evidencia, autoridades y versiones promovidas; luego exige una raíz de proveedor autorizada fuera del workspace, ejecuta un GET HTTPS, conserva la respuesta raw codificada y su SHA-256, y deriva ID, tipo y estado. Revalida los gates antes de escribir el manifiesto schema 3. Strings aportados por el operador no acreditan readback. Recién entonces limpia el workflow.
6. El expediente queda congelado. Un cambio posterior recibe otro ID y declara `successor_of`; no se reabre ni edita el anterior.

Una operación de `faro-entrega` puede suceder antes o después de otras fases según el flujo técnico, pero push, PR, release, deploy o rollback no equivalen a cerrar el item.

## Migración

El contrato `1.13.0` se lee sólo para diagnóstico y migración. Ejecutar primero `scripts/migrate_workspace_v2.py --root <root>` para obtener un plan sin escrituras. `--apply` exige autorización explícita, aborta ante colisiones o layout mixto y conserva un inventario recuperable de movimientos, hashes y snapshots de archivos de control modificados. No crea items remotos, no cambia aprobaciones y no hace sustituciones globales dentro de documentación histórica.

Un contrato posterior a la versión soportada nunca se degrada. Si el mismo ID aparece en el layout plano y en el nuevo, la migración y todas las escrituras se bloquean hasta una decisión humana.
