# Versionado y tags de entrega

## Decisión humana antes de entregar

Antes de commit, push, PR o release, inspeccionar las reglas del repositorio, versión declarada, diff y tags locales/remotos. Comparar el alcance acumulado desde la última versión publicada aplicable a la línea que se entrega, no sólo el último commit. Si el remoto no puede consultarse, informar el bloqueo; no afirmar que un tag está disponible.

Proponer una versión concreta y justificarla brevemente por impacto. Preguntar en una sola confirmación: «Propongo <versión> (<PATCH|MINOR|MAJOR>) por <motivo>. ¿Actualizamos la versión y creamos/publicamos el tag <tag> en <remoto>, junto con la entrega en <rama>?». Permitir entregar sin incrementar o sin tag cuando el usuario lo decide explícitamente.

No repetir decisiones ya autorizadas: si pidió versión y push pero no tag, preguntar sólo por crear/publicar el tag. Una petición de entrega o push no autoriza por sí sola versionar ni taguear. Si sólo se autoriza crear un tag local, no publicarlo. Si sólo se publica una versión ya preparada, verificar su commit sin incrementar otra vez. No abrir PR, crear una release en la plataforma ni desplegar por el solo hecho de publicar un tag.

## Criterio SemVer

Respetar primero la política de versionado explícita del proyecto; no imponer SemVer a un esquema distinto. Para proyectos con SemVer, evaluar el contrato público que consumen sus usuarios:

| Incremento | Impacto | Ejemplo |
| --- | --- | --- |
| PATCH | Corrección compatible de comportamiento incorrecto. | Corregir una validación sin romper el contrato. |
| MINOR | Funcionalidad nueva compatible o deprecación de una capacidad pública. | Agregar una operación opcional conservando las existentes. |
| MAJOR | Cambio incompatible que requiere adaptar consumidores. | Retirar una operación pública o exigir un dato antes opcional. |

Aplicar el mayor impacto del conjunto; al subir MINOR reiniciar PATCH, y al subir MAJOR reiniciar MINOR y PATCH. Calcular la versión con herramientas, no por orden alfabético. `fix` orienta a PATCH, `feat` a MINOR y `!`/`BREAKING CHANGE` a MAJOR, pero revisar el diff: el prefijo no prueba compatibilidad. `docs`, `test`, `ci` y `chore` no obligan por sí solos a incrementar.

En suites de skills, revisar también instrucciones, rutas y formatos públicos: corregir una guía defectuosa puede ser PATCH; agregar una capacidad compatible, MINOR; romper contratos de workspace o exigir migración, MAJOR. No equiparar cantidad de archivos o tamaño del diff con impacto. Si falta evidencia de compatibilidad, exponer la duda antes de confirmar. Para `0.y.z` o prereleases, seguir la política explícita del proyecto sin asumir estabilidad ni publicar una prerelease como estable.

## Publicación verificada

1. Confirmar versión, nombre del tag, commit objetivo, rama y remoto. Usar la convención del repositorio; en FARO, `v<MAJOR>.<MINOR>.<PATCH>`. Comprobar colisiones locales y remotas. Nunca mover, sobrescribir, borrar ni reutilizar un tag publicado para contenido diferente.
2. Si se autorizó incrementar, sincronizar los metadatos y el changelog antes del commit. En FARO: `manifest.json.version`, `references/suite-provenance.json.packageVersion/ref` bajo `faro/`, `faro/references/suite-changelog.json`, `CHANGELOG.md` y `checksums.sha256`. No cambiar `contractVersion` ni versiones individuales de skills sólo para igualarlas con la versión del paquete.
3. Ejecutar las validaciones del repositorio y revisar el diff. Crear el commit con el mensaje definido por `faro-entrega`. Crear un tag anotado sobre el SHA validado mediante `git tag -a <tag> <SHA> -m <mensaje>`; firmarlo sólo si la política lo exige y la capacidad está disponible. Si el tag ya existe y coincide, verificarlo en vez de recrearlo.
4. Publicar sólo la rama y el tag autorizados mediante referencias explícitas. Preferir `git push --atomic <remoto> <ref-rama> <ref-tag>` cuando se publican juntos y el servidor lo admite. No usar `--tags` ni force push; si la publicación es parcial, informar qué referencia falta sin declarar la entrega completa.
5. Leer el remoto con `git ls-remote` y comprobar que la rama publicada y el commit resuelto del tag coinciden con el SHA validado. Para un tag anotado, comparar la referencia pelada `refs/tags/<tag>^{}`, no el SHA del objeto tag. Verificar también el contenido versionado e integridad del commit etiquetado. Un push de rama no publica automáticamente el tag.
6. Reportar versión, commit, rama, tag local/remoto y validaciones reales. Un tag publicado no demuestra que se haya creado una release en la plataforma ni ejecutado o validado un despliegue. En FARO, una versión sin su tag remoto sigue pendiente para instalación con procedencia verificada.

## Fuentes

- SemVer 2.0.0 (texto original): https://semver.org/; traducción: https://semver.org/lang/es/
- Conventional Commits 1.0.0: https://www.conventionalcommits.org/en/v1.0.0/
- Git, tags anotados: https://git-scm.com/docs/git-tag
- Skill de referencia inspeccionada: `git-workflow-and-versioning`, de `addyosmani/agent-skills`, https://github.com/addyosmani/agent-skills/blob/main/skills/git-workflow-and-versioning/SKILL.md. No se instala ni importa su política de ramas; el criterio se fundamenta en las especificaciones anteriores.
