---
schema_version: "2.0"
catalog_kind: "FARO_FUNCTIONAL_DOCUMENTS"
---

# Catálogo de documentación funcional vigente

Este catálogo localiza documentación funcional duradera. No contiene expedientes de cambio ni estados operativos.

## Reservas

| ID | Fuente de reserva serializada | Fecha y zona |
| --- | --- | --- |

## Documentos

| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |
| --- | --- | --- | --- | --- | --- | --- |

Las rutas son relativas al root. La carpeta debe tener la forma `context/requirements/functional/<DF-ID>` y `Documento principal` almacena sólo el basename de un Markdown directo dentro de ella. ID, carpeta, basename y valor de `df_id` usan siempre `DF-NNN` en mayúsculas; no se normaliza silenciosamente otro casing. Los documentos nuevos usan `<DF-ID>.md`; una migración conserva el basename histórico y lo registra explícitamente. La fuente serializada se conserva después de publicar para que un reintento resuelva el mismo DF. El catálogo permanece en `context/requirements/functional-documents-catalog.md`; la solicitud y su delta viven en un expediente RM separado.
