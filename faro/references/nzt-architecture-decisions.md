# Referencia NZT — decisiones de arquitectura (ADR/RFC)

## Fuente inspeccionada

Esta referencia documenta el patrón analizado en el checkout local de NZT, sin convertirlo en dependencia runtime ni copiar su router:

- Repositorio: `/Volumes/Data-GYC/ProyectsAgents/nzt-ai`
- Ref inspeccionada: `2094543` (`main`, `Presentation improved`)
- `skills/nzt/architecture/adr/SKILL.md`
- `skills/nzt/architecture/rfc/SKILL.md`
- `skills/nzt/architecture/SKILL.md`
- `skills/nzt/architecture/review/SKILL.md`
- `skills/nzt/architecture/design-product/SKILL.md`

## Principio adoptado

**RFC pregunta; ADR registra.**

NZT define ADR para una decisión difícil de revertir, que limita opciones futuras o que fue controvertida. El registro incluye qué la forzó, opciones con costos, decisión, consecuencias y esfuerzo de reversión. Su RFC se usa sólo si hay una decisión de ese calibre que necesita acuerdo de personas fuera de la conversación; guarda discusión y posiciones mientras está abierto. Un RFC aceptado produce un ADR; no se edita el RFC para convertirlo en el registro de la decisión.

También se adopta:

- un identificador numerado estable y no reutilizable;
- estados explícitos y sucesión enlazada, sin borrar historia;
- silencio no equivale a aceptación;
- un RFC abierto bloquea únicamente el trabajo dependiente;
- toda alternativa muestra su costo, incluida la elegida;
- una decisión no se inventa desde gusto, patrón de moda o código observado.

## Adaptación FARO

FARO conserva su propio contrato y rutas:

| NZT | Adaptación FARO |
| --- | --- |
| `Docs/adr/ADR-NNN-<slug>.md` | `context/decisions/adr/ADR-NNN-<slug>.md` |
| `Docs/rfc/RFC-NNN-<slug>.md` | `context/decisions/rfc/RFC-NNN-<slug>.md` |
| `nzt-architecture-adr` | `faro-arq-adr` |
| `nzt-architecture-rfc` | `faro-arq-rfc` |
| arquitectura/diseño NZT | arquitectura evidenciada, RM/BUG/TEC y plan FARO |

Los directorios de decisiones son bajo demanda: no alteran la inicialización ni obligan a cada proyecto a usar ADR/RFC. Los artefactos se indexan en `context/README.md` cuando existen.

FARO no adopta las decisiones, documentación de producto, opt-ins, comandos ni autoridad de NZT. Esta referencia sólo justifica el patrón de gobernanza de decisiones y permanece trazable a la fuente inspeccionada.
