"""Behavioral contract tests for FARO v2 doctor and initialization assets."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"
DOCTOR = FARO / "faro-doctor/scripts/doctor.py"
NOW = "2026-11-17T12:00:00-03:00"


class DoctorV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "workspace"
        self.root.mkdir()

    def snapshot(self) -> dict[str, tuple[str, bytes | None]]:
        snapshot: dict[str, tuple[str, bytes | None]] = {}
        for path in sorted(self.root.rglob("*")):
            relative = path.relative_to(self.root).as_posix()
            if path.is_symlink():
                snapshot[relative] = ("symlink", os.readlink(path).encode())
            elif path.is_file():
                snapshot[relative] = ("file", path.read_bytes())
            elif path.is_dir():
                snapshot[relative] = ("directory", None)
        return snapshot

    def run_doctor(
        self, *arguments: str, doctor: Path = DOCTOR, expect: int = 0
    ) -> subprocess.CompletedProcess[str]:
        before = self.snapshot()
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(doctor),
                "--root",
                str(self.root),
                *arguments,
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        self.assertEqual(self.snapshot(), before, "doctor modificó el workspace")
        return result

    def materialize_current(self, *, external_agents: bool = False) -> None:
        config = json.loads(
            (FARO / "templates/faro-workspace-config.json").read_text(encoding="utf-8")
        )
        for relative in config["requiredDirectories"]:
            (self.root / relative).mkdir(parents=True, exist_ok=True)
        sources = config["templateSources"]
        mapping = {
            "AGENTS.md": sources["agents"],
            config["workspace"]["manifestPath"]: sources["manifest"],
            config["workspace"]["statePath"]: sources["stats"],
            config["workspace"]["indexPath"]: sources["index"],
            config["workspace"]["profilePath"]: sources["projectProfile"],
            config["workspace"]["requirementsCatalogPath"]: sources[
                "requirementsCatalog"
            ],
            config["workspace"]["functionalCatalogPath"]: sources[
                "functionalCatalog"
            ],
        }
        for destination, source in mapping.items():
            target = self.root / destination
            target.parent.mkdir(parents=True, exist_ok=True)
            content = (ROOT / source).read_text(encoding="utf-8")
            if destination == "AGENTS.md" and external_agents:
                content = "# Regla externa\n\nNo borrar.\n\n" + content + "\nOtra regla.\n"
            target.write_text(content, encoding="utf-8")
        stats_path = self.root / config["workspace"]["statePath"]
        stats = json.loads(stats_path.read_text(encoding="utf-8"))
        provenance = json.loads(
            (FARO / "references/suite-provenance.json").read_text(encoding="utf-8")
        )
        stats["faro"]["version"] = provenance["packageVersion"]
        stats["project"] = {
            "name": "Fixture",
            "type": "existing",
            "repositories": [],
        }
        stats["state"] = "initializing"
        stats["updatedAt"] = NOW
        stats_path.write_text(
            json.dumps(stats, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )

    def materialize_legacy(self) -> None:
        (self.root / "context/requirements").mkdir(parents=True)
        (self.root / "AGENTS.md").write_text(
            """# Reglas externas

<!-- FARO:START -->
## FARO — instancia gestionada

- Contrato instalado: FARO `1.13.0`.
- Manifiesto de instancia: `context/faro-workspace.json`.
- Estado e identidad: `context/stats.json`.
- Índice de fuentes: `context/README.md`.
- Configuración específica del proyecto: `context/requirements/project-profile.md`.
<!-- FARO:END -->
""",
            encoding="utf-8",
        )
        manifest = {
            "schemaVersion": 1,
            "contractVersion": "1.13.0",
            "contractSource": "faro/templates/faro-workspace-config.json",
            "managedArtifacts": [
                "AGENTS.md",
                "context/faro-workspace.json",
                "context/stats.json",
                "context/README.md",
                "context/requirements/project-profile.md",
            ],
        }
        stats = {
            "schemaVersion": 1,
            "contractVersion": "1.13.0",
            "faro": {"name": "legacy-fixture", "version": "1.9.4"},
            "project": {"name": "Legacy", "type": "existing", "repositories": []},
            "state": "available",
            "updatedAt": NOW,
        }
        (self.root / "context/faro-workspace.json").write_text(
            json.dumps(manifest), encoding="utf-8"
        )
        (self.root / "context/stats.json").write_text(
            json.dumps(stats), encoding="utf-8"
        )
        (self.root / "context/README.md").write_text(
            "# Índice legacy\n", encoding="utf-8"
        )
        (self.root / "context/requirements/project-profile.md").write_text(
            """---
project: Legacy
profile_version: 1
work_tracking:
  mode: OFF
  provider: null
functional_documentation: DESHABILITADA
updated_at: 2025-01-01T00:00:00Z
---
""",
            encoding="utf-8",
        )
        # 1.13 could have this optional, source-oriented catalog.  Its mere
        # filename is not evidence of the v2 catalog schema.
        (self.root / "context/requirements/functional-documents-catalog.md").write_text(
            "# Documentos funcionales legacy\n\n| ID | Documento |\n| --- | --- |\n",
            encoding="utf-8",
        )

    def test_unrelated_agents_alone_is_absent_and_read_only(self) -> None:
        (self.root / "AGENTS.md").write_text(
            "# Reglas del proyecto\n\nContenido ajeno a FARO.\n", encoding="utf-8"
        )

        result = self.run_doctor()

        self.assertIn("Clasificación del workspace: absent", result.stdout)
        self.assertIn("contenido ajeno preservable", result.stdout)
        self.assertIn("Siguiente ruta recomendada: faro-inicializacion", result.stdout)

    def test_current_v2_with_external_agents_and_dotnet_is_strictly_valid(self) -> None:
        self.materialize_current(external_agents=True)
        (self.root / "src").mkdir()
        (self.root / "src/Fixture.csproj").write_text(
            "<Project Sdk=\"Microsoft.NET.Sdk\" />\n", encoding="utf-8"
        )

        result = self.run_doctor("--strict")

        self.assertIn("Clasificación del workspace: current", result.stdout)
        self.assertIn("Evidencia .NET/C#: detectada", result.stdout)
        self.assertIn("Siguiente ruta recomendada: faro-arq-dotnet", result.stdout)
        self.assertIn("Faltantes/bloqueos: ninguno detectado", result.stdout)

    def test_clean_legacy_is_migratable_and_only_recommends_dry_run(self) -> None:
        self.materialize_legacy()

        result = self.run_doctor()

        self.assertIn("Clasificación del workspace: legacy-migratable", result.stdout)
        self.assertIn("Migración recomendada (dry-run, no escribe)", result.stdout)
        self.assertNotIn("--apply", result.stdout.split("Migración recomendada", 1)[1].splitlines()[0])
        strict = self.run_doctor("--strict", expect=1)
        self.assertIn("legacy-migratable", strict.stdout)

    def test_profile_version_tokens_outside_frontmatter_do_not_change_classification(self) -> None:
        self.materialize_legacy()
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_text(
            "# Perfil dañado\n\n```yaml\nprofile_version: 2\n```\n",
            encoding="utf-8",
        )

        result = self.run_doctor()

        self.assertIn("Clasificación del workspace: corrupt", result.stdout)
        self.assertNotIn("Clasificación del workspace: mixed-ambiguous", result.stdout)

    def test_duplicate_catalog_metadata_is_corrupt(self) -> None:
        self.materialize_current()
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace(
                'schema_version: "2.0"',
                'schema_version: "2.0"\nschema_version: "2.0"',
                1,
            ),
            encoding="utf-8",
        )

        result = self.run_doctor()

        self.assertIn("Clasificación del workspace: corrupt", result.stdout)
        self.assertIn("front matter duplica schema_version", result.stdout)

    def test_mixed_future_and_corrupt_are_distinct(self) -> None:
        self.materialize_legacy()
        shutil.copyfile(
            FARO / "templates/requirements-catalog.md",
            self.root / "context/requirements/requirements-catalog.md",
        )
        mixed = self.run_doctor()
        self.assertIn("Clasificación del workspace: mixed-ambiguous", mixed.stdout)

        shutil.rmtree(self.root)
        self.root.mkdir()
        self.materialize_current()
        for path in (
            self.root / "AGENTS.md",
            self.root / "context/faro-workspace.json",
            self.root / "context/stats.json",
        ):
            if path.suffix == ".md":
                path.write_text(
                    path.read_text(encoding="utf-8").replace("`2.0.0`", "`3.0.0`"),
                    encoding="utf-8",
                )
            else:
                value = json.loads(path.read_text(encoding="utf-8"))
                value["schemaVersion"] = 3
                value["contractVersion"] = "3.0.0"
                path.write_text(json.dumps(value), encoding="utf-8")
        future = self.run_doctor()
        self.assertIn("Clasificación del workspace: future-unsupported", future.stdout)

        shutil.rmtree(self.root)
        self.root.mkdir()
        (self.root / "context").mkdir()
        (self.root / "context/faro-workspace.json").write_bytes(b'{"schemaVersion":')
        corrupt = self.run_doctor()
        self.assertIn("Clasificación del workspace: corrupt", corrupt.stdout)

    def test_unverified_profile_cannot_claim_azure_defaults(self) -> None:
        self.materialize_current()
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_text(
            profile.read_text(encoding="utf-8").replace(
                "      TASK: null", "      TASK: Task", 1
            ),
            encoding="utf-8",
        )

        result = self.run_doctor()

        self.assertIn("Clasificación del workspace: corrupt", result.stdout)
        self.assertIn("tipo remoto TASK=Task", result.stdout)

    def test_package_and_contract_versions_are_independent(self) -> None:
        self.materialize_current()
        suite = Path(self.temporary.name) / "faro-copy"
        shutil.copytree(FARO, suite)
        provenance_path = suite / "references/suite-provenance.json"
        provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
        provenance["packageVersion"] = "9.8.7"
        provenance["ref"] = "refs/tags/v9.8.7"
        provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
        changelog_path = suite / "references/suite-changelog.json"
        changelog = json.loads(changelog_path.read_text(encoding="utf-8"))
        changelog["releases"][0]["version"] = "9.8.7"
        changelog_path.write_text(json.dumps(changelog), encoding="utf-8")

        result = self.run_doctor(
            "--strict", doctor=suite / "faro-doctor/scripts/doctor.py"
        )

        self.assertIn("Clasificación del workspace: current", result.stdout)
        self.assertIn("Matriz de versiones", result.stdout)
        self.assertIn("Suite FARO (paquete distribuido): 9.8.7", result.stdout)
        self.assertIn("Skill principal faro (router): 2.0.0", result.stdout)
        self.assertIn("Contrato instalado en workspace: 2.0.0", result.stdout)
        self.assertIn("Workflow: sin workflow activo", result.stdout)
        self.assertIn("faro.version registrada 2.0.0; paquete actual 9.8.7", result.stdout)
        self.assertIn("Versión canónica esperada: 2.0.0", result.stdout)

    def test_initialization_contract_declares_empty_v2_materialization(self) -> None:
        initialization = (FARO / "faro-inicializacion/SKILL.md").read_text(
            encoding="utf-8"
        )
        profile = (FARO / "templates/project-profile.md").read_text(encoding="utf-8")
        for text in (
            "cuatro directorios",
            "siete archivos obligatorios",
            "requirements-catalog.md",
            "functional-documents-catalog.md",
            "No crear unidades",
            "no crea RM/BUG/TEC/DF/INC",
            "faro.version` desde `references/suite-provenance.json",
        ):
            self.assertIn(text, initialization)
        self.assertNotIn("TASK: Task", profile)
        self.assertNotIn("Microsoft.VSTS.Common.Activity", profile)
        self.assertNotIn("Microsoft.VSTS.Scheduling.RemainingWork", profile)
        self.assertRegex(profile, r"(?m)^\s+estimate: null$")


if __name__ == "__main__":
    unittest.main()
