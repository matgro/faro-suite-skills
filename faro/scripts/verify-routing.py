#!/usr/bin/env python3
"""Static contract checks for FARO routing, policy authority and templates."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from suite_validation import normalize_field, validate_suite, validate_workflow_structure

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "faro", "faro-inicializacion", "faro-doctor", "faro-bootstrap-laravel", "faro-bootstrap-dotnet", "faro-arq-laravel", "faro-arq-dotnet", "faro-arq-mobile",
    "faro-arq-generica", "faro-arq-adr", "faro-arq-rfc", "faro-documentacion-funcional", "faro-req-ingenieria",
    "faro-req-analisis-tecnico", "faro-req-desarrollo", "faro-qa-ejecucion",
    "faro-req-validacion", "faro-ux", "faro-entrega", "faro-incidentes", "faro-int-jira", "faro-int-azure-devops",
    "faro-cierre", "azure-devops-rest-v7",
}
CONFIG_PATH = ROOT / "templates" / "faro-workspace-config.json"
MANIFEST_PATH = ROOT / "templates" / "faro-workspace-manifest.json"
PROVENANCE_PATH = ROOT / "references" / "suite-provenance.json"
EXPECTED_VERSION = "2.0.0"
EXPECTED_FILES = {
    "AGENTS.md", "context/faro-workspace.json", "context/stats.json",
    "context/README.md", "context/requirements/project-profile.md",
    "context/requirements/requirements-catalog.md",
    "context/requirements/functional-documents-catalog.md",
}
EXPECTED_DIRECTORIES = {
    "context", "context/requirements", "context/requirements/functional",
    "context/requirements/work-items",
}
EXPECTED_WORKSPACE_PATHS = {
    "manifestPath": "context/faro-workspace.json",
    "statePath": "context/stats.json",
    "indexPath": "context/README.md",
    "profilePath": "context/requirements/project-profile.md",
    "requirementsRoot": "context/requirements",
    "requirementsCatalogPath": "context/requirements/requirements-catalog.md",
    "functionalRoot": "context/requirements/functional",
    "functionalCatalogPath": "context/requirements/functional-documents-catalog.md",
    "workItemsRoot": "context/requirements/work-items",
    "workflowPath": "context/workflow.json",
    "glossaryPath": "context/glossary.md",
    "migrationRecordPath": "context/faro-migration-v2.json",
    "agentsPath": "AGENTS.md",
}
EXPECTED_TEMPLATE_SOURCES = {
    "agents": "faro/templates/AGENTS.md",
    "manifest": "faro/templates/faro-workspace-manifest.json",
    "stats": "faro/templates/stats.json",
    "index": "faro/templates/context-README.md",
    "projectProfile": "faro/templates/project-profile.md",
    "requirementsCatalog": "faro/templates/requirements-catalog.md",
    "functionalCatalog": "faro/templates/functional-documents-catalog.md",
    "workItemClosure": "faro/templates/work-item-closure.json",
    "workflow": "faro/templates/workflow.json",
    "glossary": "faro/templates/glossary.md",
}
EXPECTED_WORKFLOW_FIELDS = {
    "schemaVersion", "updatedAt", "phase", "authorization", "workItemRef",
    "waitingOn", "nextRoute", "checkpoint", "notes",
}


def frontmatter(path: Path) -> dict[str, str]:
    text = path.read_text(encoding="utf-8")
    match = re.match(r"\A---\n(.*?)\n---\n", text, flags=re.DOTALL)
    if not match:
        raise ValueError("frontmatter delimitado ausente")
    result: dict[str, str] = {}
    for line in match.group(1).splitlines():
        if ":" in line and not line.startswith((" ", "\t")):
            key, value = line.split(":", 1)
            result[key.strip()] = value.strip().strip('"')
    return result


def load_json(path: Path, failures: list[str]) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("debe ser un objeto JSON")
        return payload
    except Exception as error:
        failures.append(f"{path.name} inválido: {error}")
        return {}


def main() -> int:
    failures: list[str] = validate_suite(ROOT)
    discovered: dict[str, Path] = {}
    for skill in [ROOT / "SKILL.md", *sorted(ROOT.glob("*/SKILL.md"))]:
        try:
            meta = frontmatter(skill)
        except ValueError as error:
            failures.append(f"{skill}: {error}")
            continue
        name, description = meta.get("name"), meta.get("description", "")
        if not name:
            failures.append(f"{skill}: name ausente")
        elif name in discovered:
            failures.append(f"nombre duplicado: {name}")
        else:
            discovered[name] = skill
        if not description or len(description) > 60:
            failures.append(f"{skill}: description inválida ({len(description)} chars)")

    missing = REQUIRED - discovered.keys()
    if missing:
        failures.append("skills requeridas ausentes: " + ", ".join(sorted(missing)))

    router = (ROOT / "SKILL.md").read_text(encoding="utf-8")
    for name in REQUIRED - {"faro"}:
        if f"`{name}`" not in router:
            failures.append(f"router FARO no referencia {name}")

    agents = (ROOT / "templates" / "AGENTS.md").read_text(encoding="utf-8")
    if "<!-- FARO:START -->" not in agents or "<!-- FARO:END -->" not in agents:
        failures.append("plantilla AGENTS no contiene bloque gestionado")
    for required_text in ("instancia gestionada", "context/faro-workspace.json", "skills centrales FARO"):
        if required_text not in agents:
            failures.append(f"plantilla AGENTS no declara manifiesto mínimo: {required_text}")
    for forbidden_skill in ("`faro-int-jira`", "`faro-arq-laravel`", "`faro-req-ingenieria`", "`faro-entrega`"):
        if forbidden_skill in agents:
            failures.append(f"plantilla AGENTS replica política global: {forbidden_skill}")

    config = load_json(CONFIG_PATH, failures)
    required_config_fields = {
        "schemaVersion", "contractVersion", "authority", "workspace", "requiredDirectories",
        "requiredFiles", "conditionalFiles", "templateSources", "supportedStates", "compatibility",
        "workItems", "functionalDocuments", "initialization",
    }
    absent = required_config_fields - config.keys()
    if absent:
        failures.append("configuración FARO sin campos: " + ", ".join(sorted(absent)))
    if config.get("schemaVersion") != 2:
        failures.append("configuración FARO no declara schemaVersion 2")
    if config.get("contractVersion") != EXPECTED_VERSION:
        failures.append(f"configuración FARO no declara contractVersion {EXPECTED_VERSION}")
    required_files = config.get("requiredFiles")
    if not isinstance(required_files, list) or set(required_files) != EXPECTED_FILES:
        failures.append("configuración FARO tiene archivos obligatorios inesperados")
    if not isinstance(required_files, list) or len(required_files) != len(EXPECTED_FILES):
        failures.append("configuración FARO debe declarar siete archivos obligatorios únicos")
    required_directories = config.get("requiredDirectories")
    if (
        not isinstance(required_directories, list)
        or set(required_directories) != EXPECTED_DIRECTORIES
        or len(required_directories) != len(EXPECTED_DIRECTORIES)
    ):
        failures.append("configuración FARO tiene directorios obligatorios inesperados")
    authority = config.get("authority")
    if not isinstance(authority, dict) or authority.get("globalPolicy") != "faro/SKILL.md y skills faro-*":
        failures.append("configuración FARO no declara la autoridad global central")
    workspace = config.get("workspace", {})
    if not isinstance(workspace, dict):
        workspace = {}
    if any(workspace.get(key) != value for key, value in EXPECTED_WORKSPACE_PATHS.items()):
        failures.append("configuración FARO no declara las rutas canónicas v2 del workspace")
    template_sources = config.get("templateSources", {})
    if not isinstance(template_sources, dict):
        template_sources = {}
    if any(template_sources.get(key) != value for key, value in EXPECTED_TEMPLATE_SOURCES.items()):
        failures.append("configuración FARO no declara todas las plantillas canónicas v2")
    initialization = config.get("initialization", {})
    if not isinstance(initialization, dict):
        initialization = {}
    if workspace.get("glossaryPath") != "context/glossary.md":
        failures.append("configuración FARO sin ruta canónica de glosario")
    conditional_files = config.get("conditionalFiles")
    conditional_paths = {
        item.get("path") for item in conditional_files if isinstance(item, dict)
    } if isinstance(conditional_files, list) else set()
    if "context/glossary.md" not in conditional_paths:
        failures.append("glosario debe ser condicional, no obligatorio")
    if "context/faro-migration-v2.json" not in conditional_paths:
        failures.append("registro de migración v2 debe ser condicional, no obligatorio")
    if template_sources.get("glossary") != "faro/templates/glossary.md" or not (ROOT / "templates/glossary.md").is_file():
        failures.append("plantilla canónica de glosario ausente")
    for name, path in discovered.items():
        if name == "azure-devops-rest-v7":
            continue
        text = path.read_text(encoding="utf-8")
        if "domain-glossary.md" not in text or "context/glossary.md" not in text:
            failures.append(f"{name}: falta política transversal de glosario")
    if initialization.get("workTrackingModes") != ["OFF", "REQUIRED"]:
        failures.append("configuración FARO no declara modos de seguimiento válidos")
    if initialization.get("workTrackingProviders") != ["JIRA", "AZURE_DEVOPS"]:
        failures.append("configuración FARO no declara proveedores de seguimiento válidos")
    compatibility = config.get("compatibility", {})
    if not isinstance(compatibility, dict):
        compatibility = {}
    if (
        compatibility.get("diagnosticReadContracts") != ["1.13.0", EXPECTED_VERSION]
        or compatibility.get("writeContract") != EXPECTED_VERSION
        or compatibility.get("migrationCatalog") != "faro/references/contract-migrations.json"
    ):
        failures.append("configuración FARO no declara compatibilidad/migración v2 canónica")
    work_items = config.get("workItems", {})
    if not isinstance(work_items, dict):
        work_items = {}
    if work_items.get("supportedKinds") != ["RM", "BUG", "TEC"]:
        failures.append("configuración FARO no declara RM/BUG/TEC como expedientes v2")
    if work_items.get("idPattern") != "^(RM|BUG|TEC)-[0-9]{4}$":
        failures.append("configuración FARO no declara el patrón canónico de expedientes")
    if work_items.get("directoryPattern") != "context/requirements/work-items/<ID>":
        failures.append("configuración FARO no declara el directorio estable de expedientes")
    if work_items.get("primaryDocumentPattern") != "<ID>.md" or work_items.get("closurePattern") != "<ID>-cierre.json":
        failures.append("configuración FARO no declara primario/cierre canónicos de expedientes")
    if work_items.get("operationalStateAuthority") != "EXTERNAL_WORK_TRACKER":
        failures.append("configuración FARO no asigna el estado operativo al gestor externo")
    catalog_forbidden = work_items.get("catalogMustNotContain")
    forbidden_catalog_fields = {
        normalize_field(value) for value in catalog_forbidden
    } if isinstance(catalog_forbidden, list) else set()
    expected_forbidden = {
        normalize_field(value)
        for value in ("estado", "status", "prioridad", "priority", "asignado", "assignee", "sprint", "iteración", "área", "backlog")
    }
    if not expected_forbidden <= forbidden_catalog_fields:
        failures.append("configuración FARO no prohíbe estado/prioridad/asignación/backlog en catálogos")
    functional = config.get("functionalDocuments", {})
    if not isinstance(functional, dict):
        functional = {}
    if functional.get("idPattern") != "^DF-[0-9]{3}$":
        failures.append("configuración FARO no declara el patrón canónico de DF")
    if functional.get("directoryPattern") != "context/requirements/functional/<ID>":
        failures.append("configuración FARO no declara el directorio estable de DF")
    if functional.get("primaryDocumentPattern") != "<ID>.md":
        failures.append("configuración FARO no declara el primario canónico de DF")

    manifest = load_json(MANIFEST_PATH, failures)
    if manifest.get("schemaVersion") != 2:
        failures.append("manifiesto template no declara schemaVersion 2")
    if manifest.get("contractVersion") != EXPECTED_VERSION:
        failures.append("manifiesto template no coincide con la versión de contrato")
    if manifest.get("contractSource") != "faro/templates/faro-workspace-config.json":
        failures.append("manifiesto template no apunta al contrato central")
    if manifest.get("managedArtifacts") != config.get("requiredFiles"):
        failures.append("manifiesto template no coincide con artefactos obligatorios")

    for template in (
        "stats.json", "context-README.md", "project-profile.md", "requirements-catalog.md",
        "functional-documents-catalog.md", "work-item-closure.json", "workflow.json",
    ):
        if not (ROOT / "templates" / template).exists():
            failures.append(f"plantilla obligatoria ausente: {template}")
    stats = load_json(ROOT / "templates" / "stats.json", failures)
    if {"schemaVersion", "contractVersion", "faro", "project", "state", "updatedAt"} - stats.keys():
        failures.append("plantilla stats sin campos requeridos")
    if stats.get("contractVersion") != EXPECTED_VERSION:
        failures.append("stats template no coincide con la versión de contrato")
    if stats.get("schemaVersion") != 2:
        failures.append("stats template no declara schemaVersion 2")

    requirements_catalog_path = ROOT / "templates/requirements-catalog.md"
    if requirements_catalog_path.is_file():
        requirements_catalog = requirements_catalog_path.read_text(encoding="utf-8")
        expected_headers = {
            "| ID | Tipo | Fuente de reserva serializada | Fecha y zona |",
            "| ID | Tipo | Ruta canónica | Documento principal | Fuente de reserva serializada | Proveedor | ID remoto | URL remota | Relacionados |",
        }
        actual_headers = {line for line in requirements_catalog.splitlines() if line.startswith("| ID |")}
        if "catalog_kind: \"FARO_WORK_ITEMS\"" not in requirements_catalog or actual_headers != expected_headers:
            failures.append("catálogo de expedientes no declara el esquema localizador v2")
    functional_catalog_path = ROOT / "templates/functional-documents-catalog.md"
    if functional_catalog_path.is_file():
        functional_catalog = functional_catalog_path.read_text(encoding="utf-8")
        expected_headers = {
            "| ID | Fuente de reserva serializada | Fecha y zona |",
            "| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |",
        }
        actual_headers = {line for line in functional_catalog.splitlines() if line.startswith("| ID |")}
        if "catalog_kind: \"FARO_FUNCTIONAL_DOCUMENTS\"" not in functional_catalog or actual_headers != expected_headers:
            failures.append("catálogo funcional no declara el esquema localizador v2")

    provenance = load_json(PROVENANCE_PATH, failures)
    if provenance.get("schemaVersion") != 1 or provenance.get("ref") != f"refs/tags/v{provenance.get('packageVersion')}":
        failures.append("provenance de suite no declara su tag inmutable")
    if provenance.get("repository") != "https://github.com/matgro/faro-suite-skills" or provenance.get("integrityFile") != "checksums.sha256":
        failures.append("provenance de suite no declara repositorio/checksums válidos")

    workflow = load_json(ROOT / "templates" / "workflow.json", failures)
    if set(workflow) != EXPECTED_WORKFLOW_FIELDS:
        failures.append("workflow template no contiene exactamente los campos v2")
    if workflow.get("updatedAt") != "UPDATED_AT":
        failures.append("workflow template debe conservar el marcador UPDATED_AT")
    workflow_example = dict(workflow)
    workflow_example["updatedAt"] = "2000-01-01T00:00:00Z"
    failures.extend(
        "workflow template inválido: " + problem.removeprefix("workflow: ")
        for problem in validate_workflow_structure(workflow_example)
    )

    cases = ROOT / "references" / "routing-cases.md"
    if not cases.exists():
        failures.append("casos de ruteo ausentes")
    else:
        cases_text = cases.read_text(encoding="utf-8")
        for case in ("Inicialización nueva", "Inicialización repetida", "faro-doctor"):
            if case not in cases_text:
                failures.append(f"caso de ruteo ausente: {case}")

    if failures:
        print("FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1
    print(f"PASS: {len(discovered)} skills FARO, autoridad central y contrato {EXPECTED_VERSION} válidos")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
