---
name: faro-qa-ejecucion
description: Use when FARO runs QA cases with evidence.
version: 2.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, qa, testing, evidence, bugs]
    related_skills: [faro, faro-req-desarrollo, faro-req-validacion, faro-req-ingenieria, faro-cierre, faro-int-jira, faro-int-azure-devops]
---

# FARO — Ejecución de QA

En cada interacción, antes de interpretar términos del pedido, leer y aplicar [Glosario de dominio](../references/domain-glossary.md): consultar `context/glossary.md` si existe y evaluar actualizaciones sustentadas dentro de los límites de escritura de esta fase, sin alterar alcance ni autorizaciones.

Leer y aplicar [Expedientes y conocimiento duradero](../references/work-item-lifecycle.md) antes de resolver la unidad, crear evidencia o derivar un BUG.

## Rol
Diseña y ejecuta pruebas de aplicación para un incremento construido, con evidencia por criterio de aceptación. No modifica código, no aprueba el RM y no sustituye las pruebas que acompañan implementación.

Los casos y su evidencia se guardan en `context/requirements/work-items/<ID>/<ID>-qa.md`, creado desde `assets/qa-report.md`. Resolver primero con `python -B <skills-root>/faro/scripts/work_item_contract.py resolve --root <root> --id <ID> --json`; catálogo, `workflow.workItemRef`, primario, plan y tareas deben apuntar al mismo expediente mutable. `PASSED`, `FAILED`, `BLOCKED` y `PENDING` son resultados de casos, no estado operativo del work item.

## Precondiciones
- Existe RM/BUG/TEC con versión identificada.
- Seguimiento está `REQUIRED`, verificado y enlazado al item remoto del expediente.
- Incremento y tareas implementadas están identificados.
- La autorización cubre entorno, datos y efectos materiales: mensajes, pagos, borrados e integraciones.
- Se conocen terminal, HTTP, navegador u otras limitaciones reales.
- El expediente no contiene `<ID>-cierre.json`; un expediente congelado no admite una nueva corrida ni evidencia añadida.

## Procedimiento
1. Leer primario, CA, plan, tareas, arquitectura, evidencia y workflow desde el expediente resuelto. Si seguimiento está `REQUIRED`, sincronizar el inicio de QA con una actualización concisa conforme a `../references/comment-format.md` y enlace a `<ID>-qa.md`, manteniendo el estado remoto de trabajo; si falla, bloquear antes de ejecutar. **Completo:** cada escenario tiene origen funcional, ruta estable y trazabilidad remota.
2. Crear o actualizar `<ID>-qa.md` desde el asset y definir casos antes de ejecutar: API, UI o ambos; precondiciones, datos, pasos, esperado, efectos y limpieza. **Completo:** ningún esperado deriva del comportamiento actual.
3. Registrar la autorización de datos/efectos faltante. No usar datos reales sin autorización. **Completo:** escenario ejecutable o BLOCKED con causa.
4. Ejecutar por CA y registrar evidencia. Estados permitidos: `PENDING`, `PASSED`, `FAILED`, `BLOCKED`. **Completo:** UI no se acredita con API.
5. Para cada fallo reproducible contra un CA/esperado sustentado, resolver un BUG existente o dar de alta uno nuevo sin corregirlo durante la corrida. El alta ejecuta `python -B <skills-root>/faro/scripts/work_item_contract.py reserve --root <root> --kind BUG --source <evidencia-del-caso> --apply --json`, crea/importa y relee el item mediante el adaptador remoto configurado, materializa `<BUG-ID>/<BUG-ID>.md` desde el asset de mantenimiento y ejecuta primero una previsualización y luego `python -B <skills-root>/faro/scripts/work_item_contract.py register --root <root> --id <BUG-ID> --primary context/requirements/work-items/<BUG-ID>/<BUG-ID>.md --reservation-source <misma-evidencia> --external-provider <proveedor> --external-id <id-remoto> --external-url <url-remota> --related <ID-padre> --apply --json`. `--primary` recibe la ruta completa para validarla, mientras el catálogo guarda el basename `Documento principal`. Validar y resolver el BUG antes del handoff, y registrar `derived_from` tanto en el hijo como en el reporte padre. Si el remoto se creó pero la publicación falló, reconciliar ese mismo item sin duplicarlo. Un BUG existente, incluido uno migrado, usa `primaryPath` devuelto por el helper. Un síntoma sin esperado o causa confirmados fuera de esos CA conserva evidencia y se deriva a `faro-incidentes`. **Completo:** BUG, reproducción, impacto, padre y autoridad remota son trazables.
6. Actualizar workflow conservando `workItemRef`: fallo conocido → expediente BUG y `faro-req-analisis-tecnico` o regreso autorizado a desarrollo; síntoma no clasificado → `faro-incidentes`; éxito → `faro-req-validacion`. Si seguimiento está `REQUIRED`, publicar el resultado material sin copiar su estado al Markdown. Validar estrictamente el contrato de work items antes del handoff. **Completo:** próxima ruta real y expediente íntegro.

## Invariantes
- Caso no ejecutado nunca es PASSED.
- BLOCKED exige causa externa, no preparación autorizada omitida.
- Evidencia se revisa para secretos, PII y contenido sensible.
- QA distingue causa sospechada de hecho confirmado.
- No exigir INC para fallos conocidos contra CA: crear o resolver el BUG trazable; INC se reserva para síntomas todavía no clasificados.
- Un BUG derivado nunca reutiliza el ID del expediente probado ni queda sólo como una fila de QA.
- Un resultado QA no congela ni cierra el expediente.

## Verificación
- [ ] Cada CA tiene caso, estado y evidencia o limitación.
- [ ] Datos aislados fueron limpiados o su deuda quedó registrada.
- [ ] Fallos reproducibles tienen BUG trazable.
- [ ] No se cambió código durante QA.
- [ ] Workflow refleja el handoff real.
- [ ] `<ID>-qa.md` pertenece al expediente resuelto y todo BUG derivado tiene catálogo, primario, relación y referencia remota cuando aplica.
