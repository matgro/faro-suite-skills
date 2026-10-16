#!/usr/bin/env python3
"""Validate the portable FARO skill-suite package without third-party modules."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS_ROOT = ROOT / "faro"
BOOTSTRAP = ROOT / "bootstrap" / "SKILL.md"
MANIFEST = ROOT / "manifest.json"
CHECKSUMS = ROOT / "checksums.sha256"
SECRET_PATTERNS = {
    "private key": r"-----BEGIN (?:[A-Z ]*PRIVATE KEY|OPENSSH PRIVATE KEY)-----",
    "credential URL": r"https?://[^\s/@:]+:[^\s/@]+@",
    "AWS key": r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b",
    "GitHub token": r"\bgh[pousr]_[A-Za-z0-9_]{20,}\b",
    "GitLab token": r"\bglpat-[A-Za-z0-9_-]{20,}\b",
    "Slack token": r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b",
    "JWT": r"\beyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\b",
}


def fail(message: str) -> None:
    print(f"FAIL: {message}", file=sys.stderr)
    raise SystemExit(1)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def skill_name(path: Path) -> str | None:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---\n"):
        return None
    match = re.search(r"^name:\s*([^\s#]+)\s*$", text, re.MULTILINE)
    return match.group(1) if match else None


def files_under(root: Path) -> dict[Path, Path]:
    return {
        path.relative_to(root): path
        for path in root.rglob("*")
        if path.is_file() and path.name != ".DS_Store"
    }


def read_checksums() -> dict[Path, str]:
    if not CHECKSUMS.is_file():
        fail("missing checksums.sha256")
    entries: dict[Path, str] = {}
    for number, line in enumerate(CHECKSUMS.read_text(encoding="utf-8").splitlines(), 1):
        match = re.fullmatch(r"([0-9a-f]{64})  (faro/.+)", line)
        if not match:
            fail(f"invalid checksum entry at line {number}")
        relative = Path(match.group(2))
        if relative in entries:
            fail(f"duplicate checksum entry: {relative}")
        entries[relative] = match.group(1)
    return entries


def validate_checksums(tree: Path, expected: dict[Path, str]) -> int:
    actual = files_under(tree)
    actual_with_prefix = {Path("faro") / relative: path for relative, path in actual.items()}
    if set(actual_with_prefix) != set(expected):
        fail("checksummed file paths differ from tree")
    changed = [str(rel) for rel, path in actual_with_prefix.items() if sha256(path) != expected[rel]]
    if changed:
        fail("checksum mismatch: " + ", ".join(changed))
    return len(actual)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--installed-at", type=Path, help="Compare a copied faro/ tree byte-for-byte.")
    args = parser.parse_args()

    if not SKILLS_ROOT.is_dir() or not (SKILLS_ROOT / "SKILL.md").is_file():
        fail("missing faro/SKILL.md")
    if not BOOTSTRAP.is_file() or skill_name(BOOTSTRAP) != "faro-bootstrap":
        fail("missing or invalid bootstrap/SKILL.md")
    try:
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"invalid manifest.json: {exc}")

    expected_skills = set(manifest.get("skills", []))
    actual_paths = sorted(SKILLS_ROOT.rglob("SKILL.md"))
    actual_skills = {skill_name(path) for path in actual_paths}
    if None in actual_skills:
        fail("a runtime SKILL.md is missing YAML frontmatter or a name field")
    if actual_skills != expected_skills:
        fail(f"manifest skills mismatch; missing={sorted(expected_skills - actual_skills)}, extra={sorted(actual_skills - expected_skills)}")
    bootstrap = manifest.get("bootstrap", {})
    if manifest.get("entrypoint") != "faro" or skill_name(SKILLS_ROOT / "SKILL.md") != "faro":
        fail("entrypoint must be faro/SKILL.md")
    if bootstrap.get("path") != "bootstrap/SKILL.md" or bootstrap.get("name") != "faro-bootstrap":
        fail("manifest bootstrap declaration is invalid")

    checksums = read_checksums()
    count = validate_checksums(SKILLS_ROOT, checksums)
    for path in list(files_under(SKILLS_ROOT).values()) + [BOOTSTRAP]:
        if path.suffix in {".md", ".py", ".json", ".txt", ".yaml", ".yml"}:
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, pattern in SECRET_PATTERNS.items():
                if re.search(pattern, text, re.IGNORECASE):
                    fail(f"possible {label} in {path.relative_to(ROOT)}")

    if args.installed_at:
        installed = args.installed_at.resolve()
        if not installed.is_dir():
            fail(f"installed path does not exist: {installed}")
        validate_checksums(installed, checksums)
        print(f"OK: installed tree matches checksums ({count} files)")

    print(f"OK: {len(actual_skills)} runtime skills, bootstrap, {count} distributable files, manifest, checksums, and basic secret scan validated")


if __name__ == "__main__":
    main()
