#!/usr/bin/env python3
"""Verify FARO functional-documentation routing and document-ID integrity."""
from __future__ import annotations

import argparse
import re
from pathlib import Path
import unicodedata

DF_DIRECTORY = re.compile(r"^DF-(\d{3})$")
DF_PRIMARY_FILENAME = re.compile(r"^DF-(\d{3})(?:[-.].*)?\.md$")
CATALOG_ID = re.compile(r"^DF-\d{3}$")
DOCUMENT_HEADERS = [
    "ID", "Ruta canónica", "Documento principal", "Fuente de reserva serializada",
    "Dominio o proceso", "Versión / baseline", "Relacionados",
]
RESERVATION_HEADERS = ["ID", "Fuente de reserva serializada", "Fecha y zona"]


def require_text(path: Path, snippets: list[str], failures: list[str]) -> None:
    if path.is_symlink():
        failures.append(f"symlink is not allowed: {path}")
        return
    if not path.is_file():
        failures.append(f"missing file: {path}")
        return

    text = path.read_text(encoding="utf-8")
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"missing required text in {path}: {snippet!r}")


def normalize_header(raw: str) -> str:
    decomposed = unicodedata.normalize("NFKD", raw)
    return " ".join(
        "".join(character for character in decomposed if not unicodedata.combining(character))
        .lower()
        .split()
    )


def catalog_rows(catalog: Path, section: str, failures: list[str]) -> list[dict[str, str]]:
    if catalog.is_symlink() or not catalog.is_file():
        return []
    active = False
    table: list[list[str]] = []
    for line in catalog.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            if active:
                break
            active = normalize_header(line[3:]) == normalize_header(section)
            continue
        if active and line.lstrip().startswith("|"):
            table.append([cell.strip() for cell in line.strip().strip("|").split("|")])

    if len(table) < 2:
        failures.append(f"missing Markdown table in ## {section}: {catalog}")
        return []
    if len(table[1]) != len(table[0]) or not all(
        re.fullmatch(r":?-{3,}:?", value.replace(" ", "")) for value in table[1]
    ):
        failures.append(f"invalid Markdown separator in ## {section}: {catalog}")
        return []
    headers = [normalize_header(value) for value in table[0]]
    expected = DOCUMENT_HEADERS if normalize_header(section) == "documentos" else RESERVATION_HEADERS
    expected_normalized = [normalize_header(value) for value in expected]
    if headers != expected_normalized:
        failures.append(
            f"catalog columns in ## {section} must be exactly {expected}: {catalog}"
        )
        return []
    rows: list[dict[str, str]] = []
    for number, values in enumerate(table[2:], start=1):
        if len(values) != len(headers):
            failures.append(f"invalid row {number} in ## {section}: {catalog}")
            continue
        rows.append(dict(zip(headers, values)))
    return rows


def catalog_documents(
    catalog: Path,
    root: Path,
    failures: list[str],
    seen_ids: set[str],
    seen_sources: dict[str, str],
    published_bindings: dict[str, str],
) -> dict[str, tuple[Path, Path]]:
    documents: dict[str, tuple[Path, Path]] = {}
    for row in catalog_rows(catalog, "Documentos", failures):
        identifier = row["id"].strip()
        if not CATALOG_ID.fullmatch(identifier):
            failures.append(f"invalid functional document ID in catalog: {row['id']!r}")
            continue
        if identifier in documents:
            failures.append(f"duplicate functional document ID in catalog: {identifier}")
            continue
        seen_ids.add(identifier.casefold())
        source = row["fuente de reserva serializada"].strip()
        source_key = source.casefold()
        if not source or source in {"-", "—"}:
            failures.append(f"published DF without serialized reservation source: {identifier}")
        elif source_key in seen_sources:
            failures.append(
                f"duplicate DF reservation source: {source!r} "
                f"({seen_sources[source_key]} / {identifier})"
            )
        else:
            seen_sources[source_key] = identifier
            published_bindings[identifier] = source

        related = row["relacionados"].strip()
        for token in re.findall(r"(?i)(?<![A-Za-z0-9])df-[0-9]{3}(?![0-9])", related):
            if token != token.upper():
                failures.append(
                    f"non-canonical DF token in Relacionados for {identifier}: {token!r}"
                )

        expected_directory = Path("context/requirements/functional") / identifier
        directory_value = Path(row["ruta canonica"])
        if directory_value != expected_directory:
            failures.append(
                f"catalog path mismatch for {identifier}: {directory_value.as_posix()!r}, "
                f"expected {expected_directory.as_posix()!r}"
            )

        primary_value = Path(row["documento principal"])
        if primary_value.is_absolute() or ".." in primary_value.parts:
            failures.append(f"unsafe primary document for {identifier}: {primary_value}")
            continue
        if len(primary_value.parts) != 1 or primary_value.name != row["documento principal"]:
            failures.append(f"primary document must be a basename for {identifier}: {primary_value}")
            continue
        primary_relative = expected_directory / primary_value
        match = DF_PRIMARY_FILENAME.fullmatch(primary_relative.name)
        if (
            match is None
            or f"DF-{match.group(1)}" != identifier
            or primary_relative.stem.casefold().endswith("-investigacion-interna")
        ):
            failures.append(f"primary filename does not match {identifier}: {primary_relative.name}")
            continue
        documents[identifier] = (root / expected_directory, root / primary_relative)
    return documents


def verify_catalog_reservations(
    catalog: Path,
    failures: list[str],
    seen_ids: set[str],
    seen_sources: dict[str, str],
    published_bindings: dict[str, str],
) -> None:
    rows = catalog_rows(catalog, "Reservas", failures)
    seen: set[str] = set()
    bound: set[str] = set()
    for row in rows:
        identifier = row.get("id", "").strip()
        if not CATALOG_ID.fullmatch(identifier):
            failures.append(f"invalid/non-canonical DF reservation ID: {identifier!r}")
            continue
        folded = identifier.casefold()
        if identifier in seen:
            failures.append(f"duplicate DF reservation ID: {identifier}")
        seen.add(identifier)
        source = row.get("fuente de reserva serializada", "").strip()
        if not source or source in {"-", "—"}:
            failures.append(f"DF reservation without serialized source: {identifier}")
        elif identifier in published_bindings:
            if identifier in bound:
                failures.append(f"duplicate preserved DF source binding: {identifier}")
            elif source != published_bindings[identifier]:
                failures.append(
                    f"preserved DF source binding mismatch for {identifier}: "
                    f"{source!r} / {published_bindings[identifier]!r}"
                )
            bound.add(identifier)
        elif folded in seen_ids:
            failures.append(f"duplicate DF reservation ID: {identifier}")
        elif source.casefold() in seen_sources:
            failures.append(
                f"duplicate DF reservation source: {source!r} "
                f"({seen_sources[source.casefold()]} / {identifier})"
            )
        else:
            seen_sources[source.casefold()] = identifier
            seen_ids.add(folded)
    for identifier in sorted(set(published_bindings) - bound):
        failures.append(f"published DF lacks preserved reservation source binding: {identifier}")


def frontmatter_df_id(path: Path, failures: list[str]) -> str | None:
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        failures.append(f"missing front matter: {path}")
        return None
    try:
        end = next(index for index in range(1, len(lines)) if lines[index].strip() == "---")
    except StopIteration:
        failures.append(f"unclosed front matter: {path}")
        return None
    values: list[str] = []
    for line in lines[1:end]:
        match = re.fullmatch(r"df_id:\s*(.*?)\s*", line)
        if match:
            raw = match.group(1)
            if not raw:
                failures.append(f"empty df_id in {path}")
                continue
            if raw[0] in {'\"', "'"}:
                if len(raw) < 2 or raw[-1] != raw[0]:
                    failures.append(f"mismatched df_id quotes in {path}: {raw!r}")
                    continue
                value = raw[1:-1]
            elif '"' in raw or "'" in raw:
                failures.append(f"invalid df_id quoting in {path}: {raw!r}")
                continue
            else:
                value = raw
            values.append(value)
        elif re.match(r"(?i)^df_id\s*:", line):
            failures.append(f"df_id key must use exact lowercase spelling in {path}: {line!r}")
    if len(values) != 1:
        failures.append(f"front matter must declare df_id exactly once: {path}")
        return None
    return values[0]


def verify_mermaid_blocks(path: Path, text: str, failures: list[str]) -> None:
    """Keep optional Mermaid diagrams readable and structurally complete in a DF."""
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        if lines[index].strip().lower() != "```mermaid":
            index += 1
            continue

        start = index + 1
        index += 1
        while index < len(lines) and not lines[index].strip().startswith("```"):
            index += 1
        if index == len(lines):
            failures.append(f"Mermaid sin cierre en {path.name}")
            return

        body = [line.strip() for line in lines[start:index] if line.strip()]
        if not body:
            failures.append(f"Mermaid vacío en {path.name}")
        elif not body[0].startswith(("flowchart", "stateDiagram-v2", "sequenceDiagram")):
            failures.append(f"tipo Mermaid no permitido en {path.name}: {body[0]!r}")
        index += 1


def verify_document_ids(root: Path, functional: Path, catalog: Path, failures: list[str]) -> None:
    if functional.is_symlink():
        failures.append(f"functional root cannot be a symlink: {functional}")
        return
    if not functional.is_dir():
        failures.append(f"missing directory: {functional}")
        return

    seen_catalog_ids: set[str] = set()
    seen_sources: dict[str, str] = {}
    published_bindings: dict[str, str] = {}
    documents = catalog_documents(
        catalog, root, failures, seen_catalog_ids, seen_sources, published_bindings,
    )
    verify_catalog_reservations(
        catalog, failures, seen_catalog_ids, seen_sources, published_bindings,
    )
    discovered: set[str] = set()

    for directory in sorted(functional.iterdir()):
        if directory.name.startswith("."):
            failures.append(f"hidden entry is not allowed in functional root: {directory}")
            continue
        if not directory.is_dir() or directory.is_symlink():
            failures.append(f"invalid entry in functional root: {directory}")
            continue
        directory_match = DF_DIRECTORY.fullmatch(directory.name)
        if directory_match is None:
            failures.append(f"invalid functional document directory: {directory}")
            continue

        df_id = f"DF-{directory_match.group(1)}"
        discovered.add(df_id)
        catalog_entry = documents.get(df_id)
        if catalog_entry is None:
            failures.append(f"functional document is not cataloged: {directory}")
            continue
        catalog_directory, primary = catalog_entry
        if directory.resolve() != catalog_directory.resolve():
            failures.append(f"catalog directory mismatch for {df_id}: {catalog_directory}")

        if primary.is_symlink():
            failures.append(f"primary document cannot be a symlink: {primary}")
        elif not primary.is_file():
            failures.append(f"missing deliverable for {df_id}: {primary}")
        else:
            text = primary.read_text(encoding="utf-8")
            declared = frontmatter_df_id(primary, failures)
            if declared is not None and declared != df_id:
                failures.append(
                    f"DF ID mismatch: {primary.name} declares {declared!r}, expected {df_id!r}"
                )
            try:
                primary_lines = primary.read_text(encoding="utf-8").splitlines()
                end = next(index for index in range(1, len(primary_lines)) if primary_lines[index].strip() == "---")
                canonical_values = [
                    match.group(1).strip().strip('"\'')
                    for line in primary_lines[1:end]
                    if (match := re.fullmatch(r"canonical_path:\s*(.*?)\s*", line))
                ]
            except (OSError, StopIteration):
                canonical_values = []
            if canonical_values:
                expected_path = primary.relative_to(root).as_posix()
                if len(canonical_values) != 1 or canonical_values[0] != expected_path:
                    failures.append(
                        f"canonical_path mismatch for {df_id}: {canonical_values!r}, expected {expected_path!r}"
                    )
            verify_mermaid_blocks(primary, text, failures)

        internal_notes: list[Path] = []
        for markdown in directory.glob("*.md"):
            if markdown == primary:
                continue
            if markdown.is_symlink():
                failures.append(f"DF artifact cannot be a symlink: {markdown}")
                continue
            recognizable = re.match(r"^df-", markdown.name, flags=re.IGNORECASE) is not None
            try:
                encoded_identity = re.search(
                    r"(?im)^df_id\s*:", markdown.read_text(encoding="utf-8"),
                ) is not None
            except (OSError, UnicodeError) as error:
                failures.append(f"cannot read DF artifact {markdown}: {error}")
                continue
            canonical_prefix = re.match(rf"^{re.escape(df_id)}(?=[-.])", markdown.name) is not None
            if (recognizable or encoded_identity) and not canonical_prefix:
                failures.append(
                    f"DF artifact basename must use canonical uppercase delimited prefix {df_id}: "
                    f"{markdown.name}"
                )
            if recognizable or encoded_identity:
                declared = frontmatter_df_id(markdown, failures)
                if declared is not None and declared != df_id:
                    failures.append(
                        f"DF ID mismatch: {markdown.name} declares {declared!r}, expected {df_id!r}"
                    )
            if canonical_prefix and markdown.stem.casefold().endswith("-investigacion-interna"):
                internal_notes.append(markdown)
        if len(internal_notes) > 1:
            failures.append(
                f"multiple internal investigations for {df_id}: "
                + ", ".join(note.name for note in internal_notes)
            )

    for df_id, (directory, _primary) in documents.items():
        if df_id not in discovered:
            failures.append(f"catalog points to missing functional directory: {directory}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    failures: list[str] = []

    ed_router = Path(__file__).resolve().parents[1] / "SKILL.md"
    require_text(ed_router, ["faro-documentacion-funcional", "Para una solicitud de cambio", "no crear RM"], failures)
    profile = root / "context/requirements/project-profile.md"
    if profile.is_symlink():
        failures.append(f"symlink is not allowed: {profile}")
    elif not profile.is_file():
        failures.append(f"missing file: {profile}")
    else:
        profile_text = profile.read_text(encoding="utf-8")
        if re.search(
            r"^functional_documentation:\s*[\"']?HABILITADA[\"']?\s*$",
            profile_text,
            re.MULTILINE,
        ) is None:
            failures.append(f"functional documentation is not HABILITADA in {profile}")
    requirements = root / "context/requirements"
    functional = requirements / "functional"
    catalog = requirements / "functional-documents-catalog.md"
    require_text(catalog, ["## Reservas", "## Documentos", "Documento principal"], failures)
    for legacy in requirements.glob("[dD][fF]-*.md"):
        failures.append(f"flat legacy functional document requires migration: {legacy}")
    verify_document_ids(root, functional, catalog, failures)

    if failures:
        print("FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("PASS: functional-documentation routing and document IDs are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
