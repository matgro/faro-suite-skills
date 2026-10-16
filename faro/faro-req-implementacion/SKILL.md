---
name: faro-req-implementacion
description: Use when FARO implements an approved requirement plan.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, implementation, requirements, code, verification]
    related_skills: [faro, faro-req-analisis-tecnico, faro-qa-ejecucion, faro-req-validacion, faro-ux]
---

# FARO — Implementación de requerimientos

## Rol
Implementa una unidad autorizada de un RM, BUG o TEC con plan técnico `LISTO_PARA_DESARROLLO`. No redefine comportamiento funcional, no acepta la entrega, no realiza QA de aplicación ni hace commit, PR o despliegue sin la ruta `faro-entrega`.

## Precondiciones
- FARO está `available`.
- La entrada identifica ID, versión, alcance y autorización humana vigente.
- Plan y tareas pertenecen a la misma versión y están `LISTO_PARA_DESARROLLO`.
- Se leyeron `AGENTS.md`, arquitectura, instrucciones del repositorio, Git y tarea activa.
- Antes de editar código, la rama activa debe cumplir `feature/<RM-ID>-<descripcion-kebab-case>`. Si no existe, crearla desde la base autorizada antes de modificar archivos. Si hay cambios no atribuibles a la unidad, bloquear y pedir decisión.

Si una precondición falla, actualizar `context/workflow.json` con `waitingOn`, no modificar código y devolver la ruta a `faro`, `faro-req-ingenieria` o `faro-req-analisis-tecnico`.

## Procedimiento
1. Confirmar la unidad en el plan y marcarla `doing` en workflow. Si Jira está `REQUIRED`, transicionar la issue a `Haciendo` cuando corresponda y registrar un comentario con unidad, versión y enlace a la rama cuando exista; si falla, bloquear antes de editar código. **Completo:** unidad, versión, autorización y Jira trazables.
2. Inspeccionar implementaciones, consumidores, pruebas y convenciones locales antes de editar. **Completo:** se reutiliza o justifica una ruta nueva.
3. Si existe interfaz, cargar `faro-ux` antes de modificar pantallas. En Laravel revisar `/template`, `resources/views/template/components` y pantallas del mismo dominio antes de escribir markup. **Completo:** catálogo, dominio y markup único respetados.
4. Implementar sólo el alcance de la tarea; mantener contratos salvo orden explícita del RM. **Completo:** no hay alcance adicional ni rutas paralelas.
5. Escribir o ajustar pruebas que viajan con el código y ejecutarlas. **Completo:** resultados reales o bloqueo registrado.
6. Actualizar tareas, fuentes técnicas afectadas y workflow: `done`, evidencia y `nextRoute`. **Completo:** reanudable sin chat.
7. Detenerse y reportar cambios, comprobaciones, límites y siguiente ruta. QA de aplicación se enruta a `faro-qa-ejecucion`.

## Invariantes
- El plan técnico guía el cómo; el RM autorizado guía el qué.
- Un fallo derivado del cambio se corrige dentro de la unidad; ambigüedad funcional vuelve a `faro-req-ingenieria`.
- No declarar conformidad funcional; pertenece a `faro-req-validacion`.
- No tratar compilación o inspección como prueba ejecutada.
- No exponer secretos ni usar producción sin autorización.

## Verificación
- [ ] ID, versión, autorización y tarea coinciden.
- [ ] Se leyó código vecino, consumidores y pruebas.
- [ ] UI revisó catálogo local cuando aplica.
- [ ] Pruebas ejecutadas o bloqueo evidenciado.
- [ ] Tarea/workflow registran resultado y siguiente ruta.
- [ ] No hubo entrega ni aceptación implícitas.
