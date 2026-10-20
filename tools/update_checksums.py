#!/usr/bin/env python3
"""Regenerate the integrity inventory while maintaining a new FARO release."""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package-root", type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument("--normalize-line-endings", action="store_true", help="Explicitly convert runtime text CRLF to LF when preparing a NEW release, never when verifying one.")
    args = parser.parse_args()
    root = args.package_root.resolve()
    suite = root / "faro"
    if not (suite / "SKILL.md").is_file():
        parser.error(f"missing {suite / 'SKILL.md'}")
    files = sorted((path for path in suite.rglob("*") if path.is_file() and path.name != ".DS_Store"), key=lambda path: path.relative_to(root).as_posix())
    normalized = 0
    if args.normalize_line_endings:
        for path in files:
            if path.suffix not in {".md", ".py", ".json", ".txt", ".yaml", ".yml"}:
                continue
            original = path.read_bytes()
            updated = original.replace(b"\r\n", b"\n")
            if updated != original:
                path.write_bytes(updated)
                normalized += 1
    lines = [f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.relative_to(root).as_posix()}\n" for path in files]
    with (root / "checksums.sha256").open("w", encoding="utf-8", newline="\n") as checksum_file:
        checksum_file.write("".join(lines))
    print(f"OK: {len(files)} checksums generated; {normalized} runtime text files normalized to LF")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
