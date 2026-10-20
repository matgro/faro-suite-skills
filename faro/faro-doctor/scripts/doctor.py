#!/usr/bin/env python3
"""Read-only FARO workspace diagnostics."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

SKILL_ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = SKILL_ROOT / "templates" / "faro-workspace-config.json"
PROVENANCE_PATH = SKILL_ROOT / "references" / "suite-provenance.json"
EXTERNAL_SKILLS_PATH = SKILL_ROOT / "references" / "laravel-external-skills.json"

sys.dont_write_bytecode = True
sys.path.insert(0, str(SKILL_ROOT / "scripts"))
from suite_validation import validate_suite, validate_workflow


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

    suite_problems = validate_suite(SKILL_ROOT)
    workflow_problems = validate_workflow(root / "context/workflow.json", SKILL_ROOT)
    problems: list[str] = suite_problems + workflow_problems
    provenance, _ = load_json(PROVENANCE_PATH)
    package_version = provenance.get("packageVersion", "no registrada") if provenance else "no registrada"
    print(f"Versión del paquete de skills: {package_version} (independiente del contrato {expected_version})")
    print("Coherencia local de la suite: " + ("inválida" if suite_problems else "válida"))
    print(f"Historial de actualización: {SKILL_ROOT / 'references/suite-changelog.json'}")
    origin_error: str | None = None
    if args.verify_suite_origin:
        origin, origin_error = verify_suite_origin()
        print(f"Origen Git de la suite: {origin}")
        if origin_error:
            problems.append(f"origen Git de la suite: {origin_error}")
    else:
        print("Origen Git de la suite: no comprobado (usar --verify-suite-origin)")
    if args.check_external_skills:
        problems.extend(check_external_skills())
    else:
        print("Skills externas Laravel: no comprobadas (usar --check-external-skills)")
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
        print(f"Seguimiento de trabajo: {profile_value(content, 'mode')}")
        print(f"Proveedor de seguimiento: {profile_value(content, 'provider')}")
        print(f"Documentación funcional del proyecto: {profile_value(content, 'functional_documentation')}")
    architectures = [root / "context/architecture-laravel.md", root / "context/architecture-mobile.md", root / "context/architecture.md"]
    print("Arquitectura registrada: " + (next((item.name for item in architectures if item.exists()), "no registrada")))
    workflow = root / "context/workflow.json"
    print("Workflow activo: " + ("sí" if workflow.exists() else "no"))

    if stats and stats.get("state") == "disabled":
        recommendation = "detener FARO"
    elif suite_problems or origin_error:
        recommendation = "actualizar la suite completa mediante bootstrap, con comparación y confirmación; no reinicializar el workspace"
    elif workflow_problems:
        recommendation = "revisar el workflow y el changelog; autorizar sólo una corrección identificada, sin reinicializar ni modificar aprobaciones"
    elif not exists:
        recommendation = "faro-inicializacion"
    elif problems:
        recommendation = "faro-inicializacion sólo con autorización explícita de reparación"
    elif stats and stats.get("state") in {"new", "initializing"}:
        profile_content = profile.read_text(encoding="utf-8", errors="replace") if profile.exists() else ""
        mode = profile_value(profile_content, "mode")
        provider = profile_value(profile_content, "provider")
        if mode == "REQUIRED" and provider == "JIRA":
            recommendation = "faro-int-jira"
        elif mode == "REQUIRED" and provider == "AZURE_DEVOPS":
            recommendation = "faro-int-azure-devops"
        else:
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
