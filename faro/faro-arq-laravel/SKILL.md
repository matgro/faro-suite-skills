---
name: faro-arq-laravel
description: Use when FARO documents an evidenced Laravel architecture.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, laravel, architecture, discovery, documentation]
    related_skills: [faro]
---

# FARO Arquitectura Laravel

## Overview

Produce el registro arquitectónico Laravel de FARO con evidencia del repositorio y la plantilla canónica `templates/architecture-laravel.md`. La salida es `context/architecture-laravel.md` en el root coordinador FARO. No inventa hechos ni sustituye reglas locales.

## When to Use

- FARO confirmó un repositorio Laravel/API.
- FARO debe escanear, crear o actualizar su arquitectura Laravel.

No usar para modificar código Laravel ni para reemplazar este flujo con una skill genérica de gobernanza.

## Flujo de escaneo

1. Leer `AGENTS.md`, `context/stats.json` y `context/README.md`; confirmar ruta y estado activo. **Completo:** el repositorio fue confirmado y FARO no está desactivado.
2. Registrar rama y cambios con `git status --short --branch`; no modificar el repositorio inspeccionado. **Completo:** estado Git separado de cambios FARO.
3. Leer instrucciones locales, `composer.json`, `composer.lock`, manifest/lock JS, pruebas, CI, despliegue y configuración no secreta. **Completo:** versión y comando citados tienen artefacto fuente.
4. Mapear entradas, módulos, persistencia, integraciones y frontend desde rutas, `app/`, recursos, configuración, base de datos y documentación. **Completo:** sólo se nombran elementos observados.
5. Usar `templates/architecture-laravel.md`; sustituir marcadores únicamente por evidencia y conservar pendientes. **Completo:** no hay afirmaciones sin fuente.
6. Validar índice y rutas; actualizar `stats.json.updatedAt` UTC y permitir `available` sólo con evidencia completa. **Completo:** índice, estado y documento concuerdan.

## Registro obligatorio

Incluir ruta/ref/estado Git, fuentes, PHP/Laravel/Livewire/dependencias verificadas, comandos, módulos/límites, contratos/API, integraciones, frontend, pruebas, operación, documentación local/ADRs y pendientes.

## Reglas de evidencia

- `composer.json` declara restricciones; `composer.lock` confirma versiones resueltas.
- «No encontrado durante la inspección» no equivale a «no existe».
- No leer ni copiar secretos, `.env`, tokens o claves.
- Si existe `/template`, revisar `/template`, `resources/views/template/components` y pantallas del mismo dominio antes de registrar frontend.

## Relación con requerimientos FARO

Cuando el registro arquitectónico sea parte de un cambio funcional solicitado, el alcance debe referenciar el RM/BUG/TEC y su versión de `context/requirements/`. Cargar `faro-req-ingenieria` antes de transformar la solicitud; este skill conserva su función de escaneo y no acredita aprobación funcional.

1. Citar versiones sólo desde el manifest. Contrastar lockfile.
2. Declarar repositorio limpio sin capturar Git.
3. Inventar CI, base de datos, despliegue o ADRs.
4. Sobrescribir documentación de dominio en vez de indexarla.

## Verification Checklist

- [ ] Se usó la plantilla Laravel FARO.
- [ ] Toda versión, comando e integración tiene fuente.
- [ ] Estado Git registrado sin tocar el repositorio.
- [ ] `context/README.md` indexa el documento.
- [ ] Pendientes diferenciados de hechos.
