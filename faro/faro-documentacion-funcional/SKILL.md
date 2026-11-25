---
name: faro-documentacion-funcional
description: Use when FARO creates or maintains a functional document.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, functional-documentation, requirements, traceability]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico, faro-req-validacion, faro-ux, faro-cierre]
---

# FARO — Documentación funcional

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

Antes de resolver rutas o promover cambios, leer [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md). Sus reglas de catálogo, compatibilidad migrada e inmutabilidad prevalecen sobre nombres recordados.

## Overview

Crea y mantiene un único Documento Funcional (DF) entregable por dominio o proceso, redactado para sus usuarios de negocio. La investigación, fuentes de código, contratos, estados internos, hipótesis y trazabilidad detallada viven en una nota interna vinculada; nunca se mezclan con el DF entregable. Cuando el perfil habilita documentación funcional, esta es la ruta obligatoria antes de formalizar una solicitud funcional. Un DF puede originarse por investigación o análisis de un dominio sin requerir un RM.

El DF no sustituye al RM: el DF documenta el comportamiento consolidado; el RM preserva una solicitud de cambio y su delta. Un cambio aprobado no modifica el DF vigente hasta contar con validación que justifique incorporarlo a una nueva baseline.

## When to Use

- El perfil del proyecto declara documentación funcional `HABILITADA` y se recibe una solicitud funcional, de datos, permisos, integración o interfaz.
- Se pide investigar, analizar, crear, completar o mantener un documento funcional de un proceso, módulo o dominio.
- Se necesita localizar la sección de referencia que una solicitud cambiaría antes de crear o actualizar un RM.

No usar para una consulta de estado sin cambio documental, un plan técnico, implementación, QA o entrega. No usar para inventar comportamiento a partir del código: el comportamiento observado se etiqueta como tal y no equivale a decisión funcional aprobada.

## Fuentes de verdad, resolución y estados

- Perfil: `context/requirements/project-profile.md` habilita o deshabilita esta ruta.
- Raíz durable: `context/requirements/functional/` conserva conocimiento funcional vigente, separado de los expedientes de cambio.
- Catálogo DF: `context/requirements/functional-documents-catalog.md` reserva IDs y localiza documentos; `Documento principal` conserva sólo el basename dentro de la carpeta canónica y la fuente serializada sobrevive a la publicación. El identificador y todo prefijo de basename usan exactamente `DF-NNN` en mayúsculas; una comparación case-insensitive sólo detecta colisiones y nunca autoriza normalización. No es fuente normativa ni conserva estado operativo.
- Expediente documental: `context/requirements/functional/DF-<NNN>/` es la ruta estable de un DF. No se mueve entre carpetas por su madurez.
- DF entregable: es el `Documento principal` que el catálogo resuelve dentro de `context/requirements/functional/DF-<NNN>/`. Una unidad nueva usa `DF-<NNN>.md`; una migrada puede conservar un basename histórico con slug. Es el único documento funcional que se comparte con el usuario.
- Investigación interna: una unidad nueva usa `DF-<NNN>-investigacion-interna.md` en la misma carpeta; una migrada puede conservar su basename histórico validado. Contiene fuentes, observaciones, términos técnicos, decisiones y pendientes de levantamiento; no se comparte como DF.
- El DF usa estados `DRAFT`, `PENDING_DEFINITION`, `READY_FOR_REVIEW`, `BASELINED` y `SUPERSEDED`.
- Estados de evidencia: `CONFIRMADA`, `OBSERVADA`, `DERIVADA` o `PROPUESTA`. Código, pruebas o interfaces sólo sustentan `OBSERVADA` salvo una fuente humana o documental que confirme la regla.

La madurez del DF y sus baselines son propiedades documentales. Estado de trabajo, prioridad y asignación pertenecen al gestor configurado cuando `work_tracking.mode` es `REQUIRED`; no se copian al catálogo ni al DF. `context/workflow.json` es sólo continuidad temporal y, cuando existe, su `workItemRef` apunta al expediente de cambio que motivó la actualización.

Los documentos funcionales no se vinculan al seguimiento remoto por sí mismos. Seguimiento `REQUIRED` aplica cuando se formaliza un RM; no crear una issue o work item para investigación documental sin solicitud de cambio. Cuando un DF se actualiza como promoción de un expediente validado, conservar el ID y la ruta de ese expediente como evidencia, no su estado remoto.

## Visuales Markdown/Mermaid

Los visuales funcionales viven dentro del DF, RM o plan que explican; no se crean archivos de diseño paralelos ni imágenes opacas. Usar bloques `mermaid` en Markdown: el código es legible sin renderizado en un README y los visores compatibles lo dibujan. Cada visual es un apoyo de lectura, no una fuente adicional de requisitos: debe enlazar sólo RF/RN/CA/PD existentes y no agregar reglas, actores, transiciones o decisiones.

- Usar `flowchart` cuando el proceso tiene bifurcaciones, varios actores, excepciones o más de tres pasos relevantes.
- Usar `stateDiagram-v2` cuando una entidad tiene ciclo de vida, transiciones, guardas o responsables que puedan malinterpretarse.
- Usar `sequenceDiagram` sólo cuando la interacción entre usuario, sistema y tercero sea necesaria para definir el contrato funcional; contratos técnicos detallados permanecen en el plan técnico.
- Mantener antes o después del bloque una tabla o texto que enumere sus elementos y trazabilidad `RF/RN/CA/PD`; quien lea el Markdown sin renderizar debe poder entenderlo.
- Para una pantalla, navegación o estados visibles, `faro-ux` completa el mismo artefacto FARO con un flujo Mermaid proporcional; no crea un mockup ni un archivo visual aparte salvo pedido humano expreso.
- Si el visual no aporta claridad, declarar `No aplica` y conservar la especificación tabular/textual. No diagramar por decoración.

## Procedimiento

1. Antes de redactar contenido o formular preguntas funcionales, leer `context/README.md`, `project-profile.md`, el catálogo DF, los DF relacionados, el contrato de requerimientos y las fuentes aportadas. Inspeccionar además los repositorios, arquitectura, documentación, rutas/contratos, pantallas y pruebas indexados que correspondan al dominio; buscar por los términos del dominio en cada repositorio disponible. Registrar sólo los hallazgos pertinentes como `OBSERVADA`, con ruta y localizador, y registrar las fuentes no accesibles. Confirmar que el perfil está `HABILITADA`; si está deshabilitado, seguir el ruteo normal de FARO. **Completo:** antes de responder funcionalmente existen fuentes revisadas de cada repositorio aplicable o una limitación explícita; se conoce la habilitación y si existe un DF aplicable.
2. Clasificar el pedido: investigación/creación de DF, mantenimiento de DF o solicitud de cambio. Para investigación o creación, no crear RM por defecto. Para una solicitud de cambio, localizar o crear primero la referencia DF mínima y registrar el impacto; después entregar la ruta a `faro-req-ingenieria` para formalizar el RM. **Completo:** el propósito y la siguiente ruta no son ambiguos.
3. Antes de editar un DF existente, validar el contrato con `python -B <skills-root>/faro/scripts/work_item_contract.py validate --root <root>` y exigir código 0; los errores estructurales bloquean, mientras una advertencia de referencia remota faltante en otro expediente migrado no impide documentación permitida bajo `OFF`. Combinar únicamente la carpeta canónica con el basename `Documento principal`; ID, `df_id` del front matter y catálogo deben coincidir. Para uno nuevo, reservar de forma serializada con `python -B <skills-root>/faro/scripts/work_item_contract.py reserve --root <root> --kind DF --source <evidencia> --apply --json`; conservar exactamente el ID y la fuente devueltos, crear los archivos canónicos desde los assets y previsualizar `register` sin `--apply`. Publicar luego con `python -B <skills-root>/faro/scripts/work_item_contract.py register --root <root> --id <DF-ID> --primary context/requirements/functional/<DF-ID>/<DF-ID>.md --reservation-source <misma-evidencia> --apply --json`, agregando `--domain`, `--baseline` o `--related` sólo cuando correspondan. `--primary` recibe la ruta completa relativa al root para validarla, pero el catálogo guarda sólo su basename. El helper consume la reserva únicamente si carpeta, primario y front matter concuerdan. Ante duplicidad, ruta fuera de raíz, basename ambiguo, ID incoherente, symlink o nota huérfana, detenerse: no renombrar ni renumerar automáticamente. Una unidad migrada conserva los basenames resueltos. **Completo:** catálogo, directorio, documento principal y metadatos resuelven un único DF estable.
4. Redactar el DF para el usuario: propósito, alcance/exclusiones, participantes, proceso operativo, reglas de negocio, información a registrar, casos especiales, criterios de aceptación y pendientes. Cuando el proceso, sus estados o una interacción requieran claridad adicional, añadir el visual Markdown/Mermaid proporcional y su trazabilidad; usar lenguaje del negocio; no incluir rutas de archivos, endpoints, clases, tablas, estados internos ni identificadores de fuentes. Mantener evidencia, observaciones y vocabulario técnico exclusivamente en la nota interna. **Completo:** una persona usuaria puede entender y revisar el DF sin conocer la implementación, incluso sin renderizar Mermaid.
5. Para un RM relacionado, resolver su ruta exclusivamente por `context/requirements/requirements-catalog.md` y mantener trazabilidad bidireccional: el RM incluye una matriz `DF-ID#elemento → tipo de impacto → delta`; el DF incluye el RM, su versión, su ruta estable, las secciones afectadas y el resultado de incorporación. Tipos válidos: `AGREGA`, `MODIFICA`, `ELIMINA`, `SIN_IMPACTO`. **Completo:** un revisor navega entre conocimiento durable y expediente sin depender de rutas inferidas.
6. Si el RM aún no está validado, conservar el DF vigente sin alterar su baseline; el delta, incluido diseño visible propuesto, vive en el expediente del RM. Tras un resultado `VERIFIED`, `faro-cierre` solicita esta ruta para incorporar únicamente los elementos conformes, crear una nueva baseline del mismo DF y registrar evidencia `INCORPORADO`. No congelar el expediente ni cerrar el item remoto mientras esta promoción requerida esté pendiente. **Completo:** el DF no presenta comportamiento futuro como vigente y el cierre puede comprobar la promoción.
7. Ejecutar la lista de verificación, actualizar sólo localización/reserva en el catálogo y, cuando el trabajo requiera continuidad, actualizar `context/workflow.json` sin duplicar contenido del DF. Para una solicitud nueva de cambio, `nextRoute` es `faro-req-ingenieria`; para una promoción solicitada por cierre, devolver `nextRoute: faro-cierre`; para un DF sin cambio, finalizar o indicar la revisión faltante. **Completo:** documento, catálogo, trazabilidad y handoff concuerdan.

## Contenido mínimo de un DF

El vocabulario de negocio se consulta en `context/glossary.md` y puede explicarse en el DF con las mismas definiciones sustentadas; fuentes técnicas y discrepancias quedan en la investigación interna. Un cambio del glosario implica no reescribir baselines ni modificar automáticamente DF históricos.

- Identificación, versión, estado, propósito, alcance, exclusiones y fuentes.
- Contexto, glosario, actores y permisos.
- Procesos y estados, incluidos alternos y excepciones conocidos.
- Visuales Markdown/Mermaid trazables cuando reduzcan ambigüedad de proceso, estados, integración o navegación.
- RF, RN, datos, validaciones, integraciones, RNF y restricciones identificados.
- CA verificables, pendientes y decisiones con evidencia.
- Matriz de trazabilidad de RM y registro de versiones/baselines.

## Invariantes

- Un DF es el único documento funcional compartible por dominio; la investigación vinculada no es un segundo DF ni un entregable al usuario.
- No incluir rutas de archivos, endpoints, clases, tablas, estados internos, identificadores de fuentes ni detalles de implementación en un DF entregable.
- Un diagrama Mermaid no sustituye texto/tablas ni introduce comportamiento; su versión legible sin renderizado y su trazabilidad son obligatorias.
- Un RM no se crea para investigar o documentar un dominio si no existe una solicitud de cambio.
- Un DF no concede aprobación, autorización de implementación, merge ni despliegue.
- Un RM aprobado no altera el comportamiento vigente del DF hasta su validación e incorporación explícita.
- El catálogo nunca conserva estado, prioridad o asignación del trabajo; una promoción registra evidencia y versión, no una copia del estado remoto.
- El DF conserva una ruta estable. Madurez o supersesión se registran dentro del documento; nunca se mueve entre carpetas `active`/`completed`.
- No inferir reglas, roles, permisos, límites, mensajes, contratos o decisiones de negocio desde el código.
- Si no existe DF del dominio, crear el mínimo que permita identificar el alcance y conservar el resto como `NO DEFINIDO` o `PD`.

## Verification Checklist

- [ ] Existe un único DF entregable en lenguaje de negocio; la investigación, evidencia y detalles técnicos están fuera de él.
- [ ] Antes de redactar o preguntar, se inspeccionaron los repositorios y fuentes indexadas aplicables al dominio; las limitaciones de acceso están registradas.
- [ ] Perfil leído y estado `HABILITADA` comprobado antes de ejecutar esta ruta obligatoria.
- [ ] Catálogo, reserva, directorio, ID, primario y nota interna son únicos y coherentes.
- [ ] Cada elemento normativo identifica evidencia, derivación o PD; lo observado no se presenta como confirmado.
- [ ] Cada visual Mermaid aplicable usa sólo elementos existentes, identifica RF/RN/CA/PD y conserva explicación legible sin renderizado.
- [ ] Cada RM relacionado tiene vínculos bidireccionales por sección y tipo de impacto.
- [ ] El comportamiento vigente del DF no contiene cambios no validados.
- [ ] Catálogo, historial de versión y `workflow.json` (si aplica) apuntan a los mismos documentos y versiones.
- [ ] La siguiente ruta es `faro-req-ingenieria` sólo para una solicitud que formalizar, o `faro-cierre` después de una promoción verificada; no se crea RM para investigación documental.
