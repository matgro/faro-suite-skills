---
name: faro-int-jira
description: Use when FARO configures and syncs required Jira work.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, jira, integration, intake, synchronization]
    related_skills: [faro, faro-inicializacion, faro-doctor, faro-req-ingenieria, faro-incidentes, faro-entrega, faro-cierre, jira-rest-v3]
---

# FARO — Integración Jira

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase. El vocabulario por sí solo no crea ni actualiza issues remotas.

## Rol

`faro-int-jira` es el adaptador de gobernanza entre FARO y la capability externa `jira-rest-v3`. Configura Jira sólo por petición humana expresa, importa una issue como fuente `SRC` y, cuando `work_tracking.mode` es `REQUIRED` y su proveedor es `JIRA`, sincroniza el seguimiento operativo de RM, BUG, TEC, INC y TASK.

No sustituye el expediente local, su aprobación, análisis, QA, validación ni cierre. No implementa cambios de código. Jira es la fuente canónica del estado operativo, prioridad, asignación y pertenencia a backlog/sprint; los expedientes FARO conservan definición, decisiones, evidencia y resultados verificables.

## Cuándo usar

- Durante inicialización, después de que `faro-inicializacion` registre seguimiento `REQUIRED` y proveedor `JIRA` en el perfil.
- En un proyecto `available`, sólo si el usuario pide explícitamente agregar o configurar Jira.
- Cuando el usuario entrega una URL o clave Jira y el proyecto tiene Jira habilitado.

## Política y autorización

1. Leer el contrato FARO, `context/stats.json`, el perfil de requerimientos y el estado de integración. Confirmar que el proyecto está `available`, salvo configuración dentro de una inicialización. **Completo:** proyecto y política conocidos.
2. Durante una inicialización, verificar que `faro-inicializacion` ya registró la decisión `REQUIRED`, proveedor `JIRA`, URL y clave confirmadas —o su pendiente explícito— en el perfil; no repetir la consulta de bootstrap. Para un proyecto `available`, exigir petición explícita de agregar/configurar la integración y autorización humana antes de registrar o cambiar su política. **Completo:** decisión, URL y clave confirmadas, y fuente de autorización registradas sin secretos.
3. Registrar modo, proveedor, URL confirmada, clave del proyecto Jira, estado de credenciales y capacidades permitidas bajo `work_tracking` en `context/requirements/project-profile.md`. Con política `REQUIRED`, la URL y clave de proyecto son obligatorias antes de crear o importar trabajo y se usan como fuentes de verdad para cada llamada; los valores no sensibles del entorno del agente sólo se aceptan si coinciden. Nunca registrar tokens, contraseñas, cookies, cabeceras Authorization ni contenido de `.env`. **Completo:** la configuración sólo contiene metadatos no sensibles y la URL/clave pertenecen inequívocamente al proyecto.
4. Descubrir y registrar mapeos por clase local, no uno global supuesto: `RM`, `BUG`, `TEC`, `INC` y `TASK` → tipo Jira confirmado; para cada tipo usado, equivalencias reales `PENDING`, `DOING`, `DONE` y, si existe, `CANCELLED`; además, relaciones verificadas para padre/hijo y relación entre origen y derivado. Un proyecto puede usar workflows distintos por tipo. `BUG` exige defecto confirmado; `INC` nuevo exige tipo neutral; `TASK` exige tipo apto para vínculo con su unidad padre. Si falta un tipo o transición necesaria, bloquear sólo esa operación y pedir la decisión/configuración; no reutilizar otro tipo por conveniencia. **Completo:** tipos, workflows y relaciones corresponden al proyecto real.
5. Con `REQUIRED`, localizar y verificar sin revelar valores las credenciales Jira disponibles para el agente, separadas de las credenciales de la aplicación, y comprobar el acceso al proyecto antes de procesar trabajo. Las variables necesarias pueden leerse desde el entorno ya inyectado o desde cualquier `.env` global perteneciente a un agente, aunque no sea Hermes; FARO puede buscarlas en directorios de configuración de agentes fuera del workspace. Nunca buscar ni leer `.env` del workspace, de repositorios indexados ni de una aplicación. Usar los valores sólo para ejecutar la llamada autenticada y no imprimirlos, exportarlos ni persistirlos. **Completo:** se comprobaron credenciales y configuración sin exposición ni reutilización de secretos de la aplicación.
6. Si no se encuentran credenciales Jira válidas en el entorno inyectado o en los `.env` globales de agentes, no consultar ni modificar Jira. Solicitar su configuración segura en el entorno de un agente, fuera del repositorio y del workspace, o aceptar URL, exportación o texto aportado por el usuario como fuente manual únicamente si la política no es `REQUIRED`. Nunca reutilizar credenciales de la aplicación. **Completo:** se buscaron sólo fuentes globales de agentes, sin exposición, persistencia ni llamada remota no autenticada.

## Trazabilidad Jira REQUIRED

1. Toda unidad RM/BUG/TEC/INC con seguimiento `REQUIRED` debe estar vinculada a una issue propia o recibida. Una issue recibida se registra como `SRC-JIRA-<KEY>` y se entrega a la ruta FARO que corresponda por evidencia, no por el tipo remoto: un síntoma o causa desconocida va a `faro-incidentes`; un tipo remoto Bug no confirma un defecto. Registrar en el catálogo/expediente local proveedor, clave, URL, tipo observado y fecha de lectura, sin copiar estado, prioridad o asignación como autoridad local.
2. Para altas nuevas, usar el tipo mapeado de la clase local. Un RM crea su issue al formalizarse; BUG y TEC sólo después de quedar clasificados y autorizados; INC usa tipo neutral confirmado; TASK sólo cuando existe una tarea material del plan y autorización para crearla. Cada TASK se vincula como hija de su RM/BUG/TEC, sin convertir `tasks.md` en un segundo gestor de estados.
3. Un BUG derivado de INC requiere autorización explícita y una issue nueva o una issue de corrección ya recibida. Nunca convertir ni reclasificar silenciosamente la issue del INC. Mantener vínculos bidireccionales locales y remotos entre origen y derivado; cerrar BUG/RM/TEC no cierra INC, y cerrar INC no completa sus correcciones.
4. El item remoto recibe el identificador FARO y los vínculos disponibles al expediente estable, plan, rama, PR, evidencia de QA, validación o entrega. No copiar adjuntos ni datos sensibles salvo petición y autorización explícitas. Si un vínculo cambia por una migración de layout, no editar Jira sin autorización de esa mutación y readback posterior.
5. El estado operativo remoto es canónico. Antes de responder por estado, decidir una transición, publicar un hito o ejecutar una fase que dependa del seguimiento, releer la issue y comprobar tipo, estado y relaciones pertinentes. Después de crear, transicionar, comentar o vincular, releer el recurso afectado y verificar exactamente el efecto pedido. Una respuesta HTTP exitosa o un snapshot local no bastan.
6. `PENDING` y `DOING` reflejan cola y trabajo real conforme al workflow verificado. Push, PR, merge, release, tag o despliegue son evidencia de entrega y no autorizan ni implican `DONE`. `DONE` sólo se solicita mediante una operación explícita de cierre de la unidad, después de verificar sus gates FARO y la incorporación o decisión sobre conocimiento durable. `CANCELLED` exige cancelación humana explícita. La aprobación, readiness del plan, resultados QA y veredicto de validación permanecen en artefactos FARO y no se deducen del estado Jira.
7. Si una sincronización o readback obligatorio falla, conservar evidencia local y registrar `waitingOn` con el error real; no avanzar en la operación dependiente ni declarar estado, vínculo o cierre remoto. No exponer secretos ni ocultar el fallo.

En `faro-cierre`, este adaptador solicita la transición autorizada pero no redacta un recibo manual. El comando central `work_item_contract.py freeze --apply` valida primero todos los gates locales y luego ejecuta su propio GET HTTPS autenticado. Exige `JIRA_BASE_URL`, `JIRA_EMAIL` y `JIRA_API_TOKEN` fuera del workspace; la raíz global debe coincidir exactamente con `jira.base_url` y con la URL catalogada antes de enviar el token. Contrasta clave, tipo, categoría `done` y estado `DONE` mapeado, conserva la respuesta raw codificada y su SHA-256, y sólo entonces congela. Los antiguos strings `--remote-state`, `--readback-at` y `--readback-evidence` no son evidencia válida.

Un expediente migrado puede estar catalogado con proveedor, ID y URL vacíos porque la migración no crea trabajo remoto. Después de crear o importar **ese mismo** item mediante este adaptador y releer clave, URL y proyecto, previsualizar y aplicar `python -B <skills-root>/faro/scripts/work_item_contract.py link-external --root <root> --id <ID> --external-provider JIRA --external-id <KEY> --external-url <URL> --apply --json`. El helper sólo completa atómicamente un triple totalmente vacío; una referencia parcial, existente o distinta bloquea y se reconcilia, nunca se sobrescribe ni se compensa creando otra issue.

## Límites permanentes

- `REQUIRED` autoriza crear o vincular únicamente la issue RM/BUG/TEC/INC solicitada y las TASK materialmente definidas, con tipos y relaciones confirmados; actualizar vínculos configurados; añadir hitos relevantes; y aplicar transiciones permitidas por esta regla. No crear un BUG derivado, una TASK ni una relación sin la autorización correspondiente.
- Asignar, editar prioridad/campos no configurados, adjuntar, borrar, registrar tiempos y gestionar sprints requieren autorización explícita independiente.
- Jira no equivale a aprobación funcional, QA, validación, entrega ni cierre FARO; cada expediente conserva esas fuentes de verdad.
- No persistir un segundo estado operativo en catálogo, expediente o workflow. Un último readback puede registrarse sólo como evidencia fechada y no canónica.
- No exponer secretos, identificadores personales innecesarios ni información clínica en fuentes o reportes.

## Verificación

- [ ] Modo, autorización, proyecto, tipos, relaciones y workflow por clase fueron comprobados.
- [ ] Credenciales globales de agentes permanecieron fuera de repositorios y artefactos FARO.
- [ ] Cada RM/BUG/TEC/INC requerido tiene issue, `SRC` y vínculo bidireccional con su expediente; cada TASK remota tiene padre verificado.
- [ ] Cada hito o unidad material relevante dejó un estado o comentario Jira conciso y verificable.
- [ ] La issue quedó vinculada como fuente, no como aprobación implícita.
- [ ] Toda escritura fue releída; ninguna entrega se confundió con `DONE`.
- [ ] Se indicó el siguiente handoff o el bloqueo real.
