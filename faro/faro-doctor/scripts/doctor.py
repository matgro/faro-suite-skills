#!/usr/bin/env python3
"""Read-only FARO workspace diagnostics."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = SKILL_ROOT / "templates" / "faro-workspace-config.json"


def load_json(path: Path) -> tuple[dict | None, str | None]:
    if not path.exists():
        return None, "ausente"
    try:
        return json.loads(path.read_text(encoding="utf-8")), None
    except Exception as error:
        return None, f"inválido: {error}"


def profile_value(text: str, key: str) -> str:
    match = re.search(rf"^\s*{re.escape(key)}:\s*(.+)$", text, flags=re.MULTILINE)
    return match.group(1).strip() if match else "no registrado"


def main() -> int:
    parser = argparse.ArgumentParser(description="Diagnostica un workspace FARO sin modificarlo.")
    parser.add_argument("--root", type=Path, default=Path.cwd(), help="Root coordinador a inspeccionar.")
    parser.add_argument("--strict", action="store_true", help="Falla si falta o es inválido un requisito obligatorio.")
    args = parser.parse_args()
    root = args.root.resolve()
    config, config_error = load_json(CONFIG_PATH)
    if config_error:
        print(f"ERROR: configuración canónica {config_error}: {CONFIG_PATH}")
        return 2

    required = [Path(item) for item in config["requiredFiles"]]
    expected_artifacts = [str(item) for item in config["requiredFiles"]]
    expected_version = config["contractVersion"]
    expected_source = "faro/templates/faro-workspace-config.json"
    agents = root / "AGENTS.md"
    exists = agents.exists() or any((root / item).exists() for item in required[1:])
    print(f"Espacio FARO existente: {'sí' if exists else 'no'}")
    print(f"Root inspeccionado: {root}")
    print(f"Versión canónica esperada: {expected_version}")

    problems: list[str] = []
    print("Archivos requeridos:")
    for relative in required:
        path = root / relative
        if not path.exists():
            status = "ausente"
            problems.append(f"{relative}: ausente")
        elif path.suffix == ".json":
            _, error = load_json(path)
            status = error or "presente"
            if error:
                problems.append(f"{relative}: {error}")
        else:
            status = "presente"
        print(f"- {relative}: {status}")

    if agents.exists():
        text = agents.read_text(encoding="utf-8", errors="replace")
        starts, ends = text.count("<!-- FARO:START -->"), text.count("<!-- FARO:END -->")
        agent_status = "válido" if starts == ends == 1 else f"inválido (START={starts}, END={ends})"
        print(f"Bloque FARO de AGENTS.md: {agent_status}")
        if starts != ends or starts != 1:
            problems.append("AGENTS.md: bloque FARO delimitado inválido")

    manifest, manifest_error = load_json(root / "context/faro-workspace.json")
    stats, stats_error = load_json(root / "context/stats.json")
    if manifest:
        installed = manifest.get("contractVersion", "no registrado")
        compatibility = "coincide" if installed == expected_version else "no coincide"
        print(f"Versión instalada: {installed} ({compatibility})")
        print(f"Origen declarado: {manifest.get('contractSource', 'no registrado')}")
        if compatibility != "coincide":
            problems.append("manifiesto: versión de contrato no coincide")
        if manifest.get("contractSource") != expected_source:
            problems.append("manifiesto: origen del contrato no coincide")
        if manifest.get("managedArtifacts") != expected_artifacts:
            problems.append("manifiesto: artefactos instalados no coinciden")
    elif manifest_error:
        problems.append(f"manifiesto: {manifest_error}")

    if stats:
        print(f"Estado: {stats.get('state', 'no registrado')}")
        print(f"Proyecto: {stats.get('project', {}).get('name', 'no registrado')}")
        print(f"FARO instalado: {stats.get('faro', {}).get('version', 'no registrado')}")
        if stats.get("contractVersion") != expected_version:
            problems.append("stats.json: contractVersion no coincide")
    elif stats_error:
        problems.append(f"stats.json: {stats_error}")

    profile = root / "context/requirements/project-profile.md"
    if profile.exists():
        content = profile.read_text(encoding="utf-8", errors="replace")
        print(f"Jira del proyecto: {profile_value(content, 'mode')}")
        print(f"Documentación funcional del proyecto: {profile_value(content, 'functional_documentation')}")
    architectures = [root / "context/architecture-laravel.md", root / "context/architecture-mobile.md", root / "context/architecture.md"]
    print("Arquitectura registrada: " + (next((item.name for item in architectures if item.exists()), "no registrada")))
    workflow = root / "context/workflow.json"
    print("Workflow activo: " + ("sí" if workflow.exists() else "no"))

    if not exists:
        recommendation = "faro-inicializacion"
    elif problems:
        recommendation = "faro-inicializacion sólo con autorización explícita de reparación"
    elif stats and stats.get("state") in {"new", "initializing"}:
        recommendation = "faro-arq-laravel, faro-arq-mobile o faro-arq-generica según evidencia"
    elif stats and stats.get("state") == "disabled":
        recommendation = "detener FARO"
    else:
        recommendation = "seguir la ruta FARO del pedido actual"
    print("Faltantes/bloqueos: " + ("; ".join(problems) if problems else "ninguno detectado"))
    print(f"Siguiente ruta recomendada: {recommendation}")
    return 1 if args.strict and problems else 0


if __name__ == "__main__":
    raise SystemExit(main())
