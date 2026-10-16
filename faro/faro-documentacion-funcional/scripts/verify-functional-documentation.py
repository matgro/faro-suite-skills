#!/usr/bin/env python3
"""Verify FARO functional-documentation routing and document-ID integrity."""
from __future__ import annotations

import argparse
import re
from collections import defaultdict
from pathlib import Path

DF_FILENAME = re.compile(r"^df-(\d+)-.+\.md$", re.IGNORECASE)
DF_FRONT_MATTER = re.compile(r"^df_id:\s*[\"']?([^\"'\n]+)", re.MULTILINE | re.IGNORECASE)
CATALOG_ID = re.compile(r"^\|\s*(DF-\d+)\s*\|", re.IGNORECASE)


def require_text(path: Path, snippets: list[str], failures: list[str]) -> None:
    if not path.is_file():
        failures.append(f"missing file: {path}")
        return

    text = path.read_text(encoding="utf-8")
    for snippet in snippets:
        if snippet not in text:
            failures.append(f"missing required text in {path}: {snippet!r}")


def canonical_id(raw: str) -> str:
    return raw.strip().upper()


def catalog_document_ids(catalog: Path) -> list[str]:
    if not catalog.is_file():
        return []

    active_section = False
    identifiers: list[str] = []
    for line in catalog.read_text(encoding="utf-8").splitlines():
        if line.startswith("## "):
            active_section = line.strip().lower() == "## documentos"
            continue
        if active_section:
            match = CATALOG_ID.match(line)
            if match:
                identifiers.append(canonical_id(match.group(1)))
    return identifiers


def verify_document_ids(requirements: Path, failures: list[str]) -> None:
    documents: dict[str, list[tuple[Path, bool]]] = defaultdict(list)

    for path in sorted(requirements.glob("[dD][fF]-*.md")):
        filename_match = DF_FILENAME.match(path.name)
        if filename_match is None:
            continue

        df_id = f"DF-{filename_match.group(1)}"
        internal_note = path.stem.lower().endswith("-investigacion-interna")
        text = path.read_text(encoding="utf-8")
        metadata_match = DF_FRONT_MATTER.search(text)
        if metadata_match and canonical_id(metadata_match.group(1)) != df_id:
            failures.append(
                f"DF ID mismatch: {path.name} declares {metadata_match.group(1)!r}, expected {df_id!r} from its filename"
            )
        documents[df_id].append((path, internal_note))

    catalog = requirements / "functional-documents-catalog.md"
    catalog_ids = catalog_document_ids(catalog)
    for df_id, entries in documents.items():
        deliverables = [path.name for path, internal in entries if not internal]
        internal_notes = [path.name for path, internal in entries if internal]
        if len(deliverables) != 1:
            failures.append(
                f"duplicate or missing deliverable for {df_id}: {', '.join(deliverables) or 'none'}"
            )
        if len(internal_notes) > 1:
            failures.append(
                f"multiple internal notes for {df_id}: {', '.join(internal_notes)}"
            )
        if internal_notes and not deliverables:
            failures.append(f"internal note without deliverable for {df_id}: {internal_notes[0]}")
        if catalog.is_file() and catalog_ids.count(df_id) != 1:
            failures.append(
                f"catalog must list {df_id} exactly once in ## Documentos; found {catalog_ids.count(df_id)}"
            )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("project_root", type=Path)
    args = parser.parse_args()
    root = args.project_root.resolve()
    failures: list[str] = []

    ed_router = Path(__file__).resolve().parents[1] / "SKILL.md"
    require_text(ed_router, ["faro-documentacion-funcional", "Para una solicitud de cambio", "no crear RM"], failures)
    require_text(root / "AGENTS.md", ["Con documentación funcional `HABILITADA`"], failures)
    require_text(root / "context/requirements/project-profile.md", ["## Documentación funcional", "**Estado:** `HABILITADA`"], failures)
    requirements = root / "context/requirements"
    require_text(requirements / "functional-documents-catalog.md", ["## Reservas", "## Documentos"], failures)
    verify_document_ids(requirements, failures)

    if failures:
        print("FAIL")
        print("\n".join(f"- {failure}" for failure in failures))
        return 1

    print("PASS: functional-documentation routing and document IDs are valid.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
