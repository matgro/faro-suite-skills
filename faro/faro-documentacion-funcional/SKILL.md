---
name: faro-documentacion-funcional
description: Use when FARO creates or maintains a functional document.
version: 1.2.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, functional-documentation, requirements, traceability]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico, faro-req-validacion, faro-ux]
---

# FARO — Documentación funcional

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

## Overview

Crea y mantiene un único Documento Funcional (DF) entregable por dominio o proceso, redactado para sus usuarios de negocio. La investigación, fuentes de código, contratos, estados internos, hipótesis y trazabilidad detallada viven en una nota interna vinculada; nunca se mezclan con el DF entregable. Cuando el perfil habilita documentación funcional, esta es la ruta obligatoria antes de formalizar una solicitud funcional. Un DF puede originarse por investigación o análisis de un dominio sin requerir un RM.

El DF no sustituye al RM: el DF documenta el comportamiento consolidado; el RM preserva una solicitud de cambio y su delta. Un cambio aprobado no modifica el DF vigente hasta contar con validación que justifique incorporarlo a una nueva baseline.

## When to Use

- El perfil del proyecto declara documentación funcional `HABILITADA` y se recibe una solicitud funcional, de datos, permisos, integración o interfaz.
- Se pide investigar, analizar, crear, completar o mantener un documento funcional de un proceso, módulo o dominio.
- Se necesita localizar la sección de referencia que una solicitud cambiaría antes de crear o actualizar un RM.

No usar para una consulta de estado sin cambio documental, un plan técnico, implementación, QA o entrega. No usar para inventar comportamiento a partir del código: el comportamiento observado se etiqueta como tal y no equivale a decisión funcional aprobada.

## Fuentes de verdad y estados

- Perfil: `context/requirements/project-profile.md` habilita o deshabilita esta ruta.
- Catálogo DF: `context/requirements/functional-documents-catalog.md` localiza documentos; no es fuente normativa.
- DF entregable: `context/requirements/DF-<NNN>-<dominio>.md` es el único documento funcional que se comparte con el usuario.
- Investigación interna: `context/requirements/DF-<NNN>-<dominio>-investigacion-interna.md` contiene fuentes, observaciones, términos técnicos, decisiones y pendientes de levantamiento; no se comparte como DF.
- El DF usa estados `DRAFT`, `PENDING_DEFINITION`, `READY_FOR_REVIEW`, `BASELINED` y `SUPERSEDED`.
- Estados de evidencia: `CONFIRMADA`, `OBSERVADA`, `DERIVADA` o `PROPUESTA`. Código, pruebas o interfaces sólo sustentan `OBSERVADA` salvo una fuente humana o documental que confirme la regla.

Los documentos funcionales no se vinculan al seguimiento remoto por sí mismos. Seguimiento `REQUIRED` aplica cuando se formaliza un RM; no crear una issue o work item para investigación documental sin solicitud de cambio.

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
3. Antes de reservar, inventariar todos los archivos `DF-<NNN>-*.md` del directorio de requisitos y comparar, sin distinguir mayúsculas/minúsculas, el ID del nombre, el `df_id` del front matter y las entradas activas de `## Documentos`/`## Reservas` del catálogo. Un ID sólo puede corresponder a un DF entregable; puede tener como máximo una nota cuyo nombre termine exactamente en `-investigacion-interna.md`, con el mismo ID y sin condición de DF entregable. Si existe más de un DF entregable, un ID de archivo/front matter/catálogo no coincide, o se encuentra una nota interna sin DF padre, detenerse: no crear, actualizar, consumir ni renumerar automáticamente. Informar la colisión y pedir una decisión humana que identifique qué DF conserva el ID y cuál recibe un nuevo ID; después actualizar en la misma operación el nombre, front matter, título, catálogo, referencias cruzadas y nota interna. Sólo entonces reservar mediante una entrada serializada de `Reservas`; no usar máximo+1 de manera concurrente. Crear el DF entregable desde `assets/functional-document.md` y, cuando haya investigación, su nota interna desde `assets/functional-investigation.md`. **Completo:** el inventario no contiene colisiones; existe un solo DF compartible por ID, su investigación queda fuera de él y ambos usan el mismo ID estable.
4. Redactar el DF para el usuario: propósito, alcance/exclusiones, participantes, proceso operativo, reglas de negocio, información a registrar, casos especiales, criterios de aceptación y pendientes. Cuando el proceso, sus estados o una interacción requieran claridad adicional, añadir el visual Markdown/Mermaid proporcional y su trazabilidad; usar lenguaje del negocio; no incluir rutas de archivos, endpoints, clases, tablas, estados internos ni identificadores de fuentes. Mantener evidencia, observaciones y vocabulario técnico exclusivamente en la nota interna. **Completo:** una persona usuaria puede entender y revisar el DF sin conocer la implementación, incluso sin renderizar Mermaid.
5. Para un RM relacionado, mantener trazabilidad bidireccional: el RM incluye una matriz `DF-ID#elemento → tipo de impacto → delta`; el DF incluye el RM, su versión, las secciones afectadas y estado de incorporación. Tipos válidos: `AGREGA`, `MODIFICA`, `ELIMINA`, `SIN_IMPACTO`. **Completo:** un revisor puede navegar del cambio al DF y del DF al cambio sin inferencias.
6. Si el RM aún no está validado, conservar el DF vigente sin alterar su baseline; el delta vive en el RM. Tras validación funcional/técnica de la versión del RM, incorporar únicamente sus elementos conformes en una versión nueva del DF, actualizar el historial y marcar el vínculo como `INCORPORADO`. **Completo:** el DF no presenta comportamiento futuro como vigente.
7. Ejecutar la lista de verificación, actualizar el catálogo y, cuando el trabajo requiera continuidad, actualizar `context/workflow.json` sin duplicar contenido del DF. Para solicitudes de cambio, `nextRoute` es `faro-req-ingenieria`; para un DF sin cambio, finalizar o indicar la revisión que falta. **Completo:** documento, catálogo y workflow concuerdan.

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
- No inferir reglas, roles, permisos, límites, mensajes, contratos o decisiones de negocio desde el código.
- Si no existe DF del dominio, crear el mínimo que permita identificar el alcance y conservar el resto como `NO DEFINIDO` o `PD`.

## Verification Checklist

- [ ] Existe un único DF entregable en lenguaje de negocio; la investigación, evidencia y detalles técnicos están fuera de él.
- [ ] Antes de redactar o preguntar, se inspeccionaron los repositorios y fuentes indexadas aplicables al dominio; las limitaciones de acceso están registradas.
- [ ] Perfil leído y estado `HABILITADA` comprobado antes de ejecutar esta ruta obligatoria.
- [ ] Catálogo, reserva, ID y ruta del DF son únicos y coherentes.
- [ ] Cada elemento normativo identifica evidencia, derivación o PD; lo observado no se presenta como confirmado.
- [ ] Cada visual Mermaid aplicable usa sólo elementos existentes, identifica RF/RN/CA/PD y conserva explicación legible sin renderizado.
- [ ] Cada RM relacionado tiene vínculos bidireccionales por sección y tipo de impacto.
- [ ] El comportamiento vigente del DF no contiene cambios no validados.
- [ ] Catálogo, historial de versión y `workflow.json` (si aplica) apuntan a los mismos documentos y versiones.
- [ ] La siguiente ruta es `faro-req-ingenieria` sólo cuando hay una solicitud funcional que formalizar; no se crea RM para investigación documental.
