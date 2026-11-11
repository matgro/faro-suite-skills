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
- Para Jira: URL y clave de proyecto. Para Azure DevOps / Visual Studio: URL de organización, proyecto, área, equipo y mapeo de estados; actividad, iteración, estimación y asignado se validan contra el servicio remoto.
- El PAT de Azure DevOps se conserva fuera del perfil como `AZDO_PAT`. En la configuración global de un agente, fuera del workspace y de repositorios indexados, pueden declararse `AZDO_ORGANIZATION_URL`, `AZDO_DEFAULT_PROJECT`, `AZDO_DEFAULT_AREA_PATH` y `AZDO_DEFAULT_TEAM`; los valores sólo se registran aquí tras confirmación humana y verificación remota, y después deben coincidir con este archivo.
- Con documentación funcional `HABILITADA`, las solicitudes funcionales pasan primero por `faro-documentacion-funcional`.
- Con documentación funcional `DESHABILITADA`, las solicitudes funcionales siguen la ruta estándar de FARO.
- Este archivo no contiene tokens, contraseñas, cookies ni contenido de archivos `.env`.
