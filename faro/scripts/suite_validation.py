#!/usr/bin/env python3
"""Read-only validation shared by package checks and workspace diagnostics."""
from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import re
import unicodedata

SKILL_NAME = re.compile(r"(?:faro(?:-[a-z0-9]+)*|azure-devops-rest-v7)\Z")
SEMVER = re.compile(r"\d+\.\d+\.\d+\Z")
WORKFLOW_FIELDS = {
    "schemaVersion", "updatedAt", "phase", "authorization", "workItemRef",
    "waitingOn", "nextRoute", "checkpoint", "notes",
}
AUTHORIZATION_FIELDS = {"status", "source", "artifactVersion", "scope"}
WORK_ITEM_ID = re.compile(r"(?:RM|BUG|TEC|INC)-[0-9]{4}\Z")
OPERATIONAL_WORKFLOW_FIELDS = {
    "active", "currentUnit", "status", "state", "estado", "priority", "prioridad",
    "assignedTo", "assigned", "assignee", "asignado", "backlog", "queue", "cola",
    "completedUnits", "todo", "doing", "done", "dropped", "sprint", "iteration",
    "iteracion", "area",
}


def suite_inventory(suite: Path) -> tuple[set[str], list[str]]:
    names: set[str] = set()
    references: list[tuple[Path, str]] = []
    problems: list[str] = []
    router_names: set[str] = set()
    for path in sorted(suite.rglob("SKILL.md")):
        text = path.read_text(encoding="utf-8")
        header = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        if not header:
            problems.append(f"{path.relative_to(suite)}: frontmatter ausente")
            continue
        name_match = re.search(r"^name:\s*([a-z0-9-]+)\s*$", header.group(1), re.MULTILINE)
        if not name_match:
            problems.append(f"{path.relative_to(suite)}: name inválido")
            continue
        name = name_match.group(1)
        expected_path = Path("SKILL.md") if name == "faro" else Path(name) / "SKILL.md"
        if path.relative_to(suite) != expected_path:
            problems.append(f"{path.relative_to(suite)}: nombre/ruta no coincide con {name}")
        if name in names:
            problems.append(f"nombre de skill duplicado: {name}")
        names.add(name)
        related = re.search(r"^\s+related_skills:\s*\[([^\]]*)\]\s*$", header.group(1), re.MULTILINE)
        if not related:
            problems.append(f"{path.relative_to(suite)}: related_skills debe ser una lista inline")
            continue
        related_names = [value.strip() for value in related.group(1).split(",") if value.strip()]
        references.extend((path, value) for value in related_names)
        if name == "faro":
            router_names = set(related_names)

    if "faro" not in names:
        problems.append("falta el router faro/SKILL.md")
    elif router_names != names - {"faro"}:
        problems.append("el catálogo related_skills del router no coincide con las skills distribuidas")
    for path, name in references:
        if SKILL_NAME.fullmatch(name) and name not in names:
            problems.append(f"{path.relative_to(suite)}: related_skills apunta a skill ausente: {name}")
    for path in sorted(suite.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for relative in sorted(set(re.findall(r"\[[^\]]+\]\(((?:\.\./)?references/[^)\s#]+)(?:#[^)\s]*)?\)", text))):
            reference = path.parent / relative
            if not reference.is_file():
                problems.append(f"{path.relative_to(suite)}: archivo de referencia ausente: {relative}")
            elif reference.suffix == ".md" and not reference.read_text(encoding="utf-8").strip():
                problems.append(f"{path.relative_to(suite)}: archivo de referencia vacío: {relative}")
        for name in sorted(set(re.findall(r"`(faro-[a-z0-9-]+|azure-devops-rest-v7)`", text))):
            if name not in names:
                problems.append(f"{path.relative_to(suite)}: referencia a skill ausente: {name}")
    return names, problems


def read_changelog(suite: Path) -> dict:
    path = suite / "references/suite-changelog.json"
    changelog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(changelog, dict) or changelog.get("schemaVersion") != 1:
        raise ValueError("schemaVersion debe ser 1")
    releases = changelog.get("releases")
    if not isinstance(releases, list) or not releases:
        raise ValueError("releases debe ser una lista no vacía")
    versions: set[str] = set()
    renamed: dict[str, str] = {}
    for release in releases:
        if not isinstance(release, dict):
            raise ValueError("release debe ser un objeto")
        version = release.get("version")
        if not isinstance(version, str) or not re.fullmatch(r"\d+\.\d+\.\d+", version) or version in versions:
            raise ValueError("versión de release inválida o duplicada")
        versions.add(version)
        changes = release.get("changes")
        if not isinstance(changes, list) or not changes or not all(isinstance(item, str) and item.strip() for item in changes):
            raise ValueError(f"{version}: changes debe contener descripciones")
        mappings = release.get("renamedSkills", {})
        if not isinstance(mappings, dict):
            raise ValueError(f"{version}: renamedSkills debe ser un objeto")
        for old, new in mappings.items():
            if not SKILL_NAME.fullmatch(old) or not isinstance(new, str) or not SKILL_NAME.fullmatch(new) or old == new:
                raise ValueError(f"{version}: renombre inválido")
            if old in renamed:
                raise ValueError(f"renombre duplicado: {old}")
            renamed[old] = new
    for old in renamed:
        visited: set[str] = set()
        target = old
        while target in renamed:
            if target in visited:
                raise ValueError(f"ciclo de renombres: {old}")
            visited.add(target)
            target = renamed[target]
    return changelog


def is_relative_catalog_path(value: object) -> bool:
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9_./-]+", value):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def normalize_field(value: object) -> str:
    text = unicodedata.normalize("NFKD", str(value).casefold())
    return re.sub(r"[^a-z0-9]", "", "".join(character for character in text if not unicodedata.combining(character)))


def is_safe_workflow_path(value: object) -> bool:
    if (
        not isinstance(value, str)
        or not value
        or value.startswith(("/", "\\"))
        or "\\" in value
        or ":" in value
        or "|" in value
    ):
        return False
    if any(ord(character) < 32 for character in value):
        return False
    return all(part not in {"", ".", ".."} for part in value.split("/"))


def is_zoned_timestamp(value: object) -> bool:
    if not isinstance(value, str) or not value.strip():
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None


def read_contract_migrations(suite: Path) -> dict:
    """Read and validate the declared, explicit workspace-contract migrations."""
    path = suite / "references/contract-migrations.json"
    catalog = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(catalog, dict) or set(catalog) != {"schemaVersion", "migrations"}:
        raise ValueError("el catálogo debe contener sólo schemaVersion y migrations")
    if catalog.get("schemaVersion") != 1:
        raise ValueError("schemaVersion debe ser 1")
    migrations = catalog.get("migrations")
    if not isinstance(migrations, list) or not migrations:
        raise ValueError("migrations debe ser una lista no vacía")

    expected_fields = {
        "fromContract", "toContract", "script", "authorization", "readCompatibility",
        "writeCompatibility", "description",
    }
    transitions: set[tuple[str, str]] = set()
    sources: set[str] = set()
    graph: dict[str, str] = {}
    for migration in migrations:
        if not isinstance(migration, dict) or set(migration) != expected_fields:
            raise ValueError("cada migración debe declarar exactamente sus siete campos")
        source, target = migration.get("fromContract"), migration.get("toContract")
        if not isinstance(source, str) or not SEMVER.fullmatch(source):
            raise ValueError("fromContract debe ser una versión semántica")
        if not isinstance(target, str) or not SEMVER.fullmatch(target) or target == source:
            raise ValueError("toContract debe ser una versión semántica diferente")
        transition = (source, target)
        if transition in transitions or source in sources:
            raise ValueError(f"migración duplicada o ambigua desde {source}")
        transitions.add(transition)
        sources.add(source)
        graph[source] = target

        script = migration.get("script")
        if not is_relative_catalog_path(script) or not str(script).startswith("faro/scripts/") or not str(script).endswith(".py"):
            raise ValueError(f"{source}: script debe ser una ruta Python segura bajo faro/scripts")
        relative_script = str(script).removeprefix("faro/")
        script_path = suite / relative_script
        if not script_path.is_file() or script_path.is_symlink():
            raise ValueError(f"{source}: script de migración ausente o no regular: {script}")
        cursor = script_path.parent
        while cursor != suite:
            if cursor.is_symlink():
                raise ValueError(f"{source}: script de migración atraviesa un symlink: {script}")
            if suite not in cursor.parents:
                raise ValueError(f"{source}: script de migración escapa de la suite: {script}")
            cursor = cursor.parent
        if migration.get("authorization") != "EXPLICIT_APPLY":
            raise ValueError(f"{source}: authorization debe ser EXPLICIT_APPLY")
        if migration.get("readCompatibility") != "DIAGNOSTIC_ONLY":
            raise ValueError(f"{source}: readCompatibility debe ser DIAGNOSTIC_ONLY")
        if migration.get("writeCompatibility") != "V2_ONLY":
            raise ValueError(f"{source}: writeCompatibility debe ser V2_ONLY")
        description = migration.get("description")
        if not isinstance(description, str) or not description.strip():
            raise ValueError(f"{source}: description debe ser texto no vacío")

    for source in graph:
        seen: set[str] = set()
        current = source
        while current in graph:
            if current in seen:
                raise ValueError(f"ciclo de migraciones desde {source}")
            seen.add(current)
            current = graph[current]

    config_path = suite / "templates/faro-workspace-config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(config, dict) or config.get("schemaVersion") != 2:
        raise ValueError("la configuración canónica debe usar schemaVersion 2")
    contract_version = config.get("contractVersion")
    compatibility = config.get("compatibility")
    if not isinstance(contract_version, str) or not SEMVER.fullmatch(contract_version):
        raise ValueError("contractVersion canónico inválido")
    if not isinstance(compatibility, dict):
        raise ValueError("compatibility debe ser un objeto")
    if compatibility.get("writeContract") != contract_version:
        raise ValueError("writeContract debe coincidir con contractVersion")
    if compatibility.get("migrationCatalog") != "faro/references/contract-migrations.json":
        raise ValueError("migrationCatalog no apunta al catálogo canónico")
    read_contracts = compatibility.get("diagnosticReadContracts")
    if (
        not isinstance(read_contracts, list)
        or not read_contracts
        or not all(isinstance(item, str) and SEMVER.fullmatch(item) for item in read_contracts)
        or len(read_contracts) != len(set(read_contracts))
    ):
        raise ValueError("diagnosticReadContracts debe listar versiones semánticas únicas")
    if set(read_contracts) != sources | {contract_version}:
        raise ValueError("diagnosticReadContracts no coincide con orígenes migrables y contrato vigente")
    if any(target != contract_version for _source, target in transitions):
        raise ValueError("cada migración debe terminar en el contrato de escritura vigente")
    return catalog


def validate_contract_migrations(suite: Path) -> list[str]:
    try:
        read_contract_migrations(suite)
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        return [f"catálogo de migraciones inválido: {error}"]
    return []


def validate_incident_capabilities(suite: Path) -> list[str]:
    """Validate declared provenance, not installation or upstream safety."""
    path = suite / "references/incident-external-skills.json"
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(catalog, dict) or catalog.get("schemaVersion") != 1:
            raise ValueError("schemaVersion debe ser 1")
        sources = catalog.get("sources")
        if not isinstance(sources, list) or not sources:
            raise ValueError("sources debe ser una lista no vacía")
        roles: set[str] = set()
        skills: set[str] = set()
        for source in sources:
            if not isinstance(source, dict):
                raise ValueError("source debe ser un objeto")
            repository = source.get("repository")
            if not isinstance(repository, str) or not re.fullmatch(r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", repository):
                raise ValueError("repository debe identificar un repositorio GitHub sin credenciales")
            revision = source.get("revision")
            if not isinstance(revision, str) or not re.fullmatch(r"[0-9a-f]{40}", revision):
                raise ValueError("revision debe ser un commit completo, no una rama mutable")
            role = source.get("role")
            if role not in {"investigation", "postmortem"} or role in roles:
                raise ValueError("role inválido o duplicado")
            roles.add(role)
            names = source.get("skills")
            if not isinstance(names, list) or not names:
                raise ValueError("skills debe ser una lista no vacía")
            for name in names:
                if not isinstance(name, str) or not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", name) or name in skills:
                    raise ValueError("nombre externo inválido o duplicado")
                skills.add(name)
            for field in ("path", "licensePath"):
                relative = source.get(field)
                if not is_relative_catalog_path(relative):
                    raise ValueError(f"{field} debe ser una ruta relativa segura")
            if source.get("entrypoint") != "SKILL.md" or source.get("license") != "MIT":
                raise ValueError("entrypoint/licencia no coincide con las capacidades revisadas")
            files = source.get("requiredFiles")
            if not isinstance(files, dict) or "SKILL.md" not in files:
                raise ValueError("requiredFiles debe incluir SKILL.md")
            for relative, digest in files.items():
                if not is_relative_catalog_path(relative):
                    raise ValueError("requiredFiles contiene una ruta insegura")
                if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                    raise ValueError("requiredFiles debe declarar hashes SHA-256")
            license_digest = source.get("licenseSha256")
            if not isinstance(license_digest, str) or not re.fullmatch(r"[0-9a-f]{64}", license_digest):
                raise ValueError("licenseSha256 debe ser SHA-256")
            if "systematic-debugging" in names and "root-cause-tracing.md" not in files:
                raise ValueError("systematic-debugging requiere root-cause-tracing.md")
        if roles != {"investigation", "postmortem"}:
            raise ValueError("se requieren roles investigation y postmortem")
    except (OSError, ValueError, TypeError) as error:
        return [f"catálogo de incidentes inválido: {error}"]
    return []


def validate_suite(suite: Path) -> list[str]:
    names, problems = suite_inventory(suite)
    if "faro-incidentes" in names:
        problems.extend(validate_incident_capabilities(suite))
    problems.extend(validate_contract_migrations(suite))
    try:
        provenance = json.loads((suite / "references/suite-provenance.json").read_text(encoding="utf-8"))
        changelog = read_changelog(suite)
        if changelog["releases"][0]["version"] != provenance["packageVersion"]:
            problems.append("changelog: la primera release no coincide con packageVersion")
        renamed = {old: new for release in changelog["releases"] for old, new in release.get("renamedSkills", {}).items()}
        for old, target in renamed.items():
            if old in names:
                problems.append(f"changelog: skill retirada todavía instalada: {old}")
            while target in renamed:
                target = renamed[target]
            if target not in names:
                problems.append(f"changelog: destino de renombre ausente: {target}")
    except (OSError, ValueError, KeyError, TypeError) as error:
        problems.append(f"changelog/provenance inválido: {error}")
    return problems


def validate_workflow_structure(workflow: object) -> list[str]:
    if not isinstance(workflow, dict):
        return ["workflow: debe ser un objeto JSON"]

    problems: list[str] = []
    fields = set(workflow)
    missing = WORKFLOW_FIELDS - fields
    extra = fields - WORKFLOW_FIELDS
    if missing:
        problems.append("workflow: faltan campos v2: " + ", ".join(sorted(missing)))
    if extra:
        problems.append("workflow: contiene campos no permitidos: " + ", ".join(sorted(extra)))
    forbidden = {normalize_field(value) for value in OPERATIONAL_WORKFLOW_FIELDS}
    operational = sorted(str(key) for key in workflow if normalize_field(key) in forbidden)
    if operational:
        problems.append("workflow: contiene estado operativo prohibido: " + ", ".join(operational))
    if workflow.get("schemaVersion") != 2:
        problems.append("workflow: schemaVersion debe ser 2")

    updated_at = workflow.get("updatedAt")
    if not is_zoned_timestamp(updated_at):
        problems.append("workflow: updatedAt debe ser ISO-8601 con zona horaria")
    phase = workflow.get("phase")
    if phase is not None and (not isinstance(phase, str) or not phase.strip()):
        problems.append("workflow: phase debe ser texto no vacío o null")

    authorization = workflow.get("authorization")
    if not isinstance(authorization, dict):
        problems.append("workflow: authorization debe ser un objeto")
    else:
        authorization_fields = set(authorization)
        if authorization_fields != AUTHORIZATION_FIELDS:
            missing_authorization = AUTHORIZATION_FIELDS - authorization_fields
            extra_authorization = authorization_fields - AUTHORIZATION_FIELDS
            detail: list[str] = []
            if missing_authorization:
                detail.append("faltan " + ", ".join(sorted(missing_authorization)))
            if extra_authorization:
                detail.append("sobran " + ", ".join(sorted(extra_authorization)))
            problems.append("workflow: authorization inválida (" + "; ".join(detail) + ")")
        status = authorization.get("status")
        if not isinstance(status, str) or not status.strip():
            problems.append("workflow: authorization.status debe ser texto no vacío")
        for field in ("source", "artifactVersion", "scope"):
            value = authorization.get(field)
            if value is not None and (not isinstance(value, str) or not value.strip()):
                problems.append(f"workflow: authorization.{field} debe ser texto no vacío o null")

    reference = workflow.get("workItemRef")
    if reference is not None:
        if not isinstance(reference, dict) or set(reference) != {"id", "path"}:
            problems.append("workflow: workItemRef debe ser null o contener exactamente id y path")
        else:
            identifier, relative = reference.get("id"), reference.get("path")
            if not isinstance(identifier, str) or not WORK_ITEM_ID.fullmatch(identifier):
                problems.append("workflow: workItemRef.id debe ser RM/BUG/TEC/INC-NNNN en mayúsculas")
            if not is_safe_workflow_path(relative):
                problems.append("workflow: workItemRef.path debe ser una ruta relativa segura")
            elif isinstance(identifier, str) and WORK_ITEM_ID.fullmatch(identifier):
                if identifier.startswith(("RM-", "BUG-", "TEC-")):
                    expected = f"context/requirements/work-items/{identifier}"
                    if relative != expected:
                        problems.append(f"workflow: workItemRef.path debe ser {expected}")
                elif not re.fullmatch(rf"context/incidents/{re.escape(identifier)}-[^/]+\.md", str(relative)):
                    problems.append("workflow: una referencia INC debe apuntar a context/incidents/<ID>-<slug>.md")

    waiting_on = workflow.get("waitingOn")
    if waiting_on is not None and not isinstance(waiting_on, (str, dict)):
        problems.append("workflow: waitingOn debe ser texto, objeto o null")
    if isinstance(waiting_on, str) and not waiting_on.strip():
        problems.append("workflow: waitingOn no puede ser texto vacío")
    notes = workflow.get("notes")
    if not isinstance(notes, list) or not all(isinstance(note, str) for note in notes):
        problems.append("workflow: notes debe ser una lista de textos")

    checkpoint = workflow.get("checkpoint")
    if checkpoint is not None and not isinstance(checkpoint, (str, dict)):
        problems.append("workflow: checkpoint debe ser null, texto u objeto")
    if isinstance(checkpoint, str) and not checkpoint.strip():
        problems.append("workflow: checkpoint no puede ser texto vacío")
    operational_nested: list[str] = []

    def visit(value: object, prefix: str) -> None:
        if isinstance(value, dict):
            for key, nested in value.items():
                location = f"{prefix}.{key}"
                if normalize_field(key) in forbidden:
                    operational_nested.append(location)
                visit(nested, location)
        elif isinstance(value, list):
            for index, nested in enumerate(value):
                visit(nested, f"{prefix}[{index}]")

    visit(checkpoint, "checkpoint")
    visit(waiting_on, "waitingOn")
    if operational_nested:
        problems.append(
            "workflow: checkpoint/waitingOn contiene estado operativo prohibido: "
            + ", ".join(operational_nested)
        )
    return problems


def validate_workflow(path: Path, suite: Path) -> list[str]:
    if path.is_symlink():
        return ["workflow: debe ser un archivo regular, no un symlink"]
    if not path.exists():
        return []
    if not path.is_file():
        return ["workflow: debe ser un archivo regular, no un symlink"]
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
        problems = validate_workflow_structure(workflow)
        if not isinstance(workflow, dict):
            return problems
        route = workflow.get("nextRoute")
        if route is None:
            return problems
        if not isinstance(route, str) or not route:
            problems.append("workflow: nextRoute debe ser un nombre de skill o null")
            return problems
        changelog = read_changelog(suite)
        renamed = {old: new for release in changelog["releases"] for old, new in release.get("renamedSkills", {}).items()}
        names, _ = suite_inventory(suite)
        if route in renamed:
            target = renamed[route]
            while target in renamed:
                target = renamed[target]
            problems.append(f"workflow: ruta renombrada {route} -> {target}; requiere autorización explícita para actualizar sólo nextRoute")
        elif route == "azure-devops-rest-v7":
            problems.append(
                "workflow: azure-devops-rest-v7 es una capability del adaptador, no una nextRoute directa"
            )
        elif route not in names:
            problems.append(f"workflow: nextRoute apunta a skill ausente: {route}")
        return problems
    except (OSError, ValueError, TypeError, json.JSONDecodeError) as error:
        return [f"workflow/changelog inválido: {error}"]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suite-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--workflow", type=Path, help="Workflow opcional; se inspecciona sin modificarlo.")
    args = parser.parse_args()
    problems = validate_suite(args.suite_root)
    if args.workflow:
        problems.extend(validate_workflow(args.workflow, args.suite_root))
    if problems:
        print("FAIL:\n" + "\n".join(f"- {item}" for item in problems))
        return 1
    print("PASS: nombres, rutas, referencias y changelog de la suite coherentes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
