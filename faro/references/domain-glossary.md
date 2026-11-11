# Glosario de dominio del workspace

## Alcance y autoridad

`context/glossary.md` conserva el vocabulario propio del sistema: conceptos, siglas, nombres de procesos y distinciones que ayudan a interpretar pedidos futuros. Es conocimiento transversal, no una fase ni una nueva skill. Leerlo en cada interacción FARO, incluidas consultas, reanudaciones e invocaciones directas de especialistas, después de confirmar root y estado y antes de interpretar términos o formular preguntas de dominio. Aplicar esta política aunque la documentación funcional esté deshabilitada.

El glosario no equivale a aprobación funcional ni sustituye DF, RM, CA, arquitectura o autorización. Documentar vocabulario por sí solo implica no crear RM, BUG, TEC, workflow, issue ni work item. Si aparece un cambio real de comportamiento, clasificarlo con el router normal; no esconderlo en una definición. No modificar el código ni renombrar identificadores por actualizar el glosario.

## Consulta y evaluación en cada interacción

1. Fijar el root coordinador del contrato: consultar únicamente su `context/glossary.md`, no el de un repositorio indexado ni otro proyecto. Si FARO está `disabled`, detener FARO; no crear ni actualizar el glosario. Sin contrato, no crear `context/` por este motivo. En bootstrap, preservar el destino vacío hasta completar el scaffold; trasladar las definiciones aportadas al handoff de inicialización, no escribir antes.
2. Si existe el glosario, leer las entradas pertinentes y sus fuentes antes de interpretar el pedido. Buscar también por alias y ámbito; una sigla puede tener significados distintos por módulo. No confundir ausencia de entrada con ausencia del concepto en el sistema.
3. Evaluar si el mensaje aporta un concepto propio, una definición nueva, un alias confirmado, una distinción útil o una corrección. Omitir términos genéricos, detalles efímeros de tareas y menciones repetidas. Si no aporta nada o sólo se consulta una definición conocida, responder sin escritura: sin cambios no escribir ni actualizar fechas por rutina.
4. Para un término desconocido, buscar primero en documentos y fuentes indexadas pertinentes, sin leer secretos ni recorrer todo el proyecto innecesariamente. Si la fuente no es accesible, indicarlo. No deducir el significado por las letras de una sigla, por semejanza con otra ni por conocimiento de otro cliente. Si la ambigüedad afecta el pedido, preguntar sólo lo que falta y no continuar con la parte dependiente; lo independiente puede seguir.
5. Evaluar al cierre si hubo conocimiento sustentado que conservar. La ruta activa mantiene el glosario como tarea documental auxiliar, sin cargar otra especialista ni cambiar `nextRoute`. Para un pedido exclusivamente terminológico, el router puede responder y mantener este archivo y su enlace en el índice sin iniciar un flujo artificial.

## Evidencia, incertidumbre y conflictos

- `CONFIRMADA`: definición explícita del usuario o documento funcional vigente que define el término; registrar fuente localizable, ámbito y fecha. Una definición del usuario confirma vocabulario, no aprueba reglas nuevas de negocio.
- `OBSERVADA`: significado explícitamente documentado en código, pruebas o interfaz, con ruta y símbolo/sección; conservar su carácter observado. Un nombre de clase o pantalla por sí solo no permite inventar su expansión ni una regla funcional.
- `PENDIENTE`: término real cuyo significado completo falta. Mantener `NO DEFINIDO` en lo desconocido; una hipótesis no ocupa el campo de significado como hecho. Registrar pregunta, fuente de la mención e impacto, sin crear un archivo sólo para acumular conjeturas.
- `CONFLICTO`: fuentes incompatibles para el mismo término y ámbito. Conservar las definiciones y ambas fuentes; no reemplazar silenciosamente la anterior ni resolver por antigüedad o frecuencia. Pedir decisión si afecta al trabajo y bloquear sólo esa interpretación.

Preservar la grafía aportada: no normalizar siglas ni corregirlas silenciosamente. Una variante sólo es alias si una fuente la vincula explícitamente al mismo concepto. Si dos módulos usan la misma sigla con otro significado, usar entradas con ámbito distinto; no fusionarlas. Una aclaración confirmada actualiza la entrada y añade al historial el significado anterior, la razón y la fuente de la corrección. Si contradice una baseline funcional, exponer la discrepancia y seguir la ruta funcional correspondiente; no reescribir baselines ni cambiar retrospectivamente aprobaciones o resultados de QA.

## Persistencia proporcional y límites de escritura

Crear `context/glossary.md` desde `faro/templates/glossary.md` sólo cuando haya al menos una definición `CONFIRMADA` u `OBSERVADA` útil, dentro de un workspace válido y una interacción que permita escritura documental. Las entradas pendientes o en conflicto pueden acompañar conocimiento sustentado, claramente separadas. No crear un glosario vacío ni copiar ejemplos de la suite al proyecto.

En espacios existentes, adoptar el archivo bajo demanda sin reinicializar, sin cambiar `contractVersion`, `managedArtifacts`, estado, perfil, aprobaciones ni workflow. Es un artefacto condicional compatible; su ausencia no es defecto del contrato. Al crearlo, añadir una sola referencia con ubicación, descripción y propósito en `context/README.md`; preservar el contenido ajeno. No modificar `AGENTS.md` existente sólo para anunciarlo: las skills centrales ya conocen la ruta. Si existe un glosario previo dentro de otro documento, usarlo como fuente y enlazarlo; no borrarlo ni migrarlo en bloque por iniciativa propia.

Una consulta de significado no autoriza escrituras por sí sola. Una definición o corrección explícita puede registrarse como conocimiento auxiliar salvo restricción de sólo lectura. Doctor, diagnóstico y pedidos de sólo lectura no crean ni actualizan glosario ni índice: informan el hallazgo o proponen la incorporación. No usar este mecanismo para reparar un contrato incompleto, sortear restricciones de la fase o escribir en repositorios externos. Ante un archivo ilegible, un directorio en su lugar o contenido ajeno que no pueda actualizarse sin pérdida, informar y pedir decisión; no sobrescribirlo con la plantilla.

Mantener un único archivo estable, sin sufijos de versión ni archivos por término. Guardar definiciones breves y fuentes precisas, no transcripciones. Para una definición aportada en conversación, registrar la fecha y un extracto mínimo fiel de la definición; añadir ID de sesión/mensaje sólo si está disponible, nunca inventarlo. Las fuentes externas se referencian sin copiar datos sensibles. No incluir secretos, credenciales, datos personales ni información clínica; no copiar a memoria global ni a otro workspace.

El vocabulario de negocio puede aparecer en DF para facilitar su lectura, consistente con el glosario; los localizadores técnicos y la trazabilidad quedan en la investigación interna. No sincronizar automáticamente documentos históricos: conservar las baselines y registrar diferencias relevantes.

## Comprobación antes de cerrar

- Se consultó el glosario existente o se comprobó su ausencia antes de interpretar términos.
- Cada alta o cambio tiene estado, ámbito y fuente; desconocidos y conflictos no se presentan como hechos.
- Si no hubo conocimiento nuevo sustentado, no hubo escritura rutinaria.
- Una creación quedó indexada; una corrección preservó su historial y no sobrescribió contenido ajeno.
- Se respetaron root, sólo lectura, estado y autorizaciones; no se creó trabajo remoto ni se alteró el alcance por registrar vocabulario.
