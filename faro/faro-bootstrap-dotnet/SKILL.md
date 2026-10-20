---
name: faro-bootstrap-dotnet
description: Use when FARO creates an authorized new .NET project.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, dotnet, csharp, bootstrap, project-creation]
    related_skills: [faro, faro-inicializacion, faro-arq-dotnet]
---

# FARO — Bootstrap .NET

## Rol

Crea el scaffold técnico real de un proyecto .NET/C# nuevo antes de que FARO materialice su contrato. Es la única ruta FARO que puede ejecutar `dotnet new` para un proyecto nuevo. No documenta arquitectura, no recibe RM/BUG/TEC y no autoriza commits, despliegues, paquetes extra, secretos ni cambios de configuración.

## Cuándo usar

- El usuario pide explícitamente crear un proyecto .NET/C# nuevo con FARO.
- El destino, identidad, plantilla `dotnet new` y autorización para crear archivos fueron confirmados.
- El root coordinador es el destino exacto, está vacío y no contiene un contrato FARO ni código técnico.

No usar para un proyecto .NET existente, para agregar código a una aplicación existente ni si el destino no está vacío. Un proyecto .NET existente continúa por `faro-inicializacion` y después `faro-arq-dotnet`.

## Precondiciones

1. Confirmar que el root actual es el destino técnico definitivo. FARO no crea el proyecto en una ruta externa ni cambia de root durante esta ruta. **Completo:** el directorio fue confirmado por el usuario.
2. Confirmar nombre/identidad, tipo `nuevo`, stack .NET/C#, plantilla exacta y autorización explícita. La plantilla puede ser `webapi`, `classlib`, `console`, `worker`, `blazor` u otra que el usuario confirme y que aparezca en la instalación real; no elegir una por defecto ni agregar autenticación, paquetes, EF Core, base de datos, Docker o tests no solicitados. **Completo:** el scaffold no depende de supuestos de arquitectura.
3. Inspeccionar el destino sin leer secretos: debe existir, ser un directorio vacío y no contener `AGENTS.md`, `context/`, `.sln`, `.csproj`, `global.json`, `.env`, `.git` ni archivos ocultos. Si no está vacío, detener: nunca reemplazar, mezclar ni borrar contenido. **Completo:** `dotnet new` no sobrescribirá un workspace ni código existente.
4. Verificar que `dotnet` está disponible y que `dotnet new list <TEMPLATE>` reconoce la plantilla confirmada. No instalar SDKs, templates, workloads, paquetes ni dependencias del sistema sin autorización independiente. **Completo:** los prerrequisitos reales se comprobaron antes de escribir.

## Procedimiento

1. Ejecutar únicamente el comando confirmado desde el root vacío. Para una plantilla estándar:

   ```bash
   dotnet new <TEMPLATE> --name <PROJECT_NAME> --output .
   ```

   Agregar argumentos sólo si el usuario los confirmó. No crear una solución adicional, proyectos de prueba, configuraciones de autenticación, secretos, paquetes ni código de dominio por cuenta propia.
2. Verificar el scaffold sin leer archivos sensibles: debe existir al menos un `.csproj` o `.sln`; inspeccionar `dotnet --info`, los archivos de proyecto, `Program.cs` cuando exista y la estructura generada. Ejecutar `dotnet build --no-restore` sólo si puede hacerse sin restaurar ni modificar el proyecto; registrar el fallo real y no alterar configuración para forzarlo. **Completo:** existe evidencia de un proyecto .NET real, no sólo una carpeta creada.
3. Entregar a `faro-inicializacion` para materializar el contrato FARO dentro del proyecto recién creado. La inicialización no debe solicitar ni ejecutar otro scaffold porque el `.csproj`/`.sln` ya evidencia el proyecto técnico. **Completo:** creación técnica y contrato permanecen separados.
4. Después de la inicialización, entregar a `faro-arq-dotnet` para registrar la arquitectura desde el scaffold, manifests y código reales. **Completo:** la arquitectura se basa en evidencia, no en una plantilla supuesta.

## Límites permanentes

- Nunca crear el scaffold si el destino no está vacío o no es el root confirmado.
- Nunca leer, copiar, imprimir ni registrar `.env`, user secrets, tokens, certificados, contraseñas o valores de `appsettings` potencialmente sensibles.
- No inicializar Git, crear commits, publicar paquetes, desplegar, instalar templates/workloads o configurar servicios externos salvo petición y autorización independientes.
- Un fallo de `dotnet`, de la plantilla o del comando no se oculta ni se sustituye por estructura simulada.

## Verificación

- [ ] Destino, stack, plantilla, nombre y autorización explícita fueron confirmados.
- [ ] El destino vacío fue inspeccionado sin borrar ni reemplazar contenido.
- [ ] SDK y plantilla `dotnet new` fueron verificados antes de crear archivos.
- [ ] El comando confirmado terminó correctamente y produjo `.csproj` o `.sln`.
- [ ] No se leyeron ni persistieron secretos o archivos de entorno.
- [ ] El handoff fue `faro-inicializacion`, seguido de `faro-arq-dotnet`.
