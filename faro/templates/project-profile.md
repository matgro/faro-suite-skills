---
project: PROJECT_NAME
profile_version: 2
work_tracking:
  mode: PENDIENTE
  provider: null
  operational_state_authority: EXTERNAL_WORK_TRACKER
  work_items_require_external_reference: true
  authorization_source: null
  credential_status: NO_VERIFICADO
  jira:
    base_url: null
    project_key: null
    type_mapping:
      RM: null
      BUG: null
      TEC: null
      INC: null
      TASK: null
    workflow_mapping_by_kind:
      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      BUG: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      TEC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      INC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      TASK: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
  azure_devops:
    organization_url: null
    project: null
    area_path: null
    team: null
    iteration_path: null
    type_mapping:
      RM: null
      BUG: null
      TEC: null
      INC: null
      TASK: null
    workflow_mapping_by_kind:
      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      BUG: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      TEC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      INC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
      TASK: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}
    task_defaults:
      activity_field: null
      activity: null
      estimate_field: null
      estimate: null
      assigned_to: null
functional_documentation: PENDIENTE
durable_documentation:
  product: context/requirements/functional
  architecture: context/decisions/adr
  operations: null
  reference: context/glossary.md
updated_at: UPDATED_AT
---

# Perfil de requerimientos — PROJECT_NAME

## Decisiones de configuración

| Decisión | Valor | Evidencia / autorización |
| --- | --- | --- |
| Seguimiento de trabajo | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |
| Documentación funcional | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |
| Autoridad de estado operativo | `EXTERNAL_WORK_TRACKER` | Estado, prioridad y asignación no se duplican en catálogos ni expedientes FARO. |

## Autoridades de documentación duradera

| Clase | Ubicación / autoridad | Regla de cierre |
| --- | --- | --- |
| Producto | `context/requirements/functional/` o fuente confirmada del proyecto | Incorporar sólo conocimiento validado; el delta permanece en el expediente. |
| Arquitectura | `context/decisions/adr/` o fuente confirmada del proyecto | Registrar únicamente decisiones duraderas que ameriten ADR. |
| Operaciones | PENDIENTE | Actualizar runbook/procedimiento cuando el cambio operativo lo exija. |
| Referencia | `context/glossary.md` u otra fuente confirmada | Actualizar contratos, APIs o vocabulario sólo con evidencia. |

## Versionado de aplicaciones

Opcional y por componente. Completar con evidencia y autorización antes de la primera entrega versionada; la ausencia de esta sección en un workspace existente no invalida su contrato. No inventar valores ni conservar aquí una segunda copia de la versión actual.

### Componente — PENDIENTE

| Campo | Decisión / evidencia |
| --- | --- |
| Componente, repositorio/root autorizado, stack y conjunto de versionado | PENDIENTE |
| Fuente única: archivo/clave exacta o generador existente | PENDIENTE |
| Lectores efectivos de la versión | PENDIENTE |
| Derivados y mapeo de versión de producto, build y revisión | PENDIENTE |
| Esquema y formato; tag y remoto, o sin tag autorizado | PENDIENTE |
| Modo de decisión | CONFIRMAR_POR_ENTREGA; AUTOMATICA sólo con autorización y límites explícitos |
| Incrementos, componentes y prereleases permitidos en modo automático | PENDIENTE |
| Escritor de la versión: agente o CI; reserva/serialización de entregas | PENDIENTE |
| Procedimiento observado de actualización y lectura segura | PENDIENTE |
| Comandos observados de validación, build y caché | PENDIENTE |
| Artefacto/digest y mecanismo de comprobación de versión efectiva | PENDIENTE |
| Permisos: edición, commit, tag local/remoto, deploy y ambientes | PENDIENTE |
| Autorización: fuente, responsable, alcance y restricciones | PENDIENTE |

El agente consulta la política central `faro/references/application-versioning.md`. Registrar valores no sensibles; no copiar contenido de `.env`. Cambiar el mecanismo de versión requiere desarrollo autorizado, no una edición incidental al entregar.

## Regla de uso

- Con seguimiento `REQUIRED`, toda solicitud se vincula a un item remoto y la configuración del proveedor debe incluir sus metadatos confirmados, sin secretos.
- Los expedientes y catálogos no son una segunda fuente de estado operativo: conservan identidad, autorización, definición y evidencia; Jira/Azure DevOps conserva estado, prioridad y asignación.
- Para Jira: URL y clave de proyecto. Para Azure DevOps / Visual Studio: URL de organización, proyecto, área, equipo y mapeo de estados; actividad, iteración, estimación y asignado se validan contra el servicio remoto.
- Las credenciales y la raíz autorizada de Jira se conservan fuera del workspace como `JIRA_BASE_URL`, `JIRA_EMAIL` y `JIRA_API_TOKEN`. `freeze --apply` exige que `JIRA_BASE_URL` coincida exactamente con `jira.base_url` antes de enviar el token; no confía sólo en una URL declarada por el repositorio.
- El PAT y la raíz autorizada de Azure DevOps se conservan fuera del perfil como `AZDO_PAT` y `AZDO_ORGANIZATION_URL`. En la configuración global de un agente también pueden declararse `AZDO_DEFAULT_PROJECT`, `AZDO_DEFAULT_AREA_PATH` y `AZDO_DEFAULT_TEAM`; los valores sólo se registran aquí tras confirmación humana y verificación remota, y después deben coincidir con este archivo. `freeze --apply` compara la raíz global, el perfil y la URL catalogada antes de enviar el PAT.
- Con documentación funcional `HABILITADA`, las solicitudes funcionales pasan primero por `faro-documentacion-funcional`.
- Con documentación funcional `DESHABILITADA`, las solicitudes funcionales siguen la ruta estándar de FARO.
- Este archivo no contiene tokens, contraseñas, cookies ni contenido de archivos `.env`.
