---
name: azure-devops-rest-v7
description: Use when Azure DevOps REST work tracking needs real calls.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [azure-devops, visualstudio, rest, work-items, boards]
    related_skills: [faro-int-azure-devops]
---

# Azure DevOps / Visual Studio REST API v7.1

## Rol

Ejecuta llamadas reales y autenticadas contra Azure DevOps Services para descubrir configuración de un proyecto y gestionar work items autorizados. Es la capability técnica de `faro-int-azure-devops`; no interpreta ni modifica contratos FARO.

No describir solamente endpoints cuando se pide una acción Azure DevOps: comprobar configuración, construir la llamada, ejecutarla con `curl`, interpretar JSON y reportar el resultado. Si no existen credenciales, no realizar llamadas remotas.

## Configuración segura

Variables requeridas:

- `AZDO_ORGANIZATION_URL`: URL de organización, por ejemplo `https://farmacity.visualstudio.com` o `https://dev.azure.com/farmacity`; sin slash final y sin proyecto.
- `AZDO_PAT`: Personal Access Token con el mínimo scope necesario. Nunca imprimirlo, persistirlo ni leerlo desde `.env`.

Variables opcionales, aceptadas sólo si coinciden con el perfil FARO:

- `AZDO_DEFAULT_PROJECT`
- `AZDO_DEFAULT_AREA_PATH`
- `AZDO_DEFAULT_TEAM`
- `AZDO_DEFAULT_ITERATION_PATH`
- `AZDO_DEFAULT_ASSIGNED_TO`
- `AZDO_HTTP_TIMEOUT_SECONDS` (predeterminado `30`)

Autenticación PAT para `curl`:

```bash
: "${AZDO_ORGANIZATION_URL:?Missing AZDO_ORGANIZATION_URL}"
: "${AZDO_PAT:?Missing AZDO_PAT}"
AZDO_BASE="${AZDO_ORGANIZATION_URL%/}"
AZDO_TIMEOUT="${AZDO_HTTP_TIMEOUT_SECONDS:-30}"
AZDO_AUTH="Authorization: Basic $(printf ':%s' "$AZDO_PAT" | base64 | tr -d '\n')"
```

Usar siempre `Accept: application/json`; en escrituras JSON Patch usar `Content-Type: application/json-patch+json`.

## Descubrimiento obligatorio en inicialización

Con `PROJECT` y `TEAM` confirmados, ejecutar estas lecturas antes de registrar valores definitivos o crear items:

| Dato | Método y ruta | Resultado que se conserva |
| --- | --- | --- |
| Conectividad/identidad | `GET /_apis/connectionData?api-version=7.1` | acceso confirmado, sin copiar identidad personal innecesaria |
| Tipos | `GET /{project}/_apis/wit/workitemtypes?api-version=7.1` | nombres y referencias de tipos válidos |
| Campos del tipo | `GET /{project}/_apis/wit/workitemtypes/{type}/fields?api-version=7.1` | actividad, estimación, estado y editabilidad |
| Áreas | `GET /{project}/_apis/wit/classificationnodes/areas?depth=10&api-version=7.1` | rutas de área válidas |
| Iteraciones del proyecto | `GET /{project}/_apis/wit/classificationnodes/iterations?depth=10&api-version=7.1` | rutas de iteración válidas |
| Iteraciones del equipo | `GET /{project}/{team}/_apis/work/teamsettings/iterations?api-version=7.1` | iteraciones que el equipo puede usar |
| Estados | `GET /{project}/_apis/wit/workitemtypes/{type}/states?api-version=7.1` | mapeo remoto PENDING/DOING/DONE/CANCELLED |

Codificar `project`, `team`, tipo y segmentos de ruta. Para una URL de proyecto como `https://farmacity.visualstudio.com/FarmaAgil/`, usar `https://farmacity.visualstudio.com` como organización y `FarmaAgil` como proyecto sólo después de confirmación humana o desde el perfil.

## Actividad, iteración, estimación y asignación

1. Para el tipo de work item configurado, consultar sus campos antes de usar `Microsoft.VSTS.Common.Activity`, el campo de estimación configurado o `System.AssignedTo`. Las actividades permitidas se obtienen del metadato/`allowedValues` del campo de actividad; no asumir la lista de otro proceso.
2. Si una actividad o iteración solicitada no está en los valores validados del perfil, volver a consultar las rutas y campos anteriores. Si sigue ausente, detenerse y reportar el valor no válido.
3. Para un tipo `Task`, el perfil debe declarar `estimate_field`. Si la petición omite la estimación, agregar el valor numérico `1` mediante JSON Patch. No reemplazar una estimación explícita ni usar `1` en otros tipos sin instrucción.
4. `default_assigned_to` es una configuración opcional. Antes de usar un valor no validado, consultar `GET /_apis/graph/users?api-version=7.1-preview.1` cuando el PAT tenga scope, o pedir el descriptor/identidad exacta al usuario. Nunca adivinar una persona por nombre parcial.
5. Cambiar asignado, área, iteración, actividad o estimación es una mutación que requiere autorización humana específica; la configuración sólo prepara y valida los valores.

## Operaciones de work item

### Crear

`PATCH /{project}/_apis/wit/workitems/${TYPE}?api-version=7.1`

Crear el archivo temporal de JSON Patch y luego ejecutar `curl`. Ejemplo de payload para un `Task` con estimación predeterminada:

```json
[
  {"op":"add","path":"/fields/System.Title","value":"Título aprobado"},
  {"op":"add","path":"/fields/System.AreaPath","value":"Área configurada"},
  {"op":"add","path":"/fields/Microsoft.VSTS.Scheduling.RemainingWork","value":1}
]
```

```bash
curl --silent --show-error --fail --max-time "$AZDO_TIMEOUT" \
  --request PATCH \
  --url "${AZDO_BASE}/${PROJECT}/_apis/wit/workitems/${TYPE}?api-version=7.1" \
  --header 'Accept: application/json' \
  --header 'Content-Type: application/json-patch+json' \
  --header "$AZDO_AUTH" \
  --data-binary @/tmp/azdo-work-item.json
```

### Leer, actualizar, comentar y estados

- Leer: `GET /{project}/_apis/wit/workitems/{id}?$expand=Relations&api-version=7.1`.
- Actualizar campos/estado: mismo `PATCH` con operaciones JSON Patch; primero leer el item y comprobar el estado/campo real.
- Comentarios: `POST /{project}/_apis/wit/workItems/{id}/comments?api-version=7.1-preview.4` con `{"text":"..."}`.
- Estados: obtenerlos por tipo antes de aplicar `System.State`; nunca traducir nombres de Jira ni asumir `Done`.

Para cada mutación, usar un archivo temporal para el payload, ejecutar una lectura posterior y reportar ID, URL y campos solicitados. `DELETE`, cambios de prioridad, sprint, adjuntos, tiempos o reasignación sólo se ejecutan con solicitud explícita.

## Fallos y verificación

- `401`: PAT ausente, vencido o inválido.
- `403`: PAT autenticado sin scope o sin permiso en organización/proyecto.
- `404`: URL, proyecto, equipo, tipo, ID o API version incorrectos; confirmar primero la configuración remota.
- `400`: JSON Patch, campo, actividad, iteración o estado no permitido.
- `429`: respetar `Retry-After` y reintentar con espera limitada.

Antes de concluir, confirmar que la respuesta vino del proyecto configurado, que no se expusieron secretos y que las mutaciones se releen desde la API.
