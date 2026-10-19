# Lineamientos comunes de desarrollo

## Cómo editar este archivo

Estas son las reglas de código por defecto de FARO. El usuario puede agregar, cambiar o quitar reglas aquí sin editar `SKILL.md`. El agente puede hacerlo cuando el usuario lo pida; no debe cambiar las reglas para justificar una implementación que no las cumple.

Escribir una regla concreta por viñeta, agrupada por tema. Si una regla depende de una tecnología, ubicarla en su archivo de lineamientos. No agregar secretos, rutas personales ni reglas de negocio de un proyecto particular.

Las instrucciones explícitas del repositorio y su arquitectura prevalecen sobre estos valores por defecto. Los lineamientos no autorizan cambios de alcance, contratos, aprobaciones ni acciones de entrega. Una contradicción sin resolución clara se informa antes de modificar código.

## Legibilidad y nombres

- Priorizar legibilidad y mantenibilidad sobre concisión o cantidad de líneas.
- Usar nombres que expresen la intención y el vocabulario del dominio. Respetar el idioma y las convenciones del repositorio.
- Separar condiciones de negocio, conversiones y asignaciones. Preferir bloques claros a expresiones anidadas o ternarios difíciles de seguir.
- Reutilizar constantes y enumeraciones existentes; no introducir números mágicos para estados, tipos o reglas del dominio.
- Comentar el motivo de una decisión no evidente, no repetir lo que el código ya dice.

## Responsabilidades y reutilización

- Leer el código vecino y sus consumidores antes de proponer una estructura nueva. Reutilizar las abstracciones y dependencias existentes.
- Centralizar una regla de negocio repetida en un lugar que sus consumidores puedan utilizar sin romper los límites de la arquitectura.
- No extraer métodos que sólo esconden una operación simple. Extraer cuando aclara una intención, separa una responsabilidad o elimina duplicación real.
- No crear interfaces, capas, fábricas ni soluciones genéricas para un único uso sin una necesidad concreta. No imponer una arquitectura distinta a la aprobada.
- Mantener límites claros entre entrada, operación de negocio y acceso a infraestructura, según la estructura real del proyecto.

## Datos, conversiones y errores

- Validar y convertir el dato una sola vez en el lugar apropiado. Usar la conversión directa al tipo de destino y tratar los datos inválidos de forma explícita.
- No reinterpretar identificadores ni quitar ceros iniciales de cuentas, códigos o documentos que el contrato define como texto.
- Distinguir errores de entrada, rechazos de negocio y fallos técnicos. No transformar un fallo en un resultado exitoso ni ocultarlo con un valor por defecto.
- Usar el manejo de errores existente. Cuando corresponda lanzar o traducir una excepción, expresar la operación que falló y conservar la causa original.
- No capturar todo un flujo para adivinar qué conversión falló ni volver a procesar datos para inferir el origen de una excepción.
- No exponer detalles internos, credenciales ni datos personales en respuestas, logs o mensajes de error.

## Configuración

- Obtener valores operativos de la configuración existente: destinatarios, direcciones de servicios, límites y parámetros que deban variar por ambiente.
- No agregar un fallback hardcodeado oculto. Si una configuración obligatoria falta o es inválida, informarlo mediante el mecanismo de validación del proyecto.
- Documentar las claves nuevas y reutilizar su mecanismo de carga. No crear otro sistema de configuración ni copiar secretos a archivos de FARO.
- No confundir una constante del dominio con un parámetro operativo configurable; conservar el contrato aprobado.

## Cambios mínimos y refactorización

- Cambiar únicamente lo necesario para la tarea. No mezclar renombres, formato masivo, actualizaciones de dependencias ni limpieza ajena al alcance.
- Mantener los contratos públicos salvo cambio autorizado. Revisar consumidores antes de modificar firmas, datos serializados o comportamiento observable.
- Refactorizar en pasos pequeños, conservando comportamiento y pruebas en verde. Si el código no tiene cobertura suficiente, agregar pruebas de caracterización antes de reorganizarlo.
- Si una mejora exige ampliar el diseño o el alcance aprobado, volver al análisis técnico o a la definición funcional; no aprovechar la tarea para incorporarla.

## Pruebas y TDD

- Para un comportamiento nuevo o una corrección, escribir primero una prueba que describa el resultado esperado desde el requerimiento autorizado.
- Ejecutarla y comprobar que falla por el comportamiento faltante o el defecto real, no por errores de preparación. Registrar comando y resultado: fase RED.
- Implementar el cambio mínimo y ejecutar la prueba hasta que pase: fase GREEN.
- Refactorizar sólo si aporta claridad y volver a ejecutar las pruebas: fase REFACTOR. Mantener la suite relevante en verde.
- Usar las herramientas y los niveles de prueba que ya existen. Probar reglas con pruebas unitarias y límites reales con las pruebas de integración que correspondan; no simular todo el sistema para obtener un resultado verde.
- Evitar pruebas acopladas a métodos privados, al orden accidental de llamadas o al formato del código. Verificar comportamiento y contratos.
- Si no hay un entorno ejecutable o un cambio no admite una prueba automatizada útil, registrar el motivo y acordar explícitamente la excepción y la verificación alternativa. No omitir TDD silenciosamente ni presentar pruebas no ejecutadas como aprobadas.
- Ejecutar las pruebas relevantes y los checks existentes de compilación, formato o análisis antes de cerrar. Distinguir sus resultados; compilar no sustituye probar.

## Comprobación antes de cerrar

- Revisar el diff: alcance, legibilidad, duplicación, contratos, configuración y ausencia de secretos.
- Registrar los lineamientos usados, las pruebas ejecutadas y cualquier excepción acordada en la evidencia de la tarea, sin crear otro sistema de estados.
- Informar errores pendientes o limitaciones reales. Estos lineamientos no reemplazan QA de aplicación ni validación funcional.
