---
name: faro-qa-ejecucion
description: Use when FARO runs QA cases with evidence.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, qa, testing, evidence, bugs]
    related_skills: [faro, faro-req-desarrollo, faro-req-validacion, faro-req-ingenieria]
---

# FARO — Ejecución de QA

## Rol
Diseña y ejecuta pruebas de aplicación para un incremento construido, con evidencia por criterio de aceptación. No modifica código, no aprueba el RM y no sustituye las pruebas que acompañan implementación.

## Precondiciones
- Existe RM/BUG/TEC con versión identificada.
- Incremento y tareas implementadas están identificados.
- La autorización cubre entorno, datos y efectos materiales: mensajes, pagos, borrados e integraciones.
- Se conocen terminal, HTTP, navegador u otras limitaciones reales.

## Procedimiento
1. Leer RM, CA, plan, tareas, arquitectura, evidencia y workflow. Si seguimiento está `REQUIRED`, sincronizar el inicio de QA con una actualización concisa conforme a `../references/comment-format.md` y enlaces a casos/evidencia cuando existan, manteniendo el estado remoto de trabajo; si falla, bloquear antes de ejecutar. **Completo:** cada escenario tiene origen funcional y trazabilidad remota.
2. Definir casos antes de ejecutar: API, UI o ambos; precondiciones, datos, pasos, esperado, efectos y limpieza. **Completo:** ningún esperado deriva del comportamiento actual.
3. Registrar la autorización de datos/efectos faltante. No usar datos reales sin autorización. **Completo:** escenario ejecutable o BLOCKED con causa.
4. Ejecutar por CA y registrar evidencia. Estados permitidos: `PENDING`, `PASSED`, `FAILED`, `BLOCKED`. **Completo:** UI no se acredita con API.
5. Crear o actualizar BUG para cada fallo reproducible contra un CA/esperado sustentado; no corregirlo durante la corrida. Si aparece un síntoma sin esperado o causa confirmados fuera de esos CA, conservar la evidencia y derivar a `faro-incidentes`, sin clasificarlo automáticamente como BUG. No exigir INC para fallos conocidos contra CA. **Completo:** reproducción, impacto y evidencia trazables.
6. Actualizar workflow: fallo contra esperado conocido → `faro-req-analisis-tecnico` o `faro-req-desarrollo`; síntoma no clasificado del paso anterior → `faro-incidentes`; éxito → `faro-req-validacion`. Si seguimiento está `REQUIRED`, publicar el resultado material de QA o su bloqueo conforme a `../references/comment-format.md`. **Completo:** próxima ruta real.

## Invariantes
- Caso no ejecutado nunca es PASSED.
- BLOCKED exige causa externa, no preparación autorizada omitida.
- Evidencia se revisa para secretos, PII y contenido sensible.
- QA distingue causa sospechada de hecho confirmado.

## Verificación
- [ ] Cada CA tiene caso, estado y evidencia o limitación.
- [ ] Datos aislados fueron limpiados o su deuda quedó registrada.
- [ ] Fallos reproducibles tienen BUG trazable.
- [ ] No se cambió código durante QA.
- [ ] Workflow refleja el handoff real.
