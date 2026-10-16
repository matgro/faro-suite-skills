---
name: faro-qa-ejecucion
description: Use when FARO runs QA cases with evidence.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, qa, testing, evidence, bugs]
    related_skills: [faro, faro-req-implementacion, faro-req-validacion, faro-req-ingenieria]
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
1. Leer RM, CA, plan, tareas, arquitectura, evidencia y workflow. Si seguimiento está `REQUIRED`, sincronizar el inicio de QA con comentario y enlaces a casos/evidencia, manteniendo el estado remoto de trabajo; si falla, bloquear antes de ejecutar. **Completo:** cada escenario tiene origen funcional y trazabilidad remota.
2. Definir casos antes de ejecutar: API, UI o ambos; precondiciones, datos, pasos, esperado, efectos y limpieza. **Completo:** ningún esperado deriva del comportamiento actual.
3. Registrar la autorización de datos/efectos faltante. No usar datos reales sin autorización. **Completo:** escenario ejecutable o BLOCKED con causa.
4. Ejecutar por CA y registrar evidencia. Estados permitidos: `PENDING`, `PASSED`, `FAILED`, `BLOCKED`. **Completo:** UI no se acredita con API.
5. Crear o actualizar BUG para cada fallo reproducible; no corregirlo durante la corrida. **Completo:** reproducción, impacto y evidencia trazables.
6. Actualizar workflow: fallo → `faro-req-analisis-tecnico` o `faro-req-implementacion`; éxito → `faro-req-validacion`. **Completo:** próxima ruta real.

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
