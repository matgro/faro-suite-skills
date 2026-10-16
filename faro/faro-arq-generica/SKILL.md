---
name: faro-arq-generica
description: Use when FARO documents an unrecognized stack.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, architecture, discovery, stack, documentation]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico]
---

# FARO — Arquitectura genérica basada en evidencia

## Rol
Documenta arquitectura para un stack confirmado que no es Laravel/API ni móvil. Es conservadora: registra evidencia y pendientes sin imponer convenciones de framework.

## Procedimiento
1. Leer contrato FARO, índice, instrucciones locales y Git; no modificar el repositorio inspeccionado. **Completo:** root y cambios previos identificados.
2. Inspeccionar manifests, lockfiles, toolchain, scripts, CI, pruebas, configuración no secreta y documentación. **Completo:** runtime, paquetes y comandos tienen fuente.
3. Mapear entradas, módulos, persistencia, contratos, UI, integraciones, pruebas, operación y distribución sólo desde evidencia. **Completo:** ausencias se expresan como no encontradas.
4. Crear o actualizar `context/architecture.md` con fuentes, referencia Git, límites, comandos verificados y pendientes. **Completo:** arquitectura útil sin patrón tecnológico supuesto.
5. Actualizar índice/stats; permitir `available` sólo si índice, proyecto, repositorios y arquitectura son verificables. **Completo:** estado y documentación coinciden.

## Invariantes
- No inferir framework, proveedor, CI, despliegue o base de datos sin fuente.
- No copiar secretos, tokens, certificados ni archivos de entorno.
- Una skill futura específica sustituye sólo metodología, no hechos documentados.

## Verificación
- [ ] Runtime, dependencias y comandos tienen fuente.
- [ ] Git fue capturado sin tocar código.
- [ ] Arquitectura distingue hechos, pendientes y no encontrados.
- [ ] No hay secretos en el registro.
