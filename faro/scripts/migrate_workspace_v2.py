#!/usr/bin/env python3
"""Plan or apply the explicit FARO workspace migration 1.13.0 -> 2.0.0."""
from __future__ import annotations

import argparse
import base64
from dataclasses import dataclass, field
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import sys
import tempfile
from typing import Any


SCRIPT_ROOT = Path(__file__).resolve().parent
FARO_ROOT = SCRIPT_ROOT.parent
sys.dont_write_bytecode = True
sys.path.insert(0, str(SCRIPT_ROOT))
import work_item_contract as contract


SOURCE_CONTRACT = "1.13.0"
TARGET_CONTRACT = "2.0.0"
WORK_ID = re.compile(r"^(RM-[0-9]{4}|BUG-[0-9]{4}|TEC-[0-9]{4})(?:[-.].*)?$", re.IGNORECASE)
DF_ID = re.compile(r"^(DF-[0-9]{3})(?:[-.].*)?$", re.IGNORECASE)
PRIMARY_WORK_TYPES = {"REQUIREMENT_SPEC", "BUG_ASSESSMENT_OR_TECHNICAL_MAINTENANCE"}
SUPPORT_TYPES = {
    "TECHNICAL_PLAN", "TECHNICAL_TASKS", "QA_REPORT", "VALIDATION_REPORT",
    "DELIVERY_EVIDENCE", "WORK_ITEM_CLOSURE",
}
SUPPORT_NAME = re.compile(
    r"-(?:plan-tecnico|tareas|qa|validacion|entrega|cierre|investigacion|evidencia)(?:[-.]|$)",
    re.IGNORECASE,
)


class MigrationError(RuntimeError):
    pass


@dataclass(frozen=True)
class Move:
    source: str
    destination: str
    sha256: str


@dataclass
class Plan:
    root: Path
    classification: str
    generated_at: str
    moves: list[Move] = field(default_factory=list)
    directories: list[str] = field(default_factory=list)
    writes: dict[str, bytes] = field(default_factory=dict)
    originals: dict[str, bytes | None] = field(default_factory=dict)
    work_entries: list[dict[str, str]] = field(default_factory=list)
    functional_entries: list[dict[str, str]] = field(default_factory=list)
    legacy_exceptions: list[dict[str, str]] = field(default_factory=list)

    def serializable(self) -> dict:
        return {
            "sourceContract": SOURCE_CONTRACT,
            "targetContract": TARGET_CONTRACT,
            "classification": self.classification,
            "mode": "no-op" if self.classification == "current" else "planned",
            "generatedAt": self.generated_at,
            "directories": self.directories,
            "moves": [move.__dict__ for move in self.moves],
            "writes": sorted(self.writes),
            "workItems": self.work_entries,
            "functionalDocuments": self.functional_entries,
            "legacyPrimaryExceptions": self.legacy_exceptions,
        }


def json_file(root: Path, relative: str, label: str) -> tuple[Path, dict]:
    try:
        path = contract.relative_target(root, relative, label=label)
    except contract.ContractError as error:
        raise MigrationError(str(error)) from error
    if not path.is_file() or path.is_symlink():
        raise MigrationError(f"{label} ausente/no regular/symlink: {path}")
    try:
        return path, contract.load_json(path)
    except contract.ContractError as error:
        raise MigrationError(str(error)) from error


def read_regular(root: Path, relative: str, label: str, *, required: bool = True) -> tuple[Path, bytes | None]:
    try:
        path = contract.relative_target(root, relative, label=label)
    except contract.ContractError as error:
        raise MigrationError(str(error)) from error
    if not path.exists():
        if required:
            raise MigrationError(f"{label} ausente: {path}")
        return path, None
    if not path.is_file() or path.is_symlink():
        raise MigrationError(f"{label} no es archivo regular: {path}")
    return path, path.read_bytes()


def digest_bytes(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


def frontmatter_or_none(path: Path) -> dict[str, str] | None:
    try:
        return contract.parse_frontmatter(path)
    except contract.ContractError as error:
        if "front matter ausente" in str(error):
            return None
        raise MigrationError(str(error)) from error


def identities(meta: dict[str, str] | None) -> list[tuple[str, str]]:
    if not meta:
        return []
    return [
        (name, meta[name]) for name in ("work_item_id", "rm_id", "bug_id", "tec_id")
        if meta.get(name)
    ]


def check_casefold(values: list[str], label: str) -> None:
    seen: dict[str, str] = {}
    for value in values:
        folded = value.casefold()
        if folded in seen:
            raise MigrationError(f"colisión case-insensitive en {label}: {seen[folded]} / {value}")
        seen[folded] = value


def choose_work_primary(identifier: str, files: list[Path]) -> tuple[Path, bool]:
    typed: list[Path] = []
    identity_primary: list[Path] = []
    exact: list[Path] = []
    fallback: list[Path] = []
    for path in files:
        if "|" in path.name or "\n" in path.name or "\r" in path.name:
            raise MigrationError(f"basename no representable en catálogo: {path.name!r}")
        if path.suffix.lower() != ".md":
            continue
        meta = frontmatter_or_none(path)
        declared = identities(meta)
        for field_name, value in declared:
            if value != identifier:
                raise MigrationError(f"{path}: {field_name}={value!r}, esperado {identifier}")
        if meta and meta.get("artifact_type") in PRIMARY_WORK_TYPES:
            typed.append(path)
        if any(name in {"rm_id", "bug_id", "tec_id"} for name, _ in declared):
            identity_primary.append(path)
        if path.name == f"{identifier}.md":
            exact.append(path)
        artifact_type = meta.get("artifact_type") if meta else None
        if artifact_type not in SUPPORT_TYPES and not SUPPORT_NAME.search(path.stem):
            fallback.append(path)
    for candidates in (typed, exact, identity_primary, fallback):
        unique = list(dict.fromkeys(candidates))
        if len(unique) == 1:
            primary = unique[0]
            meta = frontmatter_or_none(primary)
            if meta is None and identifier.startswith("RM-"):
                raise MigrationError(f"RM legado sin identidad en front matter: {primary}")
            return primary, meta is None
        if len(unique) > 1 and candidates is typed:
            raise MigrationError(f"múltiples primarios tipados para {identifier}: {', '.join(path.name for path in unique)}")
    raise MigrationError(f"no se pudo elegir un primario único para {identifier}: {', '.join(path.name for path in files)}")


def choose_df_primary(identifier: str, files: list[Path]) -> Path:
    candidates: list[Path] = []
    for path in files:
        if "|" in path.name or "\n" in path.name or "\r" in path.name:
            raise MigrationError(f"basename no representable en catálogo: {path.name!r}")
        if path.suffix.lower() != ".md":
            continue
        meta = frontmatter_or_none(path)
        try:
            df_id = contract.functional_identity(meta, path) if meta else None
        except contract.ContractError as error:
            raise MigrationError(str(error)) from error
        if df_id != identifier:
            raise MigrationError(f"DF sin df_id coherente: {path}")
        if not path.stem.lower().endswith("-investigacion-interna"):
            candidates.append(path)
    if len(candidates) != 1:
        raise MigrationError(f"DF {identifier} requiere un entregable único; encontrados: {', '.join(path.name for path in candidates) or 'ninguno'}")
    return candidates[0]


def inventory_flat(root: Path, requirements: Path) -> tuple[dict[str, list[Path]], dict[str, list[Path]]]:
    work: dict[str, list[Path]] = {}
    functional: dict[str, list[Path]] = {}
    names: list[str] = []
    for path in sorted(requirements.iterdir(), key=lambda item: item.name.casefold()):
        recognizable_name = path.name.lstrip(".")
        if path.is_symlink():
            raise MigrationError(f"requirements contiene symlink: {path}")
        if not path.is_file():
            if re.match(r"^(?:RM|BUG|TEC|DF)-", recognizable_name, flags=re.IGNORECASE):
                raise MigrationError(
                    f"artefacto FARO plano reconocible no es archivo regular: {path.name}"
                )
            continue
        names.append(path.name)
        work_match = WORK_ID.fullmatch(path.name)
        df_match = DF_ID.fullmatch(path.name)
        if work_match:
            raw_identifier = work_match.group(1)
            if raw_identifier != raw_identifier.upper():
                raise MigrationError(f"expediente plano reconocible usa ID no canónico; no se renombra implícitamente: {path.name}")
            work.setdefault(raw_identifier, []).append(path)
        elif df_match:
            raw_identifier = df_match.group(1)
            if raw_identifier != raw_identifier.upper():
                raise MigrationError(f"DF plano reconocible usa ID no canónico; no se renombra implícitamente: {path.name}")
            functional.setdefault(raw_identifier, []).append(path)
        elif re.match(r"^(?:RM|BUG|TEC|DF)-", recognizable_name, flags=re.IGNORECASE):
            raise MigrationError(f"artefacto FARO plano reconocible tiene nombre/ID no soportado; no se ignora: {path.name}")
    check_casefold(names, "archivos planos")
    return work, functional


def legacy_df_reservations(path: Path | None, published: set[str], generated_at: str) -> list[list[str]]:
    if path is None or not path.exists():
        return []
    try:
        _headers, rows = contract._table(path, "Reservas")
    except contract.ContractError:
        text = path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r"(?ms)^## Reservas\s*$\n(.*?)(?=^## |\Z)", text)
        if not match or not re.search(r"^\s*\|\s*DF-[0-9]{3}\s*\|", match.group(1), re.MULTILINE | re.IGNORECASE):
            return []
        raise MigrationError("catálogo DF legado tiene reservas que no pueden parsearse sin pérdida")
    result: list[list[str]] = []
    seen: set[str] = set()
    for row in rows:
        identifier = contract.cell(row, "ID")
        if not re.fullmatch(r"DF-[0-9]{3}", identifier):
            raise MigrationError(
                f"reserva DF legada usa ID inválido/no canónico; no se normaliza: {identifier!r}"
            )
        if identifier in published:
            continue
        if identifier.casefold() in seen:
            raise MigrationError(f"reserva DF duplicada: {identifier}")
        seen.add(identifier.casefold())
        source = contract.present(contract.cell(row, "Fuente de reserva serializada", "Fuente", "Evidencia"))
        date = contract.present(contract.cell(row, "Fecha y zona", "Fecha"))
        source = source or f"migrated:{contract.sha256(path)[:16]}:{identifier}"
        if date:
            try:
                contract.parse_timestamp(date, "fecha de reserva DF")
            except contract.ContractError:
                date = generated_at
        else:
            date = generated_at
        contract.catalog_value(source, "fuente de reserva DF")
        result.append([identifier, source, date])
    return sorted(result, key=lambda row: row[0])


def render_catalog(template_name: str, section: str, headers: list[str], rows: list[list[str]]) -> bytes:
    text = (FARO_ROOT / "templates" / template_name).read_text(encoding="utf-8")
    return contract._replace_table(text, section, headers, rows).encode("utf-8")


def suite_package_version() -> str:
    path = FARO_ROOT / "references" / "suite-provenance.json"
    try:
        provenance = contract.load_json(path)
    except contract.ContractError as error:
        raise MigrationError(f"provenance del paquete inválido: {error}") from error
    version = provenance.get("packageVersion")
    if provenance.get("schemaVersion") != 1 or not isinstance(version, str) or not re.fullmatch(
        r"[0-9]+\.[0-9]+\.[0-9]+", version,
    ):
        raise MigrationError(f"provenance del paquete no declara packageVersion semántica: {path}")
    return version


def migrate_profile(content: bytes, generated_at: str) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise MigrationError(f"project-profile legado no es UTF-8: {error}") from error
    header_match = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, flags=re.DOTALL)
    if not header_match:
        raise MigrationError("project-profile legado no tiene front matter delimitado")
    header = header_match.group(1)
    body = text[header_match.end():]
    forbidden_overlay = (
        "operational_state_authority", "work_items_require_external_reference",
        "type_mapping", "workflow_mapping_by_kind", "durable_documentation",
        "migration_mapping_reconciliation",
    )
    for key in forbidden_overlay:
        if re.search(rf"^\s*{re.escape(key)}:\s*", header, flags=re.MULTILINE):
            raise MigrationError(f"project-profile legado ya contiene overlay v2/duplicado: {key}")
    for key in ("work_tracking", "jira", "azure_devops"):
        if len(re.findall(rf"^\s*{key}:\s*$", header, flags=re.MULTILINE)) != 1:
            raise MigrationError(f"project-profile legado debe declarar {key} exactamente una vez")
    if len(re.findall(r"^profile_version:\s*1\s*$", header, flags=re.MULTILINE)) != 1:
        raise MigrationError("project-profile legado no tiene estructura 1.13 reconocible")
    header = re.sub(
        r"^profile_version:\s*1\s*$", "profile_version: 2", header,
        count=1, flags=re.MULTILINE,
    )
    tracking_overlay = (
        "work_tracking:\n"
        "  operational_state_authority: EXTERNAL_WORK_TRACKER\n"
        "  work_items_require_external_reference: true\n"
        "  migration_mapping_reconciliation: PENDING\n"
    )
    header = header.replace("work_tracking:\n", tracking_overlay, 1)
    mapping = (
        "    type_mapping:\n"
        "      RM: null\n      BUG: null\n      TEC: null\n      INC: null\n      TASK: null\n"
        "    workflow_mapping_by_kind:\n"
        "      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}\n"
        "      BUG: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}\n"
        "      TEC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}\n"
        "      INC: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}\n"
        "      TASK: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}\n"
    )
    if "  jira:\n" not in header or "  azure_devops:\n" not in header:
        raise MigrationError("project-profile legado no declara jira/azure_devops")
    header = header.replace("  jira:\n", "  jira:\n" + mapping, 1)
    header = header.replace("  azure_devops:\n", "  azure_devops:\n" + mapping, 1)
    durable = (
        "durable_documentation:\n"
        "  product: context/requirements/functional\n"
        "  architecture: context/decisions/adr\n"
        "  operations: null\n"
        "  reference: context/glossary.md\n"
    )
    markers = list(re.finditer(r"^updated_at:.*$", header, flags=re.MULTILINE))
    if len(markers) != 1:
        raise MigrationError("project-profile legado no declara updated_at")
    marker = markers[0]
    header = header[:marker.start()] + durable + f"updated_at: {generated_at}" + header[marker.end():]
    migrated = f"---\n{header}\n---\n{body}"
    migrated += (
        "\n## Migración de mapeos v2\n\n"
        "Los mapeos 1.13 permanecen como evidencia histórica en este archivo y en "
        "`context/faro-migration-v2.json`. Los mapeos por clase agregados quedan "
        "pendientes de reconciliación remota; no se aplicó un mapeo legado a todas las clases.\n"
    )
    return migrated.encode("utf-8")


def migrate_agents(content: bytes) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise MigrationError(f"AGENTS legado no es UTF-8: {error}") from error
    pattern = re.compile(r"(?s)<!-- FARO:START -->.*?<!-- FARO:END -->")
    matches = pattern.findall(text)
    if len(matches) != 1:
        raise MigrationError("AGENTS.md legado debe contener un único bloque FARO")
    template = (FARO_ROOT / "templates/AGENTS.md").read_text(encoding="utf-8")
    replacement = pattern.search(template)
    if replacement is None:
        raise MigrationError("template AGENTS v2 sin bloque FARO")
    return pattern.sub(replacement.group(0), text, count=1).encode("utf-8")


def migrate_index(content: bytes) -> bytes:
    try:
        text = content.decode("utf-8")
    except UnicodeError as error:
        raise MigrationError(f"índice legado no es UTF-8: {error}") from error
    additions = []
    for line in (
        "- **Ubicación:** `context/requirements/requirements-catalog.md`. **Descripción:** Localizador de expedientes. **Propósito:** Resolver IDs sin duplicar estado remoto.",
        "- **Ubicación:** `context/requirements/functional-documents-catalog.md`. **Descripción:** Localizador funcional. **Propósito:** Resolver DF duraderos.",
        "- **Ubicación:** `context/requirements/work-items/`. **Descripción:** Expedientes estables. **Propósito:** Conservar definición y evidencia.",
        "- **Ubicación:** `context/requirements/functional/`. **Descripción:** Baselines funcionales. **Propósito:** Conservar conocimiento vigente.",
    ):
        path = re.search(r"`([^`]+)`", line).group(1)
        if path not in text:
            additions.append(line)
    if additions:
        text += "\n## Contrato documental FARO v2\n\n" + "\n".join(additions) + "\n"
    return text.encode("utf-8")


def extract_work_identifier(value: Any) -> set[str]:
    found: set[str] = set()
    if isinstance(value, str):
        found.update(re.findall(r"\b(?:RM|BUG|TEC|INC)-[0-9]{4}\b", value))
    elif isinstance(value, dict):
        for key in ("id", "identifier", "workItemId", "work_item_id", "path"):
            if key in value:
                found.update(extract_work_identifier(value[key]))
    return found


def resolve_incident_reference(root: Path, identifier: str) -> str:
    try:
        registry = contract.relative_target(
            root, "context/incidents/README.md", label="registro de incidentes",
        )
        _headers, rows = contract._table(registry, "Registros")
    except (contract.ContractError, OSError, UnicodeError) as error:
        raise MigrationError(f"no se pudo resolver {identifier} en el registro de incidentes: {error}") from error
    matches = [row for row in rows if contract.cell(row, "ID") == identifier]
    if len(matches) != 1:
        raise MigrationError(f"el registro de incidentes debe contener exactamente una fila para {identifier}")
    path_value = contract.cell(matches[0], "Expediente estable", "Registro")
    match = contract.INCIDENT_PATH.fullmatch(path_value)
    if match is None or match.group(1) != identifier:
        raise MigrationError(f"ruta no canónica para {identifier}: {path_value!r}")
    try:
        incident = contract.relative_target(root, path_value, label=f"expediente {identifier}")
    except contract.ContractError as error:
        raise MigrationError(str(error)) from error
    if incident.is_symlink() or not incident.is_file():
        raise MigrationError(f"expediente {identifier} ausente/no regular/symlink: {incident}")
    try:
        heading = next(
            (
                line for line in incident.read_text(encoding="utf-8", errors="replace").splitlines()
                if line.startswith("# ")
            ),
            "",
        )
    except OSError as error:
        raise MigrationError(f"no se pudo leer expediente {identifier}: {error}") from error
    heading_match = re.match(r"#\s+(INC-[0-9]{4})(?:\s|—|-)", heading)
    if heading_match is None or heading_match.group(1) != identifier:
        raise MigrationError(f"encabezado principal del expediente no coincide con {identifier}")
    return path_value


def migrate_workflow(payload: dict, entries: set[str], generated_at: str, root: Path) -> dict:
    candidates = extract_work_identifier(payload.get("currentUnit")) | extract_work_identifier(payload.get("active"))
    if len(candidates) > 1:
        raise MigrationError(f"workflow legado referencia múltiples unidades: {sorted(candidates)}")
    identifier = next(iter(candidates), None)
    reference_path: str | None = None
    if identifier:
        if identifier.startswith("INC-"):
            reference_path = resolve_incident_reference(root, identifier)
        elif identifier in entries:
            reference_path = f"context/requirements/work-items/{identifier}"
        else:
            raise MigrationError(f"workflow legado apunta a unidad no migrable: {identifier}")
    authorization = payload.get("authorization")
    notes = payload.get("notes")
    next_route = payload.get("nextRoute")
    if not isinstance(authorization, dict) or set(authorization) != {"status", "source", "artifactVersion", "scope"}:
        raise MigrationError("workflow legado tiene authorization inválido/incompatible con v2")
    if not isinstance(authorization.get("status"), str) or not authorization.get("status", "").strip():
        raise MigrationError("workflow legado tiene authorization.status inválido")
    for field_name in ("source", "artifactVersion", "scope"):
        if authorization.get(field_name) is not None and not isinstance(authorization.get(field_name), str):
            raise MigrationError(f"workflow legado tiene authorization.{field_name} inválido")
    if not isinstance(notes, list) or not all(isinstance(item, str) for item in notes):
        raise MigrationError("workflow legado tiene notes inválido")
    if next_route is not None and not isinstance(next_route, str):
        raise MigrationError("workflow legado tiene nextRoute inválido")
    phase = payload.get("phase")
    if phase is not None and (not isinstance(phase, str) or not phase.strip()):
        raise MigrationError("workflow legado tiene phase inválido")
    waiting_on = payload.get("waitingOn")
    if waiting_on is not None and not isinstance(waiting_on, (str, dict)):
        raise MigrationError("workflow legado tiene waitingOn inválido")
    forbidden = {
        "active", "currentunit", "status", "state", "estado", "priority", "prioridad",
        "assignedto", "assigned", "assignee", "owner", "responsible", "responsable",
        "asignado", "backlog", "queue", "cola", "rank", "position", "posicion",
        "order", "orden", "completedunits", "todo", "doing", "done", "dropped",
        "sprint", "iteration", "iteracion", "area",
    }

    def validate_safe_json(value: object, location: str) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                normalized = contract.normalize_machine_key(str(key))
                if normalized in forbidden:
                    raise MigrationError(f"{location} contiene clave operativa no permitida: {key}")
                validate_safe_json(child, location)
        elif isinstance(value, list):
            for child in value:
                validate_safe_json(child, location)
        elif value is not None and not isinstance(value, (str, int, float, bool)):
            raise MigrationError(f"{location} contiene tipo no serializable")

    validate_safe_json(waiting_on, "workflow.waitingOn")
    return {
        "schemaVersion": 2,
        "updatedAt": generated_at,
        "phase": phase,
        "authorization": authorization,
        "workItemRef": (
            {"id": identifier, "path": reference_path}
            if identifier else None
        ),
        "waitingOn": waiting_on,
        "nextRoute": next_route,
        "checkpoint": {"migrationEvidence": "context/faro-migration-v2.json", "sourceContract": SOURCE_CONTRACT},
        "notes": notes,
    }


def add_write(plan: Plan, relative: str, content: bytes) -> None:
    path, before = read_regular(plan.root, relative, relative, required=False)
    plan.writes[relative] = content
    plan.originals[relative] = before


def prevalidate_shadow(plan: Plan) -> None:
    """Validate the exact projected v2 bytes without touching the workspace."""
    destinations = [move.destination for move in plan.moves]
    check_casefold(destinations, "destinos proyectados")
    with tempfile.TemporaryDirectory(prefix="faro-v2-preflight-") as temporary:
        shadow = Path(temporary)
        (shadow / "context/requirements/work-items").mkdir(parents=True)
        (shadow / "context/requirements/functional").mkdir(parents=True)
        for move in plan.moves:
            source = contract.relative_target(plan.root, move.source, label="origen de preflight")
            destination = shadow / move.destination
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(source.read_bytes())
        for relative, content in plan.writes.items():
            destination = shadow / relative
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(content)
        workflow_content = plan.writes.get("context/workflow.json")
        if workflow_content is not None:
            workflow = json.loads(workflow_content.decode("utf-8"))
            reference = workflow.get("workItemRef") if isinstance(workflow, dict) else None
            if isinstance(reference, dict) and str(reference.get("id", "")).startswith("INC-"):
                for relative in ("context/incidents/README.md", reference.get("path")):
                    if not isinstance(relative, str):
                        raise MigrationError("workflow INC proyectado sin ruta canónica")
                    source = contract.relative_target(plan.root, relative, label="dependencia INC de preflight")
                    if source.is_symlink() or not source.is_file():
                        raise MigrationError(f"dependencia INC ausente/no regular/symlink: {source}")
                    destination = shadow / relative
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    destination.write_bytes(source.read_bytes())
        report = contract.validate_layout(shadow)
        if report.errors:
            raise MigrationError(
                "preflight v2 proyectado inválido: "
                + "; ".join(issue.message for issue in report.errors)
            )


def build_plan(root_value: Path, generated_at: str | None = None) -> Plan:
    try:
        root = contract.workspace_root(root_value)
    except contract.ContractError as error:
        raise MigrationError(str(error)) from error
    generated_at = generated_at or contract.utc_now()
    manifest_path, manifest = json_file(root, "context/faro-workspace.json", "manifiesto")
    version = manifest.get("contractVersion")
    if version == TARGET_CONTRACT:
        if manifest.get("schemaVersion") != 2:
            raise MigrationError("workspace declara contrato v2 con schemaVersion de manifiesto incompatible")
        _stats_path, current_stats = json_file(root, "context/stats.json", "stats")
        if current_stats.get("schemaVersion") != 2 or current_stats.get("contractVersion") != TARGET_CONTRACT:
            raise MigrationError("workspace v2 parcial/incoherente: stats no coincide con manifiesto")
        current_faro = current_stats.get("faro")
        if not isinstance(current_faro, dict) or not isinstance(current_faro.get("version"), str) or not re.fullmatch(
            r"[0-9]+\.[0-9]+\.[0-9]+", current_faro["version"],
        ):
            raise MigrationError("workspace v2 parcial/incoherente: stats.faro.version no es package provenance semántica")
        report = contract.validate_layout(root)
        if report.errors:
            raise MigrationError("workspace declara v2 pero es inválido: " + "; ".join(item.message for item in report.errors))
        return Plan(root, "current", generated_at)
    if version != SOURCE_CONTRACT:
        raise MigrationError(f"contrato no migrable/no degradable: {version!r}; se esperaba {SOURCE_CONTRACT}")
    if manifest.get("schemaVersion") != 1:
        raise MigrationError("manifiesto 1.13 debe tener schemaVersion 1")
    _stats_path, stats = json_file(root, "context/stats.json", "stats")
    if stats.get("contractVersion") != SOURCE_CONTRACT or stats.get("schemaVersion") != 1:
        raise MigrationError("stats y manifiesto no coinciden en contrato 1.13")
    requirements = contract.relative_target(root, "context/requirements", label="requirements root")
    if not requirements.is_dir() or requirements.is_symlink():
        raise MigrationError("context/requirements ausente/no regular/symlink")
    record = contract.relative_target(root, "context/faro-migration-v2.json", label="registro de migración")
    if record.exists():
        raise MigrationError("registro v2 ya existe con manifiesto legado; layout mixto/interrupto")
    new_catalog = contract.relative_target(root, "context/requirements/requirements-catalog.md", label="catálogo nuevo")
    if new_catalog.exists():
        raise MigrationError("requirements-catalog v2 ya existe con contrato 1.13; layout mixto")
    for relative in ("context/requirements/work-items", "context/requirements/functional"):
        path = contract.relative_target(root, relative, label="destino v2")
        if path.exists() and (path.is_symlink() or not path.is_dir() or any(path.iterdir())):
            raise MigrationError(f"destino v2 ocupado; layout mixto: {path}")

    plan = Plan(root, "legacy-migratable", generated_at)
    work, functional = inventory_flat(root, requirements)
    check_casefold(list(work) + list(functional), "IDs legados")
    for identifier, files in sorted(work.items()):
        check_casefold([path.name for path in files], identifier)
        primary, exception = choose_work_primary(identifier, files)
        directory = f"context/requirements/work-items/{identifier}"
        plan.directories.append(directory)
        for source in files:
            destination = f"{directory}/{source.name}"
            target = contract.relative_target(root, destination, label="destino de expediente")
            if target.exists():
                raise MigrationError(f"destino ya existe: {target}")
            plan.moves.append(Move(source.relative_to(root).as_posix(), destination, contract.sha256(source)))
        entry = {
            "id": identifier,
            "kind": identifier.split("-", 1)[0],
            "path": directory,
            "primary": primary.name,
            "source": f"migration:{SOURCE_CONTRACT}:{identifier}:{contract.sha256(primary)[:16]}",
        }
        plan.work_entries.append(entry)
        if exception:
            destination = f"{directory}/{primary.name}"
            plan.legacy_exceptions.append({
                "id": identifier, "kind": identifier.split("-", 1)[0], "primary": destination,
                "sha256": contract.sha256(primary), "reason": "legacy-primary-without-frontmatter",
            })
    for identifier, files in sorted(functional.items()):
        check_casefold([path.name for path in files], identifier)
        primary = choose_df_primary(identifier, files)
        directory = f"context/requirements/functional/{identifier}"
        plan.directories.append(directory)
        for source in files:
            destination = f"{directory}/{source.name}"
            target = contract.relative_target(root, destination, label="destino DF")
            if target.exists():
                raise MigrationError(f"destino ya existe: {target}")
            plan.moves.append(Move(source.relative_to(root).as_posix(), destination, contract.sha256(source)))
        plan.functional_entries.append({
            "id": identifier,
            "path": directory,
            "primary": primary.name,
            "source": f"migration:{SOURCE_CONTRACT}:{identifier}:{contract.sha256(primary)[:16]}",
        })
    plan.directories.extend(["context/requirements/work-items", "context/requirements/functional"])
    plan.directories = sorted(set(plan.directories), key=lambda value: (value.count("/"), value))

    work_rows = [
        [
            item["id"], item["kind"], item["path"], item["primary"], item["source"],
            "—", "—", "—", "—",
        ]
        for item in plan.work_entries
    ]
    work_reservations = [
        [item["id"], item["kind"], item["source"], generated_at]
        for item in plan.work_entries
    ]
    work_catalog = render_catalog(
        "requirements-catalog.md", "Reservas", contract.WORK_RESERVATION_HEADERS,
        work_reservations,
    )
    work_catalog = contract._replace_table(
        work_catalog.decode("utf-8"), "Expedientes", contract.WORK_ENTRY_HEADERS, work_rows,
    ).encode("utf-8")
    add_write(plan, "context/requirements/requirements-catalog.md", work_catalog)
    old_df_path, old_df = read_regular(root, "context/requirements/functional-documents-catalog.md", "catálogo DF legado", required=False)
    reservations = [
        [item["id"], item["source"], generated_at]
        for item in plan.functional_entries
    ] + legacy_df_reservations(
        old_df_path if old_df is not None else None,
        {item["id"] for item in plan.functional_entries}, generated_at,
    )
    reservations.sort(key=lambda row: row[0])
    df_rows = [
        [item["id"], item["path"], item["primary"], item["source"], "—", "—", "—"]
        for item in plan.functional_entries
    ]
    df_catalog = render_catalog("functional-documents-catalog.md", "Reservas", contract.DF_RESERVATION_HEADERS, reservations)
    df_catalog = contract._replace_table(df_catalog.decode("utf-8"), "Documentos", contract.DF_ENTRY_HEADERS, df_rows).encode("utf-8")
    add_write(plan, "context/requirements/functional-documents-catalog.md", df_catalog)

    agents_path, agents = read_regular(root, "AGENTS.md", "AGENTS")
    profile_path, profile = read_regular(root, "context/requirements/project-profile.md", "perfil")
    index_path, index = read_regular(root, "context/README.md", "índice")
    assert agents is not None and profile is not None and index is not None
    add_write(plan, "AGENTS.md", migrate_agents(agents))
    add_write(plan, "context/requirements/project-profile.md", migrate_profile(profile, generated_at))
    add_write(plan, "context/README.md", migrate_index(index))

    new_manifest = json.loads((FARO_ROOT / "templates/faro-workspace-manifest.json").read_text(encoding="utf-8"))
    add_write(plan, "context/faro-workspace.json", (json.dumps(new_manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    stats["schemaVersion"] = 2
    stats["contractVersion"] = TARGET_CONTRACT
    if not isinstance(stats.get("faro"), dict):
        raise MigrationError("stats.faro inválido")
    stats["faro"]["version"] = suite_package_version()
    stats["updatedAt"] = generated_at
    add_write(plan, "context/stats.json", (json.dumps(stats, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    workflow_path, workflow_bytes = read_regular(root, "context/workflow.json", "workflow", required=False)
    legacy_workflow = None
    if workflow_bytes is not None:
        try:
            legacy_workflow = json.loads(workflow_bytes.decode("utf-8"))
        except (UnicodeError, json.JSONDecodeError) as error:
            raise MigrationError(f"workflow legado inválido: {error}") from error
        if not isinstance(legacy_workflow, dict):
            raise MigrationError("workflow legado debe ser objeto")
        migrated_workflow = migrate_workflow(
            legacy_workflow, {item["id"] for item in plan.work_entries}, generated_at, root,
        )
        add_write(plan, "context/workflow.json", (json.dumps(migrated_workflow, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))

    snapshots = {
        relative: {
            "sha256": digest_bytes(before),
            "contentBase64": base64.b64encode(before).decode("ascii"),
        }
        for relative, before in sorted(plan.originals.items()) if before is not None
    }
    writes_evidence = [
        {
            "path": relative,
            "beforeSha256": digest_bytes(plan.originals[relative]) if plan.originals[relative] is not None else None,
            "afterSha256": digest_bytes(content),
        }
        for relative, content in sorted(plan.writes.items())
    ]
    record_payload = {
        "schemaVersion": 1,
        "migration": "1.13.0-to-2.0.0",
        "sourceContract": SOURCE_CONTRACT,
        "targetContract": TARGET_CONTRACT,
        "appliedAt": generated_at,
        "moves": [move.__dict__ for move in plan.moves],
        "createdDirectories": plan.directories,
        "writes": writes_evidence,
        "snapshots": snapshots,
        "legacyWorkflowSnapshot": legacy_workflow,
        "legacyPrimaryExceptions": plan.legacy_exceptions,
        "mappingReconciliation": "PENDING",
        "notes": [
            "Los bytes y basenames documentales fueron preservados.",
            "No se crearon items remotos ni se aplicaron mapeos legados a todas las clases.",
        ],
    }
    add_write(plan, "context/faro-migration-v2.json", (json.dumps(record_payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"))
    prevalidate_shadow(plan)
    return plan


def verify_unchanged(plan: Plan) -> None:
    for move in plan.moves:
        source = contract.relative_target(plan.root, move.source, label="origen")
        if not source.is_file() or source.is_symlink() or contract.sha256(source) != move.sha256:
            raise MigrationError(f"origen cambió desde preflight: {move.source}")
    for relative, before in plan.originals.items():
        path = contract.relative_target(plan.root, relative, label="archivo de control")
        if before is None:
            if path.exists():
                raise MigrationError(f"destino apareció desde preflight: {relative}")
        elif not path.is_file() or path.is_symlink() or path.read_bytes() != before:
            raise MigrationError(f"archivo de control cambió desde preflight: {relative}")


def rollback(plan: Plan, moved: list[Move], created: list[Path]) -> list[str]:
    problems: list[str] = []
    for relative, before in reversed(list(plan.originals.items())):
        path = plan.root / relative
        try:
            if before is None:
                if path.exists() and path.is_file() and not path.is_symlink():
                    path.unlink()
            else:
                contract.safe_atomic_write(plan.root, path, before)
        except Exception as error:
            problems.append(f"restaurar {relative}: {error}")
    for move in reversed(moved):
        source = plan.root / move.source
        destination = plan.root / move.destination
        try:
            if destination.is_file() and not destination.is_symlink() and not source.exists():
                os.replace(destination, source)
        except Exception as error:
            problems.append(f"revertir {move.destination}: {error}")
    for directory in reversed(created):
        try:
            directory.rmdir()
        except OSError:
            pass
    return problems


def apply_plan(plan: Plan) -> dict:
    if plan.classification == "current":
        return {**plan.serializable(), "mode": "already-current"}
    lock_target = contract.relative_target(plan.root, "context/faro-migration-v2", label="lock de migración")
    with contract.catalog_lock(plan.root, lock_target):
        fresh = build_plan(plan.root, plan.generated_at)
        if fresh.serializable() != plan.serializable():
            raise MigrationError("el plan cambió al adquirir el lock; ejecutar dry-run nuevamente")
        verify_unchanged(plan)
        created: list[Path] = []
        moved: list[Move] = []
        try:
            for relative in plan.directories:
                directory = contract.relative_target(plan.root, relative, label="directorio de migración")
                if not directory.exists():
                    directory.mkdir()
                    created.append(directory)
            for move in plan.moves:
                source = contract.relative_target(plan.root, move.source, label="origen")
                destination = contract.relative_target(plan.root, move.destination, label="destino")
                if destination.exists():
                    raise MigrationError(f"destino apareció durante apply: {move.destination}")
                os.replace(source, destination)
                moved.append(move)
                if contract.sha256(destination) != move.sha256:
                    raise MigrationError(f"hash cambió al mover {move.destination}")
            for relative, content in plan.writes.items():
                path = contract.relative_target(plan.root, relative, label="escritura migrada")
                contract.safe_atomic_write(plan.root, path, content)
            report = contract.validate_layout(plan.root)
            if report.errors:
                raise MigrationError("validación v2 falló: " + "; ".join(item.message for item in report.errors))
        except Exception as error:
            rollback_errors = rollback(plan, moved, created)
            suffix = f"; rollback incompleto: {'; '.join(rollback_errors)}" if rollback_errors else ""
            if isinstance(error, MigrationError):
                raise MigrationError(str(error) + suffix) from error
            raise MigrationError(f"apply falló: {error}{suffix}") from error
    return {**plan.serializable(), "mode": "applied"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path.cwd())
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Sólo muestra el plan (predeterminado).")
    mode.add_argument("--apply", action="store_true", help="Aplica la migración explícitamente.")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        plan = build_plan(args.root)
        result = apply_plan(plan) if args.apply else plan.serializable()
        if args.json:
            print(json.dumps(result, ensure_ascii=False, indent=2))
        else:
            print(f"FARO migration: {result['classification']} / {result['mode']}")
            print(f"Moves: {len(result['moves'])}; writes: {len(result['writes'])}")
        return 0
    except (MigrationError, contract.ContractError, OSError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
