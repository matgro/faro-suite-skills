---
name: faro-int-azure-devops
description: Use when FARO configures Azure DevOps work tracking.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, azure-devops, visualstudio, integration, synchronization]
    related_skills: [faro, faro-inicializacion, faro-doctor, faro-req-ingenieria, faro-incidentes, faro-entrega, faro-cierre, azure-devops-rest-v7]
---

# FARO — Integración Azure DevOps / Visual Studio

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase. El vocabulario por sí solo no crea ni actualiza work items remotos.

## Rol

`faro-int-azure-devops` es el adaptador de gobernanza entre FARO y `azure-devops-rest-v7`. Configura Azure DevOps sólo por petición humana expresa, importa un work item como fuente `SRC` y, con política `REQUIRED`, sincroniza el seguimiento operativo de RM, BUG, TEC, INC y TASK.

La URL hospedada en `*.visualstudio.com` y `dev.azure.com` identifica el mismo proveedor; se conserva la URL confirmada sin transformarla. No sustituye el expediente local, aprobación humana, análisis, QA, validación, entrega ni cierre. Azure DevOps es la fuente canónica del estado operativo, prioridad, asignación, área e iteración; los expedientes FARO conservan definición, decisiones, evidencia y resultados verificables.

## Cuándo usar

- Durante inicialización después de confirmar `work_tracking.mode: REQUIRED` y `provider: AZURE_DEVOPS`.
- En un proyecto `available`, sólo cuando el usuario pide agregar o configurar Azure DevOps.
- Cuando el usuario aporta una URL Azure DevOps/Visual Studio y el perfil habilita este proveedor.

## Configuración y autorización

1. Leer el contrato FARO, `context/stats.json`, el perfil y el workflow. Confirmar `available`, salvo dentro de una inicialización. **Completo:** estado y política conocidos.
2. Registrar sólo metadatos en `project-profile.md`: proveedor, URL de organización, proyecto, área, equipo, iteración por defecto, mapeos por clase local, campos/valores aplicables, estado de credenciales y capacidades autorizadas. Los mapeos cubren `RM`, `BUG`, `TEC`, `INC` y `TASK` hacia tipos reales; workflow por tipo; relaciones padre/hijo y origen/derivado; actividad y estimación sólo donde correspondan. No registrar PAT, contraseñas, cookies ni cabeceras. **Completo:** los valores específicos del proyecto son verificables y no sensibles.
3. El PAT permanece fuera del repositorio y del workspace como `AZDO_PAT`; puede obtenerse del entorno ya inyectado o de cualquier `.env` global perteneciente a un agente, aunque no sea Hermes. Los valores no sensibles `AZDO_ORGANIZATION_URL`, `AZDO_DEFAULT_PROJECT`, `AZDO_DEFAULT_AREA_PATH`, `AZDO_DEFAULT_TEAM` y `AZDO_DEFAULT_ASSIGNED_TO` pueden obtenerse de las mismas fuentes globales. FARO puede buscar estas fuentes únicamente en directorios de configuración de agentes fuera del workspace y de repositorios indexados; nunca busca ni lee `.env` de una aplicación. Si el perfil ya declara un valor, el valor global sólo se acepta si coincide; durante inicialización, un valor global puede proponerse pero requiere confirmación humana antes de persistirlo en el perfil y verificarlo contra Azure DevOps. Si falta PAT, no consultar ni modificar Azure DevOps. **Completo:** no hubo reutilización de credenciales de la aplicación ni exposición o persistencia de secretos.
4. Con modo `REQUIRED`, ejecutar una lectura autenticada contra la organización y consultar tipos, relaciones, áreas, iteraciones del equipo, campos y estados de cada tipo que vaya a usarse. Registrar por clase local las equivalencias `PENDING`, `DOING`, `DONE` y, si existe, `CANCELLED`; un mismo proyecto puede tener workflows distintos por tipo. `BUG` exige defecto confirmado; `INC` nuevo exige tipo neutral; `TASK` exige un tipo compatible con relación padre/hijo. Si falta un tipo, relación o transición necesaria, bloquear sólo esa operación y pedir configuración; no sustituir otro valor por conveniencia. **Completo:** configuración y workflows provienen del proyecto remoto real.
5. Para crear una `TASK`, confirmar que el tipo y campo de estimación configurados están disponibles. Si no se provee estimación, usar `1`; no crearla si ese campo no es editable o no acepta el valor. Vincularla como hija del RM/BUG/TEC correspondiente y verificar la relación por lectura. **Completo:** toda TASK creada tiene estimación explícita y padre verificado.
6. Actividad, iteración y asignado son configurables. Si el valor solicitado no coincide con los valores ya validados, consultar Azure DevOps antes de crear o actualizar: actividad en los campos del work item type, iteraciones en el equipo y usuario en las identidades accesibles. No inventar valores ni sustituirlos silenciosamente. **Completo:** cada valor aplicado existe y es compatible con el proyecto.

## Trazabilidad REQUIRED

1. Toda unidad RM/BUG/TEC/INC con seguimiento `REQUIRED` se vincula a un work item propio o recibido. Un item recibido se registra como `SRC-AZDO-<ID>` y se entrega a la ruta FARO que corresponda por evidencia, no por el tipo remoto: un síntoma o causa desconocida va a `faro-incidentes`; un tipo remoto Bug no confirma un defecto. Registrar en catálogo/expediente proveedor, ID, URL, tipo observado y fecha de lectura, sin copiar estado, prioridad, asignación, área o iteración como autoridad local.
2. Para altas nuevas, usar el tipo mapeado: RM al formalizarse; BUG y TEC sólo tras clasificación y autorización; INC con tipo neutral confirmado; TASK sólo si corresponde a una tarea material del plan y fue autorizada. Una TASK se enlaza como hija de su RM/BUG/TEC; `tasks.md` conserva definición/evidencia, no un segundo estado operativo.
3. Un BUG derivado de INC requiere autorización explícita y un work item nuevo o uno de corrección ya recibido. Nunca convertir, reclasificar ni cerrar silenciosamente el item del INC. Mantener vínculos bidireccionales locales y remotos entre origen y derivado; cerrar la corrección no cierra el incidente, y cerrar el incidente no completa la corrección.
4. Azure DevOps recibe el identificador FARO y vínculos disponibles al expediente estable, plan, rama, PR, QA, validación o entrega. No copiar adjuntos ni datos sensibles sin autorización explícita. Una migración de rutas no autoriza modificar vínculos remotos; esa escritura requiere permiso y readback propios.
5. El estado operativo remoto es canónico. Antes de responder por estado, decidir una transición, publicar un hito o ejecutar una fase dependiente del seguimiento, releer item, tipo, estado y relaciones pertinentes. Después de crear, actualizar, comentar o vincular, releer el recurso afectado y verificar exactamente el efecto solicitado; una respuesta HTTP exitosa o snapshot local no bastan.
6. `PENDING` y `DOING` reflejan cola y trabajo real conforme al workflow del tipo. Push, PR, merge, release, tag o despliegue son evidencia de entrega y no autorizan ni implican `DONE`. `DONE` sólo se solicita mediante una operación explícita de cierre de la unidad, tras verificar gates FARO e incorporación o decisión sobre conocimiento durable. `CANCELLED` requiere cancelación humana explícita. Aprobación, readiness del plan, QA y validación permanecen en artefactos FARO y no se deducen del estado Azure DevOps.
7. Si una sincronización o readback obligatorio falla, conservar evidencia local, registrar `waitingOn` con el error real y no avanzar en la operación dependiente ni declarar estado, relación o cierre remoto.

En `faro-cierre`, este adaptador solicita la transición autorizada pero no redacta un recibo manual. El comando central `work_item_contract.py freeze --apply` valida primero todos los gates locales y luego ejecuta su propio GET HTTPS autenticado. Exige `AZDO_ORGANIZATION_URL` y `AZDO_PAT` fuera del workspace; la raíz global debe coincidir exactamente con el perfil, la URL catalogada y el proyecto antes de enviar el PAT. Contrasta ID, `System.WorkItemType` y `System.State`, conserva la respuesta raw codificada y su SHA-256, y sólo entonces congela. Los antiguos strings `--remote-state`, `--readback-at` y `--readback-evidence` no son evidencia válida.

Un expediente migrado puede estar catalogado con proveedor, ID y URL vacíos porque la migración no crea trabajo remoto. Después de crear o importar **ese mismo** item mediante este adaptador y releer ID, URL, organización y proyecto, previsualizar y aplicar `python -B <skills-root>/faro/scripts/work_item_contract.py link-external --root <root> --id <ID> --external-provider AZURE_DEVOPS --external-id <ID-remoto> --external-url <URL> --apply --json`. El helper sólo completa atómicamente un triple totalmente vacío; una referencia parcial, existente o distinta bloquea y se reconcilia, nunca se sobrescribe ni se compensa creando otro work item.

## Límites permanentes

- `REQUIRED` autoriza crear o vincular únicamente el item RM/BUG/TEC/INC solicitado y las TASK materialmente definidas, con tipos y relaciones confirmados; actualizar vínculos configurados; añadir hitos relevantes; y aplicar transiciones permitidas por esta regla. No crear un BUG derivado, TASK ni relación sin su autorización.
- Asignar o cambiar el asignado, área, iteración, actividad, estimación, prioridad, adjuntos, borrado, tiempo o sprints requiere autorización explícita independiente, incluso si existen valores por defecto configurados.
- Azure DevOps no equivale a aprobación funcional, QA, validación, entrega ni cierre FARO.
- No persistir un segundo estado operativo en catálogo, expediente o workflow. Un último readback puede registrarse sólo como evidencia fechada y no canónica.
- No exponer secretos, identificadores personales innecesarios ni datos sensibles.

## Verificación

- [ ] Proveedor, organización, proyecto, área, tipos, relaciones y workflows por clase fueron comprobados.
- [ ] PAT y demás credenciales permanecieron fuera del repositorio y de los artefactos FARO.
- [ ] Tipos, actividades, iteraciones y asignados provienen de consultas remotas verificables.
- [ ] Cada TASK creada tiene estimación explícita, padre verificado y valor omitido `1`.
- [ ] Cada RM/BUG/TEC/INC requerido tiene work item, `SRC` y vínculo bidireccional con su expediente.
- [ ] Cada hito o unidad material relevante dejó un estado o comentario remoto conciso y verificable.
- [ ] Toda escritura fue releída; ninguna entrega se confundió con `DONE`.
