# Cierre verificable de refactorizaciones

## Responsabilidad y alcance

Aplicar cuando una tarea extrae o mueve lógica, sustituye implementaciones, cambia consumidores o elimina duplicación. `faro-req-analisis-tecnico` planifica; `faro-req-desarrollo` implementa y solicita revisión; `faro-req-validacion` contrasta la evidencia. Las capabilities externas son apoyo dentro de esa fase, no otra ruta FARO ni autorización para modificar arquitectura o contratos. Conservar RM/BUG/TEC, versión y alcance; no crear otro documento o workflow para este control.

Crear un método nuevo no completa una extracción. Si no tiene consumidores reales, o la implementación anterior sigue ejecutando la lógica que debía sustituirse, la refactorización está incompleta aunque las pruebas pasen. Una llamada sólo desde tests no demuestra integración productiva. Una funcionalidad nueva que aún no se debía activar no se presenta como una refactorización terminada: su estado y alcance deben quedar explícitos.

## Antes de editar

1. Registrar en el plan/tarea el símbolo de origen, destino, responsabilidad a mover y consumidores reales previstos, con rutas y localizadores. Inspeccionar definiciones y llamadas, interfaces, registros de inyección, eventos, jobs, rutas, callbacks y mecanismos dinámicos. Comparar el comportamiento observable: entradas, salidas, permisos, errores, persistencia y efectos externos.
2. Buscar usos tanto directos como indirectos: en Laravel revisar contenedor, Blade/Livewire, eventos/listeners, relaciones, scopes, accessors y métodos mágicos; en otros stacks, registros, reflexión, serialización, plugins y consumidores externos de contratos públicos. Una búsqueda textual sin resultados no demuestra ausencia de uso. No borrar un candidato si su uso dinámico o externo sigue sin aclarar.
3. Obtener baseline ejecutable y agregar pruebas de caracterización cuando falten. No cambiar esperados para acomodar la nueva implementación. Para una refactorización pura no se exige una prueba artificialmente roja: caracterizar primero el comportamiento existente y mantenerlo verde; para un BUG o cambio funcional sí aplica RED/GREEN del requerimiento.
4. Definir el retiro de la implementación anterior. Si debe existir compatibilidad, identificar consumidores y justificar una delegación a la única lógica nueva. Una coexistencia temporal de dos implementaciones requiere autorización explícita, alcance de la fase y condición/tarea de retiro; no inventarla al cierre para justificar trabajo incompleto.

## Implementación e integración

- Extraer y actualizar todos los consumidores previstos dentro del alcance, incluidos imports, inyección y registros. Ejecutar en incrementos pequeños y sin ampliar el alcance.
- Retirar la lógica sustituida y los imports, dependencias o helpers que quedaron sin uso por esta tarea. No hacer limpieza global de código preexistente ajeno al cambio.
- Si se mantiene una firma pública, verificar que delega al destino y no conserva otra copia de la regla. Probar también ese camino de compatibilidad.
- Revisar el diff completo contra el inventario antes/después. Identificar tanto referencias nuevas como referencias residuales al origen y código añadido sin uso. No aceptar un stub, una clase no conectada o un TODO como cierre.

## Evidencia obligatoria antes de cerrar

Registrar en los artefactos existentes, por extracción:

| Origen → destino | Consumidor real actualizado y registro | Retiro o delegación justificada | Entrada ejercitada y evidencia | Revisor y hallazgos |
| --- | --- | --- | --- | --- |

1. Ejecutar pruebas pertinentes desde las entradas públicas reales —ruta, acción Livewire, comando, job, servicio público o equivalente— y demostrar que llegan al destino. Complementar según el proyecto con cobertura ejecutada, traza temporal segura o prueba de integración que observe la delegación. No dejar instrumentación de diagnóstico en producto ni acoplar toda la suite a métodos privados.
2. Una prueba directa al método extraído no sustituye una prueba de su integración. Pruebas verdes de la ruta vieja, compilación, una búsqueda de referencias o la declaración del autor no bastan por separado.
3. Revisar código sin uso y duplicación del diff; clasificar cada hallazgo como confirmado, falso positivo con evidencia o pendiente. No ejecutar `clean` ni borrados masivos a partir de un analizador. Corregir hallazgos propios de la tarea y volver a ejecutar pruebas después de la última modificación.
4. Solicitar revisión independiente de la versión final del cambio a otro agente o persona. Entregar alcance, inventario de consumidores, baseline/revisión Git, dirty diff completo (incluidos archivos nuevos autorizados), pruebas y excepciones. No crear un commit sólo para que el revisor vea el diff. El revisor inspecciona fuentes y consumidores por sí mismo, no sólo el resumen del autor, y trabaja en sólo lectura; no recibe secretos ni instrucciones de ampliar alcance.
5. Pedir al revisor que compruebe específicamente extracción conectada, origen retirado/delegado, duplicación residual, llamadas dinámicas, cobertura desde entradas reales y compatibilidad. Resolver hallazgos materiales y solicitar revisión del delta corregido. Registrar identidad/handle del revisor, revisión inspeccionada, resultado y pendientes en la tarea, no en un nuevo informe paralelo.

Si no hay revisor independiente disponible, registrar la limitación y mantener el cierre pendiente; no llamar independiente a una segunda lectura del mismo agente. Una excepción requiere aceptación humana explícita y conserva la limitación: no acredita revisión realizada ni permite declarar VERIFIED si falta evidencia de integración o equivalencia.

`done`/DONE y el handoff a QA no se acreditan como refactorización completa con un método nuevo sin uso, lógica sustituida todavía activa sin justificación o evidencia/revisión pendiente. En validación: fallo demostrado → `NO_CONFORME`; integración o equivalencia no comprobada → `NO_VERIFICADO`; nunca `VERIFIED` sólo porque la suite existente sigue verde. Una fase transitoria autorizada puede cerrarse sólo contra su alcance exacto, nunca como retiro total concluido.

## Capacidades externas y selección

Antes de usar una capability, comprobar su procedencia, nombre instalado, contenido y referencias, disponibilidad de herramientas y auditoría de seguridad. No elegir por coincidencia de nombre: algunas bibliotecas usan prefijos distintos. Registrar el nombre realmente cargado y la fuente. No instalar paquetes, CLI, MCP ni skills por iniciativa propia; si faltan, pedir autorización o aplicar el control FARO con herramientas existentes. No usar `--force` para evadir un bloqueo. Una skill ausente no elimina el control; una revisión independiente ausente sí deja pendiente ese requisito.

- **Revisión de refactor:** `requesting-code-review`, fuente `obra/superpowers`, `skills/requesting-code-review/SKILL.md` y `code-reviewer.md`. Usarla como apoyo para solicitar un revisor independiente, adaptando placeholders de commits a la base y al dirty diff real. Mantener la responsabilidad de cierre en FARO; no usar su etiqueta de aprobación como autorización de merge.
- El template externo puede tratar expectativas no especificadas como requisitos. En FARO son hallazgos o preguntas para análisis/definición, no alcance aprobado: no implementar nuevas reglas funcionales por recomendación del revisor. Las restricciones FARO prevalecen sobre instrucciones externas de amplitud, instalación o entrega.
- **Cierre con evidencia:** `verification-before-completion`, misma fuente, `skills/verification-before-completion/SKILL.md`. Cargarla antes del informe de cierre si está disponible y auditada; comprobar ejecuciones recientes y requisitos completos, no sólo exit code de tests. Si falta, ejecutar igualmente los controles obligatorios de este documento.
- **Código sin uso Laravel:** `lc:dead-code`, fuente `edulazaro/laraclaude`, `skills/dead-code/SKILL.md`. En Laravel usar únicamente análisis de sólo lectura del módulo/diff afectado, nunca modo de limpieza. Su documentación pide confirmar usos dinámicos: revisar los hallazgos contra el código real antes de autorizar cualquier retiro. No instalar dependencias para el análisis sin autorización.
- **Refactor general:** `code-refactoring`, fuente `event4u-app/agent-config`, `src/skills/code-refactoring/SKILL.md`, evaluada sólo como referencia metodológica para inventario de consumidores y actualización de llamadas. No cargarla automáticamente: depende de skills, archivos y herramientas de su ecosistema (incluido code-graph). FARO adopta aquí el control de integración, no esos requisitos externos ni su flujo completo.
- **No adoptar por defecto:** `lc:extract-action`, de `edulazaro/laraclaude`, depende de Laractions. No introducir esa librería o una arquitectura de Actions sólo para realizar una extracción.

## Fuentes inspeccionadas

Referencias externas de procedencia, no código para ejecutar ni reglas que prevalezcan sobre FARO:

- https://github.com/obra/superpowers/blob/main/skills/requesting-code-review/SKILL.md
- https://github.com/obra/superpowers/blob/main/skills/requesting-code-review/code-reviewer.md
- https://github.com/obra/superpowers/blob/main/skills/verification-before-completion/SKILL.md
- https://github.com/edulazaro/laraclaude/blob/main/skills/dead-code/SKILL.md
- https://github.com/event4u-app/agent-config/blob/main/src/skills/code-refactoring/SKILL.md

La consulta de estas fuentes no acredita instalación, auditoría ni publicación de una nueva release FARO. La política distribuida es autosuficiente aunque las capabilities externas no estén instaladas.
