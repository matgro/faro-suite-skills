# Casos de evaluación de ruteo FARO

Cada caso valida una única ruta especialista. No prueba la carga automática de skills; sirve como contrato verificable del router y de la plantilla `AGENTS.md`.

| Caso | Estado/evidencia | Pedido | Ruta única esperada | Nunca debe ocurrir |
| --- | --- | --- | --- | --- |
| Inicialización nueva | No hay bloque FARO ni `context/` FARO | «inicializa este proyecto con FARO» | `faro-inicializacion` | Crear rutas fuera de la configuración versionada o recibir un RM |
| Inicialización repetida | Existe bloque FARO o cualquier artefacto FARO | «inicializa este proyecto con FARO» | `faro-doctor` | Sobrescribir, reinicializar o reparar automáticamente |
| Bootstrap Laravel nuevo | Root vacío, sin contrato FARO; Laravel/API, destino y autorización de creación confirmados | «crea un Laravel nuevo con FARO» | `faro-bootstrap-laravel` | Crear sobre archivos existentes, documentar arquitectura antes del scaffold o crear un RM |
| faro-doctor | Contrato existente, completo o parcial | «revisa el estado de FARO» | `faro-doctor` | Crear/reparar artefactos durante diagnóstico |
| Inicialización Laravel | `initializing`, composer Laravel | «continúa preparando este proyecto» | `faro-arq-laravel` | Intake de RM o implementación |
| Inicialización stack desconocido | `initializing`, manifiesto no Laravel/móvil | «continúa la inicialización» | `faro-arq-generica` | Inferir framework |
| Jira requerido inicial | `initializing`, seguimiento `REQUIRED`, proveedor `JIRA` | «continúa la inicialización» | `faro-int-jira` | Repetir la consulta de bootstrap o leer credenciales de aplicación |
| Azure DevOps requerido inicial | `initializing`, seguimiento `REQUIRED`, proveedor `AZURE_DEVOPS` | «continúa la inicialización» | `faro-int-azure-devops` | Inventar tipos, actividad, iteración, asignado o leer el PAT desde el repositorio |
| Solicitud funcional con DF habilitada | `available`; perfil DF `HABILITADA` | «agrega una regla de negocio» | `faro-documentacion-funcional` | Crear RM o código antes de identificar DF/impacto |
| Solicitud funcional sin DF habilitada | `available`; perfil DF no habilitada | «agrega una regla de negocio» | `faro-req-ingenieria` | Código directo |
| RM pendiente | RM con PD | «haz RM-003» | `faro-req-ingenieria` | Planificar o implementar |
| Plan técnico | RM autorizado | «analiza impacto» | `faro-req-analisis-tecnico` | Implementar |
| Desarrollo autorizado | Plan `LISTO_PARA_DESARROLLO`, versión coincide | «desarrolla RM-003» | `faro-req-desarrollo` | Commit/deploy implícito |
| UI | RF/CA de pantalla | «diseña la pantalla de alta» | `faro-ux` | Usar markup sin catálogo |
| QA | Incremento construido | «ejecuta casos de RM-003» | `faro-qa-ejecucion` | Corregir código dentro de QA |
| Validación | Entrega y evidencia | «valida RM-003» | `faro-req-validacion` | Aprobar RM o desplegar |
| Entrega | Acción explícita y entorno nombrado | «despliega staging» | `faro-entrega` | Inferir producción |
| Consulta | Sin cambio en `available` | «¿qué estado tiene RM-003?» | Ninguna skill especialista | Crear artefactos |
