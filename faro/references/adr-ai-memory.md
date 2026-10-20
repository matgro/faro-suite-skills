# ADR como memoria arquitectónica para IA — referencias y criterios FARO

## Fuente complementaria aportada por el usuario

- Miguel Ángel Sánchez, “ADR: La memoria arquitectónica que tu IA necesita”, *All you need is Clean Code*, 25 de febrero de 2026.
- URL: https://medium.com/all-you-need-is-clean-code/adr-la-memoria-arquitect%C3%B3nica-que-tu-ia-necesita-ed1d350bf73d
- Contenido disponible: transcripción aportada por el usuario el 20 de octubre de 2026, debido a que Medium bloqueó la consulta automatizada.

## Qué criterio toma FARO de esta fuente

| Criterio del artículo | Adopción FARO | Dónde se aplica |
| --- | --- | --- |
| El ADR preserva el porqué de decisiones para sesiones futuras de IA | ADRs bajo demanda, enlazados desde arquitectura, plan o RM y desde su índice | `faro-arq-adr` y `context/decisions/adr/README.md` |
| Formato MADR: metadatos, contexto, opciones, decisión y consecuencias | Plantilla con front matter parseable y secciones MADR equivalentes | `faro-arq-adr/assets/adr.md` |
| Estados `proposed`, `accepted`, `deprecated`, `superseded` | Estados explícitos; sucesión mediante `superseded-by` y deprecación con fecha/razón | `faro-arq-adr` y plantilla ADR |
| Índice para localizar estado y decisiones vigentes | `README.md` del directorio ADR, creado con el primer ADR y actualizado después | `faro-arq-adr/assets/adr-index.md` |
| Antes de implementar, revisar ADRs para evitar contradicciones | Desarrollo identifica los ADRs relevantes, los registra en evidencia y bloquea contradicciones | `faro-req-desarrollo` |
| Una decisión nueva significativa debe sugerir ADR | Análisis técnico enruta a ADR según costo de reversión, restricción futura o controversia | `faro-req-analisis-tecnico` |

## Lo que FARO no adopta literalmente

- No usa `docs/adr/`: FARO conserva `context/decisions/adr/` porque `context/` es su área documental gobernada.
- No crea comandos `.claude/commands/` ni depende de `CLAUDE.md`. El mismo control se integra en skills FARO para funcionar con Hermes y otros agentes.
- No convierte cada decisión en ADR ni sustituye RM/BUG/TEC: la decisión funcional sigue perteneciendo a `faro-req-ingenieria`.

## Relación con NZT

`nzt-architecture-decisions.md` sigue siendo la referencia de gobernanza para la separación RFC/ADR, sucesión inmutable, costos de alternativas y bloqueo de dependencias de RFC abiertos. Esta fuente complementa la integración de ADR como memoria operativa para asistentes de IA.
