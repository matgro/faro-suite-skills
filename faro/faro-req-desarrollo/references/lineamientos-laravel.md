# Lineamientos de desarrollo Laravel

## Uso y edición

Leer este archivo junto con los lineamientos comunes sólo cuando el componente a modificar sea Laravel. El usuario puede editar estas reglas sin cambiar `SKILL.md`; el agente sólo las modifica por pedido explícito.

Confirmar Laravel en `composer.json`, contrastar versiones con `composer.lock` y revisar el código del componente. No aplicar estas reglas a cualquier proyecto PHP ni asumir versiones, paquetes o comandos.

## Estructura y responsabilidades

- Respetar la organización y las convenciones del proyecto. No introducir otra arquitectura, una capa de repositorios o un patrón de servicios si el cambio no lo necesita.
- Mantener las entradas HTTP enfocadas en recibir, validar, autorizar y delegar al flujo existente. Reutilizar los servicios, acciones u operaciones de negocio ya definidos.
- Ubicar cada regla de negocio en un único lugar del backend. No mantener versiones distintas de esa regla en controladores, modelos, formularios o plantillas.
- Separar validación de entrada y autorización. Reutilizar Form Requests, Policies o Gates cuando sean los mecanismos adoptados por el proyecto; no instalarlos ni reorganizar todo sólo para cumplir una preferencia.
- Respetar el contrato de respuesta y su serialización existente, incluidos Resources si se utilizan. No agregar campos ni exponer atributos internos de modelos por comodidad.

## Persistencia y datos

- Si el proyecto usa Eloquent, revisar relaciones, claves, casts y restricciones reales antes de cambiar modelos o consultas. No inferir el esquema únicamente a partir de un nombre.
- Filtrar y seleccionar los datos necesarios antes de materializar una consulta. Revisar accesos repetidos a relaciones y evitar N+1 con la estrategia que corresponda al caso.
- Respetar el orden, los filtros y la paginación del contrato; no agregar límites arbitrarios ni cargar todo para filtrar después en memoria.
- Controlar explícitamente qué atributos se escriben. No asignar indiscriminadamente todo el contenido del request a un modelo.
- Usar una transacción cuando el caso requiera atomicidad entre escrituras. Mantenerla corta y no incluir llamadas remotas dentro de ella.
- Crear migraciones sólo cuando el cambio de esquema esté autorizado. Revisar compatibilidad, tratamiento de datos y reversibilidad; ejecutar sobre un ambiente compartido o productivo requiere autorización específica.

## Integraciones, configuración y errores

- Reutilizar el cliente HTTP, las colas y las políticas de reintento existentes. Definir tiempos de espera y evitar reintentos que dupliquen operaciones no idempotentes.
- Acceder a parámetros operativos mediante la configuración del proyecto. Mantener la lectura de variables de ambiente en su capa de configuración, sin dispersarla por la lógica de negocio.
- Respetar el manejo centralizado de errores. No convertir una excepción en una respuesta exitosa, ni devolver su detalle interno al consumidor.
- No registrar tokens, credenciales ni payloads con datos sensibles. Conservar el contexto no secreto necesario para diagnosticar la operación.

## Blade, Livewire y frontend

- Antes de escribir markup, revisar `/template`, `resources/views/template/components` y las pantallas del mismo dominio cuando existan.
- Reutilizar componentes y convenciones visuales, pasando por `faro-ux`. No duplicar markup ni crear una nueva biblioteca de componentes para la tarea.
- No asumir que Livewire está instalado; usarlo sólo si forma parte del componente y respetar la versión verificada.
- Mantener las reglas de negocio en el backend. Las validaciones de experiencia de usuario no sustituyen validación ni autorización del servidor.
- Respetar el mecanismo de escape de las plantillas y revisar cualquier salida de contenido sin escapar.

## Pruebas y comprobaciones

- Aplicar el ciclo TDD definido en los lineamientos comunes con PHPUnit o Pest según lo que use el repositorio; no exigir ambos ni agregar dependencias sin autorización.
- Probar la regla modificada y los casos de autorización, validación y error que pertenezcan al alcance.
- Cuando el cambio afecte consultas o escrituras, cubrir su comportamiento con el esquema y el motor adecuados a la prueba; no dar por validada la persistencia con mocks solamente.
- Aislar datos y efectos externos. No enviar mensajes, ejecutar compras ni modificar datos reales durante una prueba sin autorización.
- Obtener los comandos de pruebas, formato y análisis desde `composer.json`, documentación o CI. Ejecutar sólo las herramientas disponibles y registrar resultados o bloqueos.

## Procedencia

Base adaptada a las reglas de arquitectura y frontend de `faro-arq-laravel` y a los lineamientos comunes de esta skill. No deriva de NZT ni presupone una versión de Laravel.
