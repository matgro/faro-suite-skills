---
name: faro-bootstrap-laravel
description: Use when FARO creates an authorized new Laravel project.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, laravel, bootstrap, project-creation, composer]
    related_skills: [faro, faro-inicializacion, faro-arq-laravel]
---

# FARO — Bootstrap Laravel

## Rol

Crea el scaffold técnico real de un proyecto Laravel nuevo antes de que FARO materialice su contrato. Es la única ruta FARO que puede ejecutar `composer create-project` para un proyecto Laravel nuevo. No documenta arquitectura, no recibe RM/BUG/TEC y no autoriza commits, despliegues ni configuración de secretos.

## Cuándo usar

- El usuario pide explícitamente crear un proyecto Laravel/API nuevo con FARO.
- El stack Laravel/API, el root destino y la autorización para crear archivos fueron confirmados.
- El root coordinador es el destino exacto y está vacío; no existe contrato FARO ni proyecto técnico allí.

No usar para un Laravel existente, para agregar código a una aplicación ya creada, ni si el destino contiene archivos. Un Laravel existente continúa por `faro-inicializacion` y luego `faro-arq-laravel`.

## Precondiciones

1. Confirmar que el root actual es el destino técnico definitivo. FARO no crea el proyecto en una ruta externa ni cambia de root durante esta ruta. **Completo:** el usuario confirmó el directorio donde vivirá la aplicación.
2. Confirmar nombre/identidad del proyecto, tipo `nuevo`, stack Laravel/API, variante solicitada y autorización explícita para crear el scaffold. Si no se indicó variante, proponer Laravel estándar sin starter kit; no elegir Breeze, Jetstream, Sail, Livewire, Inertia ni una base de datos por defecto. **Completo:** el alcance técnico inicial no depende de supuestos.
3. Inspeccionar el destino sin leer secretos: debe existir, ser un directorio vacío y no contener `AGENTS.md`, `context/`, `composer.json`, `.env`, `.git` ni archivos ocultos. Si no está vacío, detener y explicar que no se reemplaza, mezcla ni borra contenido. **Completo:** `composer create-project` no sobrescribirá un workspace ni código existente.
4. Verificar que `php` y `composer` están disponibles y que Composer puede resolver el paquete solicitado. No instalar herramientas, PHP, Composer ni dependencias del sistema sin autorización independiente. **Completo:** los prerrequisitos reales fueron comprobados antes de escribir.

## Procedimiento

1. Ejecutar el comando confirmado desde el root vacío. Para Laravel estándar usar:

   ```bash
   composer create-project laravel/laravel .
   ```

   Si el usuario confirmó una restricción de versión o una variante, usar únicamente los argumentos que proporcionó. No agregar starter kits, servicios, migraciones propias, credenciales ni código de dominio.

2. Verificar el resultado sin leer `.env`: deben existir `artisan`, `composer.json`, `composer.lock`, `app/`, `bootstrap/`, `config/`, `database/`, `public/`, `resources/` y `routes/`. Ejecutar `php artisan --version`; ejecutar una prueba Laravel sólo si las dependencias y el entorno la permiten, registrando el fallo real sin modificar configuración para forzarla. **Completo:** el scaffold es Laravel verificable, no sólo un directorio creado.
3. Entregar a `faro-inicializacion` para materializar el contrato FARO dentro del Laravel recién creado y registrar las decisiones ya confirmadas. Esa inicialización no debe solicitar ni ejecutar otro scaffold porque `composer.json` ya evidencia el proyecto técnico. **Completo:** existe un único siguiente handoff y no se mezclan creación técnica y contrato.
4. Después de la inicialización, entregar a `faro-arq-laravel` para documentar la arquitectura a partir del código y manifests reales. **Completo:** la arquitectura se fundamenta en evidencia del proyecto creado.

## Límites permanentes

- Nunca crear el scaffold si el destino no está vacío o no es el root confirmado.
- Nunca leer, copiar, imprimir ni registrar `.env`, tokens, claves o contraseñas generadas por Laravel o por el usuario.
- No inicializar Git, crear commits, publicar paquetes, desplegar, instalar starter kits ni configurar servicios externos salvo petición y autorización independientes.
- Un fallo de Composer, PHP o del comando no se oculta ni se sustituye por una estructura simulada.

## Verificación

- [ ] Stack, destino, variante y autorización explícita fueron confirmados.
- [ ] El destino vacío fue inspeccionado sin borrar ni reemplazar contenido.
- [ ] PHP y Composer fueron comprobados antes de crear archivos.
- [ ] `composer create-project laravel/laravel .` o el comando confirmado terminó correctamente.
- [ ] `artisan`, `composer.json`, `composer.lock` y la estructura Laravel existen.
- [ ] No se leyó ni persistió contenido de `.env`.
- [ ] El handoff fue `faro-inicializacion`, seguido de `faro-arq-laravel`.
