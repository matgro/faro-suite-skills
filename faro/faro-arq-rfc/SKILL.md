---
name: faro-arq-rfc
description: Use when FARO requests external agreement on a decision.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, architecture, rfc, decisions, governance]
    related_skills: [faro, faro-arq-adr, faro-req-analisis-tecnico, faro-req-desarrollo]
---

# FARO — Solicitud de comentarios arquitectónica (RFC)

## Rol

Formula una decisión técnica **abierta** para que las personas afectadas puedan objetar antes de comprometer el proyecto. Crea `context/decisions/rfc/RFC-NNN-<slug>.md`; no toma la decisión, no inventa posiciones y no permite implementar trabajo dependiente mientras siga abierto.

FARO adapta la referencia NZT documentada en `faro/references/nzt-architecture-decisions.md`: RFC pregunta; ADR registra. Un RFC aceptado genera un ADR mediante `faro-arq-adr`; no se edita el RFC para convertirlo en registro de decisión.

## Cuándo usar

Usar RFC sólo si concurren las tres condiciones:

- la decisión es costosa de revertir o establece un precedente estructural;
- requiere acuerdo de personas fuera de esta conversación —otro equipo, consumidor de contrato, operador o mantenedor—;
- hay al menos dos alternativas defendibles.

Una decisión que el usuario puede tomar aquí no requiere RFC: debe ir directamente a ADR si merece registro. Un RFC de una sola opción es un anuncio, no una consulta.

## Procedimiento

1. Leer arquitectura, RM/BUG/TEC, plan, ADR/RFC existentes, stakeholders identificables e instrucciones locales. Confirmar que no se está pidiendo consenso ficticio. **Completo:** problema, afectados y alternativas tienen evidencia.
2. Inventariar `RFC-NNN-*.md` en `context/decisions/rfc/`, asignar siguiente `NNN` una vez y crear el directorio sólo al abrir un RFC válido. **Completo:** numeración estable sin colisiones.
3. Redactar `assets/rfc.md` con problema, opciones y costos, propuesta, efectos por stakeholder, preguntas abiertas, ventana de comentarios con fecha y posiciones textuales de sus autores. Estado inicial: `open`. **Completo:** una persona afectada puede objetar con información suficiente.
4. Mientras el RFC esté `open`, actualizar `context/workflow.json` si existe con `waitingOn` que nombre RFC y el impedimento, y no enviar a desarrollo ninguna tarea que dependa de la decisión. El trabajo independiente puede continuar. **Completo:** la pausa es verificable y limitada.
5. Al cerrar, registrar `accepted`, `rejected` o `withdrawn` con fecha y razón. Silencio no es aceptación: registrar “cerrado sin respuesta” si corresponde. Para `accepted`, entregar a `faro-arq-adr`, que registra la decisión permanente y cita el RFC. **Completo:** el resultado no se confunde con consenso ni se pierde la discusión.

## Invariantes

- Nada dependiente de un RFC abierto se implementa, prueba como entregable ni valida como aprobado.
- No atribuir, resumir como acuerdo ni borrar objeciones de personas afectadas.
- La ventana de comentarios es una fecha explícita, no una sensación.
- No registrar secretos, tokens, `.env`, credenciales o datos personales no necesarios.
- Un RFC no aprueba RM, presupuesto, release, despliegue ni cambios de código.

## Verificación

- [ ] Las tres condiciones para RFC están demostradas.
- [ ] Hay alternativas reales, costos y stakeholders identificados.
- [ ] La ventana, estado y posiciones tienen fecha/fuente.
- [ ] Un RFC abierto bloquea sólo sus dependencias mediante `waitingOn`.
- [ ] Un RFC aceptado enlaza al ADR; uno rechazado o retirado conserva su historial.
