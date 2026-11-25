---
schema_version: "2.0"
catalog_kind: "FARO_WORK_ITEMS"
---

# Catálogo de expedientes FARO

Este catálogo localiza expedientes y conserva reservas y referencias remotas. No es una fuente de estado, prioridad ni asignación; esos datos pertenecen al gestor externo configurado.

## Reservas

| ID | Tipo | Fuente de reserva serializada | Fecha y zona |
| --- | --- | --- | --- |

## Expedientes

| ID | Tipo | Ruta canónica | Documento principal | Fuente de reserva serializada | Proveedor | ID remoto | URL remota | Relacionados |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |

Las rutas son relativas al root. La carpeta debe tener la forma `context/requirements/work-items/<ID>` y `Documento principal` almacena sólo el basename de un Markdown directo dentro de ella. Las unidades nuevas usan `<ID>.md`; una migración conserva el basename histórico y lo registra explícitamente. Al publicar se conserva la fila de reserva como binding histórico y su fuente debe coincidir con la del expediente, para que un reintento resuelva el mismo ID. RM, BUG y TEC comparten un único namespace de fuente: la misma evidencia de intake no puede reservar dos clasificaciones. No registrar aquí estado, prioridad, asignación, sprint, iteración, área ni un backlog paralelo.
