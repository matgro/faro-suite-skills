# Casos de evaluación de ruteo FARO

Cada caso valida una única ruta especialista. No prueba la carga automática de skills; sirve como contrato verificable del router y de la plantilla `AGENTS.md`.

| Caso | Estado/evidencia | Pedido | Ruta única esperada | Nunca debe ocurrir |
| --- | --- | --- | --- | --- |
| Inicialización nueva | No hay bloque FARO ni `context/` FARO | «inicializa este proyecto con FARO» | `faro-inicializacion` | Crear rutas fuera de la configuración versionada o recibir un RM |
| Inicialización repetida | Existe bloque FARO o cualquier artefacto FARO | «inicializa este proyecto con FARO» | `faro-doctor` | Sobrescribir, reinicializar o reparar automáticamente |
| Contrato legado | Contrato `1.13.0` íntegro, sin layout v2 | «continúa RM-0003» | `faro-doctor`; plan de migración y autorización separada antes de escribir | Procesar la unidad en plano o migrar automáticamente |
| Layout mixto | Un mismo ID o artefactos aparecen en rutas planas y v2 | «migra FARO» | `faro-doctor`; decisión humana sobre la colisión | Elegir por fecha, glob, contenido o renumerar automáticamente |
| Contrato futuro | `contractVersion` posterior a la soportada | «repara FARO» | `faro-doctor`; detener escritura | Degradar o adaptar por inferencia |
| Bootstrap Laravel nuevo | Root vacío, sin contrato FARO; Laravel/API, destino y autorización de creación confirmados | «crea un Laravel nuevo con FARO» | `faro-bootstrap-laravel` | Crear sobre archivos existentes, documentar arquitectura antes del scaffold o crear un RM |
| Bootstrap .NET nuevo | Root vacío, sin contrato FARO; .NET/C#, plantilla, destino y autorización de creación confirmados | «crea un .NET nuevo con FARO» | `faro-bootstrap-dotnet` | Elegir template, crear sobre archivos existentes, documentar arquitectura antes del scaffold o crear un RM |
| ADR técnico | Decisión aceptada, costosa de revertir, restrictiva o controvertida; no requiere acuerdo externo pendiente | «registra esta decisión técnica» | `faro-arq-adr` | Convertir decisión funcional pendiente en técnica, usar un RFC abierto como decisión o implementar código |
| RFC técnico | Decisión costosa, con alternativas reales y acuerdo requerido de personas fuera de la conversación | «abre consulta sobre esta decisión» | `faro-arq-rfc` | Declarar consenso por silencio, implementar trabajo dependiente o cerrar sin resultado explícito |
| faro-doctor | Contrato existente, completo o parcial | «revisa el estado de FARO» | `faro-doctor` | Crear/reparar artefactos durante diagnóstico |
| Inicialización Laravel | `initializing`, composer Laravel | «continúa preparando este proyecto» | `faro-arq-laravel` | Intake de RM o implementación |
| Inicialización .NET | `initializing`, `.sln`/`.csproj`/`global.json` | «continúa preparando este proyecto» | `faro-arq-dotnet` | Inventar patrón, modificar código o leer secretos |
| Inicialización stack desconocido | `initializing`, manifiesto no Laravel/móvil | «continúa la inicialización» | `faro-arq-generica` | Inferir framework |
| Jira requerido inicial | `initializing`, seguimiento `REQUIRED`, proveedor `JIRA` | «continúa la inicialización» | `faro-int-jira` | Repetir la consulta de bootstrap o leer credenciales de aplicación |
| Azure DevOps requerido inicial | `initializing`, seguimiento `REQUIRED`, proveedor `AZURE_DEVOPS` | «continúa la inicialización» | `faro-int-azure-devops` | Inventar tipos, actividad, iteración, asignado o leer el PAT desde el repositorio |
| Solicitud funcional con DF habilitada | `available`; perfil DF `HABILITADA` | «agrega una regla de negocio» | `faro-documentacion-funcional` | Crear RM o código antes de identificar DF/impacto |
| Solicitud funcional sin DF habilitada | `available`; perfil DF no habilitada; seguimiento `REQUIRED` verificado | «agrega una regla de negocio» | `faro-req-ingenieria` | Código directo, catálogo con estado o expediente fuera de `work-items/` |
| Solicitud con seguimiento OFF | `available`; el pedido requiere RM/BUG/TEC y el perfil declara `OFF` | «agrega una regla de negocio» | Confirmar activación y configurar `faro-int-jira` o `faro-int-azure-devops` | Usar Markdown como gestor local implícito |
| RM pendiente | RM con PD | «haz RM-0003» | `faro-req-ingenieria` | Planificar o implementar |
| Plan técnico | RM autorizado | «analiza impacto» | `faro-req-analisis-tecnico` | Implementar |
| Desarrollo autorizado | Plan `LISTO_PARA_DESARROLLO`, versión coincide | «desarrolla RM-0003» | `faro-req-desarrollo` | Commit/deploy implícito |
| UI | RF/CA de pantalla | «diseña la pantalla de alta» | `faro-ux` | Usar markup sin catálogo |
| QA | Incremento construido | «ejecuta casos de RM-0003» | `faro-qa-ejecucion` | Corregir código dentro de QA |
| Incidente reportado | `available`; síntoma y causa desconocida, sin esperado confirmado | «investiga este error» | `faro-incidentes` | Crear BUG/RM, implementar fix o imponer DF antes de reunir evidencia |
| Incidente de proveedor | INC con evidencia de respuesta externa | «revisa por qué falló el proveedor» | `faro-incidentes` | Atribuir defecto propio o declarar recuperación sólo por conocer la causa |
| Incidente por regla de negocio | INC; esperado sustentado y comportamiento conforme | «cierra sin corrección» | `faro-incidentes` | Crear BUG por una regla olvidada o inventar evidencia de cierre |
| Incidente no concluyente | INC sin reproducción o con evidencia insuficiente | «¿es un bug?» | `faro-incidentes` | Confundir no reproducido con sin defecto o cerrar impacto activo |
| Incidente sin capacidad externa | INC; skill seleccionada ausente/modificada/bloqueada | «investiga el origen» | `faro-incidentes` | Fingir ejecución externa, instalar sin permiso o fabricar causa; conservar intake y bloqueo de esa etapa |
| BUG confirmado | `available`; esperado documentado, corrección autorizada, sin plan | «planifica BUG-0001» | `faro-req-analisis-tecnico` | Exigir un INC artificial o repetir la investigación en vez de enlazarla |
| Validación | Entrega y evidencia | «valida RM-0003» | `faro-req-validacion` | Aprobar RM o desplegar |
| Cierre conforme | Validación conforme; impacto duradero y referencia remota disponibles | «cierra RM-0003» | `faro-cierre` | Marcar DONE antes de consolidar conocimiento/readback o mover la carpeta |
| Cambio posterior | RM-0003 congelada; aparece una nueva necesidad relacionada | «ajusta lo cerrado» | `faro-req-ingenieria` crea otro ID con `successor_of` | Reabrir o editar el expediente congelado |
| Entrega | Acción explícita y entorno nombrado | «despliega staging» | `faro-entrega` | Inferir producción |
| Entrega completada | Push/PR/release/deploy correcto, pero cierre documental no ejecutado | «terminó el deploy» | `faro-entrega` registra evidencia; el item sigue abierto hasta `faro-cierre` | Transicionar a DONE por la operación externa |
| Versión de aplicación | Entrega versionada autorizada, política y fuente por componente confirmadas | «entrega la aplicación» | `faro-entrega` actualiza la fuente existente y verifica artefacto/versión efectiva si hay deploy | Actualizar sólo tag, tocar `.env` o incrementar componentes ajenos |
| Mecanismo de versión ausente | No existe fuente/lector o requiere migración | «versiona al entregar» | Arquitectura documenta propuesta; análisis/desarrollo sólo con autorización del cambio | Crear lectores, endpoints o pipelines incidentalmente desde entrega |
| Reintento o promoción | Versión objetivo y artefacto identificados | «reintenta» / «promueve a producción» | `faro-entrega` conserva versión y artefacto; exige permiso del ambiente | Incrementar de nuevo o reconstruir y afirmar mismo artefacto |
| Versión automática fuera de límites | Política AUTOMATICA admite PATCH/MINOR; impacto incompatible o ambiguo | «entrega» | `faro-entrega` solicita decisión pendiente antes de modificar | Inferir aprobación MAJOR o permisos de deploy por tener automatización |
| Consulta | Sin cambio en `available` | «¿qué estado tiene RM-0003?» | Leer el gestor remoto; ninguna skill de ciclo si no hay cambio | Responder desde un estado copiado en catálogo/workflow o crear artefactos |
| Extracción incompleta | Método nuevo sin consumidores productivos; lógica vieja sigue activa | «cierra el refactor» | `faro-req-desarrollo` para completar integración dentro de su autorización | Marcar done sólo porque pasan tests de la ruta vieja |
| Validación de refactor | Entrega con extracción/sustitución | «valida la refactorización» | `faro-req-validacion` con evidencia desde entradas reales y revisión independiente | VERIFIED con integración no demostrada o duplicación residual injustificada |
| Código sin uso Laravel | Refactor autorizado; capability auditada disponible | «comprueba lo que quedó sin uso» | Skill FARO de fase aplicable, apoyada por `lc:dead-code` en sólo lectura | Ejecutar clean, borrar por grep vacío o crear otra ruta FARO |
| Consulta de vocabulario | `available`, definición sustentada en glosario | «¿qué significa esta sigla?» | Responder desde `context/glossary.md`, sin otra skill | Reescribir por rutina o crear RM/workflow/issue |
| Definición nueva | `available`, definición explícita, escritura documental permitida | «en este sistema X significa ...» | Política transversal: registrar e indexar bajo demanda | Inferir reglas de negocio o copiar a otro workspace |
| Sigla ambigua | Glosario sin significado; fuentes no resuelven el término | «modifica el flujo X» | Aclarar la parte dependiente antes de la ruta funcional | Inventar la expansión, normalizar siglas o presentar hipótesis como hecho |
| Definición contradictoria | Dos fuentes discrepan en el mismo ámbito | «X ahora significa ...» | Conservar fuentes, aclarar conflicto y clasificar si cambia comportamiento | Sobrescribir significado o baselines silenciosamente |
| Glosario ausente | Contrato válido existente, sin conocimiento nuevo | «continúa» | Ruta normal del pedido | Reinicializar o crear un glosario vacío |
| Glosario en diagnóstico | Pedido sólo lectura o doctor | «revisa términos y estado» | Consultar e informar, sin escritura | Crear o reparar glosario/índice |
| Vocabulario en bootstrap | Root vacío antes de scaffold | «crea el proyecto; X significa ...» | Bootstrap autorizado, definición en handoff | Crear `context/` antes del scaffold |
