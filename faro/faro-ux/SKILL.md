---
name: faro-ux
description: Use when FARO defines screens and frontend catalogue fit.
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [faro, ux, frontend, interface, accessibility]
    related_skills: [faro, faro-req-ingenieria, faro-req-implementacion, faro-arq-laravel]
---

# FARO — UX y catálogo frontend

## Rol
Define la solución visible de un RM: pantallas, navegación, contenido, estados y uso del catálogo local. No crea reglas de negocio, no decide arquitectura técnica y no implementa producto.

## Precondiciones
- Se conoce RM/BUG, versión y RF/CA visibles.
- Se leyó arquitectura e instrucciones locales.
- Para Laravel/Blade, se revisaron `/template`, `resources/views/template/components` y pantallas del mismo dominio.

## Procedimiento
1. Mapear cada elemento visible a RF/CA. Lo no definido se registra como PD y vuelve a `faro-req-ingenieria`. **Completo:** nada visible inventa comportamiento.
2. Inventariar patrones del catálogo, componentes de dominio, pantallas análogas y restricciones responsive/accesibles. **Completo:** se reutiliza patrón o se justifica excepción.
3. Definir tarea principal, navegación, jerarquía, datos y estados de carga, vacío, error, permiso, éxito y extremos relevantes. **Completo:** cada estado aplica o se descarta con motivo.
4. Registrar diseño proporcional en el artefacto FARO existente; mockup sólo si el usuario lo pidió. **Completo:** no se crean documentos visuales sin valor de revisión.
5. Si Jira está `REQUIRED`, comentar el hito UX con versión y enlace al artefacto, manteniendo `Haciendo`; si la sincronización falla, bloquear el flujo.
6. Actualizar workflow y volver a `faro-req-implementacion` cuando esté listo. **Completo:** implementación recibe decisiones concretas.

## Invariantes
- El catálogo guía el markup; detalles de dominio viven en el proyecto.
- Un componente genérico no sustituye un componente de dominio existente.
- Frontend valida forma y experiencia; reglas de negocio permanecen en dominio.
- Diseño no autoriza implementación ni introduce RF.

## Verificación
- [ ] Cada vista y estado tiene RF/CA o PD de origen.
- [ ] Se inspeccionaron catálogo y pantallas del dominio cuando aplican.
- [ ] Hay una acción primaria por tarea visible.
- [ ] Estados de carga, vacío y error están definidos o descartados.
- [ ] No se duplicó la fuente funcional.
