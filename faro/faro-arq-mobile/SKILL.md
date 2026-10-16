---
name: faro-arq-mobile
description: Use when FARO documents an evidenced mobile architecture.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, mobile, architecture, discovery, documentation]
    related_skills: [faro]
---

# FARO Arquitectura Móvil

## Overview

Produce el registro arquitectónico móvil de FARO con evidencia del repositorio y la plantilla canónica `templates/architecture-mobile.md`. La salida es `context/architecture-mobile.md` en el root coordinador FARO. No presupone framework, plataforma, SDK, navegación ni distribución.

## When to Use

- FARO confirmó un repositorio de aplicación móvil.
- FARO debe escanear, crear o actualizar su arquitectura móvil.

No usar para implementar pantallas ni para reemplazar este flujo con una skill genérica de gobernanza.

## Flujo de escaneo

1. Leer el contrato FARO y confirmar ruta/estado activo. **Completo:** repositorio confirmado y FARO habilitado.
2. Capturar rama y cambios con `git status --short --branch`; no modificar el repositorio. **Completo:** cambios previos separados de FARO.
3. Leer instrucciones, manifests, locks, configuración de plataforma, scripts, CI, EAS/fastlane, proyectos nativos y docs. **Completo:** plataforma, runtime y comandos tienen fuente.
4. Mapear pantallas, navegación, estado, componentes, estilos, permisos, almacenamiento, red/API, build/distribución y pruebas. **Completo:** cada límite está evidenciado o pendiente.
5. Usar `templates/architecture-mobile.md` y completar sólo con evidencia. **Completo:** no hay supuestos de SDK, toolchain, navegación o release.
6. Validar índice/rutas, actualizar `stats.json.updatedAt` UTC y permitir `available` sólo con arquitectura verificable. **Completo:** estado y documentación consistentes.

## Registro obligatorio

Incluir ruta/ref/estado Git, evidencia, framework/runtime/dependencias, comandos, plataformas/mínimos si están definidos, organización, navegación/estado, permisos, API, secretos/configuración, pruebas, distribución/operación y pendientes.

## Reglas de evidencia y seguridad

- `package.json` declara dependencias; lockfile registra el árbol resuelto.
- No copiar claves, tokens, certificados ni valores de entorno. Ante un fallback sensible, registrar el riesgo sin reproducir el valor.
- No confundir permisos declarados con manejo correcto de denegación.
- Ausencias de EAS, CI, `android/`, `ios/` o pruebas deben ser «no encontradas durante la inspección».

## Relación con requerimientos FARO

Cuando el registro arquitectónico sea parte de un cambio funcional solicitado, el alcance debe referenciar el RM/BUG/TEC y su versión de `context/requirements/`. Cargar `faro-req-ingenieria` antes de transformar la solicitud; este skill conserva su función de escaneo y no acredita aprobación funcional.

## Common Pitfalls

1. Inferir Expo/React Native o mínimos de SO sin artefactos.
2. Tocar archivos móviles con cambios locales durante discovery.
3. Declarar contrato API sin contrastarlo con backend disponible.
4. Poner secretos en documentación.

## Verification Checklist

- [ ] Se usó la plantilla móvil FARO.
- [ ] Plataforma, comandos y dependencias tienen fuentes.
- [ ] Estado Git registrado sin tocar el repositorio.
- [ ] Permisos, API, pruebas y distribución evidenciados o pendientes.
- [ ] `context/README.md` indexa el documento.
