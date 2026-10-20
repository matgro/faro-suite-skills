---
name: faro-arq-adr
description: Use when FARO records a significant technical decision.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, architecture, adr, decisions, governance]
    related_skills: [faro, faro-arq-rfc, faro-req-analisis-tecnico, faro-req-desarrollo, faro-req-validacion]
---

# FARO — Registro de decisión arquitectónica (ADR)

## Rol

Registra una decisión técnica **ya tomada** en `context/decisions/adr/ADR-NNN-<slug>.md`. Conserva qué la forzó, alternativas reales, costos, decisión, consecuencias y el esfuerzo de revertirla. No aprueba alcance funcional, no decide por el usuario, no implementa código ni convierte una preferencia en arquitectura.

Las referencias de diseño están en `faro/references/nzt-architecture-decisions.md` y `faro/references/adr-ai-memory.md`: FARO adopta “RFC pregunta; ADR registra” y ADR como memoria persistente para asistentes, adaptados a `context/` y al lifecycle FARO.

## Cuándo usar

Crear un ADR sólo si al menos una condición se cumple:

- la decisión es costosa de revertir —migrar datos, reescribir un componente o romper una integración—;
- restringe opciones de componentes, consumidores, equipos o mantenimiento futuro;
- hubo alternativas defendibles o controversia que debe poder reconstruirse.

No usar para una decisión reversible en una tarde, un detalle ya registrado por el stack, ni una decisión funcional pendiente: ésta vuelve a `faro-req-ingenieria`.

Si todavía se requiere acuerdo de personas fuera de la conversación, usar primero `faro-arq-rfc`. Un RFC aceptado produce su ADR y el ADR lo referencia.

## Procedimiento

1. Leer `context/README.md`, arquitectura aplicable, RM/BUG/TEC y plan técnico si existen, instrucciones locales, estado Git, el índice `context/decisions/adr/README.md` si existe y ADR/RFC relevantes. Distinguir hechos observados, restricciones aprobadas y propuestas. **Completo:** se conoce qué decisión es y qué no puede decidir esta skill.
2. Inventariar `ADR-NNN-*.md` en `context/decisions/adr/`, asignar el siguiente `NNN` una sola vez y verificar que el slug no colisione. Crear el directorio y su `README.md` desde `assets/adr-index.md` sólo cuando haya una decisión que lo merezca. **Completo:** el identificador es estable, no se reutiliza y el catálogo puede localizarlo.
3. Redactar desde `assets/adr.md`, con front matter MADR parseable: contexto/problema, opciones con costos reales, decisión humana confirmada, consecuencias positivas y negativas, alternativas descartadas, reversibilidad, evidencia y relación con RFC/RM/BUG/TEC. No presentar el silencio como aceptación ni atribuir al usuario una recomendación del agente que rechazó. **Completo:** alguien ajeno o una sesión futura puede decidir conservar o reconsiderar la decisión leyendo el documento.
4. Usar estado `proposed` sólo si todavía no fue tomada; `accepted` cuando decisión y responsable son explícitos; `deprecated` cuando dejó de aplicar sin sucesor, incluyendo fecha y razón; `superseded` sólo enlazando a un ADR posterior aceptado mediante `superseded-by`. No borrar ni reescribir el razonamiento histórico de un ADR; el sucesor apunta al anterior. **Completo:** historial, deprecación y sucesión son trazables.
5. Actualizar el índice ADR con ID, título, estado y relación; enlazar el ADR desde arquitectura, plan técnico o RM relevante y actualizar `context/README.md`. Si hay workflow activo, conservar unidad/versiones y continuar a la ruta ya autorizada. **Completo:** el registro es localizable sin duplicar su contenido.

## Invariantes

- Un ADR no es RFC ni sustituye aprobación funcional, RM, CA, QA o validación.
- Cada opción muestra costo, incluida la ganadora; no se crean hombres de paja.
- Ningún secreto, token, `.env`, connection string ni contenido sensible se registra.
- Esta skill no modifica código, dependencias, infraestructura, seguimiento remoto ni workflow salvo el handoff documental autorizado.

## Verificación

- [ ] La decisión cumple el umbral de costo, restricción futura o controversia.
- [ ] El ID no se reutiliza y el estado/fecha/decisor son explícitos; la metadata MADR es coherente.
- [ ] Las alternativas y consecuencias, incluso negativas, están documentadas.
- [ ] Un RFC relacionado se enlaza; un RFC abierto no se trata como decisión tomada.
- [ ] Arquitectura/plan/RM, el índice ADR y el índice de contexto apuntan al ADR cuando corresponda.
