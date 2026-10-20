---
project: PROJECT_NAME
profile_version: 1
work_tracking:
  mode: PENDIENTE
  provider: null
  authorization_source: null
  credential_status: NO_VERIFICADO
  jira:
    base_url: null
    project_key: null
    workflow_mapping:
      PENDING: null
      DOING: null
      DONE: null
      CANCELLED: null
  azure_devops:
    organization_url: null
    project: null
    area_path: null
    team: null
    iteration_path: null
    work_item_type: Task
    activity_field: Microsoft.VSTS.Common.Activity
    default_activity: null
    estimate_field: Microsoft.VSTS.Scheduling.RemainingWork
    default_task_estimate: 1
    default_assigned_to: null
    workflow_mapping:
      PENDING: null
      DOING: null
      DONE: null
      CANCELLED: null
functional_documentation: PENDIENTE
updated_at: UPDATED_AT
---

# Perfil de requerimientos — PROJECT_NAME

## Decisiones de configuración

| Decisión | Valor | Evidencia / autorización |
| --- | --- | --- |
| Seguimiento de trabajo | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |
| Documentación funcional | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |

## Regla de uso

- Con seguimiento `REQUIRED`, toda solicitud se vincula a un item remoto y la configuración del proveedor debe incluir sus metadatos confirmados, sin secretos.
- Para Jira: URL y clave de proyecto. Para Azure DevOps / Visual Studio: URL de organización, proyecto, área, equipo y mapeo de estados; actividad, iteración, estimación y asignado se validan contra el servicio remoto.
- El PAT de Azure DevOps se conserva fuera del perfil como `AZDO_PAT`. En la configuración global de un agente, fuera del workspace y de repositorios indexados, pueden declararse `AZDO_ORGANIZATION_URL`, `AZDO_DEFAULT_PROJECT`, `AZDO_DEFAULT_AREA_PATH` y `AZDO_DEFAULT_TEAM`; los valores sólo se registran aquí tras confirmación humana y verificación remota, y después deben coincidir con este archivo.
- Con documentación funcional `HABILITADA`, las solicitudes funcionales pasan primero por `faro-documentacion-funcional`.
- Con documentación funcional `DESHABILITADA`, las solicitudes funcionales siguen la ruta estándar de FARO.
- Este archivo no contiene tokens, contraseñas, cookies ni contenido de archivos `.env`.
