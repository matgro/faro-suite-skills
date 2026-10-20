---
name: faro-arq-dotnet
description: Use when FARO documents an evidenced .NET/C# architecture.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, dotnet, csharp, architecture, discovery]
    related_skills: [faro, faro-req-ingenieria, faro-req-analisis-tecnico]
---

# FARO — Arquitectura .NET/C# basada en evidencia

## Rol

Produce el registro arquitectónico .NET/C# de FARO mediante evidencia del proyecto y la plantilla canónica `templates/architecture-dotnet.md`. La salida es `context/architecture-dotnet.md` en el root coordinador FARO. Sirve tanto para un proyecto nuevo —después de un scaffold técnico real— como para un proyecto existente. No crea scaffolds, no modifica código, no elige patrones nuevos ni sustituye reglas locales.

La metodología toma como base inspeccionada el enfoque de `nzt-ai`: el stack se registra desde manifests y código, las alternativas de arquitectura se seleccionan sólo por evidencia y un proyecto existente conserva su estructura como restricción. FARO adapta esos principios al contrato de inicialización; no adopta routers, documentos, opt-ins ni decisiones específicas de NZT.

## Cuándo usar

- FARO confirmó un proyecto .NET/C# por evidencia de `.sln`, `.csproj`, `global.json` o estructura de código C#.
- Un proyecto .NET nuevo ya fue creado con `faro-bootstrap-dotnet` y FARO debe registrar el scaffold real.
- Un proyecto .NET existente quedó en `initializing` y debe analizarse antes de marcarlo `available`.

No usar para crear un proyecto vacío, implementar código, inferir una arquitectura desde la preferencia del agente ni reemplazar este flujo con `faro-arq-generica`.

## Flujo de escaneo

1. Leer `AGENTS.md`, `context/stats.json`, `context/README.md`, el perfil e instrucciones locales; confirmar root, estado y que FARO está habilitado. Capturar rama y cambios con `git status --short --branch`; no modificar el repositorio inspeccionado. **Completo:** se distinguieron cambios previos del registro FARO.
2. Identificar la forma del proyecto desde `.sln`, `global.json`, `Directory.Build.props`, `Directory.Build.targets`, `Directory.Packages.props`, `NuGet.Config`, archivos `.csproj`, `packages.lock.json` y configuración no sensible. Registrar SDK, `TargetFramework`, versión de C# si está declarada, proyectos, referencias entre proyectos, paquetes directos y comandos sólo desde sus archivos fuente o CI. **Completo:** versiones y toolchain tienen evidencia; las ausencias quedan como no encontradas.
3. Para un proyecto nuevo, inspeccionar el scaffold generado —sus proyectos, `Program.cs`, estructura, referencias y configuración no sensible— sin atribuirle decisiones que el usuario no confirmó. Para un proyecto existente, analizar código y pruebas sólo hasta identificar entradas, componentes, límites, consumidores, persistencia, contratos, UI, integraciones y operación; la estructura observada es una restricción, no una deuda que esta skill pueda corregir. **Completo:** el alcance corresponde al código real, no al template de `dotnet new` ni a una arquitectura ideal.
4. Clasificar por evidencia, sin forzar exclusividad: SDK Web/`Program.cs`, Controllers o Minimal APIs, Blazor, workers, bibliotecas, EF Core, otros ORMs, mensajería, autenticación, pruebas, pipelines y despliegue. Si coexisten patrones como capas, vertical slices, DDD, repositorios o acceso directo, describirlos con rutas/evidencia y registrar ambigüedad; no decidir cuál debe prevalecer. **Completo:** los conceptos técnicos no se confunden con nombres de skills ni se inventan.
5. Usar `templates/architecture-dotnet.md`; sustituir marcadores sólo por evidencia y conservar pendientes. Registrar por componente las versiones, proyectos, límites, entradas, persistencia, contratos, integraciones, UI, pruebas y operación. **Completo:** cualquier lector puede localizar la fuente de cada afirmación.
6. Actualizar el índice `context/README.md` para enlazar `context/architecture-dotnet.md`, actualizar `stats.json.updatedAt` UTC y permitir `available` sólo si el índice, proyecto, repositorios y arquitectura son verificables. **Completo:** estado y documentación concuerdan.

## Reglas de evidencia y seguridad

- `global.json`, props/targets, `.csproj`, locks y manifiestos declaran versiones y dependencias; `dotnet --info` describe el entorno observado, no sustituye los archivos del proyecto.
- No leer ni copiar secretos, `.env`, user secrets, certificados, PATs, connection strings, tokens ni valores de configuración sensibles. Registrar solamente la existencia/forma de una integración y el archivo o mecanismo no sensible que la referencia.
- No ejecutar `dotnet restore`, `dotnet build`, migraciones ni tests durante discovery si podrían escribir en el proyecto, descargar dependencias o requerir configuración. Los comandos se registran desde CI, scripts o documentación; cualquier ejecución posterior sigue su fase y autorización.
- «No encontrado durante la inspección» no equivale a «no existe».
- La existencia de EF Core, Clean Architecture, DDD, vertical slices, controllers, Minimal APIs, Blazor o una carpeta instalada no autoriza aplicarlos a código nuevo: desarrollo sigue el código, el contrato y los lineamientos .NET de FARO.

## Registro obligatorio

Incluir ref/estado Git, fuentes inspeccionadas, SDK y frameworks objetivo, solución y proyectos, referencias y paquetes directos relevantes, entradas y componentes, límites y organización observada, persistencia y datos, API/contratos e integraciones, UI si existe, pruebas, CI/operación/distribución, documentación local y pendientes explícitos.

## Relación con requerimientos FARO

Cuando el registro arquitectónico sea parte de un cambio funcional, el alcance debe referenciar el RM/BUG/TEC y su versión. Cargar `faro-req-ingenieria` antes de transformar una solicitud; esta skill sólo descubre/documenta y no acredita aprobación funcional.

## Verificación

- [ ] Se usó la plantilla .NET FARO y se registró si se trató de proyecto nuevo o proyecto existente.
- [ ] SDK, `TargetFramework`, proyectos, paquetes y comandos tienen artefacto fuente.
- [ ] Estado Git fue capturado sin tocar código.
- [ ] Entradas, componentes, persistencia, contratos, UI, pruebas y operación están evidenciados o declarados como no encontrados.
- [ ] `context/README.md` indexa `context/architecture-dotnet.md`.
- [ ] Pendientes y ambigüedades se distinguen de hechos; no hay secretos en el registro.
