#!/usr/bin/env python3
"""Static contract checks for FARO routing, policy authority and templates."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.dont_write_bytecode = True
from suite_validation import validate_suite

ROOT = Path(__file__).resolve().parents[1]
REQUIRED = {
    "faro", "faro-inicializacion", "faro-doctor", "faro-bootstrap-laravel", "faro-arq-laravel", "faro-arq-mobile",
    "faro-arq-generica", "faro-documentacion-funcional", "faro-req-ingenieria",
    "faro-req-analisis-tecnico", "faro-req-desarrollo", "faro-qa-ejecucion",
    "faro-req-validacion", "faro-ux", "faro-entrega", "faro-int-jira", "faro-int-azure-devops",
    "azure-devops-rest-v7",
}
CONFIG_PATH = ROOT / "templates" / "faro-workspace-config.json"
MANIFEST_PATH = ROOT / "templates" / "faro-workspace-manifest.json"
PROVENANCE_PATH = ROOT / "references" / "suite-provenance.json"
EXPECTED_VERSION = "1.13.0"
EXPECTED_FILES = {
    "AGENTS.md", "context/faro-workspace.json", "context/stats.json",
    "context/README.md", "context/requirements/project-profile.md",
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
        return json.loads(path.read_text(encoding="utf-8"))
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
        "requiredFiles", "conditionalFiles", "templateSources", "supportedStates", "initialization",
    }
    absent = required_config_fields - config.keys()
    if absent:
        failures.append("configuración FARO sin campos: " + ", ".join(sorted(absent)))
    if config.get("contractVersion") != EXPECTED_VERSION:
        failures.append(f"configuración FARO no declara contractVersion {EXPECTED_VERSION}")
    if set(config.get("requiredFiles", [])) != EXPECTED_FILES:
        failures.append("configuración FARO tiene archivos obligatorios inesperados")
    if config.get("authority", {}).get("globalPolicy") != "faro/SKILL.md y skills faro-*":
        failures.append("configuración FARO no declara la autoridad global central")
    if config.get("templateSources", {}).get("manifest") != "faro/templates/faro-workspace-manifest.json":
        failures.append("configuración FARO no declara la plantilla de manifiesto")
    initialization = config.get("initialization", {})
    if initialization.get("workTrackingModes") != ["OFF", "REQUIRED"]:
        failures.append("configuración FARO no declara modos de seguimiento válidos")
    if initialization.get("workTrackingProviders") != ["JIRA", "AZURE_DEVOPS"]:
        failures.append("configuración FARO no declara proveedores de seguimiento válidos")

    manifest = load_json(MANIFEST_PATH, failures)
    if manifest.get("contractVersion") != EXPECTED_VERSION:
        failures.append("manifiesto template no coincide con la versión de contrato")
    if manifest.get("contractSource") != "faro/templates/faro-workspace-config.json":
        failures.append("manifiesto template no apunta al contrato central")
    if manifest.get("managedArtifacts") != config.get("requiredFiles"):
        failures.append("manifiesto template no coincide con artefactos obligatorios")

    for template in ("stats.json", "context-README.md", "project-profile.md", "workflow.json"):
        if not (ROOT / "templates" / template).exists():
            failures.append(f"plantilla obligatoria ausente: {template}")
    stats = load_json(ROOT / "templates" / "stats.json", failures)
    if {"schemaVersion", "contractVersion", "faro", "project", "state", "updatedAt"} - stats.keys():
        failures.append("plantilla stats sin campos requeridos")
    if stats.get("contractVersion") != EXPECTED_VERSION:
        failures.append("stats template no coincide con la versión de contrato")

    provenance = load_json(PROVENANCE_PATH, failures)
    if provenance.get("schemaVersion") != 1 or provenance.get("ref") != f"refs/tags/v{provenance.get('packageVersion')}":
        failures.append("provenance de suite no declara su tag inmutable")
    if provenance.get("repository") != "https://github.com/matgro/faro-suite-skills" or provenance.get("integrityFile") != "checksums.sha256":
        failures.append("provenance de suite no declara repositorio/checksums válidos")

    workflow = load_json(ROOT / "templates" / "workflow.json", failures)
    workflow_fields = {"schemaVersion", "updatedAt", "active", "phase", "authorization", "currentUnit", "waitingOn", "nextRoute", "notes"}
    absent_workflow = workflow_fields - workflow.keys()
    if absent_workflow:
        failures.append("workflow template sin campos: " + ", ".join(sorted(absent_workflow)))

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
