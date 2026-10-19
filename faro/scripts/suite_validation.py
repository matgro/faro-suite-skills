#!/usr/bin/env python3
"""Read-only validation shared by package checks and workspace diagnostics."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re

SKILL_NAME = re.compile(r"(?:faro(?:-[a-z0-9]+)*|azure-devops-rest-v7)\Z")


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
        for relative in sorted(set(re.findall(r"\[[^\]]+\]\((references/[^)\s#]+)(?:#[^)\s]*)?\)", text))):
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


def validate_suite(suite: Path) -> list[str]:
    names, problems = suite_inventory(suite)
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


def validate_workflow(path: Path, suite: Path) -> list[str]:
    if not path.exists():
        return []
    try:
        workflow = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(workflow, dict):
            return ["workflow: debe ser un objeto JSON"]
        route = workflow.get("nextRoute")
        if route is None:
            return []
        if not isinstance(route, str):
            return ["workflow: nextRoute debe ser un nombre de skill o null"]
        changelog = read_changelog(suite)
        renamed = {old: new for release in changelog["releases"] for old, new in release.get("renamedSkills", {}).items()}
        names, _ = suite_inventory(suite)
        if route in renamed:
            target = renamed[route]
            while target in renamed:
                target = renamed[target]
            return [f"workflow: ruta renombrada {route} -> {target}; requiere autorización explícita para actualizar sólo nextRoute"]
        if route not in names:
            return [f"workflow: nextRoute apunta a skill ausente: {route}"]
    except (OSError, ValueError, TypeError) as error:
        return [f"workflow/changelog inválido: {error}"]
    return []


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
