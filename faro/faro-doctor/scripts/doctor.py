#!/usr/bin/env python3
"""Read-only FARO workspace diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = SKILL_ROOT / "templates" / "faro-workspace-config.json"
PROVENANCE_PATH = SKILL_ROOT / "references" / "suite-provenance.json"
EXTERNAL_SKILLS_PATH = SKILL_ROOT / "references" / "laravel-external-skills.json"
MIGRATIONS_PATH = SKILL_ROOT / "references" / "contract-migrations.json"
HELPER_PATH = SKILL_ROOT / "scripts" / "work_item_contract.py"
EXPECTED_VERSION = "2.0.0"
LEGACY_REQUIRED_DIRECTORIES = ("context", "context/requirements")
LEGACY_REQUIRED_FILES = (
    "AGENTS.md",
    "context/faro-workspace.json",
    "context/stats.json",
    "context/README.md",
    "context/requirements/project-profile.md",
)
WORKSPACE_CLASSIFICATIONS = {
    "absent",
    "current",
    "legacy-migratable",
    "mixed-ambiguous",
    "future-unsupported",
    "corrupt",
}

sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from suite_validation import validate_suite, validate_workflow


def load_json(path: Path) -> tuple[dict | None, str | None]:
    if path.is_symlink():
        return None, "inválido: no es un archivo regular"
    if not path.exists():
        return None, "ausente"
    if not path.is_file():
        return None, "inválido: no es un archivo regular"
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except Exception as error:
        return None, f"inválido: {error}"
    if not isinstance(value, dict):
        return None, "inválido: el JSON debe ser un objeto"
    return value, None


def profile_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else "no registrado"


def semantic_version(value: object) -> tuple[int, int, int] | None:
    if not isinstance(value, str):
        return None
    match = re.fullmatch(r"(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)", value)
    if match is None:
        return None
    return tuple(int(part) for part in match.groups())


def runtime_skill_versions() -> tuple[str, str]:
    """Return the router version and a compact inventory of runtime skill versions.

    Individual skills deliberately have their own lifecycle. This is diagnostic
    context only: the package and contract compatibility rules remain separate.
    """
    versions: list[str] = []
    router_version = "no registrada"
    skill_files = [SKILL_ROOT / "SKILL.md", *sorted(SKILL_ROOT.glob("*/SKILL.md"))]
    for path in skill_files:
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            continue
        match = re.search(r"^version:\s*([^\s#]+)\s*$", text, flags=re.MULTILINE)
        if match is None:
            continue
        version = match.group(1).strip('"\'')
        if path == SKILL_ROOT / "SKILL.md":
            router_version = version
        if semantic_version(version) is not None:
            versions.append(version)
    unique = sorted(set(versions), key=lambda value: semantic_version(value) or (0, 0, 0))
    return router_version, ", ".join(unique) if unique else "no registradas"


def workflow_schema_status(root: Path) -> str:
    """Describe workflow continuity without treating it as a release version."""
    workflow, error = load_json(root / "context/workflow.json")
    if error == "ausente":
        return "sin workflow activo"
    if error:
        return f"inválido ({error})"
    if not isinstance(workflow, dict):
        return "inválido (raíz no es objeto)"
    schema = workflow.get("schemaVersion", "no registrado")
    return f"schema {schema} (checkpoint temporal; no versión de release)"


def agents_contract(root: Path) -> dict:
    path = root / "AGENTS.md"
    result = {
        "path": path,
        "exists": path.exists() or path.is_symlink(),
        "has_marker": False,
        "valid": False,
        "block": None,
        "version": None,
        "error": None,
    }
    if not result["exists"]:
        return result
    if path.is_symlink() or not path.is_file():
        result["error"] = "AGENTS.md no es un archivo regular"
        return result
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as error:
        result["error"] = f"AGENTS.md no se puede leer: {error}"
        return result
    start_marker = "<!-- FARO:START -->"
    end_marker = "<!-- FARO:END -->"
    starts = [match.start() for match in re.finditer(re.escape(start_marker), text)]
    ends = [match.end() for match in re.finditer(re.escape(end_marker), text)]
    result["has_marker"] = bool(starts or ends)
    if not starts and not ends:
        return result
    if len(starts) != 1 or len(ends) != 1 or starts[0] >= ends[0]:
        result["error"] = (
            "AGENTS.md tiene delimitadores FARO inválidos "
            f"(START={len(starts)}, END={len(ends)})"
        )
        return result
    block = text[starts[0]:ends[0]]
    result["block"] = block
    result["valid"] = True
    version = re.search(r"Contrato instalado:\s*FARO\s*`([^`]+)`", block)
    if version:
        result["version"] = version.group(1)
    else:
        result["error"] = "bloque FARO de AGENTS.md sin versión de contrato"
    return result


def profile_schema_version(path: Path) -> int | None:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None
    matches = [
        match.group(1)
        for line in lines[1:end]
        if (match := re.fullmatch(r"profile_version:\s*[\"']?([0-9]+)[\"']?\s*", line))
    ]
    return int(matches[0]) if len(matches) == 1 else None


def validate_profile_v2(path: Path) -> list[str]:
    if path.is_symlink() or not path.is_file():
        return ["perfil v2 ausente, no regular o symlink"]
    text = path.read_text(encoding="utf-8", errors="replace")
    problems: list[str] = []
    if profile_schema_version(path) != 2:
        problems.append("perfil v2: profile_version debe ser 2")
    credential_status = profile_value(text, "credential_status").strip("`\"'")
    if credential_status != "VERIFICADO":
        assumed_defaults = {
            r"^\s+TASK:\s+Task\s*$": "tipo remoto TASK=Task",
            r"^\s+activity_field:\s+Microsoft\.VSTS\.Common\.Activity\s*$": "campo remoto de actividad",
            r"^\s+estimate_field:\s+Microsoft\.VSTS\.Scheduling\.RemainingWork\s*$": "campo remoto de estimación",
            r"^\s+estimate:\s+1(?:\.0)?\s*$": "estimación remota por defecto",
        }
        for pattern, label in assumed_defaults.items():
            if re.search(pattern, text, re.MULTILINE):
                problems.append(
                    f"perfil v2 acredita {label} sin credential_status VERIFICADO"
                )
    return problems


def catalog_metadata(path: Path) -> tuple[dict[str, str] | None, str | None]:
    if path.is_symlink() or not path.is_file():
        return None, "ausente, no regular o symlink"
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        return None, f"ilegible: {error}"
    if not lines or lines[0].strip() != "---":
        return None, "front matter ausente"
    try:
        end = next(index for index, line in enumerate(lines[1:], 1) if line.strip() == "---")
    except StopIteration:
        return None, "front matter sin cierre"
    metadata: dict[str, str] = {}
    for line in lines[1:end]:
        if not line.strip():
            continue
        if ":" not in line:
            return None, f"front matter inválido: {line!r}"
        key, value = line.split(":", 1)
        key = key.strip()
        if key in metadata:
            return None, f"front matter duplica {key}"
        metadata[key] = value.strip().strip("\"'")
    return metadata, None


def required_path_problems(
    root: Path,
    directories: list[str] | tuple[str, ...],
    files: list[str] | tuple[str, ...],
) -> list[str]:
    problems: list[str] = []
    for relative in directories:
        path = root / relative
        if path.is_symlink():
            problems.append(f"{relative}: debe ser un directorio regular sin symlink")
        elif not path.exists():
            problems.append(f"{relative}: directorio requerido ausente")
        elif not path.is_dir():
            problems.append(f"{relative}: debe ser un directorio regular sin symlink")
    for relative in files:
        path = root / relative
        if path.is_symlink():
            problems.append(f"{relative}: debe ser un archivo regular sin symlink")
        elif not path.exists():
            problems.append(f"{relative}: archivo requerido ausente")
        elif not path.is_file():
            problems.append(f"{relative}: debe ser un archivo regular sin symlink")
    return problems


def validate_manifest(
    manifest: dict | None,
    error: str | None,
    *,
    schema: int,
    version: str,
    artifacts: list[str] | tuple[str, ...],
) -> list[str]:
    if error or manifest is None:
        return [f"manifiesto: {error or 'inválido'}"]
    problems: list[str] = []
    expected_keys = {"schemaVersion", "contractVersion", "contractSource", "managedArtifacts"}
    if set(manifest) != expected_keys:
        problems.append(
            "manifiesto: campos inválidos; esperados "
            + ", ".join(sorted(expected_keys))
        )
    if manifest.get("schemaVersion") != schema:
        problems.append(f"manifiesto: schemaVersion debe ser {schema}")
    if manifest.get("contractVersion") != version:
        problems.append(f"manifiesto: contractVersion debe ser {version}")
    if manifest.get("contractSource") != "faro/templates/faro-workspace-config.json":
        problems.append("manifiesto: contractSource no coincide")
    if manifest.get("managedArtifacts") != list(artifacts):
        problems.append("manifiesto: managedArtifacts no coincide exactamente")
    return problems


def validate_stats(
    stats: dict | None,
    error: str | None,
    *,
    schema: int,
    version: str,
    states: list[str],
) -> list[str]:
    if error or stats is None:
        return [f"stats.json: {error or 'inválido'}"]
    problems: list[str] = []
    expected_keys = {
        "schemaVersion", "contractVersion", "faro", "project", "state", "updatedAt"
    }
    if set(stats) != expected_keys:
        problems.append(
            "stats.json: campos inválidos; esperados "
            + ", ".join(sorted(expected_keys))
        )
    if stats.get("schemaVersion") != schema:
        problems.append(f"stats.json: schemaVersion debe ser {schema}")
    if stats.get("contractVersion") != version:
        problems.append(f"stats.json: contractVersion debe ser {version}")
    faro = stats.get("faro")
    if not isinstance(faro, dict) or set(faro) != {"name", "version"}:
        problems.append("stats.json: faro debe ser {name, version}")
    elif not isinstance(faro.get("name"), str) or not faro.get("name"):
        problems.append("stats.json: faro.name debe ser texto no vacío")
    elif semantic_version(faro.get("version")) is None:
        problems.append("stats.json: faro.version debe ser una versión semántica")
    project = stats.get("project")
    if not isinstance(project, dict) or set(project) != {"name", "type", "repositories"}:
        problems.append("stats.json: project debe ser {name, type, repositories}")
    else:
        if project.get("name") is not None and not isinstance(project.get("name"), str):
            problems.append("stats.json: project.name debe ser texto o null")
        if project.get("type") is not None and not isinstance(project.get("type"), str):
            problems.append("stats.json: project.type debe ser texto o null")
        if not isinstance(project.get("repositories"), list):
            problems.append("stats.json: project.repositories debe ser una lista")
        elif not all(
            isinstance(repository, str) and repository.strip()
            for repository in project["repositories"]
        ):
            problems.append(
                "stats.json: cada project.repositories debe ser texto no vacío"
            )
    if stats.get("state") not in states:
        problems.append("stats.json: state no está soportado")
    updated_at = stats.get("updatedAt")
    if not isinstance(updated_at, str) or not updated_at:
        problems.append("stats.json: updatedAt debe ser texto no vacío")
    else:
        try:
            parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        except ValueError:
            parsed = None
        if parsed is None or parsed.tzinfo is None:
            problems.append("stats.json: updatedAt debe ser ISO-8601 con zona horaria")
    return problems


def migration_sources() -> tuple[set[str], list[str]]:
    catalog, error = load_json(MIGRATIONS_PATH)
    if error or catalog is None:
        return set(), [f"catálogo de migraciones: {error or 'inválido'}"]
    sources: set[str] = set()
    problems: list[str] = []
    migrations = catalog.get("migrations")
    if not isinstance(migrations, list):
        return set(), ["catálogo de migraciones: migrations debe ser una lista"]
    for entry in migrations:
        if not isinstance(entry, dict):
            problems.append("catálogo de migraciones: entrada no es un objeto")
            continue
        if entry.get("toContract") == EXPECTED_VERSION and isinstance(
            entry.get("fromContract"), str
        ):
            sources.add(entry["fromContract"])
    return sources, problems


def workspace_evidence(root: Path, agents: dict) -> bool:
    if agents["has_marker"] or agents["error"]:
        return True
    paths = (
        "context/faro-workspace.json",
        "context/stats.json",
        "context/README.md",
        "context/workflow.json",
        "context/faro-migration-v2.json",
        "context/requirements/project-profile.md",
        "context/requirements/requirements-catalog.md",
        "context/requirements/functional-documents-catalog.md",
        "context/requirements/functional",
        "context/requirements/work-items",
    )
    return any(
        (root / relative).exists() or (root / relative).is_symlink()
        for relative in paths
    ) or bool(legacy_flat_files(root))


def legacy_flat_files(root: Path) -> list[Path]:
    requirements = root / "context/requirements"
    if not requirements.is_dir() or requirements.is_symlink():
        return []
    pattern = re.compile(r"(?:RM|BUG|TEC)-[0-9]{4}.*\.md|DF-[0-9]{3}.*\.md", re.IGNORECASE)
    return [
        path
        for path in requirements.iterdir()
        if path.is_file() and not path.is_symlink() and pattern.fullmatch(path.name)
    ]


def classify_workspace(
    root: Path,
    agents: dict,
    manifest: dict | None,
    manifest_error: str | None,
    stats: dict | None,
    stats_error: str | None,
    migratable: set[str],
) -> str:
    if not workspace_evidence(root, agents):
        return "absent"
    if agents["error"] or manifest_error not in {None, "ausente"} or stats_error not in {None, "ausente"}:
        return "corrupt"

    versions: list[str] = []
    schemas: list[int] = []
    if isinstance(agents.get("version"), str):
        versions.append(agents["version"])
    for document in (manifest, stats):
        if document is None:
            continue
        if isinstance(document.get("contractVersion"), str):
            versions.append(document["contractVersion"])
        if isinstance(document.get("schemaVersion"), int):
            schemas.append(document["schemaVersion"])
    unique_versions = set(versions)
    parsed_versions = {semantic_version(value) for value in unique_versions}
    if None in parsed_versions:
        return "corrupt"
    if len(unique_versions) > 1 or len(set(schemas)) > 1:
        return "mixed-ambiguous"
    if unique_versions:
        only_version = next(iter(unique_versions))
        parsed = semantic_version(only_version)
        assert parsed is not None
        expected = semantic_version(EXPECTED_VERSION)
        assert expected is not None
        if parsed > expected:
            return "future-unsupported"

    profile_version = profile_schema_version(
        root / "context/requirements/project-profile.md"
    )
    workflow, workflow_error = load_json(root / "context/workflow.json")
    workflow_current = bool(
        workflow
        and (
            workflow.get("schemaVersion") == 2
            or "workItemRef" in workflow
            or "checkpoint" in workflow
        )
    )
    workflow_legacy = bool(
        workflow and ({"active", "currentUnit"} & set(workflow))
    )
    functional_metadata, _functional_error = catalog_metadata(
        root / "context/requirements/functional-documents-catalog.md"
    )
    current_functional_catalog = bool(
        functional_metadata
        and functional_metadata.get("schema_version") == "2.0"
        and functional_metadata.get("catalog_kind") == "FARO_FUNCTIONAL_DOCUMENTS"
    )
    current_paths = (
        "context/requirements/requirements-catalog.md",
        "context/requirements/functional",
        "context/requirements/work-items",
    )
    current_signal = (
        EXPECTED_VERSION in unique_versions
        or 2 in schemas
        or profile_version == 2
        or any((root / relative).exists() for relative in current_paths)
        or current_functional_catalog
        or workflow_current
    )
    legacy_signal = (
        bool(unique_versions & migratable)
        or 1 in schemas
        or profile_version == 1
        or bool(legacy_flat_files(root))
        or workflow_legacy
    )
    if current_signal and legacy_signal:
        return "mixed-ambiguous"
    if current_signal:
        return "current"
    if legacy_signal and len(unique_versions) == 1 and unique_versions <= migratable:
        if workflow_error not in {None, "ausente"}:
            return "corrupt"
        return "legacy-migratable"
    return "corrupt"


def current_agents_block() -> str:
    template = (SKILL_ROOT / "templates/AGENTS.md").read_text(encoding="utf-8")
    start = template.index("<!-- FARO:START -->")
    end = template.index("<!-- FARO:END -->") + len("<!-- FARO:END -->")
    return template[start:end].strip()


def validate_current_workspace(
    root: Path,
    config: dict,
    agents: dict,
    manifest: dict | None,
    manifest_error: str | None,
    stats: dict | None,
    stats_error: str | None,
    package_version: str | None,
) -> tuple[list[str], list[str]]:
    problems = required_path_problems(
        root, config["requiredDirectories"], config["requiredFiles"]
    )
    warnings: list[str] = []
    if not agents["valid"]:
        problems.append(agents["error"] or "AGENTS.md sin bloque FARO")
    elif agents["block"].strip() != current_agents_block():
        problems.append("AGENTS.md: el bloque FARO no coincide con la plantilla v2")
    problems.extend(
        validate_manifest(
            manifest,
            manifest_error,
            schema=2,
            version=EXPECTED_VERSION,
            artifacts=config["requiredFiles"],
        )
    )
    problems.extend(
        validate_stats(
            stats,
            stats_error,
            schema=2,
            version=EXPECTED_VERSION,
            states=config["supportedStates"],
        )
    )
    if stats and isinstance(stats.get("faro"), dict):
        recorded_package = stats["faro"].get("version")
        if (
            semantic_version(recorded_package) is not None
            and semantic_version(package_version) is not None
            and recorded_package != package_version
        ):
            warnings.append(
                "stats.json: faro.version registrada "
                f"{recorded_package}; paquete actual {package_version} "
                "(versiones independientes)"
            )
    problems.extend(
        validate_profile_v2(root / config["workspace"]["profilePath"])
    )

    catalogs = (
        (
            config["workspace"]["requirementsCatalogPath"],
            "FARO_WORK_ITEMS",
        ),
        (
            config["workspace"]["functionalCatalogPath"],
            "FARO_FUNCTIONAL_DOCUMENTS",
        ),
    )
    for relative, kind in catalogs:
        metadata, error = catalog_metadata(root / relative)
        if error or metadata is None:
            problems.append(f"{relative}: {error or 'metadata inválida'}")
            continue
        if metadata.get("schema_version") != "2.0":
            problems.append(f"{relative}: schema_version debe ser 2.0")
        if metadata.get("catalog_kind") != kind:
            problems.append(f"{relative}: catalog_kind debe ser {kind}")

    if not HELPER_PATH.is_file() or HELPER_PATH.is_symlink():
        problems.append("helper v2 ausente o inseguro: faro/scripts/work_item_contract.py")
    else:
        try:
            from work_item_contract import validate_layout

            report = validate_layout(root, config)
            problems.extend(
                f"helper/{issue.code}: {issue.message}" for issue in report.errors
            )
            warnings.extend(
                f"helper/{issue.code}: {issue.message}" for issue in report.warnings
            )
        except Exception as error:
            problems.append(f"helper v2 no pudo validar el workspace: {error}")
    problems.extend(validate_workflow(root / config["workspace"]["workflowPath"], SKILL_ROOT))
    return problems, warnings


def validate_legacy_workspace(
    root: Path,
    agents: dict,
    manifest: dict | None,
    manifest_error: str | None,
    stats: dict | None,
    stats_error: str | None,
    version: str,
) -> list[str]:
    problems = required_path_problems(
        root, LEGACY_REQUIRED_DIRECTORIES, LEGACY_REQUIRED_FILES
    )
    if not agents["valid"]:
        problems.append(agents["error"] or "AGENTS.md sin bloque FARO legacy")
    elif agents.get("version") != version:
        problems.append("AGENTS.md: versión legacy no coincide")
    problems.extend(
        validate_manifest(
            manifest,
            manifest_error,
            schema=1,
            version=version,
            artifacts=LEGACY_REQUIRED_FILES,
        )
    )
    problems.extend(
        validate_stats(
            stats,
            stats_error,
            schema=1,
            version=version,
            states=["new", "initializing", "available", "disabled"],
        )
    )
    profile = root / "context/requirements/project-profile.md"
    if profile_schema_version(profile) != 1:
        problems.append("perfil legacy: profile_version debe ser 1")
    elif profile.is_file():
        text = profile.read_text(encoding="utf-8", errors="replace")
        for key in ("work_tracking:", "mode:", "provider:", "functional_documentation:"):
            if key not in text:
                problems.append(f"perfil legacy sin {key.rstrip(':')}")
    workflow = root / "context/workflow.json"
    if workflow.exists():
        _value, error = load_json(workflow)
        if error:
            problems.append(f"workflow legacy: {error}")
    return problems


def project_evidence(root: Path) -> dict[str, bool]:
    evidence = {"dotnet": False, "laravel": False, "mobile": False}
    ignored = {".git", "context", "node_modules", "vendor", "bin", "obj", ".idea", ".vscode"}
    for current, directories, files in os.walk(root, followlinks=False):
        relative = Path(current).relative_to(root)
        if len(relative.parts) >= 4:
            directories[:] = []
        else:
            directories[:] = [
                name
                for name in directories
                if name not in ignored and not (Path(current) / name).is_symlink()
            ]
        names = {
            name
            for name in files
            if (Path(current) / name).is_file()
            and not (Path(current) / name).is_symlink()
        }
        if "global.json" in names or any(
            name.endswith((".sln", ".csproj")) for name in names
        ):
            evidence["dotnet"] = True
        if "composer.json" in names:
            evidence["laravel"] = True
        if {"pubspec.yaml", "build.gradle", "build.gradle.kts"} & names:
            evidence["mobile"] = True
        if all(evidence.values()):
            break
    return evidence


def verify_suite_origin() -> tuple[str, str | None]:
    provenance, error = load_json(PROVENANCE_PATH)
    if error or not provenance:
        return "no verificable", f"provenance de suite {error or 'inválida'}"

    repository = provenance.get("repository")
    ref = provenance.get("ref")
    integrity_file = provenance.get("integrityFile")
    if not isinstance(repository, str) or not isinstance(ref, str) or not isinstance(integrity_file, str):
        return "no verificable", "provenance de suite incompleta"
    if ref != f"refs/tags/v{provenance.get('packageVersion')}":
        return "no verificable", "provenance no declara la etiqueta Git de su versión de paquete"

    try:
        resolved = subprocess.run(
            ["git", "ls-remote", "--exit-code", repository, ref, ref + "^{}"],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return "no verificable", f"no se pudo consultar el remoto: {exc}"
    if resolved.returncode != 0:
        return "no verificable", f"el remoto no resolvió {ref}"
    lines = [line.split() for line in resolved.stdout.splitlines() if line.strip()]
    if not lines or any(len(line) != 2 or not re.fullmatch(r"[0-9a-f]{40}", line[0]) or line[1] not in {ref, ref + "^{}"} for line in lines):
        return "no verificable", f"respuesta Git inesperada para {ref}"
    revisions = {line[1]: line[0] for line in lines}
    if len(revisions) != len(lines) or ref not in revisions:
        return "no verificable", f"respuesta Git inesperada para {ref}"
    commit = revisions.get(ref + "^{}", revisions[ref])

    with tempfile.TemporaryDirectory(prefix="faro-suite-origin-") as temporary:
        checkout = Path(temporary) / "source"
        try:
            initialize = subprocess.run(
                ["git", "init", "--quiet", str(checkout)],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
            fetch = subprocess.run(
                ["git", "-C", str(checkout), "fetch", "--quiet", "--depth", "1", repository, commit],
                check=False,
                capture_output=True,
                text=True,
                timeout=90,
            )
            checkout_commit = subprocess.run(
                ["git", "-c", "core.autocrlf=false", "-C", str(checkout), "checkout", "--quiet", "--detach", "FETCH_HEAD"],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            return "no verificable", f"no se pudo obtener la revisión remota: {exc}"
        if initialize.returncode != 0 or fetch.returncode != 0 or checkout_commit.returncode != 0:
            return "no verificable", f"no se pudo obtener el commit remoto {commit}"

        checksums_path = checkout / integrity_file
        if not checksums_path.is_file():
            return "no verificable", f"la revisión remota no contiene {integrity_file}"
        expected: dict[Path, str] = {}
        for number, line in enumerate(checksums_path.read_text(encoding="utf-8").splitlines(), 1):
            match = re.fullmatch(r"([0-9a-f]{64})  (faro/.+)", line)
            if not match:
                return "no verificable", f"checksum remoto inválido en línea {number}"
            expected[Path(match.group(2))] = match.group(1)

    actual = {
        Path("faro") / path.relative_to(SKILL_ROOT): path
        for path in SKILL_ROOT.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }
    if set(actual) != set(expected):
        return "no coincide", "el árbol instalado no coincide con la revisión remota"
    changed = [str(path) for path, local in actual.items() if hashlib.sha256(local.read_bytes()).hexdigest() != expected[path]]
    if changed:
        return "no coincide", "checksum remoto distinto: " + ", ".join(changed)
    return f"verificado: {repository} {ref} ({commit})", None


def check_external_skills() -> list[str]:
    catalog, error = load_json(EXTERNAL_SKILLS_PATH)
    if error or not catalog:
        return [f"catálogo de skills externas {error or 'inválido'}"]
    declared = [name for source in catalog.get("sources", []) for name in source.get("skills", [])]
    if not declared or not all(isinstance(name, str) for name in declared):
        return ["catálogo de skills externas no declara nombres válidos"]
    problems: list[str] = []
    print("Skills externas Laravel:")
    for name in declared:
        try:
            result = subprocess.run(
                ["hermes", "skills", "check", name], check=False, capture_output=True,
                text=True, timeout=60,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            problems.append(f"skill externa {name}: no verificable ({exc})")
            print(f"- {name}: no verificable")
            continue
        output = (result.stdout + result.stderr).replace("\n", " ")
        if result.returncode != 0 or "No hub-installed skills to check" in output:
            problems.append(f"skill externa {name}: no verificable")
            print(f"- {name}: no verificable")
        elif "up_to_date" in output:
            print(f"- {name}: actual")
        else:
            problems.append(f"skill externa {name}: actualización disponible")
            print(f"- {name}: actualización disponible")
    return problems


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostica un workspace FARO sin modificarlo.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root coordinador a inspeccionar.")
    parser.add_argument("--strict", action="store_true", help="Falla si falta o es inválido un requisito obligatorio.")
    parser.add_argument("--verify-suite-origin", action="store_true", help="Compara la suite instalada con la etiqueta Git remota declarada.")
    parser.add_argument("--check-external-skills", action="store_true", help="Comprueba actualizaciones externas sin instalar ni actualizar.")
    args = parser.parse_args()
    raw_root = args.root.expanduser().absolute()
    if raw_root.is_symlink() or not raw_root.is_dir():
        print(f"ERROR: root ausente, no regular o symlink: {raw_root}")
        return 2
    root = raw_root.resolve()
    config, config_error = load_json(CONFIG_PATH)
    if config_error or config is None:
        print(f"ERROR: configuración canónica {config_error}: {CONFIG_PATH}")
        return 2
    if config.get("schemaVersion") != 2 or config.get("contractVersion") != EXPECTED_VERSION:
        print(f"ERROR: configuración canónica incompatible: {CONFIG_PATH}")
        return 2

    agents = agents_contract(root)
    manifest, manifest_error = load_json(root / "context/faro-workspace.json")
    stats, stats_error = load_json(root / "context/stats.json")
    provenance, _provenance_error = load_json(PROVENANCE_PATH)
    package_version = (
        provenance.get("packageVersion")
        if provenance and isinstance(provenance.get("packageVersion"), str)
        else None
    )
    migratable, migration_catalog_problems = migration_sources()
    candidate = classify_workspace(
        root,
        agents,
        manifest,
        manifest_error,
        stats,
        stats_error,
        migratable,
    )
    classification = candidate
    workspace_problems: list[str] = []
    workspace_warnings: list[str] = []

    if candidate == "current":
        workspace_problems, workspace_warnings = validate_current_workspace(
            root,
            config,
            agents,
            manifest,
            manifest_error,
            stats,
            stats_error,
            package_version,
        )
        if workspace_problems:
            classification = "corrupt"
    elif candidate == "legacy-migratable":
        legacy_version = next(
            (
                value
                for value in (
                    manifest.get("contractVersion") if manifest else None,
                    stats.get("contractVersion") if stats else None,
                    agents.get("version"),
                )
                if isinstance(value, str)
            ),
            "",
        )
        workspace_problems = validate_legacy_workspace(
            root,
            agents,
            manifest,
            manifest_error,
            stats,
            stats_error,
            legacy_version,
        )
        if workspace_problems:
            classification = "corrupt"
    elif candidate == "corrupt":
        if agents["has_marker"] and agents["error"]:
            workspace_problems.append(str(agents["error"]))
        if manifest_error not in {None, "ausente"}:
            workspace_problems.append(f"manifiesto: {manifest_error}")
        if stats_error not in {None, "ausente"}:
            workspace_problems.append(f"stats.json: {stats_error}")
        if not workspace_problems:
            workspace_problems.append(
                "artefactos FARO incompletos o sin versión/esquema reconocido"
            )
    elif candidate == "mixed-ambiguous":
        workspace_problems.append(
            "coexisten señales incompatibles de contrato/layout; no se puede elegir una migración segura"
        )
    elif candidate == "future-unsupported":
        workspace_problems.append(
            "el contrato fue creado por una versión futura no soportada; no degradar ni reparar con esta suite"
        )

    assert classification in WORKSPACE_CLASSIFICATIONS
    exists = classification != "absent"
    print(f"Espacio FARO existente: {'sí' if exists else 'no'}")
    print(f"Root inspeccionado: {root}")
    print(f"Clasificación del workspace: {classification}")

    suite_problems = validate_suite(SKILL_ROOT)
    suite_problems.extend(migration_catalog_problems)
    displayed_package_version = package_version or "no registrada"
    router_version, skill_versions = runtime_skill_versions()
    installed_contract = manifest.get("contractVersion", "no registrada") if manifest else (manifest_error or "no registrada")
    stats_faro = stats.get("faro") if stats and isinstance(stats.get("faro"), dict) else {}
    print("Matriz de versiones (cada fila tiene un propósito distinto):")
    print(f"- Suite FARO (paquete distribuido): {displayed_package_version}")
    print(f"- Skill principal faro (router): {router_version}")
    print(f"- Skills runtime (versiones declaradas): {skill_versions}")
    print(f"- Contrato canónico esperado: {EXPECTED_VERSION}")
    print(f"- Contrato instalado en workspace: {installed_contract}")
    print(f"- Paquete que materializó el workspace (stats.faro.version): {stats_faro.get('version', 'no registrado')}")
    print(f"- Workflow: {workflow_schema_status(root)}")
    print("Compatibilidad: suite y contrato se evalúan por separado; versiones de skills, documentos y workflow no sustituyen ninguna de las dos.")
    print(f"Versión canónica esperada: {EXPECTED_VERSION}")
    print("Coherencia local de la suite: " + ("inválida" if suite_problems else "válida"))
    print(f"Historial de actualización: {SKILL_ROOT / 'references/suite-changelog.json'}")
    origin_error: str | None = None
    if args.verify_suite_origin:
        origin, origin_error = verify_suite_origin()
        print(f"Origen Git de la suite: {origin}")
    else:
        print("Origen Git de la suite: no comprobado (usar --verify-suite-origin)")
    external_problems: list[str] = []
    if args.check_external_skills:
        external_problems.extend(check_external_skills())
    else:
        print("Skills externas Laravel: no comprobadas (usar --check-external-skills)")

    if classification == "legacy-migratable" or (
        classification == "corrupt"
        and manifest
        and manifest.get("contractVersion") in migratable
    ):
        required_files = list(LEGACY_REQUIRED_FILES)
    elif classification == "future-unsupported":
        required_files = []
    else:
        required_files = list(config["requiredFiles"])
    print("Archivos requeridos:")
    if not required_files:
        print("- no evaluados: el contrato futuro puede declarar otra estructura")
    for relative in required_files:
        path = root / relative
        if not path.exists():
            status = "ausente"
        elif path.is_symlink() or not path.is_file():
            status = "inválido (no regular o symlink)"
        elif path.suffix == ".json":
            _value, error = load_json(path)
            status = error or "presente"
        else:
            status = "presente"
        print(f"- {relative}: {status}")

    if agents["valid"]:
        print(f"Bloque FARO de AGENTS.md: válido ({agents['version'] or 'sin versión'})")
    elif agents["exists"] and not agents["has_marker"]:
        print("Bloque FARO de AGENTS.md: ausente; contenido ajeno preservable")
    elif agents["error"]:
        print(f"Bloque FARO de AGENTS.md: inválido ({agents['error']})")
    else:
        print("Bloque FARO de AGENTS.md: ausente")

    if manifest:
        installed = manifest.get("contractVersion", "no registrado")
        if installed == EXPECTED_VERSION:
            compatibility = "coincide"
        elif installed in migratable:
            compatibility = "legacy con migración declarada"
        elif semantic_version(installed) and semantic_version(installed) > semantic_version(EXPECTED_VERSION):
            compatibility = "futuro no soportado"
        else:
            compatibility = "no compatible"
        print(f"Compatibilidad del contrato instalado: {installed} ({compatibility})")
        print(f"Origen declarado: {manifest.get('contractSource', 'no registrado')}")
    else:
        print(f"Compatibilidad del contrato instalado: {manifest_error or 'no registrada'}")

    if stats:
        print(f"Estado: {stats.get('state', 'no registrado')}")
        project = stats.get("project") if isinstance(stats.get("project"), dict) else {}
        faro = stats.get("faro") if isinstance(stats.get("faro"), dict) else {}
        print(f"Proyecto: {project.get('name', 'no registrado')}")
        print(f"Paquete registrado en stats: {faro.get('version', 'no registrado')}")
    else:
        print("Estado: no registrado")
        print("Proyecto: no registrado")
        print("Paquete registrado en stats: no registrado")

    profile = root / "context/requirements/project-profile.md"
    if profile.is_file() and not profile.is_symlink():
        content = profile.read_text(encoding="utf-8", errors="replace")
        print(f"Seguimiento de trabajo: {profile_value(content, 'mode')}")
        print(f"Proveedor de seguimiento: {profile_value(content, 'provider')}")
        print(f"Documentación funcional del proyecto: {profile_value(content, 'functional_documentation')}")
    else:
        content = ""
        print("Seguimiento de trabajo: no registrado")
        print("Proveedor de seguimiento: no registrado")
        print("Documentación funcional del proyecto: no registrada")
    architectures = [
        root / "context/architecture-laravel.md",
        root / "context/architecture-dotnet.md",
        root / "context/architecture-mobile.md",
        root / "context/architecture.md",
    ]
    print("Arquitectura registrada: " + (next((item.name for item in architectures if item.exists()), "no registrada")))
    workflow = root / "context/workflow.json"
    print("Workflow activo: " + ("sí" if workflow.exists() else "no"))
    glossary = root / config["workspace"]["glossaryPath"]
    if glossary.is_file():
        glossary_status = "presente"
    elif glossary.exists():
        glossary_status = "ruta ocupada (no es un archivo; requiere revisión)"
    else:
        glossary_status = "no creado (opcional)"
    print(f"Glosario de dominio: {glossary_status}; contenido no validado automáticamente")
    stack = project_evidence(root)
    print("Evidencia .NET/C#: " + ("detectada" if stack["dotnet"] else "no detectada"))

    migration_command: str | None = None
    if classification == "legacy-migratable":
        migration_command = (
            f'python3 -B "{SKILL_ROOT / "scripts/migrate_workspace_v2.py"}" '
            f'--root "{root}"'
        )
        print(f"Migración recomendada (dry-run, no escribe): {migration_command}")

    all_problems = list(suite_problems) + workspace_problems + external_problems
    if origin_error:
        all_problems.append(f"origen Git de la suite: {origin_error}")
    if stats and stats.get("state") == "disabled" and classification == "current":
        recommendation = "detener FARO"
    elif suite_problems or origin_error:
        recommendation = "actualizar la suite completa mediante bootstrap, con comparación y confirmación; no reinicializar el workspace"
    elif classification == "absent":
        recommendation = "faro-inicializacion"
    elif classification == "legacy-migratable":
        recommendation = (
            "revisar el plan del migrador en dry-run; usar --apply sólo con "
            "autorización explícita"
        )
    elif classification == "mixed-ambiguous":
        recommendation = "resolver manualmente la mezcla antes de migrar; no inicializar ni escribir"
    elif classification == "future-unsupported":
        recommendation = "usar una suite compatible con la versión futura; no degradar el workspace"
    elif classification == "corrupt":
        recommendation = "reparación explícita basada en evidencia; no reinicializar ni sobrescribir"
    elif stats and stats.get("state") in {"new", "initializing"}:
        mode = profile_value(content, "mode")
        provider = profile_value(content, "provider")
        if mode == "REQUIRED" and provider == "JIRA":
            recommendation = "faro-int-jira"
        elif mode == "REQUIRED" and provider == "AZURE_DEVOPS":
            recommendation = "faro-int-azure-devops"
        elif stack["dotnet"]:
            recommendation = "faro-arq-dotnet"
        elif stack["laravel"]:
            recommendation = "faro-arq-laravel"
        elif stack["mobile"]:
            recommendation = "faro-arq-mobile"
        else:
            recommendation = "faro-arq-generica"
    else:
        recommendation = "seguir la ruta FARO del pedido actual"
    if workspace_warnings:
        print("Advertencias: " + "; ".join(workspace_warnings))
    print("Faltantes/bloqueos: " + ("; ".join(all_problems) if all_problems else "ninguno detectado"))
    print(f"Siguiente ruta recomendada: {recommendation}")
    strict_failure = classification != "current" or bool(all_problems)
    return 1 if args.strict and strict_failure else 0


if __name__ == "__main__":
    raise SystemExit(main())
