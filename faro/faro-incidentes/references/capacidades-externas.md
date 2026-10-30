# Capacidades externas para incidentes

## Selección revisada

El catálogo `faro/references/incident-external-skills.json` fija repositorio, commit completo, directorio, licencia y hashes SHA-256 de entrada/referencias requeridas. No se distribuye ni modifica código upstream dentro de FARO.

| Etapa | Capacidad preferida | Uso acotado |
| --- | --- | --- |
| Investigación técnica | `systematic-debugging`, `obra/superpowers` | Fases 1–3 y `root-cause-tracing.md` si corresponde: evidencia, reproducción autorizada, comparación e hipótesis. No fase 4. |
| Revisión/post-mortem | `incident-postmortem`, `github/awesome-copilot` | Cronología, impacto y factores contribuyentes con evidencia; sólo cuando se solicita o lo amerita la política/impacto. No es requisito para cada reporte menor. |

Se compararon fuentes primarias, historial por ruta, licencias y metadata pública de los repositorios. Superpowers aporta investigación técnica concreta; el repositorio de la organización GitHub aporta una guía breve de post-mortem. Ambos son MIT y estaban activos/no archivados durante la revisión. La popularidad es señal de adopción del repositorio, no certificación de seguridad o calidad de cada skill.

También se revisó `wshobson/agents`, `plugins/incident-response/skills/postmortem-writing` en `0874a27b17a22e2b7c2e2bcd725768e0803cad06`, y su `references/details.md`: útil para retrospectivas extensas, pero añade calendario y compromisos prescriptivos. No se incorpora como tercera dependencia obligatoria. Las skills locales `software-incident-investigation` e `incident-postmortem` pueden ser variantes de otro origen: compartir nombre no acredita procedencia ni autoriza reemplazarlas.

## Contrato de invocación

Antes de cargar una capacidad, transmitir INC, entorno, fuentes, revisiones inspeccionadas, acciones autorizadas y estas restricciones FARO:

- La capacidad es auxiliar, no router ni aprobación. Devuelve evidencia, hipótesis contrastadas, conclusiones acotadas y pendientes al INC; no genera un flujo de corrección propio.
- No ejecutar código de ejemplo, scripts empaquetados, instrumentación, operaciones comerciales, rollback, cambios de configuración ni modificaciones de aplicación automáticamente. Las pruebas y reproducciones requieren un entorno/datos/efectos autorizados; preferir aislamiento y límites simulados si corresponden.
- En `systematic-debugging`, no entrar en fase 4 ni seguir instrucciones de implementar retries/monitorización tras una causa externa. Las sugerencias de modificar una variable para probar una hipótesis tampoco autorizan cambiar producción. Una heurística sobre porcentajes o intentos fallidos no prueba causa raíz ni defecto arquitectónico.
- En `incident-postmortem`, no heredar `Status: Resolved`, ruta `docs/postmortems/`, severidad, ejemplos de personas, fechas, acciones ni los cinco porqués como obligación. Usar el registro INC como fuente de verdad; un informe adicional sólo si se solicita, enlazado sin duplicar conclusiones divergentes.
- No inventar una brecha corregible para terminar la cadena causal. Admitir proveedor, regla de negocio correcta, configuración/datos/operación, causas combinadas y conclusión no concluyente. No reproducido no significa sin bug.
- No asignar responsables, fechas, métricas, tickets ni compromisos por completar una plantilla. Registrar «no disponible» o el pendiente real. No imprimir secretos ni incorporar PII; datos de ejemplo nunca son evidencia.
- Investigar no autoriza crear BUG/RM/TEC, corregir, hacer commit/push/tag ni desplegar. Volver al orquestador para clasificación y decisión humana.

## Disponibilidad, instalación y mantenimiento

1. Descubrir la skill real del runtime, su origen y contenido. Verificar la revisión del catálogo y los hashes de `requiredFiles`; cargar también las referencias seleccionadas. Un nombre coincidente, una búsqueda web o un `check` sin procedencia no acredita disponibilidad.
2. Si falta, está modificada, tiene otro origen o el escaneo la bloqueó, conservar intake/evidencia aportada y registrar `waitingOn` para la etapa que la necesita. No declarar investigación/post-mortem ejecutados ni reconstruir silenciosamente su metodología dentro de FARO. Una etapa no aplicable no bloquea las demás.
3. Proponer instalación/actualización mediante el bootstrap de la suite o el instalador oficial del runtime y exigir autorización antes de escribir. En Hermes, consultar documentación/help vigente, auditar con `hermes skills audit <name>` y no usar `--force`. Instalar el directorio completo fijado, no sólo una URL raw de `SKILL.md` que pierda `root-cause-tracing.md`. Si el instalador no puede preservar revisión, archivos y licencia, informar que no se puede completar por esa vía; no fingir un éxito.
4. Comparar con cualquier skill ya existente del mismo nombre; conservar modificaciones y pedir confirmación antes de reemplazar. No sustituir la `incident-postmortem` local por la de GitHub sólo porque se seleccionó como upstream de FARO.
5. Verificar destino, procedencia, archivos auxiliares, licencia y escaneo tras la instalación. Una advertencia del escáner se investiga, no se trata como aprobación. No ejecutar scripts upstream para instalar o revisar.
6. Actualizar sólo con autorización explícita y revisión conjunta de entrada, referencias y archivos auxiliares; registrar nuevo commit/hash en el catálogo y repetir auditoría. No cambiar a `main`/`latest` automáticamente.

## Fuentes primarias inspeccionadas

- https://github.com/obra/superpowers/tree/2ce8aa15d05bd57213e6f746f953aafb7ded7a8b/skills/systematic-debugging — SKILL.md, root-cause-tracing.md y auxiliares; licencia en la raíz del mismo commit.
- https://github.com/github/awesome-copilot/blob/5269f7ea2d6c3a9bfda5ed878b6726cf509121fd/skills/incident-postmortem/SKILL.md — guía de post-mortem y licencia en la raíz del mismo commit.
- https://github.com/wshobson/agents/tree/0874a27b17a22e2b7c2e2bcd725768e0803cad06/plugins/incident-response/skills/postmortem-writing — alternativa revisada, no seleccionada.
- Metadata y mantenimiento: endpoints públicos `/repos/obra/superpowers`, `/repos/github/awesome-copilot` y `/repos/wshobson/agents` de https://api.github.com; commits por ruta bajo las revisiones anteriores. No se usa un número de estrellas como garantía.
- Instalación Hermes: https://hermes-agent.nousresearch.com/docs/user-guide/features/skills y `hermes skills install --help`; la compatibilidad efectiva se verifica en el runtime destino, no se presupone.
