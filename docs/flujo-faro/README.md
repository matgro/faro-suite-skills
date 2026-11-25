# FARO: cerebro de decisión y mapa completo de flujos

Guía de **FARO Suite 2.0.0**, contrato de workspace **2.0.0**. Separa conocimiento duradero de expedientes RM/BUG/TEC, declara al gestor remoto como autoridad operativa e incorpora migración versionada y cierre con congelamiento.

Las versiones del paquete, contrato, skills, artefactos funcionales y aplicaciones son independientes. Publicar o instalar la suite no modifica aplicaciones ni autoriza despliegues en proyectos existentes.

## Versiones: qué representa cada una

| Dato | Ejemplo | Para qué sirve | No significa |
| --- | --- | --- | --- |
| Suite FARO | `2.0.0` | Identifica el paquete distribuido e instalado. | Que todos los proyectos ya usan ese contrato. |
| Skill principal / otras skills | `faro 2.0.0`, otra skill `1.2.0` | Identifica la revisión de una instrucción concreta. | Compatibilidad del workspace. |
| Contrato del workspace | `2.0.0` | Determina el layout que doctor puede leer o escribir. | La versión de la aplicación ni la de un RM. |
| `stats.faro.version` | `2.0.0` | Conserva qué paquete materializó o actualizó ese workspace. | Un error si difiere del paquete instalado hoy. |
| Workflow | `schemaVersion: 2` | Valida la forma del checkpoint temporal. | Una release ni el estado remoto del item. |
| DF/RM/plan/QA/validación | `document_version: 1.3` | Identifica la baseline o evidencia de un expediente. | Permiso para cambiar el contrato o desplegar. |

`faro-doctor` muestra esta matriz antes de su recomendación. La compatibilidad se decide entre **suite** y **contrato**; los demás valores aportan trazabilidad y no se comparan como si fueran la misma versión.

Esta documentación explica lo que existe; no agrega reglas, estados ni permisos. Si cambia una skill, su fuente y el contrato central prevalecen sobre este mapa.

> FARO es una suite de instrucciones para un agente, no un motor que ejecute automáticamente todos estos nodos. Una flecha significa selección de una especialista, handoff condicionado o uso de una capacidad auxiliar. No implica aprobación humana, ejecución de herramientas ni escritura remota ya realizadas.

## Por dónde empezar

| Pregunta | Árbol detallado |
| --- | --- |
| ¿Cómo instala o actualiza el agente las skills de FARO? ¿Cómo prepara un espacio nuevo? ¿Qué pide y qué revisa doctor? | [01. Inicio del espacio y doctor](01-inicio-y-doctor.md) |
| ¿Cuándo crea código inicial? ¿Cómo elige arquitectura? ¿Cuándo usa ADR o RFC? | [02. Scaffold, arquitectura y decisiones](02-arquitectura-y-decisiones.md) |
| ¿Qué hace con un cambio, BUG, TEC o consulta? ¿Cómo llega a desarrollo, QA y validación? | [03. Solicitudes y desarrollo](03-solicitudes-y-desarrollo.md) |
| ¿Cómo investiga un incidente y decide si hay una corrección o cierre sin BUG? | [04. Incidentes](04-incidentes.md) |
| ¿Cómo se relaciona con Jira/Azure DevOps y skills externas? ¿Cómo entrega commit, push, tag o deploy? | [05. Integraciones y entrega](05-integraciones-y-entrega.md) |

Los diagramas usan Mermaid para verse en GitHub o en un visor compatible. Las tablas y árboles de texto conservan la información para lectores que no rendericen gráficos.

## 1. Las tres cosas que no deben confundirse

| Operación | Quién la gobierna | Qué cambia | Qué no demuestra |
| --- | --- | --- | --- |
| Instalar/actualizar FARO | `faro-bootstrap`, fuera del inventario runtime | El árbol completo de skills del agente, con revisión/integridad y confirmación de reemplazo | No inicializa ni migra proyectos; no instala toda capacidad externa por inferencia |
| Inicializar un workspace | `faro` → `faro-inicializacion` | Contrato y perfil del root coordinador desde plantillas | No deja el proyecto `available`, no implementa una solicitud y no crea un scaffold salvo handoff autorizado |
| Trabajar sobre una unidad | `faro` → especialista según estado, evidencia y pedido | INC, DF, RM/BUG/TEC, decisiones, plan, tareas, código o evidencia según autorización | Una fase no autoriza por sí misma la siguiente ni una salida externa |

Fuentes: [bootstrap de instalación](../../bootstrap/SKILL.md), [router](../../faro/SKILL.md), [inicialización](../../faro/faro-inicializacion/SKILL.md).

## 2. Cerebro central: contexto antes de elegir trabajo

### Cómo leer los diagramas

- **Azul:** una *skill* que FARO invoca. Una skill no invoca toda la cadena: devuelve un handoff o un bloqueo.
- **Amarillo (rombo):** una decisión o gate. La etiqueta de la flecha dice cuándo se toma cada salida.
- **Gris:** contexto, evidencia o resultado. No es una skill ni concede permiso.
- Una flecha significa “FARO selecciona esta siguiente acción cuando se cumple la condición”; no significa ejecución automática ni autorización implícita.

```mermaid
flowchart TD
    request["Pedido del usuario"] --> router["Skill: faro\nlee root, contrato y estado"]
    router --> install_q{"¿Instalar o actualizar la suite?"}
    install_q -->|"Sí"| install["Skill: faro-bootstrap"]
    install_q -->|"No"| health_q{"¿Diagnóstico, espacio existente o contrato inválido?"}
    health_q -->|"Sí"| doctor["Skill: faro-doctor\nsolo informa y recomienda"]
    health_q -->|"No"| new_q{"¿Crear proyecto Laravel/.NET nuevo autorizado?"}
    new_q -->|"Sí, root vacío"| scaffold["Skill: faro-bootstrap-laravel\no faro-bootstrap-dotnet"]
    scaffold --> initialize["Skill: faro-inicializacion"]
    new_q -->|"No"| init_q{"¿Pidió inicializar un espacio ausente?"}
    init_q -->|"Sí"| initialize
    init_q -->|"No"| no_contract["Bloqueo: falta contrato o autorización"]
    initialize --> prep["Resultado: workspace initializing"]
    router --> state_q{"¿Contrato actual y estado available?"}
    state_q -->|"No"| prep
    state_q -->|"Sí"| available["Resultado: FARO puede elegir una skill de trabajo"]
    prep --> ready_q{"¿Arquitectura e integración requerida completas?"}
    ready_q -->|"No"| wait["Resultado: mantener initializing"]
    ready_q -->|"Sí"| available
    available --> selector["Ver árbol de trabajo"]
    classDef skill fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef result fill:#f3f4f6,stroke:#6b7280,color:#111827
    class router,install,doctor,scaffold,initialize skill
    class install_q,health_q,new_q,init_q,state_q,ready_q decision
    class request,prep,no_contract,wait,available,selector result
```

La presencia del bloque FARO o de un artefacto propio del contrato distingue un espacio existente de uno ausente; un `AGENTS.md` ajeno sin bloque no basta. Doctor clasifica `current`, `legacy-migratable`, `mixed-ambiguous`, `future-unsupported` o `corrupt`: sólo `current` admite trabajo y la migración de un legado requiere dry-run y autorización separada. El root es el directorio actual; un repositorio externo indexado no recibe escrituras del contrato FARO.

Antes de seguir `nextRoute`, el router pide validar el workflow con `suite_validation.py`. Una ruta retirada o desconocida se diagnostica; no se ejecuta ni se traduce silenciosamente. Reanudar tampoco hereda autorización de otra versión o alcance.

Fuentes: [router: detección y continuidad](../../faro/SKILL.md), [validación de suite y workflow](../../faro/scripts/suite_validation.py), [configuración canónica](../../faro/templates/faro-workspace-config.json).

## 3. Cerebro de trabajo en un espacio disponible

```mermaid
flowchart TD
    available["Contexto: workspace available"] --> goal{"¿Qué pidió el usuario?"}
    goal -->|"Consulta"| query["Resultado: responder; sin crear flujo artificial"]
    goal -->|"Síntoma o causa desconocida"| incident["Skill: faro-incidentes"]
    goal -->|"Cambio funcional"| df_q{"¿DF habilitada?"}
    df_q -->|"Sí"| df["Skill: faro-documentacion-funcional"]
    df_q -->|"No"| tracking_q{"¿Seguimiento REQUIRED y verificado?"}
    df -->|"Hay cambio que formalizar"| tracking_q
    tracking_q -->|"Sí"| engineering["Skill: faro-req-ingenieria"]
    tracking_q -->|"No"| integration["Skill: faro-int-jira\no faro-int-azure-devops"]
    goal -->|"BUG confirmado o TEC autorizado"| analysis["Skill: faro-req-analisis-tecnico"]
    engineering -->|"Alcance y versión aprobados"| analysis
    goal -->|"Decisión técnica"| decision_q{"¿Falta acuerdo externo?"}
    decision_q -->|"Sí"| rfc["Skill: faro-arq-rfc"]
    decision_q -->|"No, decisión tomada"| adr["Skill: faro-arq-adr"]
    rfc -->|"Aceptado"| adr
    goal -->|"Interfaz o flujo visible"| ux["Skill: faro-ux"]
    goal -->|"Plan listo + permiso exacto"| development["Skill: faro-req-desarrollo"]
    goal -->|"QA"| qa["Skill: faro-qa-ejecucion"]
    goal -->|"Validar alcance entregado"| validation["Skill: faro-req-validacion"]
    validation -->|"VERIFIED"| close["Skill: faro-cierre"]
    goal -->|"Commit, PR, release o deploy"| delivery["Skill: faro-entrega"]
    classDef skill fill:#dbeafe,stroke:#2563eb,color:#172554
    classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef result fill:#f3f4f6,stroke:#6b7280,color:#111827
    class incident,df,engineering,integration,analysis,rfc,adr,ux,development,qa,validation,close,delivery skill
    class goal,df_q,tracking_q,decision_q decision
    class available,query result
```

Las condiciones escritas en las flechas son gates, no permisos automáticos. Por ejemplo, terminar el plan permite proponer desarrollo, pero no convierte una autorización de análisis en autorización de implementación.

Prioridades y desvíos que cambian la ruta:

- **Investigar un error no es cambiar una regla:** un síntoma con causa desconocida entra en INC aunque falte esperado o DF. No abrir RM/BUG sólo para poder investigar.
- **BUG conocido con esperado sustentado:** puede ir directamente a análisis; no exige un INC artificial.
- **QA contra un CA conocido:** crea BUG reproducible sin imponer INC; un síntoma fuera de esos CA puede derivar a incidentes.
- **UI visible:** requiere el diseño proporcional de UX antes de implementar lo dependiente; no autoriza cambiar la regla de negocio.
- **RFC abierto:** bloquea sólo implementación/QA/validación que dependan de esa decisión, no toda actividad del proyecto.
- **Seguimiento REQUIRED:** atraviesa las fases como política. No es otra fase que otorgue aprobación funcional; si una sincronización obligatoria falla, se registra el bloqueo y no se avanza de fase.
- **Seguimiento OFF:** permite consulta, arquitectura y documentación sin unidad; no habilita RM/BUG/TEC Markdown como gestor local implícito.
- **Entrega:** requiere la acción de salida expresamente pedida; ni QA correcto ni validación conforme autorizan commit, push o deploy por inferencia. Una operación externa completada tampoco cierra el item.
- **Cierre:** sólo después del veredicto global `VERIFIED` consolida o justifica conocimiento duradero, verifica la transición remota a `DONE` y congela el expediente estable.

Fuentes: [tabla de ruteo](../../faro/SKILL.md), [casos canónicos](../../faro/references/routing-cases.md), [contrato de requerimientos](../../faro/faro-req-ingenieria/references/process-contract.md), [incidentes](../../faro/faro-incidentes/SKILL.md).

## 4. Cadena común y caminos que no requieren esa cadena completa

```text
Preparación del espacio
    [scaffold autorizado, si hace falta]
        → inicialización → [seguimiento REQUIRED] → arquitectura → available

Cambio funcional
    [DF si está habilitada] → ingeniería y aprobación
        → análisis técnico y tareas → [UX y ADR/RFC según dependencia]
        → desarrollo autorizado → QA → validación → [entrega autorizada] → cierre

BUG conocido
    esperado con fuente y corrección autorizada
        → análisis técnico → desarrollo → QA → validación → [entrega] → cierre

TEC
    justificación de contrato observable preservado y autorización
        → análisis técnico → desarrollo → verificación proporcional → [entrega] → cierre

Incidente
    registro → capacidad externa verificada → evidencia/hipótesis/conclusión
        ├─ defecto propio confirmado → [BUG autorizado → cadena de corrección]
        ├─ negocio correcto → cierre sin BUG, o RM si se pide cambiar la regla
        ├─ proveedor/configuración/datos/operación → seguimiento o acción autorizada
        └─ no concluyente → evidencia pendiente; archivo sólo con sus condiciones

Consulta
    leer fuentes → responder; sin crear documentos o workflow por obligación artificial
```

Los corchetes indican una condición o autorización adicional, no un paso que pueda omitirse si realmente aplica. UX y decisiones técnicas se ubican antes del trabajo que depende de ellas; no existe una posición universal idéntica para todos los cambios.

## Controles transversales: vocabulario, visuales y cierre

- **Glosario:** después de fijar root y estado, consultar `context/glossary.md` antes de interpretar términos en cada interacción, reanudación o invocación directa. También aplica con DF deshabilitada. No crear trabajo artificial por definir una sigla; conservar ámbitos, fuentes e incertidumbre. [Reglas y límites](../../faro/references/domain-glossary.md).
- **Visuales Mermaid:** apoyar procesos, estados e interacciones en el DF/RM/plan existente, con texto legible y trazabilidad a RF/RN/CA/PD ya definidos; no inventar comportamiento ni archivos visuales paralelos. [Aplicación en solicitudes](03-solicitudes-y-desarrollo.md#visuales-mermaid-en-los-artefactos-existentes).
- **Refactor completo:** planificar origen, destino y consumidores; conectar entradas reales, retirar o delegar la lógica anterior y obtener evidencia y revisión independiente antes del cierre. Pruebas verdes aisladas no bastan. [Control de cierre](../../faro/references/refactoring-completion.md).
- **Versión de aplicación:** arquitectura descubre y propone por componente; el perfil conserva la decisión humana; desarrollo instala el mecanismo faltante sólo con autorización y entrega actualiza el existente. No es un scheduler ni un incremento por commit. [Política de aplicaciones](../../faro/references/application-versioning.md).

```mermaid
flowchart LR
    C0["Contexto confirmado"] --> C1["Leer glosario y fuentes"]
    C1 --> C2{"¿Qué control aplica a la ruta elegida?"}
    C2 -->|"Visual"| C3["Resultado: visual trazable"]
    C2 -->|"Refactor"| C4["Resultado: integración, retiro y revisión"]
    C2 -->|"Versión/entrega"| C5["Resultado: operación autorizada"]
    C3 --> C6["Evidencia y pendientes\nsin ampliar permisos"]
    C4 --> C6
    C5 --> C6
    classDef decision fill:#fef3c7,stroke:#d97706,color:#78350f
    classDef result fill:#f3f4f6,stroke:#6b7280,color:#111827
    class C2 decision
    class C0,C1,C3,C4,C5,C6 result
```

## 5. Inventario: dónde está cada skill y quién la utiliza

Esta tabla cubre todo el inventario de [manifest.json](../../manifest.json). El bootstrap de instalación se lista aparte porque no es una skill runtime dentro de `faro/`.

| Skill | Responsabilidad / llamada | Árbol |
| --- | --- | --- |
| `faro` | Punto único de entrada, estado y selección de una especialista FARO | Esta página |
| `faro-inicializacion` | Materializar contrato y decisiones de preparación | [Inicio](01-inicio-y-doctor.md) |
| `faro-doctor` | Diagnóstico de espacio y suite, sin reparación implícita | [Doctor](01-inicio-y-doctor.md) |
| `faro-bootstrap-laravel` | Scaffold Laravel nuevo autorizado, antes del contrato | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-bootstrap-dotnet` | Scaffold .NET nuevo autorizado con plantilla confirmada | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-arq-laravel` | Arquitectura Laravel observada y disponibilidad | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-arq-dotnet` | Arquitectura .NET/C# observada y disponibilidad | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-arq-mobile` | Arquitectura móvil observada y disponibilidad | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-arq-generica` | Arquitectura del stack confirmado restante | [Arquitectura](02-arquitectura-y-decisiones.md) |
| `faro-arq-adr` | Registro permanente de decisión técnica significativa | [Decisiones](02-arquitectura-y-decisiones.md) |
| `faro-arq-rfc` | Acuerdo externo sobre alternativas y dependencia bloqueada | [Decisiones](02-arquitectura-y-decisiones.md) |
| `faro-documentacion-funcional` | DF, catálogo y trazabilidad funcional bajo demanda | [Solicitudes](03-solicitudes-y-desarrollo.md) |
| `faro-req-ingenieria` | Formalización funcional, pendientes, CA y aprobación | [Solicitudes](03-solicitudes-y-desarrollo.md) |
| `faro-req-analisis-tecnico` | Inspección real, plan, tareas y registro BUG/TEC | [Solicitudes](03-solicitudes-y-desarrollo.md) |
| `faro-req-desarrollo` | Implementar sólo una unidad autorizada de plan listo | [Desarrollo](03-solicitudes-y-desarrollo.md) |
| `faro-ux` | Pantallas/estados visibles y ajuste al catálogo frontend | [Desarrollo](03-solicitudes-y-desarrollo.md) |
| `faro-qa-ejecucion` | Casos y ejecución con evidencia por CA | [QA](03-solicitudes-y-desarrollo.md) |
| `faro-req-validacion` | Conformidad contra el alcance y la versión aprobados | [Validación](03-solicitudes-y-desarrollo.md) |
| `faro-cierre` | Promoción de conocimiento, cierre remoto verificado y congelamiento del expediente | [Cierre](03-solicitudes-y-desarrollo.md) |
| `faro-incidentes` | Investigar sin asumir defecto y separar conclusión/corrección/impacto | [Incidentes](04-incidentes.md) |
| `faro-int-jira` | Gobernanza de seguimiento Jira; utiliza `jira-rest-v3` externa | [Integraciones](05-integraciones-y-entrega.md) |
| `faro-int-azure-devops` | Gobernanza de seguimiento Azure DevOps/Visual Studio | [Integraciones](05-integraciones-y-entrega.md) |
| `azure-devops-rest-v7` | Capacidad REST del adaptador Azure DevOps; no ruta de ciclo de vida | [Integraciones](05-integraciones-y-entrega.md) |
| `faro-entrega` | Commit/PR/release/deploy/rollback y decisión de versión/tag | [Entrega](05-integraciones-y-entrega.md) |

Instalación de la suite: [`faro-bootstrap`](../../bootstrap/SKILL.md) → [árbol de instalación](01-inicio-y-doctor.md).

## 6. Dónde recuerda las decisiones

| Fuente de verdad | Qué conserva |
| --- | --- |
| `faro/templates/faro-workspace-config.json` | Política central del contrato; archivos y estados permitidos |
| `AGENTS.md` del workspace | Bloque de instancia FARO; preserva instrucciones ajenas |
| `context/faro-workspace.json` | Manifiesto de versión/origen/artefactos, no otra política |
| `context/stats.json` | Estado e identidad del espacio; no es el estado de un BUG |
| `context/README.md` | Índice de repositorios y fuentes, no copia de su código |
| `context/requirements/project-profile.md` | Seguimiento, proveedor, DF y sección «Versionado de aplicaciones» por componente, sin secretos |
| `context/glossary.md`, condicional | Vocabulario de dominio con ámbito, estado, fuente e historial; no aprobación funcional |
| `context/requirements/functional/DF-ID/` | DF duradero y su investigación interna; comportamiento funcional baselineado |
| `context/requirements/work-items/ID/` | Expediente estable RM/BUG/TEC: definición, plan, tareas, QA, validación, entrega y cierre |
| `context/requirements/requirements-catalog.md` | Reservas y localización de expedientes/relaciones/referencia remota; sin estado operativo |
| Jira o Azure DevOps | Estado operativo, prioridad, asignación, iteración y cola global de RM/BUG/TEC/INC/TASK |
| `context/incidents/` | Investigación INC e índice, sólo al necesitarlos |
| `context/decisions/adr/` y `context/decisions/rfc/` | Decisiones técnicas bajo demanda |
| `context/workflow.json` | Sólo puntero/checkpoint de una unidad activa: ID/ruta, fase, autorización, espera y siguiente ruta; sin backlog ni terminadas |

Fuentes: [configuración](../../faro/templates/faro-workspace-config.json), [perfil](../../faro/templates/project-profile.md), [workflow](../../faro/templates/workflow.json), [ciclo de expedientes](../../faro/references/work-item-lifecycle.md), [contrato funcional](../../faro/faro-req-ingenieria/references/process-contract.md).

La madurez documental (`spec_maturity`, `assessment_maturity`, `plan_readiness`), los resultados de QA y el veredicto de validación permanecen locales porque son evidencia semántica: no es el mismo vocabulario que el estado remoto y no debe copiarlo. Una carpeta no se mueve a `completed/`: el cierre genera un manifiesto de hashes y un cambio posterior crea un sucesor enlazado.

## 7. Límites de esta guía y mantenimiento

- Los gráficos describen gates y handoffs de instrucciones. Los validadores Python comprueban integridad/coherencia y algunos campos; no ejecutan ni garantizan el razonamiento de todas las skills.
- El código observado no prueba que una regla sea la aprobada ni que esa revisión esté desplegada. Los informes deben conservar la procedencia y sus límites.
- La existencia de una skill en un catálogo no demuestra instalación, descubrimiento o auditoría del runtime. Las dependencias de incidentes conservan su pin y controles propios.
- Las páginas detalladas señalan diferencias entre la política de una skill y lo que su script comprueba efectivamente. Documentarlas no las corrige ni convierte su recomendación en permiso de reparación.
- Si se cambia una ruta, revisar su diagrama, su fila de inventario, las páginas afectadas y las fuentes. No editar el runtime para hacer coincidir esta documentación.
