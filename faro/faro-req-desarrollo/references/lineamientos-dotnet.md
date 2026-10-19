# Lineamientos de desarrollo .NET y C#

## Uso y edición

Leer este archivo junto con los lineamientos comunes sólo para componentes .NET/C#. El usuario puede editar estas reglas sin cambiar `SKILL.md`; el agente sólo las modifica por pedido explícito.

Estas reglas adaptan las guías del paquete NZT aportado por el usuario. Son valores por defecto, no una orden de migrar proyectos existentes: prevalecen sus instrucciones explícitas, arquitectura y convenciones establecidas. Aplicar únicamente las secciones que correspondan al componente y a la tarea.

## Plataforma y convenciones

- Confirmar `TargetFramework`, versión de C#, SDK y paquetes en los archivos reales del proyecto y su configuración. No actualizar versiones para hacer compilar un ejemplo o habilitar una preferencia de estilo.
- Reutilizar los nombres del dominio y su glosario. Para nombres nuevos sin convención previa, usar inglés; los textos visibles conservan el idioma y contenido del contrato.
- No cambiar el ORM, el patrón de endpoints, el modelo de dominio ni la estrategia de resultados dentro de una tarea que no autorice esa decisión.

## Estilo de C#

- Usar tipos explícitos en declaraciones, variables de `foreach` y resultados LINQ; no usar `var` como convención por defecto.
- Usar constructores convencionales. Para dependencias inyectadas, declarar campos `readonly` y asignarlos en el constructor; no introducir constructores primarios por defecto.
- Mantener un tipo principal por archivo y nombrar el archivo como el tipo. Usar namespaces de archivo cuando la versión y las convenciones lo permitan.
- Declarar clases `sealed` por defecto cuando no exista un uso de herencia o un requisito del framework que lo impida. No cerrar una jerarquía existente ni impedir proxies por aplicar esta preferencia.
- Agrupar miembros en este orden: tipos anidados, constantes y campos estáticos, campos de instancia, constructores, propiedades y métodos. Mantener grupos contiguos; respetar el orden propio de DTOs y modelos de dominio existentes.
- Escribir los `using` necesarios en el archivo. No agregar `global using`, `using static` o alias como atajo de estilo; respetar las excepciones justificadas y las convenciones del repositorio.
- No cambiar `ImplicitUsings`, `Nullable` ni otras opciones del proyecto para imponer estas reglas. No editar código generado para que siga una preferencia manual.
- Resolver los valores nulos explícitamente. No usar el operador de supresión `!` ni desactivar advertencias para ocultar casos no tratados; no introducir nuevas advertencias de nullabilidad.
- Preferir guard clauses y retornos claros para evitar anidamientos innecesarios. Mantener condiciones, conversiones y asignaciones legibles, sin concentrarlas en expresiones complejas.
- Para tipos de datos nuevos, preferir propiedades explícitas; usar `record`, clase o `struct` según la semántica y el contrato existentes, sin convertir DTOs públicos sólo por estilo.
- Evitar reflexión escrita a mano para acceder a propiedades conocidas. Usar contratos tipados; si una integración exige reflexión, justificar la excepción antes de incorporarla.

## Async, cancelación y LINQ

- Mantener `async`/`await` de extremo a extremo en operaciones asíncronas. No bloquear con `.Result`, `.Wait()` ni `.GetAwaiter().GetResult()`.
- Recibir y propagar `CancellationToken` cuando el llamador y la API lo permitan, incluidos acceso a datos y clientes externos. No perderlo en una capa intermedia ni convertir una cancelación en un rechazo de negocio.
- No usar `async void` para operaciones de aplicación; limitarlo a handlers de eventos que realmente requieran esa firma.
- Elegir los operadores LINQ por intención y evitar enumeraciones repetidas. No materializar antes de filtrar ni cambiar el orden de filtros, agrupaciones o paginación si modifica el resultado.
- Devolver una colección vacía en lugar de null sólo cuando el contrato no distinga esos estados; no cambiar su significado silenciosamente.

## Arquitectura y dominio

- En Clean Architecture, respetar las dependencias hacia el núcleo y la composición existente. No agregar proyectos, capas o carpetas vacías para reproducir una plantilla.
- En arquitectura hexagonal, mantener el núcleo independiente de los adaptadores y conectar las implementaciones mediante los contratos y la composición adoptados.
- En vertical slice, mantener juntas las piezas de una operación y no depender de detalles internos de otra slice. No convertir incidentalmente el módulo en una arquitectura por capas.
- Si existe un modelo DDD, preservar encapsulación, invariantes y límites de agregados. No abrir setters para facilitar persistencia ni introducir value objects, eventos o IDs tipados sin necesidad aprobada.
- Si el modelo es anémico, mantener las reglas en las operaciones de negocio existentes. No migrar parcialmente a un modelo rico ni duplicar una regla entre ambos estilos.
- Distinguir modelo de dominio y persistencia: DDD no obliga a usar repositorios. Si hay acceso directo, no introducir repositorios o Unit of Work sólo por plantilla; si existen, respetar sus responsabilidades y límites de guardado.

## Entradas, operaciones y errores

- Mantener Minimal APIs o Controllers según el componente. No trasladar negocio a los endpoints ni cambiar rutas, binding, cuerpos, estados HTTP o serialización sin autorización.
- Validar la entrada antes de consultar estado o producir efectos, usando el mecanismo existente. Derivar formatos, límites y mensajes del contrato, no de suposiciones del desarrollador.
- Distinguir validación de forma, invariantes de dominio y reglas dependientes de datos. Los mappers transforman datos; no consultan persistencia ni deciden negocio o respuestas HTTP.
- Reutilizar los DTOs y la estrategia de mapping apropiados al contrato. No exponer entidades ni agregar campos para simplificar la implementación.
- Si el proyecto usa `Result` o un equivalente, representar con él los fallos esperables y comprobar éxito antes de leer el payload. No instalar otro patrón de resultados ni copiar los tipos de NZT como contrato nuevo.
- Mantener la traducción a HTTP donde el proyecto la haya definido. No introducir acoplamiento a HTTP en el dominio o aplicación si su arquitectura lo prohíbe, ni cambiar los códigos de un resultado existente.
- Tratar como conocidos sólo los conflictos identificados de manera concreta. No convertir cualquier excepción de persistencia, timeout o cancelación en un error de duplicado; conservar los fallos inesperados en el manejo centralizado.

## EF Core, sólo si el componente lo utiliza

- Mantener `DbContext` dentro de su scope. No capturarlo en un singleton, compartirlo entre operaciones concurrentes ni usarlo en tareas que sobrevivan al scope.
- Distinguir lecturas de entidades destinadas a modificación. Usar consultas sin tracking cuando corresponda, sin cambiar la configuración global incidentalmente.
- Filtrar, proyectar, ordenar y paginar en la base antes de materializar. Evitar N+1 y cargas de columnas o relaciones que la operación no necesita.
- No usar `AsEnumerable` o `ToListAsync` para ocultar una consulta que no se puede traducir. Verificar el comportamiento con el proveedor y la versión reales; parametrizar SQL manual cuando sea necesario.
- Usar una comprobación de existencia en lugar de cargar o contar todas las filas cuando sólo se necesita saber si hay alguna. Respetar el límite de persistencia adoptado al devolver consultas o resultados.
- Paginar con un orden determinista y un desempate único. Mantener tamaño, filtros, conteos y semántica de página según el contrato, sin truncamientos ocultos.
- Modificar entidades tracked sin marcar indiscriminadamente todos sus campos como modificados. Evitar `SaveChangesAsync` por fila y coordinar el guardado de una operación atómica.
- Usar una transacción explícita sólo cuando la operación lo requiera. Un guardado no protege automáticamente lecturas previas ni efectos externos; no incluir llamadas remotas en una transacción de base.
- Para unicidad, alinear comprobación y restricción con el tenant, la normalización, los nulos y el borrado lógico. Excluir el propio registro al actualizar y considerar carreras concurrentes: un pre-check no reemplaza la restricción de base.
- Reconocer conflictos de escritura mediante códigos y restricciones conocidos del proveedor, no mediante texto localizado de la excepción. Mantener el mismo tratamiento de negocio para el conflicto reconocido.
- Usar operaciones bulk sólo si no omiten invariantes, eventos, auditoría o controles de concurrencia necesarios; considerar también el estado del tracker y las filas afectadas.
- No calcular una regla de todo un agregado sobre una colección cargada parcialmente. Obtener la información suficiente y respetar la estrategia de concurrencia de la operación.
- Revisar mappings, precisión, relaciones e índices contra el esquema y las consultas reales. Generar migraciones con el tooling del proyecto y revisar drops, renombres y tratamiento de datos; generarlas no autoriza aplicarlas a un ambiente compartido.

## Seguridad y pruebas

- Obtener identidad y ámbito de acceso del contexto confiable del servidor. Un ID, header o tenant enviado por el cliente no acredita permiso sobre un recurso.
- Autorizar antes de exponer datos o producir efectos. Cubrir también listados, conteos, exportaciones y relaciones padre-hijo; los jobs no constituyen un bypass.
- Aplicar la disciplina de pruebas de los lineamientos comunes con el framework y runner existentes. No imponer xUnit, NUnit, MSTest, mocks, contenedores ni librerías nuevas sólo por aparecer en una guía.
- Probar comportamiento, límites y rechazos del alcance, incluida la ausencia de escrituras o efectos externos cuando una operación falla.
- Verificar traducción SQL, restricciones, concurrencia o migraciones con el proveedor real en un entorno de prueba autorizado cuando sean parte del cambio. Mocks o EF InMemory no acreditan esos aspectos.
- Obtener los comandos de compilación, pruebas y análisis del repositorio o de CI. Registrar lo ejecutado y lo que quedó sin verificar; no confundir compilación con prueba de integración.

## Procedencia de la adaptación

Fuentes del ZIP `nzt-ai 3.zip`, bajo `nzt-ai/`:

- `skills/nzt/build/csharp/SKILL.md`, `csharp/dtos/SKILL.md` y `csharp/linq/SKILL.md`: estilo, nullabilidad, async, DTOs y consultas.
- `skills/nzt/build/backend/dotnet/SKILL.md` y sus guías `architecture/`, `domain/` y `persistence/`: selección por evidencia y alternativas de arquitectura.
- Sus guías `api/`, `endpoints/`, `use-cases/`, `validation/` y `results/`: entradas, operaciones y tratamiento de resultados.
- Sus guías `ef-core/`, `security/` y `testing/`: persistencia, autorización y comprobaciones.
- `skills/nzt/build/tdd/SKILL.md` y `skills/nzt/build/refactor/SKILL.md`: pruebas y preservación de comportamiento; la adopción por defecto de TDD la establece la guía común de FARO.

Se adaptaron las reglas, no los routers ni los contratos específicos de NZT. No hace falta instalar NZT ni conservar el ZIP para usar o editar este archivo.
