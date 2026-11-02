# Lineamientos de desarrollo Blazor

## Uso y selección por evidencia

Leer junto con los lineamientos comunes y .NET sólo cuando el componente modificado use Blazor. Esta guía complementa `faro-ux`: no define pantallas, textos, reglas de negocio ni una arquitectura nueva. Las instrucciones locales y la arquitectura aprobada prevalecen; no reorganizar código existente sólo para ajustarlo a estos valores por defecto.

- Confirmar `TargetFramework`, SDK y paquetes, componentes `.razor`, arranque, registros de servicios y configuración real de renderizado. Razor/Blade, MVC o Razor Pages no implican Blazor por compartir conceptos de markup.
- Distinguir Blazor Server o WebAssembly existentes de una Blazor Web App con render modes. No migrar un modelo al otro ni actualizar .NET para habilitar una API de esta guía.
- Obtener de la arquitectura y del código el modo efectivo, sus límites de interactividad y si hay prerenderizado. Aplicar sólo el modo y las secciones que afecte la tarea; no cambiar el modo por preferencia ni leerlo como sinónimo de prerenderizado.
- Respetar `inline` (`@code`) o `code-behind` (`.razor.cs` parcial con nombre y namespace coincidentes) según el proyecto. Resolver una ambigüedad real antes de crear componentes, sin inventar un nuevo documento obligatorio.
- Revisar el catálogo, sistema de diseño y componentes del dominio mediante `faro-ux`; reutilizar la biblioteca adoptada antes de crear controles propios. No instalar MudBlazor, Radzen u otra biblioteca por aparecer en un ejemplo.

## Componentes, estado y límites

- Mantener directivas, markup y código en un orden legible conforme a la convención existente. Agregar los `@using` necesarios en el componente; no ampliar `_Imports.razor` incidentalmente para una necesidad local.
- Declarar entradas mediante `[Parameter]`; usar `[EditorRequired]` cuando corresponda, sin confundir su diagnóstico de diseño con validación en ejecución. El receptor no muta los parámetros ni el estado que pertenece al padre.
- Comunicar cambios hacia el padre con `EventCallback<T>` y esperar `InvokeAsync`. No crear estado estático o un servicio nuevo sólo para transportar un evento.
- Usar `@key` estable y único entre hermanos cuando una lista admita inserciones, eliminaciones o reordenamientos; no usar el índice como identidad del elemento.
- Inyectar cada dependencia una sola vez: `@inject` en inline o propiedades `[Inject]` en code-behind según el patrón local. No duplicarla entre parciales ni ocultar una dependencia no inicializada con `!`; tratar su disponibilidad explícitamente. Los clientes y servicios ordinarios conservan la inyección por constructor de la guía .NET.
- Separar presentación y transporte: por defecto, el componente usa el cliente tipado o servicio existente de su funcionalidad, no construye URLs ni interpreta respuestas HTTP. Reutilizar contratos y manejo de resultados del proyecto; no introducir otro `Result`, wrappers, DTOs o clientes por plantilla. Una arquitectura existente diferente requiere una excepción explícita, no una migración incidental.
- Mantener las reglas de negocio y autorización en el backend. Mostrar sus rechazos mediante el mecanismo del proyecto, distinguiendo error esperado, cancelación y fallo técnico sin exponer excepciones crudas.
- Cubrir carga, vacío, error y datos disponibles según el diseño aprobado; una cancelación o timeout no debe dejar carga infinita. No inventar textos ni estados de negocio.

## Ciclo de vida, asincronía y limpieza

- Usar `OnInitialized{Async}` para preparación independiente de parámetros, sin escrituras o efectos de negocio: el prerenderizado puede crear otra instancia y repetir la inicialización.
- Cargar datos dependientes de parámetros en `OnParametersSetAsync`, comprobando qué clave cambió. No duplicar la misma carga en inicialización ni permitir que una respuesta antigua reemplace la de una navegación o búsqueda posterior.
- Dejar un estado renderizable antes de cada `await`. Cuando corresponda, cancelar la carga anterior y propagar el token por el cliente; antes de asignar el resultado comprobar que sigue vigente y que el componente no fue descartado. Cancelar no garantiza que nunca llegue una respuesta.
- No bloquear con `.Result` o `.Wait()` ni usar `Task.Run` como supuesto arreglo del hilo de UI. Si se necesita trabajo paralelo real, comprobar las capacidades y restricciones del runtime adoptado antes de proponerlo.
- Ejecutar JS dependiente del DOM en `OnAfterRenderAsync`, cuando haya renderizado interactivo, con `firstRender` o una condición acotada. No asumir que se ejecuta durante SSR estático o prerenderizado; evitar ciclos de `StateHasChanged`.
- Despachar notificaciones externas mediante `InvokeAsync`, observando sus errores. Liberar suscripciones, temporizadores, recursos JS y fuentes de cancelación que pertenezcan al componente en `Dispose`/`DisposeAsync`; no solicitar renderizado al descartarlo.
- No modificar por JS el DOM que administra Blazor ni asumir que el circuito sigue conectado durante la limpieza. Tratar la desconexión esperable de JS interop sin ocultar otros fallos; usar el mecanismo de limpieza apropiado al recurso.

## Formularios

- Usar un modelo de edición propio, sin enlazar indiscriminadamente una entidad o respuesta API. Reutilizar el mecanismo de validación adoptado y no agregar campos al contrato para facilitar el binding.
- En `EditForm`, proporcionar `Model` o `EditContext`, no ambos. Elegir `OnValidSubmit`/`OnInvalidSubmit` o validación manual con `OnSubmit`, sin mezclar enfoques.
- Validar forma, formato y límites de entrada en UI y mostrar los errores por campo con labels accesibles; las reglas de negocio y comprobaciones de seguridad se validan en el servidor.
- Impedir envíos simultáneos con una guarda en el handler y deshabilitar la acción mientras esté en curso; restaurar el estado tanto ante éxito como ante error. Esto no reemplaza la idempotencia o concurrencia del backend.
- En formularios SSR estáticos, usar identificación de formulario y binding compatibles con la versión real (`FormName` y `[SupplyParameterFromForm]` cuando apliquen). Inicializar el modelo sólo si falta, sin sobrescribir el POST. No asumir callbacks .NET o validación interactiva al escribir: comprobar la capacidad de la versión y configuración adoptadas.
- Mantener antiforgery en formularios y endpoints que lo requieran; no desactivarlo para resolver un error de envío. Comprobar tokens, middleware y destino del POST; usar `Enhance` sólo en endpoints compatibles.

## Renderizado: aplicar sólo el caso evidenciado

### Server / Interactive Server

- Mantener el estado de cada usuario en su ámbito/circuito, nunca en un singleton compartido entre usuarios. Considerar latencia por interacción y memoria por circuito.
- Tratar reconexión y pérdida del circuito como situaciones distintas: la recuperación del estado no está garantizada tras expiración, reinicio o recarga completa. Un circuito o su persistencia no sustituyen almacenamiento durable.
- No acceder directamente a la base desde una pantalla por el solo hecho de ejecutar en servidor; respetar el límite de aplicación adoptado y los clientes/servicios existentes.

### WebAssembly / Interactive WebAssembly

- Tratar código, configuración y estado enviados al navegador como inspeccionables por el usuario: no incluir secretos, credenciales privilegiadas ni datos fuera de su autorización. El backend no confía en validaciones del cliente.
- Medir descarga y arranque con caché fría antes de añadir dependencias u optimizar carga. No asumir soporte de hilos o acceso a servicios exclusivos del servidor.
- Resolver dependencias también en el servidor si existe prerenderizado. WebAssembly standalone no tiene una pasada de prerenderizado del servidor por defecto.

### Interactive Auto

- Verificar funcionamiento tanto en servidor como en navegador y registrar dependencias en ambos hosts con el lifetime adecuado. El código descargable no puede depender de base de datos, secretos o servicios exclusivos del servidor.
- No modelar Auto como migración de una instancia en ejecución entre hosts: la selección ocurre al crear la instancia; comprobar primera visita y visitas posteriores con recursos cacheados.
- Respetar los límites entre raíces estáticas e interactivas: no anidar modos interactivos incompatibles ni cruzar la frontera con delegates o `RenderFragment` no serializables. No asumir que los valores en cascada atraviesan esa frontera automáticamente.
- Verificar el host efectivo con las APIs disponibles en la versión del proyecto, no deducirlo sólo del render mode configurado.

### SSR estático

- No asumir handlers .NET de eventos DOM, circuito interactivo ni `OnAfterRender{Async}`. Las acciones se resuelven mediante navegación o POST y una nueva petición; streaming o navegación mejorada no convierten la página en interactiva.
- Resolver lecturas en el ciclo inicial sin efectos de negocio. Si el requerimiento exige interactividad, volver al análisis técnico para definir su límite; no habilitarla globalmente por conveniencia.

## Prerenderizado y estado inicial

- Comprobar si existe prerenderizado en cada host y ruta; no asumir que inicialización ocurre exactamente una vez o exactamente dos. Probar carga completa y navegación interna.
- Reutilizar la lectura inicial mediante la persistencia de estado apropiada a la versión (`PersistentComponentState` o APIs declarativas disponibles), cargando sólo cuando falta y actualizando si cambia su clave. No forzar una API reciente ni desactivar prerenderizado para esconder una carga duplicada.
- Persistir sólo datos necesarios y autorizados. Estado enviado a WebAssembly o Auto es visible en el navegador; no incluir secretos ni estado de otro usuario.
- Verificar los registros y lifetimes que exija la API de servicios persistentes adoptada en cada host; no generalizar que todo servicio del navegador debe ser singleton. Liberar también las suscripciones a persistencia cuando corresponda.
- Tratar streaming, persistencia y render mode como decisiones distintas. Un indicador de carga por sí solo no evita la espera del prerenderizado; medir el caso real antes de cambiar su estrategia.

## Organización y rendimiento

- Mantener la arquitectura existente. Si está aprobada vertical slice, agrupar por funcionalidad páginas, componentes, clientes y DTOs, respetando sus límites y el inventario compartido; no crear carpetas vacías, duplicar contratos o partir una funcionalidad entre hosts incompatibles sólo para reproducir NZT.
- Ubicar los componentes que puedan ejecutarse en navegador en proyectos/ensamblados que éste pueda cargar, según la solución real. No imponer dos proyectos ni nombres `.Client` a soluciones que ya tienen otra composición válida.
- Medir antes y después con datos representativos y build publicado. Elegir paginación o `Virtualize` según evidencia y accesibilidad; un `ItemsProvider` respeta inicio, cantidad, cancelación y total sin cargar todo el conjunto.
- Usar debounce/cancelación para búsquedas y throttle de eventos frecuentes sólo cuando corresponda al comportamiento requerido y al coste medido; en Server, limitar eventos antes de cruzar el circuito cuando sea necesario.
- No introducir `ShouldRender`, `IsFixed`, sustitución de componentes por `RenderFragment`, ni overrides de `IHandleEvent`/`SetParametersAsync` por intuición. Justificar la mejora y preservar notificaciones, renderizado, identidad y propagación de errores. `@key` no elimina por sí mismo renders o asignaciones.

## Verificación proporcional a la tarea

- Ejecutar build, pruebas y analizadores existentes; no instalar otro framework de componentes o E2E sólo por esta guía. Distinguir pruebas de contrato de FARO de una aplicación Blazor realmente ejecutada.
- Probar los cambios de parámetros, respuestas fuera de orden, cancelación y descarte cuando afecten la tarea; para formularios, envío válido/inválido/repetido y fallo remoto.
- Ejercitar los hosts adoptados y sus límites: desconexión/reconexión en Server, arranque con caché fría en WebAssembly, primera visita y host navegador en Auto, POST y recarga en SSR, estado ausente/restaurado en prerenderizado.
- Registrar qué se ejecutó, qué guía se aplicó y cualquier limitación real en la evidencia existente. No declarar probados navegador, accesibilidad, reconexión o performance sólo por compilar.

## Procedencia y licencia

Adaptación de NZT, repositorio `https://github.com/Ezefeola/nzt-ai`, rama `main`, commit `92af9c5` inspeccionado. Fuentes: `skills/nzt/build/frontend/blazor/SKILL.md`, sus nueve referencias `components.md`, `forms.md`, `architecture-vertical-slice.md`, `render-server.md`, `render-webassembly.md`, `render-auto.md`, `render-static.md`, `prerendering.md` y `performance.md`; también `skills/nzt/build/references/frontend-{components,forms,rendering,performance,architecture-vertical-slice}.md`.

Se adaptan reglas al contrato FARO y a las convenciones del proyecto; no se copian routers, rutas `Docs/`, estados de workflow ni autorizaciones de NZT. No se requiere instalar NZT. Las APIs dependientes de versión se comprueban en la documentación oficial de ASP.NET Core correspondiente al `TargetFramework` antes de usarlas.

Aviso de la fuente adaptada:

MIT License

Copyright (c) 2026 Ezefeola

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
