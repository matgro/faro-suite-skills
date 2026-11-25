# Control de calidad del RM

Aplicar al contenido real y a sus fuentes; no marcar automáticamente.

## Fidelidad
- [ ] Solicitud, actor, acción y alcance se preservan.
- [ ] Hechos confirmados tienen fuente localizable.
- [ ] Código aparece como OBSERVADO, no como aprobación.
- [ ] Reglas no agregan estados, límites o valores por intuición.
- [ ] Propuestas y contradicciones están separadas mediante PD.

## Definición y trazabilidad
- [ ] ID, directorio, primario y catálogo coinciden; el expediente resuelve por el CLI central y no está congelado.
- [ ] RF observables, RN de negocio, RNF/RES medibles si aplican.
- [ ] CA verificables sin requerimientos añadidos.
- [ ] PD indica impacto, fase, bloqueo, estado y evidencia de resolución.
- [ ] IDs estables; cada elemento implementable enlaza fuente y CA.
- [ ] READY_FOR_REVIEW no tiene PD bloqueantes.
- [ ] APPROVED identifica versión, persona, momento y evidencia humana.
- [ ] La matriz de conocimiento durable identifica DF/producto, arquitectura, operaciones y referencia, o justifica `NO_APLICA`.
- [ ] Estado, prioridad y asignación no se duplicaron desde el gestor remoto.

Resultado: APTO_PARA_REVISION / REQUIERE_DEFINICION. No es aprobación ni validación de código.
