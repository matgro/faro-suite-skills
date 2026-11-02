# Versionado de aplicaciones por arquitectura

## Autoridad y fuente única

La versión de aplicación identifica el producto entregado; no es la versión del framework, de FARO, del contrato de workspace ni de un RM. Un tag identifica una revisión Git, pero por sí solo no actualiza la versión que ejecuta o muestra la aplicación. Mantener una sola fuente autoritativa por componente o conjunto que se versione junto; los demás valores son derivados verificables, nunca números decididos por separado.

- Arquitectura descubre el mecanismo existente, sus lectores y build/CI, documenta hechos y propone una política; no modifica código, no ejecuta builds ni migra mecanismos por iniciativa propia.
- La política aprobada se conserva en `context/requirements/project-profile.md`, sección `Versionado de aplicaciones`. Una ausencia no bloquea la inicialización ni convierte un workspace válido en incompleto. Antes de la primera entrega versionada, resolver los campos necesarios sin reinicializar y sin cambiar estado o aprobaciones ajenas; no modificar `contractVersion`.
- `faro-entrega` aplica cambios de valores de versión sólo en fuentes/derivados existentes y autorizados. No implementa lectores, pantallas, endpoints, scripts, pipelines ni nuevos archivos de configuración. Si falta el mecanismo o hay que migrarlo, pedir autorización y pasar por análisis/desarrollo autorizado; una orden de entregar no autoriza ese trabajo adicional.
- El root del workspace contiene la política y evidencia; los archivos de aplicación sólo se actualizan en el repositorio/componente exacto cuyo cambio y entrega fueron autorizados. Nunca editar repositorios indexados sólo porque aparezcan en arquitectura.

## Política por componente

Completar el bloque de la plantilla de perfil con evidencia, sin copiar secretos. Registrar componente, repositorio/root autorizado, stack, conjunto de versionado, fuente (archivo y clave exacta o generador existente), formato, lectores, destinos derivados, comandos observados de edición/verificación/build/caché, tag/remoto y permisos por operación/ambiente. Conservar la fuente de autorización y sus límites. `NO APLICA` se justifica; `PENDIENTE` no habilita escrituras.

Modos de decisión:

- `CONFIRMAR_POR_ENTREGA` es el valor por defecto: proponer el número según impacto acumulado y confirmar sólo lo pendiente, junto con tag/publicación, como define `faro-entrega/references/versionado-y-tags.md`.
- `AUTOMATICA` requiere autorización persistente explícita con esquema de incremento, impactos permitidos (por ejemplo, PATCH/MINOR), prereleases, componentes y acciones incluidas. Sólo dentro de esos límites se calcula y aplica la siguiente versión sin preguntar otra vez. Un impacto dudoso, MAJOR no permitido o una colisión devuelve a confirmación humana. La política no autoriza desplegar, publicar tags, operar en producción o iniciar entregas por sí sola: cada acción debe estar cubierta por la autorización vigente.

Automatizar la actualización no significa incrementar por cada interacción. Distinguir política de versionado y permiso para ejecutar una entrega concreta. Conservar el esquema existente si no es SemVer. No imponer SemVer a números técnicos de build ni a APIs públicas con otra política.

## Selección por arquitectura

### Laravel

Si no hay un mecanismo acordado, proponer un valor literal versionado en Git en `config/app.php`, clave `version`, consumido con `config('app.version')`. Es una convención FARO propuesta para la aplicación, no una clave de producto que Laravel proporcione automáticamente. La primera incorporación y conexión de lectores requiere desarrollo autorizado; una entrega posterior sólo cambia el valor existente.

La fuente de versión no depende de `env('APP_VERSION')`: no leer ni escribir `.env` ni registrar sus valores. Para este esquema no crear `VERSION` como segunda fuente ni mantener otro número manual en Blade, Livewire, frontend o contenedor. Si existe `config/version.php`, un generador de CI u otro mecanismo, documentarlo y conservarlo hasta que se autorice una adaptación. Un lector actual basado en env no se sustituye silenciosamente durante la entrega: registrar la dependencia sin abrir `.env` y proponer su migración.

Editar sólo la clave de versión, sin ejecutar PHP para extraerla ni volcar configuración completa. Verificar después mediante los comandos/pruebas seguros del proyecto. Si utiliza configuración cacheada, registrar el paso de regeneración en el proceso de despliegue autorizado (habitualmente `php artisan config:cache`); no ejecutarlo durante discovery ni cachear configuración de producción dentro de un artefacto con secretos. Comprobar el valor efectivo tras desplegar, no sólo el archivo. Reiniciar procesos persistentes o invalidar cachés sólo según procedimiento y permisos aprobados.

### .NET y Blazor

Proponer `Version` en el `.csproj` del componente si se versiona solo, o en `Directory.Build.props` si un conjunto de proyectos comparte realmente el ciclo de release. Identificar importaciones, condiciones, `VersionPrefix`/`VersionSuffix`, herramientas de versionado y overrides de CI: un valor XML no prueba el valor efectivo de MSBuild. No crear otra fuente si el proyecto ya usa un generador.

Registrar el mapeo de `Version`, `FileVersion`, `AssemblyVersion` e `InformationalVersion` según SDK y configuración reales. No reemplazar ciegamente `AssemblyVersion`: puede haber una política de compatibilidad independiente y los valores numéricos no admiten todos los sufijos SemVer. Los datos Git añadidos a `InformationalVersion` son metadata derivada; verificar versión de producto y revisión según ese mapeo, sin exigir igualdad textual con un tag que incluye prefijo o sufijo de build.

En Blazor, la versión visible se obtiene de la aplicación/assembly objetivo o de metadata generada desde la misma fuente. Distinguir host y cliente WebAssembly si se entregan por separado; no asumir que un helper en otra biblioteca devuelve la versión del producto correcto. No introducir un número manual en `appsettings.json` ni en la UI como segunda fuente. Un lector ausente se implementa en desarrollo, no al taguear. Verificar también caché del cliente/service worker si forma parte del despliegue aprobado; no declarar actualizado un navegador que aún sirve el artefacto anterior.

### Otros stacks y aplicaciones móviles

Inspeccionar el manifiesto nativo y la cadena real de build/distribución; no inventar comandos, archivos ni propiedades por el nombre del framework. Identificar si `package.json` pertenece al producto, a tooling o a un frontend que se entrega por separado antes de proponer cambios. Distinguir versión visible, versión de paquete, build number y requisitos de una tienda. Conservar restricciones y monotonía de build que declare el proyecto; no incrementar todos los manifests ni todos los componentes de un monorepo por una entrega parcial.

## Una entrega, una versión: idempotencia

Registrar la preparación en el artefacto de entrega/tarea existente (y una referencia en `workflow.notes` sólo si hay workflow activo), sin un archivo nuevo obligatorio. Campos mínimos: identificador de entrega, componente, base/revisión, versión anterior, versión objetivo acordada, tag si aplica, operaciones autorizadas, SHA final, artefacto/digest, ambiente y evidencia real. No agregar ese registro efímero a la fuente de versión del producto ni duplicar el valor actual en el perfil como otra autoridad.

- Nueva entrega versionada: asignar versión una vez, dentro de la política; no incrementar por cada commit, push, PR o comando de deploy.
- Reintento: recuperar versión objetivo y resultado de pasos anteriores. Si la fuente ya coincide, verificar en lugar de incrementar; si hay cambios inesperados, detener. Reconciliar con Git/CI/remoto para no depender sólo de un registro que pudo faltar tras un fallo.
- Si CI gobierna la versión, FARO no la edita en paralelo. Designar un único escritor y usar la serialización/lock del proyecto para evitar que entregas concurrentes asignen el mismo número. Sin reserva o protección suficiente, detener la automatización concurrente y resolver la colisión.
- Promoción staging → producción: usar el mismo artefacto y digest; conservar versión. No reconstruir sólo para cambiar ambiente. Si el mecanismo actual exige builds distintos, declarar esa limitación y obtener una política explícita; no afirmar promoción del mismo artefacto.
- Rollback: restaurar el artefacto anterior identificado y verificar su versión efectiva. No inventar una versión nueva ni reescribir el tag histórico; tampoco revertir datos sin autorización específica.
- Una entrega explícitamente sin versión o sin tag es válida dentro de su alcance. No modificar la aplicación por un commit de documentación. Cambiar contenido de un artefacto ya publicado exige otra entrega/versionado según política, no reutilizar el tag.

## Secuencia de entrega y comprobación

1. Confirmar componente/root, política, alcance e impacto acumulado, versiones local/efectiva conocida y tags remotos. Verificar que la fuente es la declarada, que se permite editarla y que no hay cambios ajenos en la región. No normalizar valores desconocidos ni sobrescribirlos para que encajen.
2. Resolver la versión objetivo una sola vez. Actualizar únicamente la fuente y los derivados autorizados usando el procedimiento probado del proyecto. No ejecutar bump tools que creen commits/tags, instalen dependencias o alteren otros componentes por efectos implícitos.
3. Leer de nuevo las claves modificadas, revisar diff y ejecutar validaciones; abortar el cierre ante discrepancias. Ante fallo, no hacer rollback ciego del working tree ni descartar cambios ajenos: informar qué quedó preparado.
4. Crear commit/tag anotado únicamente cuando corresponda a la autorización; verificar que el tag apunta al SHA validado. Construir/empaquetar desde ese SHA con los valores efectivos acordados y registrar artefacto y digest. Si CI construye al publicar el tag, registrar el fallo real del build y no declarar la aplicación entregada sólo porque el tag existe. No mover un tag para corregirlo.
5. Desplegar sólo en ambiente autorizado y comprobar por lectura el artefacto instalado, versión efectiva y revisión/digest cuando esté disponible, usando un mecanismo existente y seguro. No inventar ni exponer un endpoint público para hacer la comprobación. Un valor visible o un endpoint por sí solos no prueban toda la salud de la aplicación.
6. Reportar por separado versión preparada, commit/tag local o remoto, build, despliegue y comprobación. Si no se autorizó desplegar, dejarlo como no solicitado; si se desplegó sin poder acreditar la versión efectiva, registrar `NO_VERIFICADO`, no éxito completo. No confundir verificación de versión con QA ni aceptación funcional.

## Evidencia de referencia

Fuentes oficiales consultadas para los mecanismos; no reemplazan la inspección de la versión y código reales de cada aplicación:

- Laravel configuración y caché: https://laravel.com/docs/13.x/configuration y su fuente https://github.com/laravel/docs/blob/13.x/configuration.md.
- .NET propiedades de assembly: https://learn.microsoft.com/en-us/dotnet/standard/assembly/set-attributes-project-file.
- MSBuild y propiedades por directorio: https://learn.microsoft.com/en-us/visualstudio/msbuild/customize-by-directory.

Estas instrucciones son ejecutadas por el agente durante una entrega autorizada. No instalan un job, listener ni proceso automático dentro de las aplicaciones.
