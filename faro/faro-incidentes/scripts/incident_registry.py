#!/usr/bin/env python3
"""Validate and mutate the FARO incident registry without creating remote work.

Writes are opt-in (``--apply``), serialized by an exclusive lock and committed
with an atomic replace.  The registry remains a locator/evidence index; it does
not become an authority for operational status, priority or assignment.
"""
from __future__ import annotations

import argparse
import errno
import json
import os
import re
import stat
import sys
import tempfile
import time
import unicodedata
from dataclasses import dataclass
from pathlib import Path, PurePosixPath

try:  # POSIX advisory locks are released by the kernel when a process exits.
    import fcntl
except ImportError:  # pragma: no cover - exercised on Windows
    fcntl = None

try:  # Windows equivalent; also released when the process/descriptor exits.
    import msvcrt
except ImportError:  # pragma: no cover - exercised on POSIX
    msvcrt = None


INCIDENT_ID = re.compile(r"INC-[0-9]{4}\Z")
INCIDENT_FILE = re.compile(r"(INC-[0-9]{4})-[a-z0-9]+(?:-[a-z0-9]+)*\.md\Z")
SEPARATOR = re.compile(r":?-{3,}:?\Z")
RESERVATION_HEADERS = ("ID", "Alcance", "Fuente de reserva serializada")
RECORD_HEADERS = (
    "ID",
    "Expediente estable",
    "Fuente de reserva serializada",
    "Seguimiento remoto y último readback",
    "Conclusión / impacto",
    "Derivados y relaciones",
)
LEGACY_RECORD_HEADERS_V1 = (
    "ID",
    "Registro",
    "Estado",
    "Conclusión",
    "Acciones derivadas / seguimiento",
)
LEGACY_RECORD_HEADERS_WITHOUT_SOURCE = (
    "ID",
    "Expediente estable",
    "Seguimiento remoto y último readback",
    "Conclusión / impacto",
    "Derivados y relaciones",
)
FORBIDDEN_AUTHORITY_HEADERS = {
    "estado",
    "status",
    "prioridad",
    "priority",
    "asignado",
    "asignada",
    "assignee",
    "assigned to",
    "sprint",
    "iteracion",
    "iteration",
    "area",
    "backlog",
    "cola",
}
LOCK_NAME = ".faro-incidents-registry.lock"
LOCK_TIMEOUT_SECONDS = 10.0
MAX_CELL_LENGTH = 2000


class RegistryError(RuntimeError):
    """A safe, user-facing registry contract error."""


@dataclass
class MarkdownTable:
    start: int
    end: int
    headers: tuple[str, ...]
    rows: list[dict[str, str]]


@dataclass
class Registry:
    lines: list[str]
    records: MarkdownTable
    reservations: MarkdownTable
    record_schema: str = "current"


def normalize(value: str) -> str:
    decomposed = unicodedata.normalize("NFKD", value)
    return " ".join(
        "".join(char for char in decomposed if not unicodedata.combining(char))
        .lower()
        .split()
    )


def clean_cell(value: str, label: str) -> str:
    cleaned = value.strip()
    if not cleaned:
        raise RegistryError(f"{label} no puede estar vacío")
    if len(cleaned) > MAX_CELL_LENGTH:
        raise RegistryError(f"{label} excede {MAX_CELL_LENGTH} caracteres")
    if "|" in cleaned or "\n" in cleaned or "\r" in cleaned:
        raise RegistryError(f"{label} no puede contener pipes ni saltos de línea")
    if any(ord(char) < 32 for char in cleaned):
        raise RegistryError(f"{label} contiene caracteres de control")
    return cleaned


def canonical_id(value: str) -> str:
    identifier = clean_cell(value, "ID").upper()
    if not INCIDENT_ID.fullmatch(identifier):
        raise RegistryError(f"ID de incidente inválido: {value!r}")
    return identifier


def safe_record_path(value: str, identifier: str) -> str:
    raw = clean_cell(value, "ruta del expediente")
    if "\\" in raw or raw.startswith("/"):
        raise RegistryError(f"ruta de incidente insegura: {raw!r}")
    relative = PurePosixPath(raw)
    if any(part in {"", ".", ".."} for part in relative.parts):
        raise RegistryError(f"ruta de incidente insegura: {raw!r}")
    if len(relative.parts) != 3 or relative.parts[:2] != ("context", "incidents"):
        raise RegistryError(
            "la ruta debe ser context/incidents/INC-NNNN-<slug>.md"
        )
    match = INCIDENT_FILE.fullmatch(relative.name)
    if match is None or match.group(1) != identifier:
        raise RegistryError(
            f"el archivo {relative.name!r} no coincide con {identifier}"
        )
    return relative.as_posix()


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def find_section(lines: list[str], title: str) -> int:
    wanted = normalize(title)
    matches = [
        index
        for index, line in enumerate(lines)
        if line.startswith("## ") and normalize(line[3:]) == wanted
    ]
    if len(matches) != 1:
        raise RegistryError(f"se esperaba exactamente una sección ## {title}")
    return matches[0]


def parse_table(
    lines: list[str],
    section: str,
    expected_headers: tuple[str, ...],
    *,
    alternate_headers: tuple[tuple[str, ...], ...] = (),
) -> MarkdownTable:
    heading = find_section(lines, section)
    next_heading = next(
        (index for index in range(heading + 1, len(lines)) if lines[index].startswith("## ")),
        len(lines),
    )
    table_start = next(
        (index for index in range(heading + 1, next_heading) if lines[index].lstrip().startswith("|")),
        None,
    )
    if table_start is None:
        raise RegistryError(f"falta tabla Markdown en ## {section}")
    table_end = table_start
    while table_end < next_heading and lines[table_end].lstrip().startswith("|"):
        table_end += 1
    if any(
        line.lstrip().startswith("|")
        for line in lines[table_end:next_heading]
    ):
        raise RegistryError(
            f"## {section} contiene más de una tabla o filas separadas"
        )
    table_lines = lines[table_start:table_end]
    if len(table_lines) < 2:
        raise RegistryError(f"tabla incompleta en ## {section}")
    headers = tuple(split_row(table_lines[0]))
    normalized_headers = tuple(normalize(value) for value in headers)
    allowed_headers = (expected_headers, *alternate_headers)
    if normalized_headers not in {
        tuple(normalize(value) for value in candidate)
        for candidate in allowed_headers
    }:
        forbidden = sorted(
            {normalize(value) for value in headers} & FORBIDDEN_AUTHORITY_HEADERS
        )
        if forbidden:
            raise RegistryError(
                f"## {section} contiene columnas de autoridad operativa: {', '.join(forbidden)}"
            )
        raise RegistryError(
            f"columnas inválidas en ## {section}; se esperaban: {', '.join(expected_headers)}"
        )
    separator = split_row(table_lines[1])
    if len(separator) != len(headers) or not all(
        SEPARATOR.fullmatch(cell.replace(" ", "")) for cell in separator
    ):
        raise RegistryError(f"separador de tabla inválido en ## {section}")
    rows: list[dict[str, str]] = []
    for number, line in enumerate(table_lines[2:], start=1):
        cells = split_row(line)
        if len(cells) != len(headers):
            raise RegistryError(
                f"fila {number} de ## {section} tiene {len(cells)} columnas; "
                f"se esperaban {len(headers)}"
            )
        rows.append(dict(zip(headers, cells)))
    return MarkdownTable(table_start, table_end, headers, rows)


def _legacy_value(value: str, label: str, *, default: str = "—") -> str:
    if not value.strip():
        return default
    return clean_cell(value, label)


def migrate_legacy_records(
    table: MarkdownTable, schema: str
) -> MarkdownTable:
    migrated: list[dict[str, str]] = []
    for row in table.rows:
        identifier = row_value(row, "ID")
        source = f"LEGACY:{identifier.upper()}"
        if schema == "legacy-v1":
            old_status = _legacy_value(row_value(row, "Estado"), "estado legacy")
            if old_status == "—":
                tracking = "Migración legacy; estado histórico no informado; sin readback"
            else:
                tracking = (
                    "Migración legacy; estado histórico no autoritativo: "
                    f"{old_status}; sin readback"
                )
            values = (
                identifier,
                row_value(row, "Registro"),
                source,
                tracking,
                _legacy_value(row_value(row, "Conclusión"), "conclusión legacy"),
                _legacy_value(
                    row_value(row, "Acciones derivadas / seguimiento"),
                    "derivados legacy",
                ),
            )
        else:
            values = (
                identifier,
                row_value(row, "Expediente estable"),
                source,
                _legacy_value(
                    row_value(row, "Seguimiento remoto y último readback"),
                    "seguimiento legacy",
                ),
                _legacy_value(
                    row_value(row, "Conclusión / impacto"),
                    "conclusión legacy",
                ),
                _legacy_value(
                    row_value(row, "Derivados y relaciones"),
                    "derivados legacy",
                ),
            )
        migrated.append(dict(zip(RECORD_HEADERS, values)))
    return MarkdownTable(
        table.start,
        table.end,
        RECORD_HEADERS,
        migrated,
    )


def parse_registry(content: str) -> Registry:
    lines = content.splitlines()
    records = parse_table(
        lines,
        "Registros",
        RECORD_HEADERS,
        alternate_headers=(
            LEGACY_RECORD_HEADERS_V1,
            LEGACY_RECORD_HEADERS_WITHOUT_SOURCE,
        ),
    )
    normalized_record_headers = tuple(normalize(value) for value in records.headers)
    if normalized_record_headers == tuple(
        normalize(value) for value in RECORD_HEADERS
    ):
        record_schema = "current"
    elif normalized_record_headers == tuple(
        normalize(value) for value in LEGACY_RECORD_HEADERS_V1
    ):
        record_schema = "legacy-v1"
        records = migrate_legacy_records(records, record_schema)
    else:
        record_schema = "legacy-without-source"
        records = migrate_legacy_records(records, record_schema)
    reservations = parse_table(lines, "Reservas", RESERVATION_HEADERS)
    return Registry(lines, records, reservations, record_schema)


def row_value(row: dict[str, str], header: str) -> str:
    return row[header].strip()


def ensure_root(root: Path) -> Path:
    if root.is_symlink() or not root.is_dir():
        raise RegistryError(f"root debe ser un directorio regular, no symlink: {root}")
    return root.resolve()


def reject_symlink_chain(root: Path, relative: PurePosixPath) -> Path:
    current = root
    for part in relative.parts:
        current = current / part
        if current.exists() or current.is_symlink():
            if current.is_symlink():
                raise RegistryError(f"no se permiten enlaces simbólicos: {current}")
    return current


def registry_path(root: Path) -> Path:
    return reject_symlink_chain(
        root, PurePosixPath("context/incidents/README.md")
    )


def template_content() -> str:
    template = Path(__file__).resolve().parents[1] / "assets" / "incident-index.md"
    if template.is_symlink() or not template.is_file():
        raise RegistryError(f"plantilla de índice ausente o insegura: {template}")
    return template.read_text(encoding="utf-8")


def read_registry(root: Path, *, allow_missing: bool) -> tuple[Path, str, Registry]:
    path = registry_path(root)
    if not path.exists():
        if not allow_missing:
            raise RegistryError(f"registro de incidentes ausente: {path}")
        content = template_content()
        return path, content, parse_registry(content)
    if path.is_symlink() or not path.is_file():
        raise RegistryError(f"registro debe ser un archivo regular: {path}")
    content = path.read_text(encoding="utf-8")
    return path, content, parse_registry(content)


def verify_incident_document(root: Path, path_value: str, identifier: str) -> Path:
    relative = PurePosixPath(safe_record_path(path_value, identifier))
    path = reject_symlink_chain(root, relative)
    try:
        resolved = path.resolve(strict=True)
    except OSError as error:
        raise RegistryError(f"expediente ausente: {path}: {error}") from error
    try:
        resolved.relative_to(root)
    except ValueError as error:
        raise RegistryError(f"expediente fuera del workspace: {path}") from error
    if path.is_symlink() or not path.is_file():
        raise RegistryError(f"expediente debe ser un archivo regular: {path}")
    heading: str | None = None
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("# "):
            heading = line
            break
    match = re.match(r"#\s+(INC-[0-9]{4})(?:\s|—|-)", heading or "")
    if match is None or match.group(1) != identifier:
        raise RegistryError(
            f"el encabezado principal de {path} no coincide con {identifier}"
        )
    return path


def validate_registry(root: Path, registry: Registry, *, verify_files: bool = True) -> None:
    ids: dict[str, str] = {}
    sources: dict[str, str] = {}

    for row in registry.reservations.rows:
        identifier = canonical_id(row_value(row, "ID"))
        if row_value(row, "ID") != identifier:
            raise RegistryError(f"ID reservado debe ser canónico: {row_value(row, 'ID')}")
        scope = clean_cell(row_value(row, "Alcance"), "alcance")
        source = clean_cell(
            row_value(row, "Fuente de reserva serializada"), "fuente de reserva"
        )
        _register_unique(ids, identifier.casefold(), identifier, "ID")
        _register_unique(sources, source.casefold(), source, "fuente")
        del scope

    for row in registry.records.rows:
        identifier = canonical_id(row_value(row, "ID"))
        if row_value(row, "ID") != identifier:
            raise RegistryError(f"ID registrado debe ser canónico: {row_value(row, 'ID')}")
        path_value = safe_record_path(
            row_value(row, "Expediente estable"), identifier
        )
        source = clean_cell(
            row_value(row, "Fuente de reserva serializada"), "fuente de reserva"
        )
        for header in RECORD_HEADERS[3:]:
            clean_cell(row_value(row, header), header)
        _register_unique(ids, identifier.casefold(), identifier, "ID")
        _register_unique(sources, source.casefold(), source, "fuente")
        if verify_files:
            verify_incident_document(root, path_value, identifier)


def _register_unique(
    seen: dict[str, str], key: str, display: str, label: str
) -> None:
    if key in seen:
        raise RegistryError(
            f"{label} duplicado sin distinguir mayúsculas/minúsculas: "
            f"{seen[key]!r} / {display!r}"
        )
    seen[key] = display


def render_table(table: MarkdownTable) -> list[str]:
    rendered = [
        "| " + " | ".join(table.headers) + " |",
        "| " + " | ".join("---" for _ in table.headers) + " |",
    ]
    rendered.extend(
        "| " + " | ".join(row[header] for header in table.headers) + " |"
        for row in table.rows
    )
    return rendered


def render_registry(registry: Registry) -> str:
    replacements = sorted(
        (
            (registry.records.start, registry.records.end, render_table(registry.records)),
            (
                registry.reservations.start,
                registry.reservations.end,
                render_table(registry.reservations),
            ),
        ),
        reverse=True,
    )
    lines = list(registry.lines)
    for start, end, rendered in replacements:
        lines[start:end] = rendered
    return "\n".join(lines) + "\n"


def atomic_write(path: Path, content: str) -> None:
    if path.exists() and (path.is_symlink() or not path.is_file()):
        raise RegistryError(f"destino de registro inseguro: {path}")
    path.parent.mkdir(mode=0o755, parents=False, exist_ok=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{path.name}.", dir=path.parent
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, 0o644)
        if path.exists() and path.is_symlink():
            raise RegistryError(f"destino de registro se convirtió en symlink: {path}")
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


class RegistryLock:
    def __init__(self, root: Path):
        context = reject_symlink_chain(root, PurePosixPath("context"))
        if context.is_symlink() or not context.is_dir():
            raise RegistryError(
                f"context debe existir como directorio regular: {context}"
            )
        self.path = context / LOCK_NAME
        self.descriptor: int | None = None
        self.backend: str | None = None

    def _try_lock(self) -> bool:
        assert self.descriptor is not None
        if fcntl is not None:
            try:
                fcntl.flock(
                    self.descriptor,
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
                self.backend = "fcntl"
                return True
            except BlockingIOError:
                return False
            except OSError as error:
                if error.errno in {errno.EACCES, errno.EAGAIN}:
                    return False
                raise
        if msvcrt is not None:  # pragma: no cover - exercised on Windows
            if os.fstat(self.descriptor).st_size == 0:
                os.write(self.descriptor, b"\0")
                os.fsync(self.descriptor)
            os.lseek(self.descriptor, 0, os.SEEK_SET)
            try:
                msvcrt.locking(self.descriptor, msvcrt.LK_NBLCK, 1)
                self.backend = "msvcrt"
                return True
            except OSError as error:
                if error.errno in {
                    errno.EACCES,
                    errno.EAGAIN,
                    errno.EDEADLK,
                }:
                    return False
                raise
        raise RegistryError("la plataforma no ofrece un lock de archivo soportado")

    def _close(self) -> None:
        if self.descriptor is not None:
            os.close(self.descriptor)
            self.descriptor = None
        self.backend = None

    def __enter__(self) -> "RegistryLock":
        if self.path.is_symlink():
            raise RegistryError(f"lock inseguro (symlink): {self.path}")
        flags = os.O_CREAT | os.O_RDWR
        if hasattr(os, "O_NOFOLLOW"):
            flags |= os.O_NOFOLLOW
        try:
            self.descriptor = os.open(self.path, flags, 0o600)
            descriptor_stat = os.fstat(self.descriptor)
            path_stat = self.path.lstat()
            if (
                not stat.S_ISREG(descriptor_stat.st_mode)
                or stat.S_ISLNK(path_stat.st_mode)
                or descriptor_stat.st_dev != path_stat.st_dev
                or descriptor_stat.st_ino != path_stat.st_ino
            ):
                raise RegistryError(f"lock inseguro o reemplazado: {self.path}")
            deadline = time.monotonic() + LOCK_TIMEOUT_SECONDS
            while not self._try_lock():
                if time.monotonic() >= deadline:
                    raise RegistryError(
                        f"no se pudo adquirir el lock del registro: {self.path}"
                    )
                time.sleep(0.01)
            os.ftruncate(self.descriptor, 0)
            os.write(
                self.descriptor,
                f"pid={os.getpid()} acquired={time.time()}\n".encode("ascii"),
            )
            os.fsync(self.descriptor)
            return self
        except BaseException:
            self._close()
            raise

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        if self.descriptor is None:
            return
        try:
            if self.backend == "fcntl":
                assert fcntl is not None
                fcntl.flock(self.descriptor, fcntl.LOCK_UN)
            elif self.backend == "msvcrt":  # pragma: no cover - Windows
                assert msvcrt is not None
                os.lseek(self.descriptor, 0, os.SEEK_SET)
                msvcrt.locking(self.descriptor, msvcrt.LK_UNLCK, 1)
        finally:
            # The lock file is intentionally persistent.  Removing it would
            # introduce an inode race; the OS releases the advisory lock on
            # close or process death, so stale file contents never block.
            self._close()


def find_by_source(registry: Registry, source: str) -> tuple[str, dict[str, str]] | None:
    wanted = source.casefold()
    for kind, table in (
        ("registered", registry.records),
        ("reserved", registry.reservations),
    ):
        for row in table.rows:
            if row_value(row, "Fuente de reserva serializada").casefold() == wanted:
                return kind, row
    return None


def find_by_id(registry: Registry, identifier: str) -> tuple[str, dict[str, str]] | None:
    wanted = identifier.casefold()
    for kind, table in (
        ("registered", registry.records),
        ("reserved", registry.reservations),
    ):
        for row in table.rows:
            if row_value(row, "ID").casefold() == wanted:
                return kind, row
    return None


def result_from_row(kind: str, row: dict[str, str], *, mode: str) -> dict:
    result = {
        "mode": mode,
        "status": kind,
        "id": row_value(row, "ID"),
        "source": row_value(row, "Fuente de reserva serializada"),
    }
    if kind == "registered":
        result["path"] = row_value(row, "Expediente estable")
    else:
        result["scope"] = row_value(row, "Alcance")
    return result


def next_identifier(registry: Registry) -> str:
    numbers = [
        int(row_value(row, "ID").split("-", 1)[1])
        for table in (registry.records, registry.reservations)
        for row in table.rows
    ]
    next_number = max(numbers, default=0) + 1
    if next_number > 9999:
        raise RegistryError("se agotó el espacio de IDs INC-NNNN")
    return f"INC-{next_number:04d}"


def require_current_schema(registry: Registry, operation: str) -> None:
    if registry.record_schema != "current":
        raise RegistryError(
            f"{operation} requiere el índice INC vigente; ejecutar primero "
            "upgrade en dry-run y luego upgrade --apply"
        )


def preflight_current_schema(
    root: Path, *, allow_missing: bool, operation: str
) -> None:
    _path, _content, registry = read_registry(root, allow_missing=allow_missing)
    validate_registry(root, registry)
    require_current_schema(registry, operation)


def reserve(root: Path, source: str, scope: str, *, apply: bool) -> dict:
    source = clean_cell(source, "fuente")
    scope = clean_cell(scope, "alcance")

    def operation() -> dict:
        path, _content, registry = read_registry(root, allow_missing=True)
        validate_registry(root, registry)
        require_current_schema(registry, "reserve")
        existing = find_by_source(registry, source)
        if existing:
            if (
                existing[0] == "reserved"
                and row_value(existing[1], "Alcance") != scope
            ):
                raise RegistryError(
                    "la fuente ya tiene una reserva con un alcance diferente"
                )
            return result_from_row(
                existing[0], existing[1], mode="unchanged"
            )
        identifier = next_identifier(registry)
        row = dict(zip(RESERVATION_HEADERS, (identifier, scope, source)))
        registry.reservations.rows.append(row)
        validate_registry(root, registry)
        if apply:
            atomic_write(path, render_registry(registry))
        return result_from_row(
            "reserved", row, mode="applied" if apply else "dry-run"
        )

    if not apply:
        return operation()
    preflight_current_schema(root, allow_missing=True, operation="reserve")
    with RegistryLock(root):
        return operation()


def register(
    root: Path,
    identifier: str,
    source: str,
    path_value: str,
    *,
    apply: bool,
) -> dict:
    identifier = canonical_id(identifier)
    source = clean_cell(source, "fuente")
    path_value = safe_record_path(path_value, identifier)

    def operation() -> dict:
        index_path, _content, registry = read_registry(root, allow_missing=False)
        validate_registry(root, registry)
        require_current_schema(registry, "register")
        existing_source = find_by_source(registry, source)
        if existing_source and existing_source[0] == "registered":
            row = existing_source[1]
            if (
                row_value(row, "ID") != identifier
                or row_value(row, "Expediente estable") != path_value
            ):
                raise RegistryError(
                    "la fuente ya está registrada con otro ID o expediente"
                )
            return result_from_row("registered", row, mode="unchanged")
        reservation = find_by_id(registry, identifier)
        if reservation is None or reservation[0] != "reserved":
            raise RegistryError(f"no existe una reserva activa para {identifier}")
        reservation_row = reservation[1]
        if (
            row_value(reservation_row, "Fuente de reserva serializada").casefold()
            != source.casefold()
        ):
            raise RegistryError(
                f"la fuente no coincide con la reserva de {identifier}"
            )
        if existing_source is None or existing_source[1] is not reservation_row:
            raise RegistryError("la fuente no resuelve inequívocamente a la reserva")
        verify_incident_document(root, path_value, identifier)
        reserved_source = row_value(
            reservation_row, "Fuente de reserva serializada"
        )
        registry.reservations.rows = [
            row
            for row in registry.reservations.rows
            if row_value(row, "ID").casefold() != identifier.casefold()
        ]
        record = dict(
            zip(
                RECORD_HEADERS,
                (identifier, path_value, reserved_source, "—", "—", "—"),
            )
        )
        registry.records.rows.append(record)
        registry.records.rows.sort(key=lambda row: row_value(row, "ID"))
        validate_registry(root, registry)
        if apply:
            atomic_write(index_path, render_registry(registry))
        return result_from_row(
            "registered", record, mode="applied" if apply else "dry-run"
        )

    if not apply:
        return operation()
    preflight_current_schema(root, allow_missing=False, operation="register")
    with RegistryLock(root):
        return operation()


def resolve(root: Path, *, identifier: str | None, source: str | None) -> dict:
    _path, _content, registry = read_registry(root, allow_missing=False)
    validate_registry(root, registry)
    if identifier is not None:
        found = find_by_id(registry, canonical_id(identifier))
    else:
        cleaned_source = clean_cell(source or "", "fuente")
        found = find_by_source(registry, cleaned_source)
    if found is None:
        raise RegistryError("incidente no localizado en registros ni reservas")
    result = result_from_row(found[0], found[1], mode="read-only")
    result["schema"] = registry.record_schema
    if registry.record_schema != "current":
        result["schema_upgrade"] = "pending"
    return result


def upgrade(root: Path, *, apply: bool) -> dict:
    def operation() -> dict:
        path, _content, registry = read_registry(root, allow_missing=False)
        validate_registry(root, registry)
        result = {
            "status": "valid",
            "records": len(registry.records.rows),
            "reservations": len(registry.reservations.rows),
            "schema": registry.record_schema,
        }
        if registry.record_schema == "current":
            result["mode"] = "unchanged"
            return result
        result["schema_upgrade_from"] = registry.record_schema
        result["schema_after"] = "current"
        if apply:
            atomic_write(path, render_registry(registry))
            result["mode"] = "applied"
        else:
            result["mode"] = "dry-run"
        return result

    if not apply:
        return operation()
    with RegistryLock(root):
        return operation()


def emit(result: dict, as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, ensure_ascii=False, sort_keys=True))
        return
    if result.get("status") == "valid":
        print(
            "Registro INC válido: "
            f"{result['records']} registros, {result['reservations']} reservas"
        )
    else:
        suffix = f" -> {result['path']}" if "path" in result else ""
        print(
            f"{result['id']}: {result['status']} ({result['mode']}){suffix}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("--root", type=Path, default=Path.cwd())
    validate_parser.add_argument("--json", action="store_true")

    upgrade_parser = subparsers.add_parser("upgrade")
    upgrade_parser.add_argument("--root", type=Path, default=Path.cwd())
    upgrade_parser.add_argument("--apply", action="store_true")
    upgrade_parser.add_argument("--json", action="store_true")

    reserve_parser = subparsers.add_parser("reserve")
    reserve_parser.add_argument("--root", type=Path, default=Path.cwd())
    reserve_parser.add_argument("--source", required=True)
    reserve_parser.add_argument("--scope", required=True)
    reserve_parser.add_argument("--apply", action="store_true")
    reserve_parser.add_argument("--json", action="store_true")

    register_parser = subparsers.add_parser("register")
    register_parser.add_argument("--root", type=Path, default=Path.cwd())
    register_parser.add_argument("--id", required=True)
    register_parser.add_argument("--source", required=True)
    register_parser.add_argument("--path", required=True)
    register_parser.add_argument("--apply", action="store_true")
    register_parser.add_argument("--json", action="store_true")

    resolve_parser = subparsers.add_parser("resolve")
    resolve_parser.add_argument("--root", type=Path, default=Path.cwd())
    lookup = resolve_parser.add_mutually_exclusive_group(required=True)
    lookup.add_argument("--id")
    lookup.add_argument("--source")
    resolve_parser.add_argument("--json", action="store_true")

    args = parser.parse_args()
    try:
        root = ensure_root(args.root)
        if args.command == "validate":
            _path, _content, registry = read_registry(root, allow_missing=False)
            validate_registry(root, registry)
            result = {
                "mode": "read-only",
                "status": "valid",
                "records": len(registry.records.rows),
                "reservations": len(registry.reservations.rows),
                "schema": registry.record_schema,
            }
            if registry.record_schema != "current":
                result["schema_upgrade"] = "pending"
        elif args.command == "upgrade":
            result = upgrade(root, apply=args.apply)
        elif args.command == "reserve":
            result = reserve(
                root, args.source, args.scope, apply=args.apply
            )
        elif args.command == "register":
            result = register(
                root,
                args.id,
                args.source,
                args.path,
                apply=args.apply,
            )
        else:
            result = resolve(
                root, identifier=args.id, source=args.source
            )
        emit(result, args.json)
        return 0
    except (RegistryError, OSError, UnicodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
