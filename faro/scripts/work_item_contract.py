#!/usr/bin/env python3
"""FARO v2 catalog, resolver, integrity and immutable-close contract.

The module is dependency-free and is shared by doctor, migration and lifecycle
skills. Catalog mutations are serialized with an OS file lock and committed by
atomic replacement. Without ``--apply`` every mutating command is a preview.
"""
from __future__ import annotations

import argparse
import base64
import binascii
import hashlib
import json
import os
import re
import sys
import tempfile
import unicodedata
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path, PurePosixPath
from typing import Iterator
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener

try:  # POSIX and Windows use the same lock-file protocol with native backends.
    import fcntl  # type: ignore
except ImportError:  # pragma: no cover - exercised on Windows runners.
    fcntl = None  # type: ignore
    import msvcrt  # type: ignore


FARO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = FARO_ROOT / "templates" / "faro-workspace-config.json"
EMPTY_VALUES = {"", "-", "—", "PENDIENTE", "NO_REGISTRADO", "NULL", "NONE"}
LEGACY_WORK_FILE = re.compile(r"^(RM|BUG|TEC)-[0-9]{4}(?:[-.].*)?$", re.IGNORECASE)
LEGACY_DF_FILE = re.compile(r"^DF-[0-9]{3}(?:[-.].*)?$", re.IGNORECASE)
RESERVED_LEGACY_PREFIX = re.compile(r"^(?:RM|BUG|TEC|DF)-", re.IGNORECASE)
WORK_RESERVATION_HEADERS = ["ID", "Tipo", "Fuente de reserva serializada", "Fecha y zona"]
WORK_ENTRY_HEADERS = [
    "ID", "Tipo", "Ruta canónica", "Documento principal", "Fuente de reserva serializada", "Proveedor",
    "ID remoto", "URL remota", "Relacionados",
]
DF_RESERVATION_HEADERS = ["ID", "Fuente de reserva serializada", "Fecha y zona"]
DF_ENTRY_HEADERS = [
    "ID", "Ruta canónica", "Documento principal", "Fuente de reserva serializada", "Dominio o proceso",
    "Versión / baseline", "Relacionados",
]
IMPACT_FIELDS = (
    "impact_functional", "impact_architecture", "impact_operations", "impact_reference",
)
INCIDENT_ID = re.compile(r"INC-[0-9]{4}\Z")
INCIDENT_PATH = re.compile(
    r"context/incidents/(INC-[0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md\Z"
)
CRITERION_ID = re.compile(r"CA-[0-9]{3,}\Z")
PROMOTION_DESTINATIONS = {
    "FUNCTIONAL": "functional",
    "ARCHITECTURE": "architecture",
    "OPERATIONS": "operations",
    "REFERENCE": "reference",
}
DURABLE_AUTHORITY_KEYS = {
    "FUNCTIONAL": "product",
    "ARCHITECTURE": "architecture",
    "OPERATIONS": "operations",
    "REFERENCE": "reference",
}
PLACEHOLDER_VALUES = {
    "", "-", "—", "PENDIENTE", "PENDING", "NO DEFINIDO", "NO_DEFINIDO",
    "NO APLICA", "NO_APLICA", "NOT APPLICABLE", "N/A", "NA",
    "TBD", "TODO", "NULL", "NONE",
}


@dataclass(frozen=True)
class Issue:
    severity: str
    code: str
    message: str


@dataclass(frozen=True)
class WorkItemEntry:
    identifier: str
    kind: str
    path: str
    primary: str
    reservation_source: str
    provider: str | None = None
    external_id: str | None = None
    external_url: str | None = None
    related: str | None = None


@dataclass(frozen=True)
class FunctionalDocumentEntry:
    identifier: str
    path: str
    primary: str
    reservation_source: str
    domain: str | None = None
    baseline: str | None = None
    related: str | None = None


@dataclass
class ValidationReport:
    contract_version: str
    layout: str
    work_items: dict[str, WorkItemEntry] = field(default_factory=dict)
    functional_documents: dict[str, FunctionalDocumentEntry] = field(default_factory=dict)
    legacy_work_files: list[str] = field(default_factory=list)
    legacy_functional_files: list[str] = field(default_factory=list)
    issues: list[Issue] = field(default_factory=list)

    @property
    def errors(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "error"]

    @property
    def warnings(self) -> list[Issue]:
        return [issue for issue in self.issues if issue.severity == "warning"]

    def serializable(self) -> dict:
        return {
            "contractVersion": self.contract_version,
            "layout": self.layout,
            "workItems": {key: asdict(value) for key, value in sorted(self.work_items.items())},
            "functionalDocuments": {
                key: asdict(value) for key, value in sorted(self.functional_documents.items())
            },
            "legacyWorkFiles": self.legacy_work_files,
            "legacyFunctionalFiles": self.legacy_functional_files,
            "issues": [asdict(issue) for issue in self.issues],
        }


class ContractError(RuntimeError):
    pass


def load_json(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as error:
        raise ContractError(f"JSON inválido o ausente: {path}: {error}") from error
    if not isinstance(value, dict):
        raise ContractError(f"JSON debe ser un objeto: {path}")
    return value


def load_contract_config(path: Path = CONFIG_PATH) -> dict:
    config = load_json(path)
    if config.get("schemaVersion") != 2 or config.get("contractVersion") != "2.0.0":
        raise ContractError(f"configuración central v2 incompatible: {path}")
    return config


def normalize_header(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    plain = "".join(char for char in decomposed if not unicodedata.combining(char))
    return " ".join(plain.lower().split())


def _markdown_h2(line: str) -> str | None:
    match = re.fullmatch(r"[ \t]{0,3}##[ \t]+(.*?)[ \t]*", line)
    if not match:
        return None
    title = match.group(1)
    closing = re.fullmatch(r"(.*?)[ \t]+#+[ \t]*", title)
    if closing:
        title = closing.group(1)
    return title.strip()


def _markdown_visible(lines: list[str]) -> list[bool]:
    """Mark lines outside fenced code and HTML comments."""
    visible: list[bool] = []
    fence_char: str | None = None
    fence_size = 0
    in_comment = False
    for line in lines:
        stripped = line.lstrip(" ")
        indent = len(line) - len(stripped)
        if fence_char is not None:
            visible.append(False)
            close = re.match(rf"^{re.escape(fence_char)}{{{fence_size},}}[ \t]*$", stripped)
            if indent <= 3 and close:
                fence_char = None
                fence_size = 0
            continue
        fence = re.match(r"^(`{3,}|~{3,})", stripped) if indent <= 3 else None
        if fence:
            fence_char = fence.group(1)[0]
            fence_size = len(fence.group(1))
            visible.append(False)
            continue
        if in_comment:
            visible.append(False)
            if "-->" in line:
                in_comment = False
            continue
        if "<!--" in line:
            visible.append(False)
            if "-->" not in line.split("<!--", 1)[1]:
                in_comment = True
            continue
        visible.append(True)
    return visible


def normalize_machine_key(value: str) -> str:
    """Normalize JSON/YAML-like keys across camel, snake, kebab and spaced forms."""
    return re.sub(r"[^a-z0-9]", "", normalize_header(value))


def safe_relative(value: str) -> bool:
    if not value or "\\" in value or value.startswith("/"):
        return False
    path = PurePosixPath(value)
    return all(part not in {"", ".", ".."} for part in path.parts)


def _is_within(root: Path, target: Path) -> bool:
    try:
        target.relative_to(root)
        return True
    except ValueError:
        return False


def workspace_root(value: Path) -> Path:
    raw = value.expanduser().absolute()
    if raw.is_symlink():
        raise ContractError(f"el root no puede ser un enlace simbólico: {raw}")
    try:
        resolved = raw.resolve(strict=True)
    except OSError as error:
        raise ContractError(f"root inaccesible: {raw}: {error}") from error
    if not resolved.is_dir():
        raise ContractError(f"root no es un directorio: {resolved}")
    return resolved


def relative_target(root: Path, value: str, *, label: str) -> Path:
    if not safe_relative(value):
        raise ContractError(f"{label} no es una ruta relativa segura: {value!r}")
    candidate = root.joinpath(*PurePosixPath(value).parts)
    current = root
    for part in PurePosixPath(value).parts:
        current = current / part
        if current.is_symlink():
            raise ContractError(f"{label} atraviesa un enlace simbólico: {current}")
    resolved = candidate.resolve(strict=False)
    if not _is_within(root, resolved):
        raise ContractError(f"{label} escapa del root: {value}")
    return candidate


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_timestamp(value: str, label: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except (AttributeError, ValueError) as error:
        raise ContractError(f"{label} debe ser ISO-8601: {value!r}") from error
    if parsed.tzinfo is None:
        raise ContractError(f"{label} debe incluir zona horaria: {value!r}")
    return parsed


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def catalog_value(value: str, label: str) -> str:
    stripped = value.strip()
    if not stripped or "|" in stripped or "\n" in stripped or "\r" in stripped:
        raise ContractError(f"{label} no puede estar vacío ni contener '|'/saltos de línea")
    return stripped


def strict_catalog_token(value: str, label: str) -> str:
    """Validate identity-like CLI input without silently trimming it."""
    if not isinstance(value, str) or value != value.strip():
        raise ContractError(f"{label} no admite espacios externos ni normalización implícita")
    return catalog_value(value, label)


def validated_external_url(value: str) -> str:
    value = catalog_value(value, "external-url")
    parsed = urlparse(value)
    try:
        parsed.port
    except ValueError as error:
        raise ContractError("external-url contiene un puerto inválido") from error
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.username or parsed.password:
        raise ContractError("external-url debe ser http(s), tener host y no incluir credenciales")
    return value


def remote_url_identity(value: str) -> str:
    """Return a stable comparison key without changing the persisted URL."""
    parsed = urlparse(validated_external_url(value))
    host = (parsed.hostname or "").lower()
    port = parsed.port
    if port and not ((parsed.scheme == "https" and port == 443) or (parsed.scheme == "http" and port == 80)):
        host = f"{host}:{port}"
    path = parsed.path.rstrip("/") or "/"
    query = urlencode(sorted(parse_qsl(parsed.query, keep_blank_values=True)))
    return f"{parsed.scheme.lower()}://{host}{path}?{query}".rstrip("?")


def _service_root(value: str, label: str) -> tuple[str, str, int, str]:
    value = validated_external_url(value)
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.query or parsed.fragment:
        raise ContractError(f"{label} debe ser una raíz HTTPS sin query ni fragment")
    port = parsed.port or 443
    path = parsed.path.rstrip("/")
    return parsed.scheme.lower(), (parsed.hostname or "").casefold(), port, path


def _url_belongs_to_service(value: str, service: str, label: str) -> str:
    value = validated_external_url(value)
    parsed = urlparse(value)
    service_scheme, service_host, service_port, service_path = _service_root(service, label)
    value_port = parsed.port or (443 if parsed.scheme == "https" else 80)
    path = parsed.path.rstrip("/")
    if (
        parsed.scheme.lower() != service_scheme
        or (parsed.hostname or "").casefold() != service_host
        or value_port != service_port
        or (service_path and path != service_path and not path.startswith(service_path + "/"))
    ):
        raise ContractError(f"{label} no coincide con la URL remota catalogada")
    return value


def _url_has_identifier(value: str, identifier: str) -> bool:
    parsed = urlparse(value)
    wanted = identifier.casefold()
    path_values = [unquote(part).casefold() for part in parsed.path.split("/") if part]
    query_values = [unquote(item).casefold() for _key, item in parse_qsl(parsed.query, keep_blank_values=True)]
    return wanted in path_values or wanted in query_values


def _path_segments(value: str) -> list[str]:
    return [unquote(part) for part in urlparse(validated_external_url(value)).path.split("/") if part]


def _validate_provider_item_url(provider: str, value: str, identifier: str) -> None:
    """Bind an item URL to the provider's canonical path slot, never a decoy query."""
    parsed = urlparse(validated_external_url(value))
    if parsed.fragment:
        raise ContractError("URL remota de item no admite fragment")
    segments = _path_segments(value)
    expected = identifier.casefold()
    valid = False
    if provider == "JIRA":
        for index, segment in enumerate(segments[:-1]):
            if segment.casefold() == "browse" and segments[index + 1].casefold() == expected:
                valid = index + 2 == len(segments)
            if (
                segment.casefold() == "issue"
                and segments[index + 1].casefold() == expected
                and index >= 3
                and [item.casefold() for item in segments[index - 3:index]]
                in (["rest", "api", "2"], ["rest", "api", "3"])
            ):
                valid = index + 2 == len(segments)
    elif provider == "AZURE_DEVOPS":
        lowered = [item.casefold() for item in segments]
        for marker in ("_workitems", "workitems"):
            for index, segment in enumerate(lowered):
                if segment == marker:
                    if marker == "_workitems":
                        valid = (
                            index + 2 < len(segments)
                            and lowered[index + 1] == "edit"
                            and segments[index + 2].casefold() == expected
                            and index + 3 == len(segments)
                        )
                    else:
                        valid = (
                            index >= 2
                            and index + 1 < len(segments)
                            and lowered[index - 2:index] == ["_apis", "wit"]
                            and segments[index + 1].casefold() == expected
                            and index + 2 == len(segments)
                        )
    else:
        raise ContractError(f"proveedor sin formato URL soportado: {provider}")
    if not valid:
        raise ContractError(
            f"URL remota {provider} no identifica {identifier} en el segmento canónico del item"
        )


def _azure_org_identity(value: str, label: str) -> str:
    parsed = urlparse(validated_external_url(value))
    if parsed.scheme != "https" or parsed.username or parsed.password:
        raise ContractError(f"{label} debe ser HTTPS sin credenciales")
    host = (parsed.hostname or "").casefold()
    segments = _path_segments(value)
    if host == "dev.azure.com" and segments:
        return segments[0].casefold()
    suffix = ".visualstudio.com"
    if host.endswith(suffix) and host != suffix:
        organization = host[: -len(suffix)]
        if re.fullmatch(r"[a-z0-9][a-z0-9-]*", organization):
            return organization
    raise ContractError(f"{label} no es una raíz/URL oficial de Azure DevOps")


def _azure_project_from_item_url(value: str) -> str:
    segments = _path_segments(value)
    lowered = [part.casefold() for part in segments]
    indexes = [
        index for index, part in enumerate(lowered)
        if part in {"_workitems", "_apis"}
    ]
    if len(indexes) != 1 or indexes[0] == 0:
        raise ContractError("URL remota Azure DevOps no contiene proyecto en posición canónica")
    project = segments[indexes[0] - 1]
    if project.casefold() == "defaultcollection" and indexes[0] >= 2:
        project = segments[indexes[0] - 2]
    if not project:
        raise ContractError("URL remota Azure DevOps no contiene proyecto")
    return project


def substantive(value: str | None) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.strip().strip("`*_<>[](){}\"'").strip()
    normalized = normalized.rstrip(".:;!?").strip().upper()
    return normalized not in PLACEHOLDER_VALUES


def _validate_df_token_casing(value: str, label: str) -> None:
    for match in re.finditer(r"(?i)(?<![A-Za-z0-9])df-[0-9]{3}(?![0-9])", value):
        if match.group(0) != match.group(0).upper():
            raise ContractError(
                f"{label} contiene un identificador DF no canónico: {match.group(0)!r}"
            )


def canonical_remote_id(provider: str, external_id: str) -> str:
    """Reject known provider aliases instead of normalizing them silently."""
    if provider == "AZURE_DEVOPS":
        if not re.fullmatch(r"[1-9][0-9]*", external_id):
            raise ContractError(
                "ID remoto Azure DevOps debe ser un entero decimal positivo canónico sin ceros iniciales"
            )
    elif provider == "JIRA":
        if not re.fullmatch(r"[A-Z][A-Z0-9_]*-[0-9]+", external_id):
            raise ContractError(
                "ID remoto Jira debe ser una clave canónica PROJECT-N en mayúsculas"
            )
    else:
        raise ContractError(f"proveedor externo no permitido: {provider}")
    return external_id


def present(value: str) -> str | None:
    stripped = value.strip()
    return None if stripped.upper() in EMPTY_VALUES else stripped


def cell(row: dict[str, str], *names: str) -> str:
    for name in names:
        normalized = normalize_header(name)
        if normalized in row:
            return row[normalized].strip()
    return ""


def _table(path: Path, section: str) -> tuple[list[str], list[dict[str, str]]]:
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"catálogo ausente, no regular o symlink: {path}")
    lines = path.read_text(encoding="utf-8").splitlines()
    visible = _markdown_visible(lines)
    wanted = normalize_header(section)
    headings = [
        index for index, line in enumerate(lines)
        if visible[index]
        and (title := _markdown_h2(line)) is not None
        and normalize_header(title) == wanted
    ]
    if not headings:
        raise ContractError(f"{path}: falta ## {section}")
    if len(headings) != 1:
        raise ContractError(f"{path}: ## {section} debe existir exactamente una vez")
    heading = headings[0]
    runs: list[list[str]] = []
    current: list[str] = []
    for index in range(heading + 1, len(lines)):
        line = lines[index]
        if visible[index] and _markdown_h2(line) is not None:
            break
        if visible[index] and line.lstrip().startswith("|"):
            current.append(line)
        elif current:
            runs.append(current)
            current = []
    if current:
        runs.append(current)
    if len(runs) != 1:
        raise ContractError(
            f"{path}: ## {section} debe contener exactamente una tabla Markdown contigua"
        )
    raw = [
        [item.strip() for item in line.strip().strip("|").split("|")]
        for line in runs[0]
    ]
    if len(raw) < 2:
        raise ContractError(f"{path}: tabla ausente en ## {section}")
    headers = raw[0]
    separator = raw[1]
    if len(separator) != len(headers) or not all(
        re.fullmatch(r":?-{3,}:?", item.replace(" ", "")) for item in separator
    ):
        raise ContractError(f"{path}: separador inválido en ## {section}")
    normalized = [normalize_header(item) for item in headers]
    if len(set(normalized)) != len(normalized):
        raise ContractError(f"{path}: columnas duplicadas en ## {section}")
    rows: list[dict[str, str]] = []
    for number, values in enumerate(raw[2:], start=1):
        if len(values) != len(headers):
            raise ContractError(
                f"{path}: fila {number} de ## {section} tiene {len(values)} columnas; "
                f"se esperaban {len(headers)}"
            )
        rows.append(dict(zip(normalized, values)))
    return headers, rows


def _safe_table(path: Path, section: str, issues: list[Issue]) -> tuple[list[str], list[dict[str, str]]]:
    try:
        return _table(path, section)
    except (ContractError, OSError, UnicodeError) as error:
        issues.append(Issue("error", "catalog-invalid", str(error)))
        return [], []


def _replace_table(text: str, section: str, headers: list[str], rows: list[list[str]]) -> str:
    lines = text.splitlines()
    wanted = normalize_header(section)
    heading: int | None = None
    for index, line in enumerate(lines):
        if line.startswith("## ") and normalize_header(line[3:]) == wanted:
            heading = index
            break
    if heading is None:
        raise ContractError(f"falta ## {section}")
    start: int | None = None
    end: int | None = None
    for index in range(heading + 1, len(lines)):
        if lines[index].startswith("## "):
            break
        if lines[index].lstrip().startswith("|"):
            start = index
            end = index
            while end < len(lines) and lines[end].lstrip().startswith("|"):
                end += 1
            break
    if start is None or end is None:
        raise ContractError(f"tabla ausente en ## {section}")
    rendered = [
        "| " + " | ".join(headers) + " |",
        "| " + " | ".join("---" for _ in headers) + " |",
    ]
    for row in rows:
        if len(row) != len(headers):
            raise ContractError(f"fila interna inválida para ## {section}")
        rendered.append("| " + " | ".join(row) + " |")
    result = lines[:start] + rendered + lines[end:]
    return "\n".join(result) + "\n"


def _require_headers(actual: list[str], expected: list[str], path: Path, section: str) -> None:
    if [normalize_header(item) for item in actual] != [normalize_header(item) for item in expected]:
        raise ContractError(
            f"{path}: columnas de ## {section} deben ser exactamente: {', '.join(expected)}"
        )


def allowed_providers(config: dict) -> set[str]:
    values = config.get("initialization", {}).get("workTrackingProviders", [])
    return {value for value in values if isinstance(value, str) and value}


def _assert_catalog_integrity(
    config: dict,
    published: list[dict[str, str]],
    reservations: list[dict[str, str]],
    *,
    functional: bool,
) -> None:
    pattern = re.compile(
        config["functionalDocuments"]["idPattern"] if functional
        else config["workItems"]["idPattern"]
    )
    seen_ids: dict[str, str] = {}
    seen_sources: dict[tuple[str, str], str] = {}
    seen_remote_ids: dict[tuple[str, str], str] = {}
    seen_remote_urls: dict[tuple[str, str], str] = {}
    published_rows: dict[str, dict[str, str]] = {}
    bound_publications: set[str] = set()
    for row in published:
        identifier = cell(row, "ID")
        if identifier != identifier.upper() or not pattern.fullmatch(identifier):
            raise ContractError(f"ID publicado inválido/no canónico: {identifier!r}")
        if identifier.casefold() in seen_ids:
            raise ContractError(f"ID duplicado sin distinguir mayúsculas: {identifier}")
        seen_ids[identifier.casefold()] = identifier
        published_rows[identifier.casefold()] = row
        path_value = cell(row, "Ruta canónica")
        expected_root = config["workspace"]["functionalRoot" if functional else "workItemsRoot"]
        if path_value != f"{expected_root}/{identifier}":
            raise ContractError(f"ruta publicada no canónica para {identifier}: {path_value!r}")
        primary = cell(row, "Documento principal")
        if not primary or PurePosixPath(primary).name != primary or "\\" in primary or PurePosixPath(primary).suffix.lower() != ".md":
            raise ContractError(f"Documento principal inválido para {identifier}: {primary!r}")
        if functional and not re.fullmatch(rf"{re.escape(identifier)}(?:[-.].*)?\.md", primary):
            raise ContractError(
                f"Documento principal DF debe comenzar exactamente por {identifier} en mayúsculas: {primary!r}"
            )
        if functional:
            _validate_df_token_casing(cell(row, "Relacionados"), f"Relacionados de {identifier}")
        kind = "DF" if functional else cell(row, "Tipo")
        source = present(cell(row, "Fuente de reserva serializada"))
        if source is None:
            raise ContractError(f"publicación {identifier} sin fuente de reserva serializada")
        catalog_value(source, "fuente de reserva")
        source_namespace = "DF" if functional else "WORK"
        source_key = (source_namespace, source.casefold())
        if source_key in seen_sources:
            raise ContractError(
                f"fuente de reserva duplicada para {source_namespace}: {source} "
                f"({seen_sources[source_key]} / {identifier})"
            )
        seen_sources[source_key] = identifier
        if not functional:
            if kind != identifier.split("-", 1)[0]:
                raise ContractError(f"tipo publicado no coincide con {identifier}")
            remote = tuple(present(cell(row, name)) for name in ("Proveedor", "ID remoto", "URL remota"))
            if sum(value is not None for value in remote) not in {0, 3}:
                raise ContractError(f"referencia externa parcial para {identifier}")
            if all(remote) and remote[0] not in allowed_providers(config):
                raise ContractError(f"proveedor externo no permitido para {identifier}: {remote[0]}")
            if all(remote):
                provider, external_id, external_url = remote
                assert provider is not None and external_id is not None and external_url is not None
                canonical_remote_id(provider, external_id)
                _validate_provider_item_url(provider, external_url, external_id)
                remote_id_key = (provider.casefold(), external_id.casefold())
                remote_url_key = (provider.casefold(), remote_url_identity(external_url))
                if remote_id_key in seen_remote_ids:
                    raise ContractError(
                        f"item remoto duplicado por proveedor/ID: {seen_remote_ids[remote_id_key]} / {identifier}"
                    )
                if remote_url_key in seen_remote_urls:
                    raise ContractError(
                        f"item remoto duplicado por proveedor/URL: {seen_remote_urls[remote_url_key]} / {identifier}"
                    )
                seen_remote_ids[remote_id_key] = identifier
                seen_remote_urls[remote_url_key] = identifier
    for row in reservations:
        identifier = cell(row, "ID")
        if identifier != identifier.upper() or not pattern.fullmatch(identifier):
            raise ContractError(f"reserva inválida/no canónica: {identifier!r}")
        kind = "DF" if functional else cell(row, "Tipo")
        if kind != identifier.split("-", 1)[0]:
            raise ContractError(f"tipo de reserva no coincide con {identifier}")
        source = present(cell(row, "Fuente de reserva serializada"))
        if source is None:
            raise ContractError(f"reserva {identifier} sin fuente serializada")
        catalog_value(source, "fuente de reserva")
        source_namespace = "DF" if functional else "WORK"
        key = (source_namespace, source.casefold())
        published_row = published_rows.get(identifier.casefold())
        if published_row is not None:
            if identifier.casefold() in bound_publications:
                raise ContractError(f"binding de reserva publicado duplicado: {identifier}")
            published_source = cell(published_row, "Fuente de reserva serializada")
            published_kind = "DF" if functional else cell(published_row, "Tipo")
            if source != published_source or kind != published_kind:
                raise ContractError(
                    f"binding de reserva publicado no coincide con {identifier}: "
                    f"{source!r} / {published_source!r}"
                )
            bound_publications.add(identifier.casefold())
        elif identifier.casefold() in seen_ids:
            raise ContractError(f"ID duplicado entre reservas: {identifier}")
        else:
            seen_ids[identifier.casefold()] = identifier
        if published_row is None and key in seen_sources:
            raise ContractError(
                f"fuente de reserva duplicada para {source_namespace}: {source} "
                f"({seen_sources[key]} / {identifier})"
            )
        if published_row is None:
            seen_sources[key] = identifier
        timestamp = cell(row, "Fecha y zona")
        parse_timestamp(timestamp, f"fecha de reserva {identifier}")
    missing_bindings = sorted(
        row_id for folded, row_id in seen_ids.items()
        if folded in published_rows and folded not in bound_publications
    )
    if missing_bindings:
        raise ContractError(
            "publicaciones sin binding preservado en Reservas: " + ", ".join(missing_bindings)
        )


def parse_frontmatter(path: Path) -> dict[str, str]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeError) as error:
        raise ContractError(f"no se pudo leer front matter de {path}: {error}") from error
    if not lines or lines[0].strip() != "---":
        raise ContractError(f"front matter ausente: {path}")
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration as error:
        raise ContractError(f"front matter sin cierre: {path}") from error
    result: dict[str, str] = {}
    for line in lines[1:end]:
        match = re.match(r"^([A-Za-z_][A-Za-z0-9_-]*):\s*(.*?)\s*$", line)
        if not match:
            continue
        key, value = match.groups()
        if key in result:
            raise ContractError(f"front matter duplica {key}: {path}")
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]
        result[key] = value
    return result


def functional_identity(meta: dict[str, str], path: Path) -> str | None:
    """Return the sole canonical DF identity key, rejecting casing aliases."""
    identity_keys = [key for key in meta if key.casefold() == "df_id"]
    noncanonical = [key for key in identity_keys if key != "df_id"]
    if noncanonical:
        raise ContractError(
            f"{path}: la clave de identidad DF debe ser exactamente df_id; "
            f"no se admiten aliases de casing: {', '.join(noncanonical)}"
        )
    if len(identity_keys) > 1:
        raise ContractError(f"{path}: identidad DF duplicada")
    return meta.get("df_id")


def _legacy_exceptions(root: Path, config: dict, issues: list[Issue]) -> dict[str, dict]:
    try:
        record_path = relative_target(root, config["workspace"]["migrationRecordPath"], label="registro de migración")
    except ContractError as error:
        issues.append(Issue("error", "migration-record-invalid", str(error)))
        return {}
    if not record_path.exists():
        return {}
    if record_path.is_symlink() or not record_path.is_file():
        issues.append(Issue("error", "migration-record-invalid", f"registro de migración inválido: {record_path}"))
        return {}
    try:
        payload = load_json(record_path)
    except ContractError as error:
        issues.append(Issue("error", "migration-record-invalid", str(error)))
        return {}
    if (
        payload.get("schemaVersion") != 1
        or payload.get("migration") != "1.13.0-to-2.0.0"
        or payload.get("sourceContract") != "1.13.0"
        or payload.get("targetContract") != "2.0.0"
    ):
        issues.append(Issue("error", "migration-record-invalid", "registro no acredita migración canónica 1.13.0-to-2.0.0"))
        return {}
    try:
        parse_timestamp(payload.get("appliedAt"), "migration.appliedAt")
    except ContractError as error:
        issues.append(Issue("error", "migration-record-invalid", str(error)))
        return {}
    moves = payload.get("moves")
    if not isinstance(moves, list):
        issues.append(Issue("error", "migration-record-invalid", "registro sin moves verificables"))
        return {}
    move_hashes: dict[str, str] = {}
    for move in moves:
        if not isinstance(move, dict) or set(move) != {"source", "destination", "sha256"}:
            issues.append(Issue("error", "migration-record-invalid", "move inválido en registro"))
            return {}
        source, destination, digest = move.get("source"), move.get("destination"), move.get("sha256")
        if not isinstance(source, str) or not safe_relative(source) or not isinstance(destination, str) or not safe_relative(destination):
            issues.append(Issue("error", "migration-record-invalid", "move contiene ruta insegura"))
            return {}
        if not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest) or destination.casefold() in {key.casefold() for key in move_hashes}:
            issues.append(Issue("error", "migration-record-invalid", "move contiene hash/destino duplicado inválido"))
            return {}
        move_hashes[destination] = digest
    raw = payload.get("legacyPrimaryExceptions", [])
    if not isinstance(raw, list):
        issues.append(Issue("error", "migration-record-invalid", "legacyPrimaryExceptions debe ser una lista"))
        return {}
    result: dict[str, dict] = {}
    for item in raw:
        if not isinstance(item, dict):
            issues.append(Issue("error", "migration-record-invalid", "excepción de primario debe ser objeto"))
            continue
        primary = item.get("primary")
        if not isinstance(primary, str) or not safe_relative(primary) or primary in result:
            issues.append(Issue("error", "migration-record-invalid", f"primary inválido/duplicado: {primary!r}"))
            continue
        identifier = item.get("id")
        kind = item.get("kind")
        if kind not in {"BUG", "TEC"} or not isinstance(identifier, str) or not re.fullmatch(rf"{kind}-[0-9]{{4}}", identifier):
            issues.append(Issue("error", "migration-record-invalid", f"excepción histórica sólo admite BUG/TEC canónico: {identifier!r}/{kind!r}"))
            continue
        primary_path = PurePosixPath(primary)
        expected_parent = PurePosixPath(f"context/requirements/work-items/{identifier}")
        if (
            primary_path.parent != expected_parent
            or not primary_path.name.startswith(identifier)
            or primary_path.suffix.lower() != ".md"
        ):
            issues.append(Issue("error", "migration-record-invalid", f"ruta de excepción no canónica: {primary}"))
            continue
        if item.get("reason") != "legacy-primary-without-frontmatter":
            issues.append(Issue("error", "migration-record-invalid", f"razón no permitida para {primary}"))
            continue
        if not re.fullmatch(r"[0-9a-f]{64}", str(item.get("sha256", ""))):
            issues.append(Issue("error", "migration-record-invalid", f"hash inválido para {primary}"))
            continue
        if move_hashes.get(primary) != item.get("sha256"):
            issues.append(Issue("error", "migration-record-invalid", f"excepción no coincide con move acreditado: {primary}"))
            continue
        result[primary] = item
    return result


def _legacy_exception_ok(
    root: Path,
    identifier: str,
    kind: str,
    primary_value: str,
    primary: Path,
    exceptions: dict[str, dict],
) -> bool:
    full_primary = f"{primary.parent.relative_to(root).as_posix()}/{primary.name}"
    item = exceptions.get(full_primary)
    return bool(
        item
        and kind in {"BUG", "TEC"}
        and item.get("id") == identifier
        and item.get("kind") == kind
        and item.get("sha256") == sha256(primary)
    )


def _validate_frontmatter_identity(
    path: Path,
    identifier: str,
    kind: str,
    issues: list[Issue],
    *,
    primary_value: str,
    root: Path,
    exceptions: dict[str, dict],
    functional: bool = False,
    allow_legacy: bool = True,
) -> None:
    try:
        meta = parse_frontmatter(path)
    except ContractError as error:
        if allow_legacy and _legacy_exception_ok(root, identifier, kind, primary_value, path, exceptions):
            issues.append(Issue(
                "info", "legacy-primary-exception",
                f"{identifier} conserva primario legado sin front matter acreditado por hash: {primary_value}",
            ))
            return
        issues.append(Issue("error", "primary-frontmatter", str(error)))
        return
    if functional:
        try:
            df_id = functional_identity(meta, path)
        except ContractError as error:
            issues.append(Issue("error", "primary-id-ambiguous", str(error)))
            return
        candidates = [("df_id", df_id)]
    else:
        candidates = [
            (name, meta.get(name))
            for name in ("work_item_id", "rm_id", "bug_id", "tec_id")
            if meta.get(name) not in (None, "")
        ]
    candidates = [(name, value) for name, value in candidates if value not in (None, "")]
    if not candidates:
        required = "df_id" if functional else "work_item_id/rm_id/bug_id/tec_id"
        issues.append(Issue("error", "primary-id-missing", f"{path}: falta {required} en front matter"))
        return
    if not allow_legacy and len(candidates) != 1:
        issues.append(Issue("error", "primary-id-ambiguous", f"{path}: un alta v2 debe declarar un solo campo de identidad"))
        return
    for name, value in candidates:
        if value != identifier:
            issues.append(Issue("error", "primary-id-mismatch", f"{path}: {name}={value!r}, esperado {identifier}"))
        implied = {"rm_id": "RM", "bug_id": "BUG", "tec_id": "TEC", "df_id": "DF"}.get(name)
        if implied and implied != kind:
            issues.append(Issue("error", "primary-kind-mismatch", f"{path}: {name} no coincide con tipo {kind}"))
    declared_kind = meta.get("work_item_kind") or meta.get("item_kind") or meta.get("kind")
    if declared_kind and declared_kind != kind:
        issues.append(Issue("error", "primary-kind-mismatch", f"{path}: kind={declared_kind!r}, esperado {kind}"))


def _validate_primary(
    root: Path,
    identifier: str,
    kind: str,
    directory_value: str,
    primary_value: str,
    issues: list[Issue],
    exceptions: dict[str, dict],
    *,
    functional: bool = False,
    allow_legacy: bool = True,
) -> Path | None:
    try:
        directory = relative_target(root, directory_value, label=f"carpeta de {identifier}")
        if not primary_value or PurePosixPath(primary_value).name != primary_value or "\\" in primary_value:
            raise ContractError(f"Documento principal de {identifier} debe ser sólo un basename: {primary_value!r}")
        full_primary_value = f"{directory_value}/{primary_value}"
        primary = relative_target(root, full_primary_value, label=f"primario de {identifier}")
    except ContractError as error:
        issues.append(Issue("error", "primary-path-invalid", str(error)))
        return None
    if PurePosixPath(primary_value).suffix.lower() != ".md":
        issues.append(Issue("error", "primary-path-invalid", f"primario de {identifier} debe ser Markdown: {primary_value}"))
    if not primary.is_file() or primary.is_symlink():
        issues.append(Issue("error", "primary-missing", f"primario ausente/no regular/symlink: {primary}"))
        return None
    _validate_frontmatter_identity(
        primary, identifier, kind, issues, primary_value=full_primary_value, root=root,
        exceptions=exceptions, functional=functional, allow_legacy=allow_legacy,
    )
    return primary


def _validate_dossier_artifacts(identifier: str, dossier: Path, issues: list[Issue]) -> None:
    seen: dict[str, str] = {}
    for item in sorted(dossier.rglob("*")):
        relative = item.relative_to(dossier).as_posix()
        folded = relative.casefold()
        if folded in seen:
            issues.append(Issue("error", "artifact-case-collision", f"{dossier}: {seen[folded]} / {relative}"))
        else:
            seen[folded] = relative
        if item.is_symlink():
            issues.append(Issue("error", "artifact-symlink", f"expediente contiene symlink: {item}"))
            continue
        if not item.is_file() or item.suffix.lower() != ".md":
            continue
        try:
            meta = parse_frontmatter(item)
        except ContractError:
            continue
        for field in ("work_item_id", "rm_id", "bug_id", "tec_id"):
            value = meta.get(field)
            if value and value != identifier:
                issues.append(Issue("error", "artifact-id-mismatch", f"{item}: {field}={value!r}, esperado {identifier}"))


def _validate_functional_artifacts(
    root: Path,
    identifier: str,
    directory: Path,
    issues: list[Issue],
) -> None:
    seen: dict[str, str] = {}
    for item in sorted(directory.rglob("*")):
        relative = item.relative_to(directory).as_posix()
        folded = relative.casefold()
        if folded in seen:
            issues.append(Issue("error", "functional-artifact-case-collision", f"{directory}: {seen[folded]} / {relative}"))
        else:
            seen[folded] = relative
        if item.is_symlink():
            issues.append(Issue("error", "functional-artifact-symlink", f"DF contiene symlink: {item}"))
            continue
        if not item.is_file() or item.suffix.lower() != ".md":
            continue
        canonical_prefix = re.match(rf"^{re.escape(identifier)}(?=[-.])", item.name) is not None
        if re.match(r"^df-", item.name, flags=re.IGNORECASE) and not canonical_prefix:
            issues.append(Issue(
                "error", "functional-artifact-id-case",
                f"{item}: el basename debe comenzar exactamente por {identifier} en mayúsculas",
            ))
        try:
            meta = parse_frontmatter(item)
        except ContractError:
            continue
        try:
            df_id = functional_identity(meta, item)
        except ContractError as error:
            issues.append(Issue("error", "functional-artifact-id-ambiguous", str(error)))
            continue
        if df_id:
            if df_id != identifier:
                issues.append(Issue("error", "functional-artifact-id-mismatch", f"{item}: df_id={df_id!r}, esperado {identifier}"))
            if not canonical_prefix:
                issues.append(Issue(
                    "error", "functional-artifact-id-case",
                    f"{item}: un artefacto con df_id debe usar prefijo {identifier} en el basename",
                ))
            canonical_path = meta.get("canonical_path")
            if canonical_path is not None:
                expected_path = item.relative_to(root).as_posix()
                try:
                    _validate_df_token_casing(canonical_path, f"canonical_path de {item}")
                except ContractError as error:
                    issues.append(Issue("error", "functional-canonical-path", str(error)))
                if canonical_path != expected_path:
                    issues.append(Issue(
                        "error", "functional-canonical-path",
                        f"{item}: canonical_path={canonical_path!r}, esperado {expected_path!r}",
                    ))


def dossier_files(dossier: Path, closure_name: str) -> dict[str, Path]:
    result: dict[str, Path] = {}
    seen: set[str] = set()
    for path in sorted(dossier.rglob("*")):
        if path.is_symlink():
            raise ContractError(f"un expediente no puede contener enlaces simbólicos: {path}")
        if not path.is_file() or path == dossier / closure_name:
            continue
        if path.name == closure_name:
            raise ContractError(
                f"el basename reservado de cierre sólo puede existir en la raíz del expediente: {path}"
            )
        relative = path.relative_to(dossier).as_posix()
        if not safe_relative(relative):
            raise ContractError(f"ruta insegura dentro del expediente: {relative}")
        if relative.casefold() in seen:
            raise ContractError(f"colisión sin distinguir mayúsculas en expediente: {relative}")
        seen.add(relative.casefold())
        result[relative] = path
    return result


def _section_table(path: Path, section: str, headers: list[str]) -> list[dict[str, str]]:
    actual, rows = _table(path, section)
    _require_headers(actual, headers, path, section)
    return rows


def _criterion_contracts(primary: Path) -> list[dict[str, str]]:
    raw_text = primary.read_text(encoding="utf-8")
    raw_lines = raw_text.splitlines(keepends=True)
    visible = _markdown_visible([line.rstrip("\r\n") for line in raw_lines])
    text = "".join(line if visible[index] else "\n" for index, line in enumerate(raw_lines))
    headings = list(re.finditer(
        r"^(#{2,6})\s+(CA-[0-9]{3,})\b[^\n]*$",
        text, flags=re.MULTILINE | re.IGNORECASE,
    ))
    if not headings:
        raise ContractError(f"freeze exige al menos un CA canónico en el primario: {primary}")
    seen: set[str] = set()
    result: list[dict[str, str]] = []
    for index, heading in enumerate(headings):
        identifier = heading.group(2)
        if identifier != identifier.upper() or not CRITERION_ID.fullmatch(identifier):
            raise ContractError(f"CA inválido/no canónico en {primary}: {identifier}")
        if identifier in seen:
            raise ContractError(f"CA duplicado en {primary}: {identifier}")
        seen.add(identifier)
        following_heading = re.search(r"^#{2,6}\s+", text[heading.end():], flags=re.MULTILINE)
        end = heading.end() + following_heading.start() if following_heading else len(text)
        block = text[heading.start():end].rstrip() + "\n"

        def authoritative_field(name: str) -> str:
            matches = re.findall(
                rf"^- {re.escape(name)}:\s*(.*?)\s*$", block,
                flags=re.MULTILINE,
            )
            if len(matches) != 1 or not substantive(matches[0]):
                raise ContractError(
                    f"{identifier} debe declarar una vez '- {name}:' con valor material en {primary}"
                )
            return matches[0]

        result.append({
            "id": identifier,
            "origin": authoritative_field("Origen"),
            "expected": authoritative_field("Resultado esperado"),
            "authoritySha256": hashlib.sha256(block.encode("utf-8")).hexdigest(),
        })
    return result


def _required_delivery_operations(primary: Path) -> list[dict[str, str]]:
    rows = _section_table(
        primary, "Operaciones de entrega requeridas", ["Operación", "Origen del alcance"],
    )
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    for number, row in enumerate(rows, start=1):
        operation = cell(row, "Operación")
        origin = cell(row, "Origen del alcance")
        if not substantive(operation) or not substantive(origin):
            raise ContractError(
                f"operación de entrega autorizada {number} contiene placeholders en {primary}"
            )
        folded = operation.casefold()
        if folded in seen:
            raise ContractError(f"operación de entrega autorizada duplicada: {operation}")
        seen.add(folded)
        result.append({"operation": operation, "origin": origin})
    return result


def _promotion_requirements(primary: Path) -> dict[str, dict[str, str]]:
    rows = _section_table(
        primary, "Impacto en conocimiento durable",
        ["Destino", "Delta autorizado", "Resolución requerida", "Fuente / autorización"],
    )
    if len(rows) != len(PROMOTION_DESTINATIONS):
        raise ContractError(
            "autoridad primaria de impacto durable exige exactamente "
            "FUNCTIONAL/ARCHITECTURE/OPERATIONS/REFERENCE"
        )
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        destination = cell(row, "Destino")
        delta = cell(row, "Delta autorizado")
        resolution = cell(row, "Resolución requerida")
        source = cell(row, "Fuente / autorización")
        if destination not in PROMOTION_DESTINATIONS or destination in result:
            raise ContractError(f"destino durable inválido/duplicado en primario: {destination!r}")
        if resolution not in {"INCORPORAR", "NO_APLICA"}:
            raise ContractError(
                f"resolución durable de {destination} debe ser INCORPORAR o NO_APLICA"
            )
        if not substantive(source):
            raise ContractError(f"impacto durable {destination} carece de fuente/autorización")
        if resolution == "INCORPORAR" and not substantive(delta):
            raise ContractError(f"impacto durable {destination} carece de delta autorizado")
        if resolution == "NO_APLICA" and present(delta) is not None:
            raise ContractError(f"impacto durable {destination} NO_APLICA debe usar delta —")
        result[destination] = {
            "delta": delta,
            "resolution": resolution,
            "source": source,
        }
    return result


def _evidence_snapshot(
    dossier: Path,
    raw: str,
    *,
    label: str,
    forbidden: set[str],
) -> list[dict[str, str]]:
    if not substantive(raw):
        raise ContractError(f"{label} exige evidencia local")
    result: list[dict[str, str]] = []
    seen: set[str] = set()
    seen_file_ids: set[tuple[int, int]] = set()
    forbidden_file_ids: set[tuple[int, int]] = set()
    for forbidden_value in forbidden:
        if not safe_relative(forbidden_value):
            continue
        forbidden_path = relative_target(
            dossier, forbidden_value, label=f"artefacto declarativo prohibido de {label}",
        )
        if forbidden_path.is_file() and not forbidden_path.is_symlink():
            stat = forbidden_path.stat()
            forbidden_file_ids.add((stat.st_dev, stat.st_ino))
    for value in (part.strip().strip("`") for part in raw.split(";")):
        if not value:
            continue
        if not safe_relative(value):
            raise ContractError(f"{label} contiene ruta de evidencia insegura: {value!r}")
        if PurePosixPath(value).as_posix() in forbidden:
            raise ContractError(f"{label} no puede autoacreditarse con {value}")
        if value.casefold() in seen:
            raise ContractError(f"{label} duplica evidencia: {value}")
        seen.add(value.casefold())
        evidence = relative_target(dossier, value, label=f"evidencia de {label}")
        if evidence.is_symlink() or not evidence.is_file():
            raise ContractError(f"{label} referencia evidencia ausente/no regular/symlink: {evidence}")
        if evidence.stat().st_size == 0:
            raise ContractError(f"{label} referencia evidencia vacía: {evidence}")
        stat = evidence.stat()
        file_id = (stat.st_dev, stat.st_ino)
        if file_id in forbidden_file_ids:
            raise ContractError(
                f"{label} no puede autoacreditarse ni usar un hardlink de un artefacto declarativo: {value}"
            )
        if file_id in seen_file_ids:
            raise ContractError(f"{label} duplica el mismo archivo/hardlink de evidencia: {value}")
        seen_file_ids.add(file_id)
        result.append({"path": value, "sha256": sha256(evidence)})
    if not result:
        raise ContractError(f"{label} exige al menos una evidencia local")
    return result


def _functional_promotion(
    root: Path,
    entry: WorkItemEntry,
    route: str,
    baseline: str,
    target: Path,
) -> None:
    config = load_contract_config()
    catalog = relative_target(
        root, config["workspace"]["functionalCatalogPath"], label="catálogo funcional",
    )
    headers, rows = _table(catalog, "Documentos")
    _require_headers(headers, DF_ENTRY_HEADERS, catalog, "Documentos")
    reservations_headers, reservations = _table(catalog, "Reservas")
    _require_headers(reservations_headers, DF_RESERVATION_HEADERS, catalog, "Reservas")
    _assert_catalog_integrity(config, rows, reservations, functional=True)
    matches = [
        row for row in rows
        if f"{cell(row, 'Ruta canónica')}/{cell(row, 'Documento principal')}" == route
    ]
    if len(matches) != 1:
        raise ContractError(
            f"promoción FUNCTIONAL no resuelve un único DF publicado para {route}"
        )
    row = matches[0]
    df_id = cell(row, "ID")
    if not re.fullmatch(config["functionalDocuments"]["idPattern"], df_id):
        raise ContractError(f"promoción FUNCTIONAL usa DF no canónico: {df_id!r}")
    if cell(row, "Versión / baseline") != baseline:
        raise ContractError(
            f"baseline promovida {baseline!r} no coincide con catálogo DF {cell(row, 'Versión / baseline')!r}"
        )
    metadata = parse_frontmatter(target)
    if metadata.get("document_status") != "BASELINED" or metadata.get("baseline") != baseline:
        raise ContractError(
            f"promoción FUNCTIONAL exige document_status BASELINED y baseline {baseline!r} en {target}"
        )
    trace_headers = [
        "Work item y versión", "Ruta estable", "Secciones/elementos", "Impacto",
        "Resultado de promoción", "Evidencia",
    ]
    trace_rows = _section_table(target, "10. Cambios promovidos desde expedientes", trace_headers)
    traced = [
        item for item in trace_rows
        if _contains_identifier_token(cell(item, "Work item y versión"), entry.identifier)
        and cell(item, "Resultado de promoción") == "INCORPORADO"
        and substantive(cell(item, "Evidencia"))
    ]
    if len(traced) != 1:
        raise ContractError(
            f"promoción FUNCTIONAL exige una fila INCORPORADO trazable a {entry.identifier} en {target}"
        )
    if not _contains_identifier_token(target.read_text(encoding="utf-8", errors="replace"), entry.identifier):
        raise ContractError(
            f"documento durable promovido no traza el expediente {entry.identifier}: {route}"
        )


def _durable_authorities(root: Path) -> dict[str, str | None]:
    config = load_contract_config()
    profile = relative_target(root, config["workspace"]["profilePath"], label="perfil")
    if not profile.is_file() or profile.is_symlink():
        raise ContractError(f"promoción durable exige perfil regular: {profile}")
    text = profile.read_text(encoding="utf-8")
    header = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, flags=re.DOTALL)
    if not header:
        raise ContractError("promoción durable exige front matter de perfil válido")
    lines = header.group(1).splitlines()
    indexes = [index for index, line in enumerate(lines) if line == "durable_documentation:"]
    if len(indexes) != 1:
        raise ContractError("perfil debe declarar durable_documentation una vez")
    start = indexes[0] + 1
    end = next(
        (
            index for index in range(start, len(lines))
            if lines[index].strip() and len(lines[index]) - len(lines[index].lstrip()) == 0
        ),
        len(lines),
    )
    result: dict[str, str | None] = {}
    for line in lines[start:end]:
        match = re.fullmatch(r"  (product|architecture|operations|reference):\s*([^#]*?)\s*", line)
        if match:
            result[match.group(1)] = _yaml_scalar(match.group(2))
    if set(result) != set(DURABLE_AUTHORITY_KEYS.values()):
        raise ContractError("perfil debe declarar autoridades product/architecture/operations/reference")
    return result


def _promotion_authority_allows(root: Path, destination: str, route: str, target: Path) -> None:
    authority = _durable_authorities(root).get(DURABLE_AUTHORITY_KEYS[destination])
    if authority is None or not safe_relative(authority):
        raise ContractError(f"promoción {destination} no tiene autoridad durable configurada")
    authority_path = relative_target(root, authority, label=f"autoridad {destination}")
    authority_relative = PurePosixPath(authority)
    route_relative = PurePosixPath(route)
    allowed = (
        route_relative == authority_relative
        if authority_path.is_file()
        else route_relative == authority_relative or authority_relative in route_relative.parents
    )
    if not allowed:
        raise ContractError(
            f"promoción {destination} apunta fuera de su autoridad {authority}: {route}"
        )
    if target.suffix.lower() != ".md":
        raise ContractError(f"promoción {destination} debe apuntar a documentación Markdown")


def _verify_promoted_version(target: Path, version: str) -> None:
    digest = sha256(target)
    normalized = version.removeprefix("sha256:")
    if re.fullmatch(r"[0-9a-f]{64}", normalized) and normalized == digest:
        return
    try:
        metadata = parse_frontmatter(target)
    except ContractError as error:
        raise ContractError(
            f"versión/baseline {version!r} no está acreditada por metadata ni SHA-256 en {target}"
        ) from error
    declared = {
        metadata.get(name)
        for name in ("document_version", "version", "baseline", "revision", "date")
        if substantive(metadata.get(name))
    }
    if version not in declared:
        raise ContractError(
            f"versión/baseline {version!r} no coincide con metadata ni SHA-256 de {target}"
        )


def _contains_identifier_token(text: str, identifier: str) -> bool:
    return re.search(
        rf"(?<![A-Za-z0-9]){re.escape(identifier)}(?![A-Za-z0-9])", text,
    ) is not None


def _validate_destination_promotion(destination: str, target: Path) -> None:
    if destination != "ARCHITECTURE":
        return
    if not re.fullmatch(r"ADR-[0-9]{3,}(?:-[A-Za-z0-9][A-Za-z0-9-]*)?\.md", target.name):
        raise ContractError(
            f"promoción ARCHITECTURE debe apuntar a un ADR canónico, no a {target.name!r}"
        )
    metadata = parse_frontmatter(target)
    if metadata.get("status") != "accepted":
        raise ContractError("promoción ARCHITECTURE exige un ADR con status: accepted")
    heading = next(
        (line for line in target.read_text(encoding="utf-8", errors="replace").splitlines() if line.startswith("# ")),
        "",
    )
    adr_id = "-".join(target.stem.split("-", 2)[:2])
    if re.match(rf"^# {re.escape(adr_id)}(?:\s|—|-|$)", heading) is None:
        raise ContractError(f"encabezado ADR no coincide con su ID canónico: {target}")


def _delivery_gate(
    root: Path,
    entry: WorkItemEntry,
    dossier: Path,
    required_operations: list[str],
) -> dict:
    path = dossier / f"{entry.identifier}-entrega.md"
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"delivery SATISFIED exige artefacto regular {path}")
    meta = parse_frontmatter(path)
    expected_canonical = path.relative_to(root).as_posix()
    if (
        meta.get("work_item_id") != entry.identifier
        or meta.get("artifact_type") != "DELIVERY_EVIDENCE"
        or meta.get("canonical_path") != expected_canonical
        or meta.get("delivery_outcome") != "SATISFIED"
        or not substantive(meta.get("document_version"))
    ):
        raise ContractError(
            "entrega debe acreditar ID, tipo, ruta, versión y delivery_outcome: SATISFIED"
        )
    headers = ["Operación", "Resultado", "Referencia", "Evidencia local", "Fecha y zona"]
    rows = _section_table(path, "Operaciones verificadas", headers)
    if not rows:
        raise ContractError("delivery SATISFIED exige al menos una operación verificada")
    operations: list[dict] = []
    seen_operations: set[str] = set()
    for number, row in enumerate(rows, start=1):
        operation = cell(row, "Operación")
        result = cell(row, "Resultado")
        reference = cell(row, "Referencia")
        evidence_value = cell(row, "Evidencia local")
        timestamp = cell(row, "Fecha y zona")
        if not all(substantive(value) for value in (operation, reference, evidence_value, timestamp)):
            raise ContractError(f"operación de entrega {number} contiene placeholders")
        if operation.casefold() in seen_operations:
            raise ContractError(f"operación de entrega duplicada: {operation}")
        seen_operations.add(operation.casefold())
        if result != "SATISFIED":
            raise ContractError(f"operación de entrega {number} no está SATISFIED: {result!r}")
        delivered_at = parse_timestamp(timestamp, f"fecha de entrega {number}")
        if delivered_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ContractError(f"fecha de entrega {number} está en el futuro: {timestamp}")
        evidence = _evidence_snapshot(
            dossier, evidence_value, label=f"entrega {number}",
            forbidden={
                entry.primary,
                f"{entry.identifier}-validacion.md",
                path.name,
                f"{entry.identifier}-cierre.json",
            },
        )
        operations.append({
            "operation": operation,
            "result": result,
            "reference": reference,
            "timestamp": timestamp,
            "evidence": evidence,
        })
    expected_operations = {value.casefold() for value in required_operations}
    if seen_operations != expected_operations or len(operations) != len(required_operations):
        raise ContractError(
            "operaciones de entrega no coinciden exactamente con el alcance requerido: "
            f"esperadas={required_operations}, observadas={[item['operation'] for item in operations]}"
        )
    return {
        "result": "SATISFIED",
        "path": expected_canonical,
        "sha256": sha256(path),
        "requiredOperations": required_operations,
        "operations": operations,
    }


def validation_gate(
    root: Path,
    entry: WorkItemEntry,
    dossier: Path,
    *,
    snapshot_promotions: dict[str, dict] | None = None,
) -> dict:
    path = dossier / f"{entry.identifier}-validacion.md"
    if not path.is_file() or path.is_symlink():
        raise ContractError(f"freeze exige reporte regular {path}")
    primary = dossier / entry.primary
    if not primary.is_file() or primary.is_symlink():
        raise ContractError(f"freeze exige primario regular {primary}")
    primary_meta = parse_frontmatter(primary)
    primary_version = primary_meta.get("document_version")
    if not substantive(primary_version):
        raise ContractError("freeze exige document_version material en el primario")
    meta = parse_frontmatter(path)
    expected_validation_path = path.relative_to(root).as_posix()
    if (
        meta.get("work_item_id") != entry.identifier
        or meta.get("artifact_type") != "VALIDATION_REPORT"
        or meta.get("canonical_path") != expected_validation_path
        or not substantive(meta.get("document_version"))
    ):
        raise ContractError("reporte de validación no acredita ID, tipo, ruta y versión")
    if meta.get("validated_primary_version") != primary_version:
        raise ContractError(
            f"validated_primary_version no coincide con primario: {meta.get('validated_primary_version')!r} / {primary_version!r}"
        )
    primary_digest = sha256(primary)
    if meta.get("validated_primary_sha256") != primary_digest:
        raise ContractError(
            "validated_primary_sha256 no coincide con el contenido actual del primario"
        )
    if meta.get("validation_outcome") != "VERIFIED":
        raise ContractError("freeze exige validation_outcome: VERIFIED")

    criterion_headers = [
        "CA", "Origen", "Resultado esperado", "Método", "Resultado observado",
        "Evidencia local", "Estado",
    ]
    criterion_rows = _section_table(path, "Resultado por criterio", criterion_headers)
    criterion_contracts = _criterion_contracts(primary)
    expected_criteria = [item["id"] for item in criterion_contracts]
    criterion_authority = {item["id"]: item for item in criterion_contracts}
    seen: set[str] = set()
    criteria: list[dict] = []
    forbidden_evidence = {
        entry.primary,
        path.name,
        f"{entry.identifier}-entrega.md",
        f"{entry.identifier}-cierre.json",
    }
    for row in criterion_rows:
        identifier = cell(row, "CA")
        if not CRITERION_ID.fullmatch(identifier):
            raise ContractError(f"validación contiene CA inválido/no canónico: {identifier!r}")
        if identifier in seen:
            raise ContractError(f"validación duplica {identifier}")
        seen.add(identifier)
        origin = cell(row, "Origen")
        expected = cell(row, "Resultado esperado")
        method = cell(row, "Método")
        observed = cell(row, "Resultado observado")
        if not all(substantive(value) for value in (origin, expected, method, observed)):
            raise ContractError(f"{identifier} contiene origen/esperado/método/observado pendiente")
        authority = criterion_authority.get(identifier)
        if authority is None:
            raise ContractError(f"{identifier} no existe en la autoridad primaria")
        if origin != authority["origin"] or expected != authority["expected"]:
            raise ContractError(
                f"{identifier} no coincide con Origen/Resultado esperado de la autoridad primaria"
            )
        state = cell(row, "Estado")
        if state != "CONFORME":
            raise ContractError(f"{identifier} no está CONFORME: {state!r}")
        evidence = _evidence_snapshot(
            dossier, cell(row, "Evidencia local"), label=identifier,
            forbidden=forbidden_evidence,
        )
        criteria.append({
            "id": identifier,
            "origin": origin,
            "expected": expected,
            "method": method,
            "observed": observed,
            "state": state,
            "authoritySha256": authority["authoritySha256"],
            "evidence": evidence,
        })
    if set(seen) != set(expected_criteria) or len(criteria) != len(expected_criteria):
        missing = sorted(set(expected_criteria) - seen)
        extra = sorted(seen - set(expected_criteria))
        raise ContractError(f"cobertura CA no coincide con primario; faltan={missing}, extras={extra}")

    execution_rows = _section_table(
        path, "Ejecuciones verificadas",
        ["Ejecución", "Entorno", "Resultado", "Evidencia local", "Fecha y zona"],
    )
    executions: list[dict] = []
    for number, row in enumerate(execution_rows, start=1):
        execution = cell(row, "Ejecución")
        environment = cell(row, "Entorno")
        result = cell(row, "Resultado")
        timestamp = cell(row, "Fecha y zona")
        if not all(substantive(value) for value in (execution, environment, timestamp)):
            raise ContractError(f"ejecución {number} contiene placeholders")
        if result != "SATISFIED":
            raise ContractError(f"ejecución {number} no está SATISFIED: {result!r}")
        executed_at = parse_timestamp(timestamp, f"fecha de ejecución {number}")
        if executed_at > datetime.now(timezone.utc) + timedelta(minutes=5):
            raise ContractError(f"fecha de ejecución {number} está en el futuro: {timestamp}")
        executions.append({
            "execution": execution,
            "environment": environment,
            "result": result,
            "timestamp": timestamp,
            "evidence": _evidence_snapshot(
                dossier, cell(row, "Evidencia local"), label=f"ejecución {number}",
                forbidden=forbidden_evidence,
            ),
        })

    finding_rows = _section_table(
        path, "Hallazgos de validación",
        ["Hallazgo", "Tipo", "Descripción", "Elementos", "Evidencia local", "Acción", "Bloquea"],
    )
    findings: list[dict] = []
    for number, row in enumerate(finding_rows, start=1):
        finding_id = cell(row, "Hallazgo")
        finding_type = cell(row, "Tipo")
        description = cell(row, "Descripción")
        elements = cell(row, "Elementos")
        action = cell(row, "Acción")
        blocks = cell(row, "Bloquea")
        if not all(substantive(value) for value in (
            finding_id, finding_type, description, elements, action,
        )):
            raise ContractError(f"hallazgo {number} contiene placeholders")
        if blocks != "NO":
            raise ContractError(f"hallazgo {finding_id} bloquea el cierre: {blocks!r}")
        findings.append({
            "id": finding_id,
            "type": finding_type,
            "description": description,
            "elements": elements,
            "action": action,
            "blocks": blocks,
            "evidence": _evidence_snapshot(
                dossier, cell(row, "Evidencia local"), label=f"hallazgo {finding_id}",
                forbidden=forbidden_evidence,
            ),
        })

    promotion_headers = [
        "Destino", "Delta validado", "Resultado", "Ruta durable",
        "Versión / baseline", "Evidencia", "Justificación",
    ]
    promotion_rows = _section_table(
        path, "Promoción de conocimiento durable", promotion_headers,
    )
    if len(promotion_rows) != len(PROMOTION_DESTINATIONS):
        raise ContractError("promoción durable exige exactamente FUNCTIONAL/ARCHITECTURE/OPERATIONS/REFERENCE")
    promotions: dict[str, dict] = {}
    promotion_authority = _promotion_requirements(primary)
    impacts: dict[str, str] = {}
    seen_destinations: set[str] = set()
    dossier_resolved = dossier.resolve()
    for row in promotion_rows:
        destination = cell(row, "Destino")
        if destination not in PROMOTION_DESTINATIONS or destination in seen_destinations:
            raise ContractError(f"destino durable inválido/duplicado: {destination!r}")
        seen_destinations.add(destination)
        key = PROMOTION_DESTINATIONS[destination]
        result = cell(row, "Resultado")
        route = cell(row, "Ruta durable")
        version = cell(row, "Versión / baseline")
        evidence = cell(row, "Evidencia")
        justification = cell(row, "Justificación")
        authority = promotion_authority[destination]
        if result == "INCORPORADO":
            if authority["resolution"] != "INCORPORAR":
                raise ContractError(
                    f"promoción {destination} incorporada contradice autoridad primaria NO_APLICA"
                )
            if cell(row, "Delta validado") != authority["delta"]:
                raise ContractError(
                    f"delta promovido de {destination} no coincide con autoridad primaria"
                )
            if not all(substantive(value) for value in (
                cell(row, "Delta validado"), route, version, evidence,
            )):
                raise ContractError(f"promoción {destination} incorporada carece de delta/ruta/versión/evidencia")
            normalized_route = route.strip("`")
            if not safe_relative(normalized_route):
                raise ContractError(f"promoción {destination} contiene ruta insegura: {route!r}")
            if snapshot_promotions is None:
                target = relative_target(root, normalized_route, label=f"promoción {destination}")
                if target.is_symlink() or not target.is_file():
                    raise ContractError(f"promoción {destination} no apunta a archivo regular: {target}")
                if _is_within(dossier_resolved, target.resolve()):
                    raise ContractError(f"promoción {destination} debe salir del expediente")
                if not _contains_identifier_token(
                    target.read_text(encoding="utf-8", errors="replace"), entry.identifier,
                ):
                    raise ContractError(f"promoción {destination} no traza {entry.identifier}: {route}")
                _promotion_authority_allows(root, destination, normalized_route, target)
                _verify_promoted_version(target, version)
                _validate_destination_promotion(destination, target)
                if destination == "FUNCTIONAL":
                    _functional_promotion(root, entry, normalized_route, version, target)
                digest_at_close = sha256(target)
            else:
                stored = snapshot_promotions.get(key)
                digest_at_close = stored.get("sha256AtClose") if isinstance(stored, dict) else None
                if not isinstance(digest_at_close, str) or not re.fullmatch(r"[0-9a-f]{64}", digest_at_close):
                    raise ContractError(f"snapshot de promoción {destination} no conserva SHA-256 válido")
            evidence_snapshot = _evidence_snapshot(
                dossier, evidence, label=f"promoción {destination}",
                forbidden={
                    entry.primary,
                    path.name,
                    f"{entry.identifier}-entrega.md",
                    f"{entry.identifier}-cierre.json",
                },
            )
            promotion = {
                "result": "INCORPORATED",
                "authority": authority,
                "path": normalized_route,
                "version": version,
                "sha256AtClose": digest_at_close,
                "evidence": evidence_snapshot,
            }
            impacts[key] = "INCORPORATED"
        elif result == "NO_APLICA":
            if authority["resolution"] != "NO_APLICA":
                raise ContractError(
                    f"promoción {destination} NO_APLICA contradice autoridad primaria INCORPORAR"
                )
            if any(present(value) is not None for value in (route, version, evidence)):
                raise ContractError(f"promoción {destination} NO_APLICA no debe declarar ruta/versión/evidencia")
            if not substantive(justification):
                raise ContractError(f"promoción {destination} NO_APLICA exige justificación material")
            promotion = {
                "result": "NOT_APPLICABLE",
                "authority": authority,
                "justification": justification,
            }
            impacts[key] = "NOT_APPLICABLE"
        else:
            raise ContractError(f"promoción {destination} no está resuelta: {result!r}")
        expected_impact = meta.get(f"impact_{key}")
        if expected_impact != impacts[key]:
            raise ContractError(
                f"impact_{key}={expected_impact!r} no coincide con tabla {impacts[key]!r}"
            )
        promotions[key] = promotion
    if seen_destinations != set(PROMOTION_DESTINATIONS):
        raise ContractError("matriz de promoción durable incompleta")

    delivery_value = meta.get("required_delivery_evidence")
    if delivery_value not in {"SATISFIED", "NOT_APPLICABLE"}:
        raise ContractError("freeze exige required_delivery_evidence resuelto")
    required_delivery_rows = _section_table(
        path, "Operaciones de entrega requeridas", ["Operación", "Origen del alcance"],
    )
    authorized_delivery = _required_delivery_operations(primary)
    required_operations: list[str] = []
    required_seen: set[str] = set()
    for number, row in enumerate(required_delivery_rows, start=1):
        operation = cell(row, "Operación")
        origin = cell(row, "Origen del alcance")
        if not substantive(operation) or not substantive(origin):
            raise ContractError(f"operación de entrega requerida {number} contiene placeholders")
        if operation.casefold() in required_seen:
            raise ContractError(f"operación de entrega requerida duplicada: {operation}")
        required_seen.add(operation.casefold())
        required_operations.append(operation)
    observed_delivery = [
        {"operation": cell(row, "Operación"), "origin": cell(row, "Origen del alcance")}
        for row in required_delivery_rows
    ]
    if observed_delivery != authorized_delivery:
        raise ContractError(
            "operaciones de entrega del reporte no coinciden exactamente con la autoridad primaria"
        )
    if delivery_value == "SATISFIED" and not required_operations:
        raise ContractError("delivery SATISFIED exige enumerar operaciones requeridas")
    if delivery_value == "NOT_APPLICABLE" and required_operations:
        raise ContractError("delivery NOT_APPLICABLE no puede enumerar operaciones requeridas")
    delivery_rows = _section_table(
        path, "Decisión de entrega", ["Resultado", "Justificación"],
    )
    if len(delivery_rows) != 1 or cell(delivery_rows[0], "Resultado") != delivery_value:
        raise ContractError("tabla Decisión de entrega no coincide con required_delivery_evidence")
    delivery_justification = cell(delivery_rows[0], "Justificación")
    if not substantive(delivery_justification):
        raise ContractError("Decisión de entrega exige justificación material")
    delivery = (
        _delivery_gate(root, entry, dossier, required_operations)
        if delivery_value == "SATISFIED"
        else {"result": "NOT_APPLICABLE", "justification": delivery_justification}
    )
    return {
        "path": expected_validation_path,
        "sha256": sha256(path),
        "outcome": "VERIFIED",
        "primary": {
            "path": f"{entry.path}/{entry.primary}",
            "version": primary_version,
            "sha256": primary_digest,
        },
        "criteria": criteria,
        "executions": executions,
        "findings": findings,
        "promotions": promotions,
        "impacts": impacts,
        "delivery": delivery,
    }


def _yaml_scalar(value: str) -> str | None:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
        value = value[1:-1]
    if value.lower() in {"null", "none", "~", ""}:
        return None
    return value


def _profile_tracking(root: Path, entry: WorkItemEntry) -> dict[str, str]:
    config = load_contract_config()
    profile = relative_target(root, config["workspace"]["profilePath"], label="perfil")
    if not profile.is_file() or profile.is_symlink():
        raise ContractError(f"readback remoto exige perfil regular: {profile}")
    text = profile.read_text(encoding="utf-8")
    header = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, flags=re.DOTALL)
    if not header:
        raise ContractError("readback remoto exige front matter de perfil válido")
    metadata = header.group(1)

    def scalar(pattern: str, label: str) -> str:
        matches = re.findall(pattern, metadata, flags=re.MULTILINE)
        if len(matches) != 1:
            raise ContractError(f"perfil debe declarar una vez {label}")
        value = _yaml_scalar(matches[0])
        if value is None:
            raise ContractError(f"perfil no configuró {label}")
        return value

    mode = scalar(r"^\s{2}mode:\s*([^#\n]+?)\s*$", "work_tracking.mode")
    credential = scalar(
        r"^\s{2}credential_status:\s*([^#\n]+?)\s*$", "work_tracking.credential_status",
    )
    if mode != "REQUIRED" or credential != "VERIFICADO":
        raise ContractError("freeze exige seguimiento REQUIRED y credenciales VERIFICADO")
    provider = scalar(r"^\s{2}provider:\s*([^#\n]+?)\s*$", "work_tracking.provider")
    if provider != entry.provider:
        raise ContractError(
            f"proveedor del perfil {provider!r} no coincide con catálogo {entry.provider!r}"
        )
    block_name = "jira" if provider == "JIRA" else "azure_devops" if provider == "AZURE_DEVOPS" else ""
    if not block_name:
        raise ContractError(f"proveedor sin readback soportado: {provider}")
    lines = metadata.splitlines()
    starts = [index for index, line in enumerate(lines) if line == f"  {block_name}:"]
    if len(starts) != 1:
        raise ContractError(f"perfil debe declarar bloque {block_name} una vez")
    start = starts[0] + 1
    end = next(
        (
            index for index in range(start, len(lines))
            if lines[index].strip()
            and len(lines[index]) - len(lines[index].lstrip()) <= 2
        ),
        len(lines),
    )
    provider_lines = lines[start:end]

    def provider_scalar(name: str) -> str:
        matches = [
            match.group(1)
            for line in provider_lines
            if (match := re.fullmatch(rf"    {re.escape(name)}:\s*([^#]+?)\s*", line))
        ]
        if len(matches) != 1 or _yaml_scalar(matches[0]) is None:
            raise ContractError(f"perfil no configuró {block_name}.{name}")
        return _yaml_scalar(matches[0]) or ""

    def mapping_value(mapping_name: str) -> str:
        indexes = [
            index for index, line in enumerate(provider_lines)
            if line == f"    {mapping_name}:"
        ]
        if len(indexes) != 1:
            raise ContractError(f"perfil no declara una vez {block_name}.{mapping_name}")
        mapping_start = indexes[0] + 1
        mapping_end = next(
            (
                index for index in range(mapping_start, len(provider_lines))
                if provider_lines[index].strip()
                and len(provider_lines[index]) - len(provider_lines[index].lstrip()) <= 4
            ),
            len(provider_lines),
        )
        prefix = f"      {entry.kind}:"
        values = [line[len(prefix):].strip() for line in provider_lines[mapping_start:mapping_end] if line.startswith(prefix)]
        if len(values) != 1:
            raise ContractError(f"perfil no mapea {mapping_name}.{entry.kind}")
        value = _yaml_scalar(values[0])
        if value is None:
            raise ContractError(f"perfil no configuró {mapping_name}.{entry.kind}")
        return value

    remote_type = mapping_value("type_mapping")
    workflow = mapping_value("workflow_mapping_by_kind")
    done_match = re.search(r"(?:^|[,{]\s*)DONE:\s*([^,}]+)", workflow)
    done_state = _yaml_scalar(done_match.group(1)) if done_match else None
    if done_state is None:
        raise ContractError(f"perfil no configuró estado DONE para {entry.kind}")
    result = {
        "provider": provider,
        "remoteType": remote_type,
        "doneState": done_state,
    }
    if provider == "JIRA":
        result["baseUrl"] = provider_scalar("base_url")
        result["project"] = provider_scalar("project_key")
    else:
        result["organizationUrl"] = provider_scalar("organization_url")
        result["project"] = provider_scalar("project")
    return result


class _NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[no-untyped-def]
        return None


def _http_get_json(url: str, authorization: str, *, timeout: float = 15.0) -> tuple[bytes, dict]:
    parsed = urlparse(url)
    if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
        raise ContractError("readback remoto sólo permite endpoint HTTPS sin credenciales en URL")
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "Authorization": authorization,
            "User-Agent": "FARO/2.0 provider-readback",
        },
        method="GET",
    )
    try:
        with build_opener(_NoRedirect).open(request, timeout=timeout) as response:
            status = response.getcode()
            raw = response.read(2_000_001)
    except HTTPError as error:
        raise ContractError(f"readback remoto respondió HTTP {error.code}") from error
    except (URLError, TimeoutError, OSError) as error:
        raise ContractError(f"readback remoto falló: {type(error).__name__}") from error
    if status != 200:
        raise ContractError(f"readback remoto respondió HTTP {status}")
    if len(raw) > 2_000_000:
        raise ContractError("readback remoto excede 2 MB")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("readback remoto no devolvió JSON UTF-8 válido") from error
    if not isinstance(payload, dict):
        raise ContractError("readback remoto debe devolver un objeto JSON")
    return raw, payload


def _derive_remote_observation(
    provider: str, payload: dict, external_id: str,
) -> tuple[str, str, str]:
    if provider == "JIRA":
        fields = payload.get("fields")
        if not isinstance(fields, dict) or str(payload.get("key", "")).casefold() != external_id.casefold():
            raise ContractError("readback Jira no corresponde a la issue catalogada")
        issue_type = fields.get("issuetype")
        status = fields.get("status")
        project = fields.get("project")
        if not isinstance(issue_type, dict) or not isinstance(status, dict) or not isinstance(project, dict):
            raise ContractError("readback Jira no contiene issuetype/status/project")
        category = status.get("statusCategory")
        category_key = category.get("key") if isinstance(category, dict) else None
        if category_key != "done":
            raise ContractError(f"readback Jira no confirmó categoría DONE: {category_key!r}")
        remote_type = issue_type.get("name")
        observed_state = status.get("name")
        remote_project = project.get("key")
    elif provider == "AZURE_DEVOPS":
        if str(payload.get("id", "")) != external_id:
            raise ContractError("readback Azure DevOps no corresponde al item catalogado")
        fields = payload.get("fields")
        if not isinstance(fields, dict):
            raise ContractError("readback Azure DevOps no contiene fields")
        remote_type = fields.get("System.WorkItemType")
        observed_state = fields.get("System.State")
        remote_project = fields.get("System.TeamProject")
    else:
        raise ContractError(f"proveedor sin readback soportado: {provider}")
    if not all(isinstance(value, str) and value for value in (
        remote_type, observed_state, remote_project,
    )):
        raise ContractError("readback remoto no devolvió tipo/estado/proyecto textuales")
    return remote_type, observed_state, remote_project


def _validate_remote_readback_snapshot(
    root: Path, entry: WorkItemEntry, readback: object,
) -> datetime:
    expected_fields = {
        "provider", "externalId", "externalUrl", "remoteType", "observedState", "remoteProject",
        "mappedRemoteType", "mappedDoneState", "mappedProject", "canonicalState", "observedAt",
        "requestUrl", "responseSha256", "responseBodyBase64",
    }
    if not isinstance(readback, dict) or set(readback) != expected_fields:
        raise ContractError("readback remoto tiene esquema incompleto")
    if (
        readback.get("provider") != entry.provider
        or readback.get("externalId") != entry.external_id
        or readback.get("externalUrl") != entry.external_url
        or readback.get("canonicalState") != "DONE"
    ):
        raise ContractError("readback remoto no coincide con la referencia catalogada")
    external_url = validated_external_url(str(readback.get("externalUrl", "")))
    external_id = str(readback.get("externalId", ""))
    provider = str(readback.get("provider"))
    _validate_provider_item_url(provider, external_url, external_id)
    try:
        raw = base64.b64decode(str(readback.get("responseBodyBase64", "")), validate=True)
    except (ValueError, binascii.Error) as error:
        raise ContractError("readback remoto no conserva una respuesta base64 válida") from error
    if not raw or len(raw) > 2_000_000:
        raise ContractError("respuesta conservada de readback está vacía o excede 2 MB")
    digest = hashlib.sha256(raw).hexdigest()
    if readback.get("responseSha256") != digest:
        raise ContractError("hash de respuesta remota no coincide con el body conservado")
    try:
        payload = json.loads(raw.decode("utf-8"))
    except (UnicodeError, json.JSONDecodeError) as error:
        raise ContractError("body conservado de readback no es JSON UTF-8 válido") from error
    if not isinstance(payload, dict):
        raise ContractError("body conservado de readback debe ser un objeto JSON")
    remote_type, observed_state, remote_project = _derive_remote_observation(
        provider, payload, external_id,
    )
    tracking = _profile_tracking(root, entry)
    if (
        readback.get("remoteType") != remote_type
        or readback.get("observedState") != observed_state
        or readback.get("remoteProject") != remote_project
        or readback.get("mappedRemoteType") != tracking["remoteType"]
        or readback.get("mappedDoneState") != tracking["doneState"]
        or readback.get("mappedProject") != tracking["project"]
        or remote_type != tracking["remoteType"]
        or observed_state != tracking["doneState"]
        or remote_project.casefold() != tracking["project"].casefold()
    ):
        raise ContractError("tipo/estado/proyecto derivados no coinciden con perfil y respuesta remota")
    request_url = validated_external_url(str(readback.get("requestUrl", "")))
    request_parsed = urlparse(request_url)
    external_parsed = urlparse(external_url)
    request_origin = (
        request_parsed.scheme.lower(), (request_parsed.hostname or "").casefold(),
        request_parsed.port or (443 if request_parsed.scheme == "https" else 80),
    )
    external_origin = (
        external_parsed.scheme.lower(), (external_parsed.hostname or "").casefold(),
        external_parsed.port or (443 if external_parsed.scheme == "https" else 80),
    )
    if request_origin[0] != "https":
        raise ContractError("requestUrl del readback debe usar HTTPS")
    if provider == "AZURE_DEVOPS":
        if _azure_org_identity(request_url, "requestUrl") != _azure_org_identity(
            external_url, "URL externa Azure DevOps",
        ):
            raise ContractError("requestUrl no pertenece a la organización Azure catalogada")
    elif request_origin != external_origin:
        raise ContractError("requestUrl del readback no pertenece al servicio catalogado")
    _validate_provider_item_url(provider, request_url, external_id)
    return parse_timestamp(str(readback.get("observedAt", "")), "observedAt")


def perform_provider_readback(root: Path, entry: WorkItemEntry) -> dict:
    root = workspace_root(root)
    if not all((entry.provider, entry.external_id, entry.external_url)):
        raise ContractError("readback remoto exige referencia externa completa")
    tracking = _profile_tracking(root, entry)
    external_url = validated_external_url(entry.external_url or "")
    external_id = entry.external_id or ""

    provider = tracking["provider"]
    canonical_remote_id(provider, external_id)
    _validate_provider_item_url(provider, external_url, external_id)
    if provider == "JIRA":
        email = os.environ.get("JIRA_EMAIL", "").strip()
        token = os.environ.get("JIRA_API_TOKEN", "").strip()
        authorized_base = os.environ.get("JIRA_BASE_URL", "").strip()
        if not email or not token or not authorized_base:
            raise ContractError(
                "readback Jira exige JIRA_BASE_URL, JIRA_EMAIL y JIRA_API_TOKEN fuera del workspace"
            )
        profile_base = tracking["baseUrl"]
        if _service_root(authorized_base, "JIRA_BASE_URL") != _service_root(profile_base, "jira.base_url"):
            raise ContractError("JIRA_BASE_URL autorizado no coincide exactamente con jira.base_url del perfil")
        base_url = authorized_base.rstrip("/")
        _url_belongs_to_service(external_url, base_url, "servicio Jira autorizado")
        if external_id.split("-", 1)[0] != tracking["project"]:
            raise ContractError("clave Jira no pertenece al project_key configurado")
        endpoint = (
            f"{base_url}/rest/api/3/issue/{quote(external_id, safe='')}?"
            + urlencode({"fields": "issuetype,status,project"})
        )
        encoded = base64.b64encode(f"{email}:{token}".encode("utf-8")).decode("ascii")
        raw, payload = _http_get_json(endpoint, f"Basic {encoded}")
    else:
        pat = os.environ.get("AZDO_PAT", "").strip()
        authorized_organization = os.environ.get("AZDO_ORGANIZATION_URL", "").strip()
        if not pat or not authorized_organization:
            raise ContractError(
                "readback Azure DevOps exige AZDO_ORGANIZATION_URL y AZDO_PAT fuera del workspace"
            )
        profile_organization = tracking["organizationUrl"]
        if _azure_org_identity(
            authorized_organization, "AZDO_ORGANIZATION_URL",
        ) != _azure_org_identity(profile_organization, "azure_devops.organization_url"):
            raise ContractError(
                "AZDO_ORGANIZATION_URL autorizado no coincide con la organización del perfil"
            )
        organization = authorized_organization.rstrip("/")
        if _azure_org_identity(external_url, "URL remota Azure DevOps") != _azure_org_identity(
            organization, "organización Azure DevOps autorizada",
        ):
            raise ContractError("URL remota Azure DevOps no pertenece a la organización autorizada")
        if _azure_project_from_item_url(external_url).casefold() != tracking["project"].casefold():
            raise ContractError("URL remota Azure DevOps no contiene el proyecto en posición canónica")
        project = quote(tracking["project"], safe="")
        endpoint = (
            f"{organization}/{project}/_apis/wit/workitems/{quote(external_id, safe='')}?"
            + urlencode({
                "fields": "System.WorkItemType,System.State,System.TeamProject",
                "api-version": "7.1",
            })
        )
        encoded = base64.b64encode(f":{pat}".encode("utf-8")).decode("ascii")
        raw, payload = _http_get_json(endpoint, f"Basic {encoded}")
    remote_type, observed_state, remote_project = _derive_remote_observation(
        provider, payload, external_id,
    )
    if remote_type != tracking["remoteType"]:
        raise ContractError(
            f"tipo remoto {remote_type!r} no coincide con mapeo {tracking['remoteType']!r}"
        )
    if observed_state != tracking["doneState"]:
        raise ContractError(
            f"estado remoto {observed_state!r} no coincide con DONE mapeado {tracking['doneState']!r}"
        )
    if remote_project.casefold() != tracking["project"].casefold():
        raise ContractError(
            f"proyecto remoto {remote_project!r} no coincide con {tracking['project']!r}"
        )
    return {
        "provider": provider,
        "externalId": external_id,
        "externalUrl": external_url,
        "remoteType": remote_type,
        "observedState": observed_state,
        "remoteProject": remote_project,
        "mappedRemoteType": tracking["remoteType"],
        "mappedDoneState": tracking["doneState"],
        "mappedProject": tracking["project"],
        "canonicalState": "DONE",
        "observedAt": utc_now(),
        "requestUrl": endpoint,
        "responseSha256": hashlib.sha256(raw).hexdigest(),
        "responseBodyBase64": base64.b64encode(raw).decode("ascii"),
    }


def _validate_gate_snapshot(root: Path, entry: WorkItemEntry, dossier: Path, gate: object) -> None:
    if not isinstance(gate, dict) or set(gate) != {
        "path", "sha256", "outcome", "primary", "criteria", "executions", "findings",
        "promotions", "impacts", "delivery",
    }:
        raise ContractError("snapshot de validationGate tiene esquema inválido")
    promotions = gate.get("promotions")
    if not isinstance(promotions, dict) or set(promotions) != set(PROMOTION_DESTINATIONS.values()):
        raise ContractError("snapshot de promociones incompleto")
    expected = validation_gate(
        root, entry, dossier, snapshot_promotions=promotions,
    )
    if gate != expected:
        raise ContractError(
            "validationGate no coincide exactamente con primario, validación, CA, evidencia, "
            "promociones y entrega congelados"
        )


def validate_closure(root: Path, entry: WorkItemEntry, dossier: Path, issues: list[Issue]) -> None:
    identifier = entry.identifier
    closure = dossier / f"{identifier}-cierre.json"
    if not closure.exists():
        return
    if not closure.is_file() or closure.is_symlink():
        issues.append(Issue("error", "closure-invalid", f"cierre inválido: {closure}"))
        return
    try:
        payload = load_json(closure)
        files = dossier_files(dossier, closure.name)
    except ContractError as error:
        issues.append(Issue("error", "closure-invalid", str(error)))
        return
    expected_payload_fields = {
        "schemaVersion", "workItemId", "reservationSource", "frozenAt",
        "externalReference", "remoteReadback", "validationGate", "hashAlgorithm", "artifacts",
    }
    if (
        set(payload) != expected_payload_fields
        or payload.get("schemaVersion") != 3
        or payload.get("workItemId") != identifier
        or payload.get("hashAlgorithm") != "sha256"
    ):
        issues.append(Issue("error", "closure-invalid", f"metadatos de cierre no coinciden: {closure}"))
        return
    if payload.get("reservationSource") != entry.reservation_source:
        issues.append(Issue(
            "error", "closure-reservation-source",
            f"fuente de reserva congelada no coincide con catálogo: {closure}",
        ))
    try:
        frozen_at = parse_timestamp(payload.get("frozenAt"), "frozenAt")
    except ContractError as error:
        issues.append(Issue("error", "closure-invalid", str(error)))
        frozen_at = None
    external = payload.get("externalReference")
    expected_external = {"provider": entry.provider, "id": entry.external_id, "url": entry.external_url}
    if external != expected_external or not all(isinstance(value, str) and value for value in expected_external.values()):
        issues.append(Issue("error", "closure-external-reference", f"referencia externa de cierre no coincide con catálogo: {closure}"))
    readback = payload.get("remoteReadback")
    try:
        readback_at = _validate_remote_readback_snapshot(root, entry, readback)
        if frozen_at is not None and frozen_at < readback_at:
            issues.append(Issue("error", "closure-order", "frozenAt no puede preceder al readback remoto"))
    except ContractError as error:
        issues.append(Issue("error", "closure-readback", str(error)))
    try:
        _validate_gate_snapshot(root, entry, dossier, payload.get("validationGate"))
    except (ContractError, OSError) as error:
        issues.append(Issue("error", "closure-validation-gate", str(error)))
    expected = payload.get("artifacts")
    if not isinstance(expected, dict) or not all(
        isinstance(key, str) and safe_relative(key)
        and isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value)
        for key, value in expected.items()
    ):
        issues.append(Issue("error", "closure-invalid", f"mapa de hashes inválido: {closure}"))
        return
    if set(expected) != set(files):
        missing = sorted(set(expected) - set(files))
        added = sorted(set(files) - set(expected))
        issues.append(Issue("error", "frozen-dossier-mutated", f"{identifier} cambió inventario; faltan={missing}, agregados={added}"))
        return
    changed = [relative for relative, path in files.items() if sha256(path) != expected[relative]]
    if changed:
        issues.append(Issue("error", "frozen-dossier-mutated", f"{identifier} fue modificado: {', '.join(changed)}"))


def legacy_inventory(root: Path, config: dict) -> tuple[list[str], list[str], list[str]]:
    try:
        requirements = relative_target(root, config["workspace"]["requirementsRoot"], label="requirements root")
    except ContractError:
        return [], [], []
    if not requirements.is_dir() or requirements.is_symlink():
        return [], [], []
    work: list[str] = []
    functional: list[str] = []
    invalid: list[str] = []
    for path in sorted(requirements.iterdir()):
        relative = path.relative_to(root).as_posix()
        visible_name = path.name.lstrip(".")
        if path.name.startswith(".") and RESERVED_LEGACY_PREFIX.match(visible_name):
            invalid.append(relative)
        elif LEGACY_WORK_FILE.fullmatch(path.name):
            work.append(relative)
        elif LEGACY_DF_FILE.fullmatch(path.name):
            functional.append(relative)
        elif RESERVED_LEGACY_PREFIX.match(path.name):
            invalid.append(relative)
    return work, functional, invalid


def validate_profile(root: Path, config: dict, issues: list[Issue]) -> None:
    try:
        profile = relative_target(root, config["workspace"]["profilePath"], label="perfil")
    except ContractError as error:
        issues.append(Issue("error", "profile-path-invalid", str(error)))
        return
    if not profile.exists():
        issues.append(Issue("error", "profile-missing", f"perfil obligatorio ausente: {profile}"))
        return
    if not profile.is_file() or profile.is_symlink():
        issues.append(Issue("error", "profile-invalid", f"perfil no es archivo regular: {profile}"))
        return
    text = profile.read_text(encoding="utf-8", errors="replace")
    header = re.match(r"\A---\n(.*?)\n---(?:\n|\Z)", text, flags=re.DOTALL)
    if not header:
        issues.append(Issue("error", "profile-v2-missing", f"perfil sin front matter delimitado: {profile}"))
        return
    metadata = header.group(1)
    expected_counts = {
        r"^work_tracking:\s*$": (1, "bloque work_tracking"),
        r"^\s{2}mode:\s*[^\s#]+\s*$": (1, "work_tracking.mode"),
        r"^\s{2}provider:\s*[^\s#]+\s*$": (1, "work_tracking.provider"),
        r"^profile_version:\s*2\s*$": (1, "profile_version 2"),
        r"^\s{2}operational_state_authority:\s*EXTERNAL_WORK_TRACKER\s*$": (1, "autoridad externa de estado"),
        r"^\s{2}work_items_require_external_reference:\s*true\s*$": (1, "referencia externa obligatoria"),
        r"^\s{2}jira:\s*$": (1, "bloque Jira"),
        r"^\s{2}azure_devops:\s*$": (1, "bloque Azure DevOps"),
        r"^\s{4}type_mapping:\s*$": (2, "mapeos de tipo Jira/Azure"),
        r"^\s{4}workflow_mapping_by_kind:\s*$": (2, "mapeos de workflow Jira/Azure"),
        r"^durable_documentation:\s*$": (1, "autoridades documentales duraderas"),
    }
    for pattern, (expected, label) in expected_counts.items():
        count = len(re.findall(pattern, metadata, flags=re.MULTILINE))
        if count != expected:
            issues.append(Issue("error", "profile-v2-missing", f"perfil requiere {label} exactamente {expected} vez/veces; encontradas {count}"))
    mode_match = re.search(r"^\s{2}mode:\s*([^\s#]+)", metadata, flags=re.MULTILINE)
    provider_match = re.search(r"^\s{2}provider:\s*([^\s#]+)", metadata, flags=re.MULTILINE)
    mode = mode_match.group(1) if mode_match else None
    provider = provider_match.group(1) if provider_match else None
    allowed_modes = set(config.get("initialization", {}).get("workTrackingModes", [])) | {"PENDIENTE"}
    if mode not in allowed_modes:
        issues.append(Issue("error", "profile-work-tracking", f"work_tracking.mode inválido: {mode!r}"))
    null_values = {"null", "~", "NULL", "None"}
    if mode == "REQUIRED" and provider not in allowed_providers(config):
        issues.append(Issue("error", "profile-work-tracking", f"REQUIRED exige proveedor permitido: {provider!r}"))
    if mode == "OFF" and provider not in null_values:
        issues.append(Issue("error", "profile-work-tracking", "OFF exige provider: null"))
    lines = metadata.splitlines()
    expected_kinds = {"RM", "BUG", "TEC", "INC", "TASK"}
    for provider_name in ("jira", "azure_devops"):
        provider_indexes = [
            index for index, line in enumerate(lines)
            if re.fullmatch(rf"  {provider_name}:\s*", line)
        ]
        if len(provider_indexes) != 1:
            continue
        start = provider_indexes[0] + 1
        end = next(
            (
                index for index in range(start, len(lines))
                if lines[index].strip() and len(lines[index]) - len(lines[index].lstrip()) <= 2
            ),
            len(lines),
        )
        provider_lines = lines[start:end]
        for mapping_name in ("type_mapping", "workflow_mapping_by_kind"):
            mapping_indexes = [
                index for index, line in enumerate(provider_lines)
                if re.fullmatch(rf"    {mapping_name}:\s*", line)
            ]
            if len(mapping_indexes) != 1:
                issues.append(Issue(
                    "error", "profile-kind-mapping",
                    f"{provider_name} requiere exactamente un bloque {mapping_name}",
                ))
                continue
            mapping_start = mapping_indexes[0] + 1
            mapping_end = next(
                (
                    index for index in range(mapping_start, len(provider_lines))
                    if provider_lines[index].strip()
                    and len(provider_lines[index]) - len(provider_lines[index].lstrip()) <= 4
                ),
                len(provider_lines),
            )
            mapped = [
                match.group(1)
                for line in provider_lines[mapping_start:mapping_end]
                if (match := re.match(r"^      ([A-Za-z][A-Za-z0-9_-]*):", line))
            ]
            if len(mapped) != len(set(mapped)) or set(mapped) != expected_kinds:
                issues.append(Issue(
                    "error", "profile-kind-mapping",
                    f"{provider_name}.{mapping_name} debe declarar una vez RM/BUG/TEC/INC/TASK",
                ))


def validate_workflow_v2(root: Path, config: dict, report: ValidationReport) -> None:
    try:
        path = relative_target(root, config["workspace"]["workflowPath"], label="workflow")
    except ContractError as error:
        report.issues.append(Issue("error", "workflow-path-invalid", str(error)))
        return
    if not path.exists():
        return
    if not path.is_file() or path.is_symlink():
        report.issues.append(Issue("error", "workflow-invalid", f"workflow no es archivo regular: {path}"))
        return
    try:
        workflow = load_json(path)
    except ContractError as error:
        report.issues.append(Issue("error", "workflow-invalid", str(error)))
        return
    expected = {"schemaVersion", "updatedAt", "phase", "authorization", "workItemRef", "waitingOn", "nextRoute", "checkpoint", "notes"}
    forbidden = {
        "active", "currentUnit", "status", "state", "estado", "priority", "prioridad",
        "assignedTo", "assigned", "assignee", "owner", "responsible", "responsable",
        "asignado", "backlog", "queue", "cola", "rank", "position", "posicion",
        "order", "orden", "completedUnits", "todo", "doing", "done", "dropped",
        "sprint", "iteration", "iteracion", "area",
    }
    missing = expected - workflow.keys()
    extra = set(workflow) - expected
    if missing:
        report.issues.append(Issue("error", "workflow-fields-missing", f"workflow v2 sin campos: {', '.join(sorted(missing))}"))
    if extra:
        report.issues.append(Issue("error", "workflow-fields-extra", f"workflow v2 contiene campos no permitidos: {', '.join(sorted(extra))}"))
    if set(workflow) & forbidden:
        report.issues.append(Issue("error", "workflow-operational-state", "workflow duplica estado/backlog operativo"))
    if workflow.get("schemaVersion") != 2:
        report.issues.append(Issue("error", "workflow-schema", "workflow v2 debe declarar schemaVersion 2"))
    try:
        parse_timestamp(workflow.get("updatedAt"), "workflow.updatedAt")
    except ContractError as error:
        report.issues.append(Issue("error", "workflow-updated-at", str(error)))
    phase = workflow.get("phase")
    if phase is not None and (not isinstance(phase, str) or not phase.strip()):
        report.issues.append(Issue("error", "workflow-phase", "phase debe ser null o texto no vacío"))
    reference = workflow.get("workItemRef")
    if reference is not None:
        if not isinstance(reference, dict) or set(reference) != {"id", "path"}:
            report.issues.append(Issue("error", "workflow-reference", "workItemRef debe ser null o {id,path}"))
        else:
            identifier = reference.get("id")
            path_value = reference.get("path")
            if isinstance(identifier, str) and INCIDENT_ID.fullmatch(identifier):
                match = INCIDENT_PATH.fullmatch(path_value) if isinstance(path_value, str) else None
                if match is None or match.group(1) != identifier:
                    report.issues.append(Issue(
                        "error", "workflow-reference",
                        "workItemRef INC debe usar context/incidents/INC-NNNN-<slug>.md canónico",
                    ))
                else:
                    try:
                        incident = relative_target(root, path_value, label="expediente INC de workflow")
                    except ContractError as error:
                        report.issues.append(Issue("error", "workflow-reference", str(error)))
                    else:
                        if incident.is_symlink() or not incident.is_file():
                            report.issues.append(Issue(
                                "error", "workflow-reference",
                                f"expediente INC ausente, no regular o symlink: {incident}",
                            ))
                        else:
                            try:
                                heading = next(
                                    (line for line in incident.read_text(
                                        encoding="utf-8", errors="replace",
                                    ).splitlines() if line.startswith("# ")),
                                    "",
                                )
                            except OSError as error:
                                report.issues.append(Issue(
                                    "error", "workflow-reference",
                                    f"no se pudo leer expediente INC {incident}: {error}",
                                ))
                            else:
                                heading_match = re.match(r"#\s+(INC-[0-9]{4})(?:\s|—|-)", heading)
                                if heading_match is None or heading_match.group(1) != identifier:
                                    report.issues.append(Issue(
                                        "error", "workflow-reference",
                                        f"encabezado principal de {incident} no coincide con {identifier}",
                                    ))

                    try:
                        registry = relative_target(
                            root, "context/incidents/README.md", label="registro de incidentes",
                        )
                        _headers, incident_rows = _table(registry, "Registros")
                    except (ContractError, OSError, UnicodeError) as error:
                        report.issues.append(Issue(
                            "error", "workflow-reference",
                            f"no se pudo comprobar el registro de {identifier}: {error}",
                        ))
                    else:
                        registered = [row for row in incident_rows if cell(row, "ID") == identifier]
                        if len(registered) != 1:
                            report.issues.append(Issue(
                                "error", "workflow-reference",
                                f"el registro de incidentes debe contener exactamente una fila para {identifier}",
                            ))
                        elif cell(registered[0], "Expediente estable", "Registro") != path_value:
                            report.issues.append(Issue(
                                "error", "workflow-reference",
                                f"workItemRef de {identifier} no coincide con el registro de incidentes",
                            ))
            else:
                entry = report.work_items.get(identifier) if isinstance(identifier, str) else None
                if entry is None or path_value != entry.path:
                    report.issues.append(Issue(
                        "error", "workflow-reference",
                        "workItemRef no coincide con catálogo RM/BUG/TEC ni con un INC registrado",
                    ))
    authorization = workflow.get("authorization")
    if not isinstance(authorization, dict):
        report.issues.append(Issue("error", "workflow-authorization", "authorization debe ser un objeto"))
    else:
        expected_authorization = {"status", "source", "artifactVersion", "scope"}
        if set(authorization) != expected_authorization:
            report.issues.append(Issue("error", "workflow-authorization", "authorization debe contener exactamente status/source/artifactVersion/scope"))
        if not isinstance(authorization.get("status"), str) or not authorization.get("status", "").strip():
            report.issues.append(Issue("error", "workflow-authorization", "authorization.status debe ser texto no vacío"))
        for field_name in ("source", "artifactVersion", "scope"):
            value = authorization.get(field_name)
            if value is not None and not isinstance(value, str):
                report.issues.append(Issue("error", "workflow-authorization", f"authorization.{field_name} debe ser texto o null"))
    if not isinstance(workflow.get("notes"), list) or not all(isinstance(note, str) for note in workflow.get("notes", [])):
        report.issues.append(Issue("error", "workflow-notes", "notes debe ser lista de textos"))
    checkpoint = workflow.get("checkpoint")
    if checkpoint is not None and not isinstance(checkpoint, (str, dict)):
        report.issues.append(Issue("error", "workflow-checkpoint", "checkpoint debe ser null, texto u objeto"))
    waiting_on = workflow.get("waitingOn")
    if waiting_on is not None and not isinstance(waiting_on, (str, dict)):
        report.issues.append(Issue("error", "workflow-waiting-on", "waitingOn debe ser null, texto u objeto"))
    next_route = workflow.get("nextRoute")
    if next_route is not None and (not isinstance(next_route, str) or not next_route.strip()):
        report.issues.append(Issue("error", "workflow-next-route", "nextRoute debe ser null o texto no vacío"))
    forbidden_normalized = {normalize_machine_key(item) for item in forbidden}

    def forbidden_nested(value: object) -> bool:
        if isinstance(value, dict):
            return any(
                normalize_machine_key(str(key)) in forbidden_normalized or forbidden_nested(child)
                for key, child in value.items()
            )
        if isinstance(value, list):
            return any(forbidden_nested(child) for child in value)
        return False

    if forbidden_nested(checkpoint) or forbidden_nested(waiting_on) or forbidden_nested(workflow.get("notes")):
        report.issues.append(Issue("error", "workflow-operational-state", "checkpoint/waitingOn/notes contiene estado operativo"))


def _catalog_path(root: Path, value: str, issues: list[Issue]) -> Path:
    try:
        path = relative_target(root, value, label="catálogo")
    except ContractError as error:
        issues.append(Issue("error", "catalog-path-invalid", str(error)))
        return root / "__invalid_catalog__"
    if path.is_symlink():
        issues.append(Issue("error", "catalog-symlink", f"catálogo no puede ser symlink: {path}"))
    return path


def validate_layout(
    root: Path,
    config: dict | None = None,
    *,
    pending_registration: str | None = None,
) -> ValidationReport:
    root = workspace_root(root)
    config = config or load_contract_config()
    issues: list[Issue] = []
    report = ValidationReport(config["contractVersion"], "empty", issues=issues)
    workspace = config["workspace"]
    work_pattern = re.compile(config["workItems"]["idPattern"], re.IGNORECASE)
    df_pattern = re.compile(config["functionalDocuments"]["idPattern"], re.IGNORECASE)
    exceptions = _legacy_exceptions(root, config, issues)

    try:
        work_root = relative_target(root, workspace["workItemsRoot"], label="work-items root")
    except ContractError as error:
        issues.append(Issue("error", "work-items-root-invalid", str(error)))
        work_root = root / "__invalid_work_items__"
    catalog = _catalog_path(root, workspace["requirementsCatalogPath"], issues)
    entry_headers, rows = _safe_table(catalog, "Expedientes", issues)
    reservation_headers, reservation_rows = _safe_table(catalog, "Reservas", issues)
    try:
        _require_headers(entry_headers, WORK_ENTRY_HEADERS, catalog, "Expedientes")
        _require_headers(reservation_headers, WORK_RESERVATION_HEADERS, catalog, "Reservas")
        _assert_catalog_integrity(config, rows, reservation_rows, functional=False)
    except ContractError as error:
        issues.append(Issue("error", "catalog-integrity", str(error)))
    forbidden = {normalize_header(value) for value in config["workItems"].get("catalogMustNotContain", [])}
    found = {normalize_header(value) for value in entry_headers} & forbidden
    if found:
        issues.append(Issue("error", "catalog-operational-state", f"catálogo contiene columnas operativas: {', '.join(sorted(found))}"))
    entries: dict[str, WorkItemEntry] = {}
    seen: dict[str, str] = {}
    for row in rows:
        identifier = cell(row, "ID")
        canonical = identifier.upper()
        kind = cell(row, "Tipo")
        path_value = cell(row, "Ruta canónica")
        primary_value = cell(row, "Documento principal")
        if not work_pattern.fullmatch(identifier):
            issues.append(Issue("error", "work-item-id-invalid", f"ID inválido: {identifier!r}"))
            continue
        if identifier != canonical:
            issues.append(Issue("error", "work-item-id-case", f"ID debe usar mayúsculas: {identifier}"))
        if canonical.casefold() in seen:
            issues.append(Issue("error", "work-item-id-collision", f"ID duplicado: {seen[canonical.casefold()]} / {identifier}"))
            continue
        seen[canonical.casefold()] = identifier
        expected_kind = canonical.split("-", 1)[0]
        if kind != expected_kind:
            issues.append(Issue("error", "work-item-kind-mismatch", f"{identifier}: tipo {kind!r}, esperado {expected_kind}"))
        expected_path = f"{workspace['workItemsRoot']}/{canonical}"
        if path_value != expected_path or not safe_relative(path_value):
            issues.append(Issue("error", "work-item-path-invalid", f"ruta de {identifier} debe ser {expected_path}"))
        provider = present(cell(row, "Proveedor"))
        external_id = present(cell(row, "ID remoto"))
        external_url = present(cell(row, "URL remota"))
        remote_count = sum(value is not None for value in (provider, external_id, external_url))
        if remote_count not in {0, 3}:
            issues.append(Issue("error", "external-reference-partial", f"referencia remota incompleta: {identifier}"))
        elif remote_count == 0:
            issues.append(Issue("warning", "external-reference-missing", f"{identifier} no puede cerrarse sin referencia remota"))
        entries[canonical] = WorkItemEntry(
            identifier=canonical,
            kind=expected_kind,
            path=path_value,
            primary=primary_value,
            reservation_source=cell(row, "Fuente de reserva serializada"),
            provider=provider,
            external_id=external_id,
            external_url=external_url,
            related=present(cell(row, "Relacionados")),
        )
    for row in reservation_rows:
        identifier = cell(row, "ID")
        kind = cell(row, "Tipo")
        if not work_pattern.fullmatch(identifier) or identifier != identifier.upper():
            issues.append(Issue("error", "reservation-id-invalid", f"reserva inválida: {identifier!r}"))
            continue
        if kind != identifier.split("-", 1)[0]:
            issues.append(Issue("error", "reservation-kind-mismatch", f"reserva {identifier} tiene tipo {kind!r}"))
        folded = identifier.casefold()
        if folded in seen:
            published = entries.get(identifier)
            if not (
                published is not None
                and published.kind == kind
                and published.reservation_source == cell(row, "Fuente de reserva serializada")
            ):
                issues.append(Issue("error", "reservation-collision", f"ID reservado/publicado duplicado: {identifier}"))
        else:
            seen[folded] = identifier

    directories: dict[str, Path] = {}
    if not work_root.exists():
        issues.append(Issue("error", "work-items-root-missing", f"work-items root obligatorio ausente: {work_root}"))
    elif not work_root.is_dir() or work_root.is_symlink():
        issues.append(Issue("error", "work-items-root-invalid", f"work-items no es directorio regular: {work_root}"))
    elif work_root.is_dir():
        directory_names: dict[str, str] = {}
        for child in sorted(work_root.iterdir(), key=lambda item: item.name.casefold()):
            if child.name.startswith("."):
                if (
                    re.fullmatch(r"\.(?:RM|BUG|TEC)-[0-9]{4}\.lock", child.name)
                    and child.is_file()
                    and not child.is_symlink()
                ):
                    continue
                issues.append(Issue("error", "work-item-hidden-entry", f"entrada oculta no permitida: {child}"))
                continue
            folded = child.name.casefold()
            if folded in directory_names:
                issues.append(Issue("error", "work-item-directory-collision", f"{directory_names[folded]} / {child.name}"))
                continue
            directory_names[folded] = child.name
            if child.is_symlink() or not child.is_dir():
                issues.append(Issue("error", "work-item-entry-invalid", f"entrada inválida: {child}"))
                continue
            canonical = child.name.upper()
            if not work_pattern.fullmatch(child.name):
                issues.append(Issue("error", "work-item-directory-invalid", f"directorio inválido: {child.name}"))
                continue
            if child.name != canonical:
                issues.append(Issue("error", "work-item-directory-case", f"directorio debe ser {canonical}"))
            directories[canonical] = child
            _validate_dossier_artifacts(canonical, child, issues)
    for identifier, entry in entries.items():
        if identifier not in directories:
            issues.append(Issue("error", "catalog-target-missing", f"expediente ausente: {entry.path}"))
            continue
        _validate_primary(root, identifier, entry.kind, entry.path, entry.primary, issues, exceptions)
        validate_closure(root, entry, directories[identifier], issues)
    for identifier, directory in directories.items():
        if identifier not in entries and identifier != pending_registration:
            issues.append(Issue("error", "uncatalogued-work-item", f"expediente sin catálogo: {directory}"))
    report.work_items = entries

    try:
        functional_root = relative_target(root, workspace["functionalRoot"], label="functional root")
    except ContractError as error:
        issues.append(Issue("error", "functional-root-invalid", str(error)))
        functional_root = root / "__invalid_functional__"
    functional_catalog = _catalog_path(root, workspace["functionalCatalogPath"], issues)
    df_headers, df_rows = _safe_table(functional_catalog, "Documentos", issues)
    df_res_headers, df_reservations = _safe_table(functional_catalog, "Reservas", issues)
    try:
        _require_headers(df_headers, DF_ENTRY_HEADERS, functional_catalog, "Documentos")
        _require_headers(df_res_headers, DF_RESERVATION_HEADERS, functional_catalog, "Reservas")
        _assert_catalog_integrity(config, df_rows, df_reservations, functional=True)
    except ContractError as error:
        issues.append(Issue("error", "catalog-integrity", str(error)))
    df_entries: dict[str, FunctionalDocumentEntry] = {}
    df_seen: dict[str, str] = {}
    for row in df_rows:
        identifier = cell(row, "ID")
        canonical = identifier.upper()
        path_value = cell(row, "Ruta canónica")
        primary_value = cell(row, "Documento principal")
        if not df_pattern.fullmatch(identifier):
            issues.append(Issue("error", "functional-id-invalid", f"DF inválido: {identifier!r}"))
            continue
        if identifier != canonical:
            issues.append(Issue("error", "functional-id-case", f"DF debe usar mayúsculas: {identifier}"))
        if canonical.casefold() in df_seen:
            issues.append(Issue("error", "functional-id-collision", f"DF duplicado: {identifier}"))
            continue
        df_seen[canonical.casefold()] = identifier
        expected_path = f"{workspace['functionalRoot']}/{canonical}"
        if path_value != expected_path or not safe_relative(path_value):
            issues.append(Issue("error", "functional-path-invalid", f"ruta de {identifier} debe ser {expected_path}"))
        df_entries[canonical] = FunctionalDocumentEntry(
            identifier=canonical,
            path=path_value,
            primary=primary_value,
            reservation_source=cell(row, "Fuente de reserva serializada"),
            domain=present(cell(row, "Dominio o proceso")),
            baseline=present(cell(row, "Versión / baseline")),
            related=present(cell(row, "Relacionados")),
        )
    for row in df_reservations:
        identifier = cell(row, "ID")
        if not df_pattern.fullmatch(identifier) or identifier != identifier.upper():
            issues.append(Issue("error", "functional-reservation-invalid", f"reserva DF inválida: {identifier!r}"))
            continue
        folded = identifier.casefold()
        if folded in df_seen:
            published = df_entries.get(identifier)
            if not (
                published is not None
                and published.reservation_source == cell(row, "Fuente de reserva serializada")
            ):
                issues.append(Issue("error", "functional-reservation-collision", f"DF reservado/publicado duplicado: {identifier}"))
        else:
            df_seen[folded] = identifier
    df_directories: dict[str, Path] = {}
    if not functional_root.exists():
        issues.append(Issue("error", "functional-root-missing", f"functional root obligatorio ausente: {functional_root}"))
    elif not functional_root.is_dir() or functional_root.is_symlink():
        issues.append(Issue("error", "functional-root-invalid", f"functional no es directorio regular: {functional_root}"))
    elif functional_root.is_dir():
        names: dict[str, str] = {}
        for child in sorted(functional_root.iterdir(), key=lambda item: item.name.casefold()):
            if child.name.startswith("."):
                issues.append(Issue("error", "functional-hidden-entry", f"entrada funcional oculta no permitida: {child}"))
                continue
            folded = child.name.casefold()
            if folded in names:
                issues.append(Issue("error", "functional-directory-collision", f"{names[folded]} / {child.name}"))
                continue
            names[folded] = child.name
            if child.is_symlink() or not child.is_dir():
                issues.append(Issue("error", "functional-entry-invalid", f"entrada funcional inválida: {child}"))
                continue
            canonical = child.name.upper()
            if not df_pattern.fullmatch(child.name):
                issues.append(Issue("error", "functional-directory-invalid", f"directorio DF inválido: {child.name}"))
                continue
            if child.name != canonical:
                issues.append(Issue("error", "functional-directory-case", f"directorio DF debe ser {canonical}"))
            df_directories[canonical] = child
            _validate_functional_artifacts(root, canonical, child, issues)
    for identifier, entry in df_entries.items():
        if identifier not in df_directories:
            issues.append(Issue("error", "functional-target-missing", f"DF ausente: {entry.path}"))
            continue
        _validate_primary(root, identifier, "DF", entry.path, entry.primary, issues, exceptions, functional=True)
    for identifier, directory in df_directories.items():
        if identifier not in df_entries and identifier != pending_registration:
            issues.append(Issue("error", "uncatalogued-functional-document", f"DF sin catálogo: {directory}"))
    report.functional_documents = df_entries

    legacy_work, legacy_df, invalid_legacy = legacy_inventory(root, config)
    report.legacy_work_files = legacy_work
    report.legacy_functional_files = legacy_df
    for relative in legacy_work + legacy_df:
        name = PurePosixPath(relative).name
        match = re.match(r"^(RM|BUG|TEC|DF)-[0-9]+", name, flags=re.IGNORECASE)
        if match and match.group(0) != match.group(0).upper():
            issues.append(Issue("error", "legacy-id-case", f"artefacto legado usa ID no canónico: {relative}"))
    for relative in invalid_legacy:
        issues.append(Issue("error", "legacy-artifact-invalid", f"artefacto FARO plano no soportado: {relative}"))
    has_current = bool(entries or directories or df_entries or df_directories or catalog.exists())
    has_legacy = bool(legacy_work or legacy_df or invalid_legacy)
    if has_current and has_legacy:
        report.layout = "mixed"
        issues.append(Issue("error", "mixed-layout", "coexisten artefactos planos 1.13 y expedientes v2"))
    elif has_legacy:
        report.layout = "legacy"
    elif has_current or functional_catalog.exists():
        report.layout = "current"
    validate_profile(root, config, issues)
    validate_workflow_v2(root, config, report)
    return report


def resolve_work_item(root: Path, identifier: str, config: dict | None = None) -> tuple[WorkItemEntry, Path, bool]:
    config = config or load_contract_config()
    canonical = identifier.upper()
    if identifier != canonical or not re.fullmatch(config["workItems"]["idPattern"], canonical):
        raise ContractError(f"ID inválido/no canónico: {identifier}")
    report = validate_layout(root, config)
    if report.errors:
        raise ContractError("contrato inválido: " + "; ".join(issue.message for issue in report.errors))
    entry = report.work_items.get(canonical)
    if entry is None:
        raise ContractError(f"expediente no localizado: {canonical}")
    resolved_root = workspace_root(root)
    dossier = relative_target(resolved_root, entry.path, label=f"expediente {canonical}")
    return entry, dossier, (dossier / f"{canonical}-cierre.json").is_file()


def atomic_write(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as target:
            target.write(content)
            target.flush()
            os.fsync(target.fileno())
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def safe_atomic_write(root: Path, path: Path, content: bytes) -> None:
    if not _is_within(root, path.resolve(strict=False)):
        raise ContractError(f"escritura fuera del root: {path}")
    relative_target(root, path.relative_to(root).as_posix(), label="destino de escritura")
    if path.is_symlink():
        raise ContractError(f"destino de escritura es symlink: {path}")
    atomic_write(path, content)


@contextmanager
def catalog_lock(root: Path, catalog: Path) -> Iterator[None]:
    lock = catalog.with_name(f".{catalog.name}.lock")
    relative_target(root, lock.relative_to(root).as_posix(), label="lock de catálogo")
    if lock.is_symlink():
        raise ContractError(f"lock de catálogo no puede ser symlink: {lock}")
    descriptor = os.open(lock, os.O_CREAT | os.O_RDWR, 0o600)
    try:
        with os.fdopen(descriptor, "a+b", closefd=True) as handle:
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
            else:  # pragma: no cover - Windows only.
                handle.seek(0, os.SEEK_END)
                if handle.tell() == 0:
                    handle.write(b"\0")
                    handle.flush()
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_LOCK, 1)
            yield
            if fcntl is not None:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            else:  # pragma: no cover - Windows only.
                handle.seek(0)
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
    except Exception:
        raise


def _id_sort(identifier: str) -> tuple[str, int]:
    prefix, number = identifier.split("-", 1)
    return prefix, int(number)


def require_valid_layout(
    root: Path,
    config: dict,
    operation: str,
    *,
    pending_registration: str | None = None,
) -> ValidationReport:
    report = validate_layout(root, config, pending_registration=pending_registration)
    if report.errors:
        raise ContractError(
            f"{operation} bloqueado por layout inválido: "
            + "; ".join(issue.message for issue in report.errors)
        )
    return report


def _reserve_locked(
    root: Path,
    config: dict,
    kind: str,
    source: str,
    requested_id: str | None,
    reserved_at: str,
    apply: bool,
) -> tuple[dict, str]:
    functional = kind == "DF"
    require_valid_layout(root, config, "reserve")
    workspace = config["workspace"]
    catalog_value_path = workspace["functionalCatalogPath"] if functional else workspace["requirementsCatalogPath"]
    catalog = relative_target(root, catalog_value_path, label="catálogo")
    if not catalog.is_file() or catalog.is_symlink():
        raise ContractError(f"catálogo ausente/no regular/symlink: {catalog}")
    reservation_section = "Reservas"
    published_section = "Documentos" if functional else "Expedientes"
    expected_res_headers = DF_RESERVATION_HEADERS if functional else WORK_RESERVATION_HEADERS
    expected_entry_headers = DF_ENTRY_HEADERS if functional else WORK_ENTRY_HEADERS
    res_headers, reservations = _table(catalog, reservation_section)
    entry_headers, published = _table(catalog, published_section)
    _require_headers(res_headers, expected_res_headers, catalog, reservation_section)
    _require_headers(entry_headers, expected_entry_headers, catalog, published_section)
    _assert_catalog_integrity(config, published, reservations, functional=functional)
    pattern = re.compile(config["functionalDocuments"]["idPattern"] if functional else config["workItems"]["idPattern"])
    existing: dict[str, tuple[str, str]] = {}
    published_by_id: dict[str, dict[str, str]] = {}
    published_source_matches: list[dict[str, str]] = []
    for row in published:
        identifier = cell(row, "ID")
        folded = identifier.casefold()
        if folded in existing:
            raise ContractError(f"ID duplicado en catálogo: {identifier}")
        existing[folded] = ("published", identifier)
        published_by_id[folded] = row
        if cell(row, "Fuente de reserva serializada").casefold() == source.casefold():
            published_source_matches.append(row)
    if len(published_source_matches) > 1:
        raise ContractError(f"fuente publicada duplicada para {kind}: {source}")
    if published_source_matches:
        row = published_source_matches[0]
        existing_id = cell(row, "ID")
        existing_kind = "DF" if functional else cell(row, "Tipo")
        if existing_kind != kind:
            raise ContractError(
                f"la fuente ya fue clasificada como {existing_kind} en {existing_id}; no puede reservar {kind}"
            )
        if requested_id and requested_id != existing_id:
            raise ContractError(f"la fuente ya publicó {existing_id}, no {requested_id}")
        return {
            "id": existing_id,
            "kind": kind,
            "source": cell(row, "Fuente de reserva serializada"),
            "path": cell(row, "Ruta canónica"),
        }, "already-registered"
    same_source: list[str] = []
    for row in reservations:
        identifier = cell(row, "ID")
        folded = identifier.casefold()
        if folded in existing:
            published_row = published_by_id.get(folded)
            if not (
                published_row is not None
                and cell(row, "Fuente de reserva serializada")
                == cell(published_row, "Fuente de reserva serializada")
                and ("DF" if functional else cell(row, "Tipo"))
                == ("DF" if functional else cell(published_row, "Tipo"))
            ):
                raise ContractError(f"ID reservado/publicado duplicado: {identifier}")
            continue
        existing[folded] = ("reserved", identifier)
        if cell(row, "Fuente de reserva serializada").casefold() == source.casefold():
            same_source.append(identifier)
    if len(same_source) > 1:
        raise ContractError(f"fuente de reserva duplicada para {kind}: {source}")
    if same_source:
        existing_id = same_source[0]
        row = next(item for item in reservations if cell(item, "ID") == existing_id)
        existing_kind = "DF" if functional else cell(row, "Tipo")
        if existing_kind != kind:
            raise ContractError(
                f"la fuente ya fue clasificada como {existing_kind} en {existing_id}; no puede reservar {kind}"
            )
        if requested_id and requested_id != existing_id:
            raise ContractError(f"la fuente ya reservó {existing_id}, no {requested_id}")
        return {
            "id": existing_id, "kind": kind, "source": cell(row, "Fuente de reserva serializada"),
            "reservedAt": cell(row, "Fecha y zona"),
        }, "already-reserved"
    if requested_id:
        if requested_id != requested_id.upper() or not pattern.fullmatch(requested_id):
            raise ContractError(f"ID solicitado inválido/no canónico: {requested_id}")
        if not requested_id.startswith(f"{kind}-") or requested_id.casefold() in existing:
            raise ContractError(f"ID solicitado no disponible para {kind}: {requested_id}")
        identifier = requested_id
    else:
        width = 3 if kind == "DF" else 4
        identifier = ""
        for number in range(1, 10 ** width):
            candidate = f"{kind}-{number:0{width}d}"
            if candidate.casefold() not in existing:
                identifier = candidate
                break
        if not identifier:
            raise ContractError(f"no hay IDs disponibles para {kind}")
    new_row = {"id": identifier, "source": source, "reservedAt": reserved_at}
    if apply:
        if functional:
            matrix = [
                [cell(row, "ID"), cell(row, "Fuente de reserva serializada"), cell(row, "Fecha y zona")]
                for row in reservations
            ]
            matrix.append([identifier, source, reserved_at])
        else:
            matrix = [
                [cell(row, "ID"), cell(row, "Tipo"), cell(row, "Fuente de reserva serializada"), cell(row, "Fecha y zona")]
                for row in reservations
            ]
            matrix.append([identifier, kind, source, reserved_at])
        matrix.sort(key=lambda values: _id_sort(values[0]))
        updated = _replace_table(catalog.read_text(encoding="utf-8"), reservation_section, expected_res_headers, matrix)
        safe_atomic_write(root, catalog, updated.encode("utf-8"))
    return new_row, "applied" if apply else "dry-run"


def reserve_identifier(
    root: Path,
    kind: str,
    source: str,
    *,
    identifier: str | None = None,
    reserved_at: str | None = None,
    apply: bool = False,
    config: dict | None = None,
) -> tuple[dict, str]:
    root = workspace_root(root)
    config = config or load_contract_config()
    kind = strict_catalog_token(kind, "kind")
    if kind != kind.upper():
        raise ContractError(f"tipo debe usar mayúsculas canónicas: {kind}")
    if kind not in {"RM", "BUG", "TEC", "DF"}:
        raise ContractError(f"tipo no reservable: {kind}")
    source = catalog_value(source, "source")
    identifier = strict_catalog_token(identifier, "id") if identifier else None
    reserved_at = reserved_at or utc_now()
    parse_timestamp(reserved_at, "reserved-at")
    workspace = config["workspace"]
    catalog = relative_target(
        root,
        workspace["functionalCatalogPath"] if kind == "DF" else workspace["requirementsCatalogPath"],
        label="catálogo",
    )
    if apply:
        with catalog_lock(root, catalog):
            return _reserve_locked(root, config, kind, source, identifier, reserved_at, True)
    return _reserve_locked(root, config, kind, source, identifier, reserved_at, False)


def _register_locked(
    root: Path,
    config: dict,
    identifier: str,
    primary_value: str,
    reservation_source: str | None,
    provider: str | None,
    external_id: str | None,
    external_url: str | None,
    related: str | None,
    domain: str | None,
    baseline: str | None,
    apply: bool,
) -> tuple[dict, str]:
    kind = identifier.split("-", 1)[0]
    functional = kind == "DF"
    workspace = config["workspace"]
    catalog = relative_target(
        root,
        workspace["functionalCatalogPath"] if functional else workspace["requirementsCatalogPath"],
        label="catálogo",
    )
    if not catalog.is_file() or catalog.is_symlink():
        raise ContractError(f"catálogo ausente/no regular/symlink: {catalog}")
    res_headers, reservations = _table(catalog, "Reservas")
    entry_section = "Documentos" if functional else "Expedientes"
    entry_headers, published = _table(catalog, entry_section)
    expected_res = DF_RESERVATION_HEADERS if functional else WORK_RESERVATION_HEADERS
    expected_entry = DF_ENTRY_HEADERS if functional else WORK_ENTRY_HEADERS
    _require_headers(res_headers, expected_res, catalog, "Reservas")
    _require_headers(entry_headers, expected_entry, catalog, entry_section)
    _assert_catalog_integrity(config, published, reservations, functional=functional)
    matches = [row for row in reservations if cell(row, "ID").casefold() == identifier.casefold()]
    published_matches = [row for row in published if cell(row, "ID").casefold() == identifier.casefold()]
    directory_value = f"{workspace['functionalRoot'] if functional else workspace['workItemsRoot']}/{identifier}"
    if not safe_relative(primary_value) or PurePosixPath(primary_value).parent.as_posix() != directory_value:
        raise ContractError(f"--primary debe ser ruta root-relative directa dentro de {directory_value}")
    primary_document = PurePosixPath(primary_value).name
    if published_matches:
        if len(published_matches) != 1:
            raise ContractError(f"publicación duplicada: {identifier}")
        require_valid_layout(root, config, "register")
        existing = published_matches[0]
        if cell(existing, "Documento principal") != primary_document or cell(existing, "Ruta canónica") != directory_value:
            raise ContractError(f"{identifier} ya publicado con otra ruta/primario")
        if reservation_source is None:
            raise ContractError("register idempotente exige --reservation-source")
        published_source = cell(existing, "Fuente de reserva serializada")
        if reservation_source.casefold() != published_source.casefold():
            raise ContractError(f"fuente no coincide con la publicación de {identifier}")
        if functional:
            comparisons = {
                "Dominio o proceso": domain,
                "Versión / baseline": baseline,
                "Relacionados": related,
            }
        else:
            supplied_remote = (provider, external_id, external_url)
            if any(value is not None for value in supplied_remote):
                if not all(isinstance(value, str) and value.strip() for value in supplied_remote):
                    raise ContractError("referencia externa idempotente debe suministrarse completa")
                current_remote = (cell(existing, "Proveedor"), cell(existing, "ID remoto"), cell(existing, "URL remota"))
                if tuple(value.strip() for value in supplied_remote if value is not None) != current_remote:
                    raise ContractError(f"{identifier} ya publicado con otra referencia externa")
            comparisons = {"Relacionados": related}
        for header, supplied_value in comparisons.items():
            if supplied_value is not None and cell(existing, header) != supplied_value.strip():
                raise ContractError(f"{identifier} ya publicado con otro valor de {header}")
        return {
            "id": identifier,
            "path": directory_value,
            "primaryDocument": primary_document,
            "primaryPath": primary_value,
            "reservationSource": published_source,
        }, "already-registered"
    if len(matches) != 1:
        raise ContractError(f"register exige una reserva única para {identifier}")
    if reservation_source is None:
        raise ContractError("register exige --reservation-source para consumir la reserva")
    reserved_source = cell(matches[0], "Fuente de reserva serializada")
    if reservation_source and reservation_source.casefold() != reserved_source.casefold():
        raise ContractError(f"fuente no coincide con la reserva de {identifier}")
    require_valid_layout(root, config, "register", pending_registration=identifier)
    directory = relative_target(root, directory_value, label=f"carpeta de {identifier}")
    if not directory.is_dir() or directory.is_symlink():
        raise ContractError(f"carpeta ausente/no regular/symlink: {directory}")
    issues: list[Issue] = []
    if functional:
        _validate_functional_artifacts(root, identifier, directory, issues)
    else:
        _validate_dossier_artifacts(identifier, directory, issues)
        closure = directory / f"{identifier}-cierre.json"
        if closure.exists():
            issues.append(Issue("error", "closure-preexisting", f"alta no puede consumir reserva con cierre preexistente: {closure}"))
    primary = _validate_primary(
        root, identifier, kind, directory_value, primary_document, issues, {},
        functional=functional, allow_legacy=False,
    )
    if primary is None or any(issue.severity == "error" for issue in issues):
        raise ContractError("; ".join(issue.message for issue in issues))
    # The consumed reservation remains as an immutable-by-contract source
    # binding. The published row and this preserved row must keep matching.
    remaining = list(reservations)
    text = catalog.read_text(encoding="utf-8")
    if functional:
        domain_value = catalog_value(domain or "—", "domain")
        baseline_value = catalog_value(baseline or "—", "baseline")
        related_value = catalog_value(related or "—", "related")
        entry_row = [identifier, directory_value, primary_document, reserved_source, domain_value, baseline_value, related_value]
        entry_object = {
            "id": identifier, "path": directory_value, "primaryDocument": primary_document,
            "primaryPath": primary_value,
            "reservationSource": reserved_source,
            "domain": domain_value, "baseline": baseline_value, "related": related_value,
        }
        reservation_matrix = [
            [cell(row, "ID"), cell(row, "Fuente de reserva serializada"), cell(row, "Fecha y zona")]
            for row in remaining
        ]
        entry_matrix = [
            [cell(row, name) for name in DF_ENTRY_HEADERS] for row in published
        ] + [entry_row]
    else:
        values = [provider, external_id, external_url]
        if not all(isinstance(value, str) and value.strip() for value in values):
            raise ContractError("register de RM/BUG/TEC exige proveedor, ID y URL remotos")
        provider_value = catalog_value(provider or "", "provider")
        external_id_value = catalog_value(external_id or "", "external-id")
        external_url_value = validated_external_url(external_url or "")
        if provider_value not in allowed_providers(config):
            raise ContractError(f"proveedor externo no permitido: {provider_value}")
        canonical_remote_id(provider_value, external_id_value)
        _validate_provider_item_url(provider_value, external_url_value, external_id_value)
        related_value = catalog_value(related or "—", "related")
        entry_row = [
            identifier, kind, directory_value, primary_document, reserved_source,
            provider_value, external_id_value, external_url_value, related_value,
        ]
        entry_object = {
            "id": identifier, "kind": kind, "path": directory_value,
            "primaryDocument": primary_document, "primaryPath": primary_value,
            "reservationSource": reserved_source,
            "externalReference": {"provider": provider_value, "id": external_id_value, "url": external_url_value},
            "related": related_value,
        }
        reservation_matrix = [
            [cell(row, "ID"), cell(row, "Tipo"), cell(row, "Fuente de reserva serializada"), cell(row, "Fecha y zona")]
            for row in remaining
        ]
        entry_matrix = [[cell(row, name) for name in WORK_ENTRY_HEADERS] for row in published] + [entry_row]
    candidate = {
        normalize_header(header): value for header, value in zip(expected_entry, entry_row)
    }
    _assert_catalog_integrity(
        config, published + [candidate], remaining, functional=functional,
    )
    reservation_matrix.sort(key=lambda values: _id_sort(values[0]))
    entry_matrix.sort(key=lambda values: _id_sort(values[0]))
    if apply:
        text = _replace_table(text, "Reservas", expected_res, reservation_matrix)
        text = _replace_table(text, entry_section, expected_entry, entry_matrix)
        safe_atomic_write(root, catalog, text.encode("utf-8"))
    return entry_object, "applied" if apply else "dry-run"


def register_identifier(
    root: Path,
    identifier: str,
    primary: str,
    *,
    reservation_source: str | None = None,
    provider: str | None = None,
    external_id: str | None = None,
    external_url: str | None = None,
    related: str | None = None,
    domain: str | None = None,
    baseline: str | None = None,
    apply: bool = False,
    config: dict | None = None,
) -> tuple[dict, str]:
    root = workspace_root(root)
    config = config or load_contract_config()
    identifier = strict_catalog_token(identifier, "id")
    if identifier != identifier.upper():
        raise ContractError(f"ID debe ser canónico: {identifier}")
    kind = identifier.split("-", 1)[0] if "-" in identifier else ""
    pattern = config["functionalDocuments"]["idPattern"] if kind == "DF" else config["workItems"]["idPattern"]
    if kind not in {"RM", "BUG", "TEC", "DF"} or not re.fullmatch(pattern, identifier):
        raise ContractError(f"ID no registrable: {identifier}")
    primary = catalog_value(primary, "primary")
    if not safe_relative(primary):
        raise ContractError(f"primary no es ruta segura: {primary}")
    reservation_source = catalog_value(reservation_source, "reservation-source") if reservation_source else None
    workspace = config["workspace"]
    catalog = relative_target(
        root,
        workspace["functionalCatalogPath"] if kind == "DF" else workspace["requirementsCatalogPath"],
        label="catálogo",
    )
    arguments = (
        root, config, identifier, primary, reservation_source, provider, external_id,
        external_url, related, domain, baseline,
    )
    if apply:
        with catalog_lock(root, catalog):
            return _register_locked(*arguments, True)
    return _register_locked(*arguments, False)


def _link_external_locked(
    root: Path,
    config: dict,
    identifier: str,
    provider: str,
    external_id: str,
    external_url: str,
    apply: bool,
) -> tuple[dict, str]:
    catalog = relative_target(root, config["workspace"]["requirementsCatalogPath"], label="catálogo")
    headers, rows = _table(catalog, "Expedientes")
    _require_headers(headers, WORK_ENTRY_HEADERS, catalog, "Expedientes")
    reservation_headers, reservations = _table(catalog, "Reservas")
    _require_headers(reservation_headers, WORK_RESERVATION_HEADERS, catalog, "Reservas")
    _assert_catalog_integrity(config, rows, reservations, functional=False)
    matches = [row for row in rows if cell(row, "ID").casefold() == identifier.casefold()]
    if len(matches) != 1:
        raise ContractError(f"link-external exige una entrada única para {identifier}")
    row = matches[0]
    if cell(row, "ID") != identifier:
        raise ContractError(f"ID del catálogo no usa casing canónico: {cell(row, 'ID')}")
    require_valid_layout(root, config, "link-external")
    current = tuple(present(cell(row, name)) for name in ("Proveedor", "ID remoto", "URL remota"))
    requested = (provider, external_id, external_url)
    if current == requested:
        return {
            "id": identifier,
            "externalReference": {"provider": provider, "id": external_id, "url": external_url},
        }, "already-linked"
    if any(value is not None for value in current):
        raise ContractError(f"{identifier} ya tiene una referencia externa parcial o diferente; no se sobrescribe")
    report = validate_layout(root, config)
    entry = report.work_items.get(identifier)
    if entry is None:
        raise ContractError(f"link-external no pudo resolver {identifier} en layout válido")
    path_value = cell(row, "Ruta canónica")
    dossier = relative_target(root, path_value, label=f"expediente {identifier}")
    if not dossier.is_dir() or dossier.is_symlink():
        raise ContractError(f"expediente ausente/no regular/symlink: {dossier}")
    if (dossier / f"{identifier}-cierre.json").exists():
        raise ContractError(f"no se enlaza referencia sobre expediente congelado: {identifier}")
    matrix: list[list[str]] = []
    for item in rows:
        values = [cell(item, name) for name in WORK_ENTRY_HEADERS]
        if cell(item, "ID") == identifier:
            values[5:8] = list(requested)
        matrix.append(values)
    projected = [
        {normalize_header(header): value for header, value in zip(WORK_ENTRY_HEADERS, values)}
        for values in matrix
    ]
    _assert_catalog_integrity(config, projected, reservations, functional=False)
    if apply:
        text = _replace_table(catalog.read_text(encoding="utf-8"), "Expedientes", WORK_ENTRY_HEADERS, matrix)
        safe_atomic_write(root, catalog, text.encode("utf-8"))
    return {
        "id": identifier,
        "externalReference": {"provider": provider, "id": external_id, "url": external_url},
    }, "applied" if apply else "dry-run"


def link_external(
    root: Path,
    identifier: str,
    provider: str,
    external_id: str,
    external_url: str,
    *,
    apply: bool = False,
    config: dict | None = None,
) -> tuple[dict, str]:
    root = workspace_root(root)
    config = config or load_contract_config()
    identifier = strict_catalog_token(identifier, "id")
    if identifier != identifier.upper() or not re.fullmatch(config["workItems"]["idPattern"], identifier):
        raise ContractError(f"ID de expediente inválido/no canónico: {identifier}")
    provider = catalog_value(provider, "provider")
    external_id = catalog_value(external_id, "external-id")
    external_url = validated_external_url(external_url)
    if provider not in allowed_providers(config):
        raise ContractError(f"proveedor externo no permitido: {provider}")
    canonical_remote_id(provider, external_id)
    _validate_provider_item_url(provider, external_url, external_id)
    catalog = relative_target(root, config["workspace"]["requirementsCatalogPath"], label="catálogo")
    if apply:
        with catalog_lock(root, catalog):
            return _link_external_locked(root, config, identifier, provider, external_id, external_url, True)
    return _link_external_locked(root, config, identifier, provider, external_id, external_url, False)


def _freeze_work_item_unlocked(
    root: Path,
    identifier: str,
    *,
    remote_readback: dict | None = None,
    frozen_at: str | None = None,
    apply: bool = False,
) -> tuple[dict, str]:
    resolved_root = workspace_root(root)
    entry, dossier, frozen = resolve_work_item(resolved_root, identifier)
    closure = dossier / f"{entry.identifier}-cierre.json"
    if frozen:
        return load_json(closure), "already-frozen"
    if apply and remote_readback is None:
        raise ContractError("freeze --apply exige readback HTTP autenticado del proveedor")
    frozen_at = frozen_at or utc_now()
    frozen_time = parse_timestamp(frozen_at, "frozen-at")
    catalog_external = (entry.provider, entry.external_id, entry.external_url)
    if not all(isinstance(value, str) and value.strip() for value in catalog_external):
        raise ContractError("freeze exige referencia completa en catálogo; usar link-external primero")
    if remote_readback is not None:
        readback_time = _validate_remote_readback_snapshot(resolved_root, entry, remote_readback)
        if frozen_time < readback_time:
            raise ContractError("frozen-at no puede preceder al readback remoto")
    gate = validation_gate(resolved_root, entry, dossier)
    files = dossier_files(dossier, closure.name)
    if not files:
        raise ContractError(f"expediente sin artefactos: {dossier}")
    payload = {
        "schemaVersion": 3,
        "workItemId": entry.identifier,
        "reservationSource": entry.reservation_source,
        "frozenAt": frozen_at,
        "externalReference": {
            "provider": catalog_external[0], "id": catalog_external[1], "url": catalog_external[2],
        },
        "remoteReadback": remote_readback,
        "validationGate": gate,
        "hashAlgorithm": "sha256",
        "artifacts": {relative: sha256(path) for relative, path in files.items()},
    }
    if apply:
        safe_atomic_write(
            resolved_root, closure,
            (json.dumps(payload, ensure_ascii=False, indent=2) + "\n").encode("utf-8"),
        )
        return payload, "applied"
    return payload, "dry-run"


def freeze_work_item(
    root: Path,
    identifier: str,
    *,
    apply: bool = False,
) -> tuple[dict, str]:
    resolved_root = workspace_root(root)
    if not apply:
        return _freeze_work_item_unlocked(resolved_root, identifier, apply=False)
    config = load_contract_config()
    canonical = identifier.upper()
    lock_target = relative_target(
        resolved_root,
        f"{config['workspace']['workItemsRoot']}/{canonical}",
        label="lock de freeze",
    )
    catalog = relative_target(
        resolved_root, config["workspace"]["requirementsCatalogPath"], label="catálogo",
    )
    with catalog_lock(resolved_root, catalog), catalog_lock(resolved_root, lock_target):
        entry_before, dossier_before, frozen_before = resolve_work_item(resolved_root, identifier)
        if frozen_before:
            return load_json(dossier_before / f"{entry_before.identifier}-cierre.json"), "already-frozen"
        # No credential leaves the process until every local gate is valid. The
        # same gates are rebuilt after the GET inside _freeze_work_item_unlocked.
        validation_gate(resolved_root, entry_before, dossier_before)
        remote_readback = perform_provider_readback(resolved_root, entry_before)
        payload, mode = _freeze_work_item_unlocked(
            resolved_root, identifier, remote_readback=remote_readback,
            frozen_at=utc_now(), apply=True,
        )
        if mode == "already-frozen" or frozen_before:
            return payload, mode
        post_issues: list[Issue] = []
        validate_closure(resolved_root, entry_before, dossier_before, post_issues)
        errors = [issue for issue in post_issues if issue.severity == "error"]
        if errors:
            closure = dossier_before / f"{entry_before.identifier}-cierre.json"
            try:
                closure.unlink()
            except OSError:
                pass
            raise ContractError("freeze no superó rehash post-escritura: " + "; ".join(issue.message for issue in errors))
        return payload, mode


def print_report(report: ValidationReport) -> None:
    print(f"Contrato: {report.contract_version}; layout: {report.layout}")
    print(f"Expedientes: {len(report.work_items)}; DF: {len(report.functional_documents)}")
    for issue in report.issues:
        print(f"- {issue.severity.upper()} [{issue.code}]: {issue.message}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    validate = commands.add_parser("validate", help="Valida layout, catálogos, primarios y cierres.")
    validate.add_argument("--root", type=Path, default=Path.cwd())
    validate.add_argument("--strict", action="store_true")
    validate.add_argument("--json", action="store_true")
    resolve = commands.add_parser("resolve", help="Resuelve un expediente sólo mediante catálogo.")
    resolve.add_argument("--root", type=Path, default=Path.cwd())
    resolve.add_argument("--id", required=True)
    resolve.add_argument("--json", action="store_true")
    reserve = commands.add_parser("reserve", help="Reserva RM/BUG/TEC/DF de forma serializada.")
    reserve.add_argument("--root", type=Path, default=Path.cwd())
    reserve.add_argument("--kind", required=True, choices=("RM", "BUG", "TEC", "DF"))
    reserve.add_argument("--source", required=True)
    reserve.add_argument("--id")
    reserve.add_argument("--reserved-at")
    reserve.add_argument("--apply", action="store_true")
    reserve.add_argument("--json", action="store_true")
    for name in ("register", "publish"):
        register = commands.add_parser(name, help="Consume una reserva y publica su entrada atómicamente.")
        register.add_argument("--root", type=Path, default=Path.cwd())
        register.add_argument("--id", required=True)
        register.add_argument("--primary", required=True)
        register.add_argument("--reservation-source", required=True)
        register.add_argument("--external-provider")
        register.add_argument("--external-id")
        register.add_argument("--external-url")
        register.add_argument("--related")
        register.add_argument("--domain")
        register.add_argument("--baseline")
        register.add_argument("--apply", action="store_true")
        register.add_argument("--json", action="store_true")
    link = commands.add_parser("link-external", help="Completa atómicamente la referencia remota vacía.")
    link.add_argument("--root", type=Path, default=Path.cwd())
    link.add_argument("--id", required=True)
    link.add_argument("--external-provider", required=True)
    link.add_argument("--external-id", required=True)
    link.add_argument("--external-url", required=True)
    link.add_argument("--apply", action="store_true")
    link.add_argument("--json", action="store_true")
    freeze = commands.add_parser(
        "freeze", help="Congela sólo después de gates semánticos y readback HTTP DONE.",
    )
    freeze.add_argument("--root", type=Path, default=Path.cwd())
    freeze.add_argument("--id", required=True)
    freeze.add_argument("--apply", action="store_true")
    freeze.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "validate":
            report = validate_layout(args.root)
            print(json.dumps(report.serializable(), ensure_ascii=False, indent=2)) if args.json else print_report(report)
            return 1 if report.errors or (args.strict and report.warnings) else 0
        if args.command == "resolve":
            entry, dossier, frozen = resolve_work_item(args.root, args.id)
            result = {
                "id": entry.identifier, "path": str(dossier),
                "primaryDocument": entry.primary,
                "primaryPath": f"{entry.path}/{entry.primary}",
                "reservationSource": entry.reservation_source,
                "frozen": frozen,
                "externalReference": {"provider": entry.provider, "id": entry.external_id, "url": entry.external_url},
            }
            print(json.dumps(result, ensure_ascii=False, indent=2)) if args.json else print(f"{entry.identifier}: {dossier} ({entry.primary})")
            return 0
        if args.command == "reserve":
            result, mode = reserve_identifier(
                args.root, args.kind, args.source, identifier=args.id,
                reserved_at=args.reserved_at, apply=args.apply,
            )
            output = {"mode": mode, "reservation": result}
        elif args.command in {"register", "publish"}:
            result, mode = register_identifier(
                args.root, args.id, args.primary,
                reservation_source=args.reservation_source,
                provider=args.external_provider, external_id=args.external_id,
                external_url=args.external_url, related=args.related, domain=args.domain,
                baseline=args.baseline, apply=args.apply,
            )
            output = {"mode": mode, "entry": result}
        elif args.command == "link-external":
            result, mode = link_external(
                args.root, args.id, args.external_provider, args.external_id,
                args.external_url, apply=args.apply,
            )
            output = {"mode": mode, "entry": result}
        else:
            result, mode = freeze_work_item(args.root, args.id, apply=args.apply)
            output = {"mode": mode, "closure": result}
        if args.json:
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"{args.command}: {output['mode']}")
        return 0
    except ContractError as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
