---
project: PROJECT_NAME
profile_version: 1
jira:
  mode: PENDIENTE
  provider: null
  base_url: null
  project_key: null
  authorization_source: null
  credential_status: NO_VERIFICADO
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
| Jira como sistema de trabajo | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |
| Documentación funcional | `PENDIENTE` | Pendiente de respuesta humana durante la inicialización. |

## Regla de uso

- Con Jira `REQUIRED`, toda solicitud se vincula a una issue y la configuración debe incluir URL y clave de proyecto confirmadas, sin secretos.
- Con documentación funcional `HABILITADA`, las solicitudes funcionales pasan primero por `faro-documentacion-funcional`.
- Con documentación funcional `DESHABILITADA`, las solicitudes funcionales siguen la ruta estándar de FARO.
- Este archivo no contiene tokens, contraseñas, cookies ni contenido de archivos `.env`.
