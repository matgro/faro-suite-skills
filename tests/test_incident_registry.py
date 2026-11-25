"""Behavioral tests for the serialized FARO incident registry."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "faro/faro-incidentes/scripts/incident_registry.py"
INDEX_TEMPLATE = ROOT / "faro/faro-incidentes/assets/incident-index.md"


class IncidentRegistryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.workspace = Path(self.temporary.name) / "workspace"
        (self.workspace / "context").mkdir(parents=True)

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def run_cli(self, *arguments: str, expect: int = 0) -> subprocess.CompletedProcess[str]:
        result = subprocess.run(
            [sys.executable, "-B", str(SCRIPT), *arguments],
            text=True,
            capture_output=True,
            timeout=20,
        )
        self.assertEqual(result.returncode, expect, result.stdout + result.stderr)
        return result

    def reserve(self, source: str, scope: str = "síntoma", *, apply: bool = True) -> dict:
        arguments = [
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            source,
            "--scope",
            scope,
            "--json",
        ]
        if apply:
            arguments.append("--apply")
        return json.loads(self.run_cli(*arguments).stdout)

    def write_incident(self, identifier: str, slug: str = "fallo-pagos") -> Path:
        path = self.workspace / f"context/incidents/{identifier}-{slug}.md"
        path.write_text(
            f"# {identifier} — Fallo observado\n\n## Evidencia\n\nPendiente.\n",
            encoding="utf-8",
        )
        return path

    def digest(self, path: Path) -> str:
        return hashlib.sha256(path.read_bytes()).hexdigest()

    def test_dry_runs_do_not_create_or_mutate_registry(self) -> None:
        template = INDEX_TEMPLATE.read_text(encoding="utf-8")
        self.assertIn(
            "| ID | Expediente estable | Fuente de reserva serializada |",
            template,
        )
        preview = self.reserve("SRC-monitor-001", apply=False)
        self.assertEqual(preview["mode"], "dry-run")
        self.assertEqual(preview["id"], "INC-0001")
        self.assertFalse((self.workspace / "context/incidents").exists())
        self.assertFalse(
            (self.workspace / "context/.faro-incidents-registry.lock").exists()
        )

        applied = self.reserve("SRC-monitor-001")
        self.assertEqual(applied["mode"], "applied")
        index = self.workspace / "context/incidents/README.md"
        lock = self.workspace / "context/.faro-incidents-registry.lock"
        self.assertTrue(lock.is_file())
        before = self.digest(index)
        lock_before = self.digest(lock)
        second_preview = self.reserve("SRC-monitor-002", apply=False)
        self.assertEqual(second_preview["id"], "INC-0002")
        self.assertEqual(self.digest(index), before)
        self.assertEqual(self.digest(lock), lock_before)

    def test_reserve_register_resolve_are_idempotent_by_source(self) -> None:
        first = self.reserve("SRC-Alert-77", "timeout del proveedor")
        repeated = self.reserve("src-alert-77", "timeout del proveedor")
        self.assertEqual(first["id"], "INC-0001")
        self.assertEqual(repeated["id"], first["id"])
        self.assertEqual(repeated["mode"], "unchanged")

        index = self.workspace / "context/incidents/README.md"
        before_incompatible = self.digest(index)
        self.run_cli(
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            "SRC-ALERT-77",
            "--scope",
            "otro alcance",
            "--apply",
            expect=2,
        )
        self.assertEqual(self.digest(index), before_incompatible)

        incident = self.write_incident(first["id"])
        relative = incident.relative_to(self.workspace).as_posix()
        before = self.digest(index)
        preview = self.run_cli(
            "register",
            "--root",
            str(self.workspace),
            "--id",
            first["id"].lower(),
            "--source",
            "src-alert-77",
            "--path",
            relative,
            "--json",
        )
        self.assertEqual(json.loads(preview.stdout)["mode"], "dry-run")
        self.assertEqual(self.digest(index), before)

        registered = json.loads(
            self.run_cli(
                "register",
                "--root",
                str(self.workspace),
                "--id",
                first["id"],
                "--source",
                "SRC-ALERT-77",
                "--path",
                relative,
                "--apply",
                "--json",
            ).stdout
        )
        self.assertEqual(registered["status"], "registered")
        repeat_register = json.loads(
            self.run_cli(
                "register",
                "--root",
                str(self.workspace),
                "--id",
                first["id"],
                "--source",
                "src-alert-77",
                "--path",
                relative,
                "--apply",
                "--json",
            ).stdout
        )
        self.assertEqual(repeat_register["mode"], "unchanged")

        by_id = json.loads(
            self.run_cli(
                "resolve",
                "--root",
                str(self.workspace),
                "--id",
                "inc-0001",
                "--json",
            ).stdout
        )
        by_source = json.loads(
            self.run_cli(
                "resolve",
                "--root",
                str(self.workspace),
                "--source",
                "SRC-ALERT-77",
                "--json",
            ).stdout
        )
        self.assertEqual(by_id["path"], relative)
        self.assertEqual(by_source["id"], first["id"])
        self.run_cli("validate", "--root", str(self.workspace), "--json")

        index_text = index.read_text(encoding="utf-8")
        self.assertEqual(index_text.count("SRC-Alert-77"), 1)
        self.assertNotIn("| Estado |", index_text)
        self.assertNotIn("| Prioridad |", index_text)
        self.assertNotIn("| Asignado |", index_text)

    def test_concurrent_reservations_are_unique_and_same_source_converges(self) -> None:
        def reserve_processes(sources: list[str]) -> list[dict]:
            processes = [
                subprocess.Popen(
                    [
                        sys.executable,
                        "-B",
                        str(SCRIPT),
                        "reserve",
                        "--root",
                        str(self.workspace),
                        "--source",
                        source,
                        "--scope",
                        "concurrencia",
                        "--apply",
                        "--json",
                    ],
                    text=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                )
                for source in sources
            ]
            results: list[dict] = []
            for process in processes:
                stdout, stderr = process.communicate(timeout=20)
                self.assertEqual(process.returncode, 0, stdout + stderr)
                results.append(json.loads(stdout))
            return results

        sources = [f"SRC-concurrent-{number:02d}" for number in range(12)]
        unique_results = reserve_processes(sources)
        unique_ids = {result["id"] for result in unique_results}
        self.assertEqual(len(unique_ids), len(sources))

        repeated = reserve_processes(["SRC-shared"] * 8)
        self.assertEqual(len({result["id"] for result in repeated}), 1)
        index = self.workspace / "context/incidents/README.md"
        self.assertEqual(index.read_text(encoding="utf-8").count("SRC-shared"), 1)
        self.run_cli("validate", "--root", str(self.workspace))

    def test_stale_lock_file_does_not_block_a_new_writer(self) -> None:
        lock = self.workspace / "context/.faro-incidents-registry.lock"
        lock.write_text("pid=999999 stale=true\n", encoding="utf-8")
        if sys.platform != "win32":
            crashed = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    "-c",
                    (
                        "import fcntl, os, sys; "
                        "stream=open(sys.argv[1], 'r+'); "
                        "fcntl.flock(stream.fileno(), fcntl.LOCK_EX); "
                        "os._exit(17)"
                    ),
                    str(lock),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )
            self.assertEqual(crashed.returncode, 17)

        reserved = self.reserve("SRC-after-crash")

        self.assertEqual(reserved["id"], "INC-0001")
        self.assertEqual(reserved["mode"], "applied")
        self.run_cli("validate", "--root", str(self.workspace))

    def test_legacy_indexes_are_read_only_compatible_and_upgrade_explicitly(self) -> None:
        incidents = self.workspace / "context/incidents"
        incidents.mkdir()
        incident = incidents / "INC-0001-legado.md"
        incident.write_text(
            "# INC-0001 — Incidente legado\n\nEvidencia preservada.\n",
            encoding="utf-8",
        )
        index = incidents / "README.md"
        index.write_text(
            """# Incidentes

## Registros

| ID | Registro | Estado | Conclusión | Acciones derivadas / seguimiento |
| --- | --- | --- | --- | --- |
| INC-0001 | context/incidents/INC-0001-legado.md | CERRADO | causa externa | EXT-7 |

## Reservas

| ID | Alcance | Fuente de reserva serializada |
| --- | --- | --- |
""",
            encoding="utf-8",
        )
        original = self.digest(index)

        validation = json.loads(
            self.run_cli(
                "validate", "--root", str(self.workspace), "--json"
            ).stdout
        )
        self.assertEqual(validation["schema"], "legacy-v1")
        self.assertEqual(validation["schema_upgrade"], "pending")
        by_id = json.loads(
            self.run_cli(
                "resolve",
                "--root",
                str(self.workspace),
                "--id",
                "INC-0001",
                "--json",
            ).stdout
        )
        by_source = json.loads(
            self.run_cli(
                "resolve",
                "--root",
                str(self.workspace),
                "--source",
                "legacy:inc-0001",
                "--json",
            ).stdout
        )
        self.assertEqual(by_id["source"], "LEGACY:INC-0001")
        self.assertEqual(by_source["path"], "context/incidents/INC-0001-legado.md")

        blocked_reserve = self.run_cli(
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            "SRC-nuevo",
            "--scope",
            "nuevo",
            "--apply",
            expect=2,
        )
        blocked_register = self.run_cli(
            "register",
            "--root",
            str(self.workspace),
            "--id",
            "INC-0001",
            "--source",
            "LEGACY:INC-0001",
            "--path",
            "context/incidents/INC-0001-legado.md",
            "--apply",
            expect=2,
        )
        self.assertIn("upgrade", blocked_reserve.stderr)
        self.assertIn("upgrade", blocked_register.stderr)
        self.assertEqual(self.digest(index), original)

        preview = json.loads(
            self.run_cli(
                "upgrade", "--root", str(self.workspace), "--json"
            ).stdout
        )
        self.assertEqual(preview["mode"], "dry-run")
        self.assertEqual(self.digest(index), original)
        self.assertFalse(
            (self.workspace / "context/.faro-incidents-registry.lock").exists()
        )

        applied = json.loads(
            self.run_cli(
                "upgrade",
                "--root",
                str(self.workspace),
                "--apply",
                "--json",
            ).stdout
        )
        self.assertEqual(applied["mode"], "applied")
        upgraded = index.read_text(encoding="utf-8")
        self.assertIn("| ID | Expediente estable | Fuente de reserva serializada |", upgraded)
        self.assertIn("LEGACY:INC-0001", upgraded)
        self.assertIn("estado histórico no autoritativo: CERRADO", upgraded)
        self.assertNotIn("| ID | Registro | Estado |", upgraded)
        current = json.loads(
            self.run_cli(
                "validate", "--root", str(self.workspace), "--json"
            ).stdout
        )
        self.assertEqual(current["schema"], "current")
        unchanged = json.loads(
            self.run_cli(
                "upgrade",
                "--root",
                str(self.workspace),
                "--apply",
                "--json",
            ).stdout
        )
        self.assertEqual(unchanged["mode"], "unchanged")

    def test_legacy_five_column_current_names_also_upgrade(self) -> None:
        incidents = self.workspace / "context/incidents"
        incidents.mkdir()
        (incidents / "INC-0007-legado.md").write_text(
            "# INC-0007 — Legado sin fuente\n", encoding="utf-8"
        )
        index = incidents / "README.md"
        index.write_text(
            """# Incidentes

## Registros

| ID | Expediente estable | Seguimiento remoto y último readback | Conclusión / impacto | Derivados y relaciones |
| --- | --- | --- | --- | --- |
| INC-0007 | context/incidents/INC-0007-legado.md | OFF; sin remoto | no concluyente | — |

## Reservas

| ID | Alcance | Fuente de reserva serializada |
| --- | --- | --- |
""",
            encoding="utf-8",
        )

        validation = json.loads(
            self.run_cli(
                "validate", "--root", str(self.workspace), "--json"
            ).stdout
        )
        self.assertEqual(validation["schema"], "legacy-without-source")
        self.run_cli(
            "upgrade",
            "--root",
            str(self.workspace),
            "--apply",
            "--json",
        )
        self.assertIn("LEGACY:INC-0007", index.read_text(encoding="utf-8"))
        self.run_cli("validate", "--root", str(self.workspace))

    def test_rejects_unsafe_values_duplicates_traversal_and_wrong_heading(self) -> None:
        self.run_cli(
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            "SRC|injected",
            "--scope",
            "x",
            "--apply",
            expect=2,
        )
        self.assertFalse((self.workspace / "context/incidents").exists())
        self.run_cli(
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            "SRC\ninjected",
            "--scope",
            "x",
            "--apply",
            expect=2,
        )
        self.assertFalse((self.workspace / "context/incidents").exists())

        reservation = self.reserve("SRC-safe")
        wrong = self.write_incident("INC-9999")
        target = wrong.with_name("INC-0001-fallo-pagos.md")
        wrong.rename(target)
        index = self.workspace / "context/incidents/README.md"
        before = self.digest(index)
        self.run_cli(
            "register",
            "--root",
            str(self.workspace),
            "--id",
            reservation["id"],
            "--source",
            "SRC-safe",
            "--path",
            "context/incidents/../outside.md",
            "--apply",
            expect=2,
        )
        self.run_cli(
            "register",
            "--root",
            str(self.workspace),
            "--id",
            reservation["id"],
            "--source",
            "SRC-safe",
            "--path",
            target.relative_to(self.workspace).as_posix(),
            "--apply",
            expect=2,
        )
        self.assertEqual(self.digest(index), before)

        text = index.read_text(encoding="utf-8")
        duplicate = "| INC-0002 | otro | src-SAFE |\n"
        text = text.replace(
            "| INC-0001 | síntoma | SRC-safe |\n",
            "| INC-0001 | síntoma | SRC-safe |\n" + duplicate,
        )
        index.write_text(text, encoding="utf-8")
        self.run_cli("validate", "--root", str(self.workspace), expect=2)

    def test_rejects_operational_authority_columns(self) -> None:
        incidents = self.workspace / "context/incidents"
        incidents.mkdir()
        index = incidents / "README.md"
        template = INDEX_TEMPLATE.read_text(encoding="utf-8")
        for header in ("Área", "Backlog", "Cola"):
            with self.subTest(header=header):
                index.write_text(
                    template.replace("Derivados y relaciones", header),
                    encoding="utf-8",
                )
                result = self.run_cli(
                    "validate", "--root", str(self.workspace), expect=2
                )
                self.assertIn("autoridad operativa", result.stderr)

    def test_rejects_symlinked_registry_roots_and_incident_files(self) -> None:
        if not hasattr(Path, "symlink_to"):
            self.skipTest("symlinks unavailable")

        outside = Path(self.temporary.name) / "outside"
        outside.mkdir()
        linked_workspace = Path(self.temporary.name) / "linked-workspace"
        (linked_workspace / "context").mkdir(parents=True)
        try:
            (linked_workspace / "context/incidents").symlink_to(
                outside, target_is_directory=True
            )
        except OSError as error:
            self.skipTest(f"symlinks unavailable: {error}")
        result = subprocess.run(
            [
                sys.executable,
                "-B",
                str(SCRIPT),
                "reserve",
                "--root",
                str(linked_workspace),
                "--source",
                "SRC-linked",
                "--scope",
                "x",
                "--apply",
            ],
            text=True,
            capture_output=True,
        )
        self.assertEqual(result.returncode, 2, result.stdout + result.stderr)
        self.assertEqual(list(outside.iterdir()), [])

        external_lock = outside / "external-lock"
        external_lock.write_text("no usar\n", encoding="utf-8")
        lock = self.workspace / "context/.faro-incidents-registry.lock"
        lock.symlink_to(external_lock)
        self.run_cli(
            "reserve",
            "--root",
            str(self.workspace),
            "--source",
            "SRC-lock-link",
            "--scope",
            "x",
            "--apply",
            expect=2,
        )
        self.assertEqual(external_lock.read_text(encoding="utf-8"), "no usar\n")
        lock.unlink()

        reservation = self.reserve("SRC-file-link")
        external_incident = outside / "real.md"
        external_incident.write_text(
            f"# {reservation['id']} — Fuera\n", encoding="utf-8"
        )
        linked_file = (
            self.workspace
            / f"context/incidents/{reservation['id']}-fuera.md"
        )
        linked_file.symlink_to(external_incident)
        self.run_cli(
            "register",
            "--root",
            str(self.workspace),
            "--id",
            reservation["id"],
            "--source",
            "SRC-file-link",
            "--path",
            linked_file.relative_to(self.workspace).as_posix(),
            "--apply",
            expect=2,
        )

        index = self.workspace / "context/incidents/README.md"
        real_index = outside / "index.md"
        real_index.write_text(INDEX_TEMPLATE.read_text(encoding="utf-8"), encoding="utf-8")
        index.unlink()
        index.symlink_to(real_index)
        self.run_cli("validate", "--root", str(self.workspace), expect=2)


if __name__ == "__main__":
    unittest.main()
