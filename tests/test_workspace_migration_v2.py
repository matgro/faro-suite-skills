from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "faro/scripts/migrate_workspace_v2.py"
SPEC = importlib.util.spec_from_file_location("migrate_workspace_v2_tests", SCRIPT)
assert SPEC and SPEC.loader
MIGRATION = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = MIGRATION
SPEC.loader.exec_module(MIGRATION)


LEGACY_AGENTS = """# External instructions

Keep this line.

<!-- FARO:START -->
## FARO legacy
- Contrato instalado: FARO `1.13.0`.
<!-- FARO:END -->

External tail.
"""

LEGACY_PROFILE = """---
project: Example
profile_version: 1
work_tracking:
  mode: REQUIRED
  provider: JIRA
  authorization_source: human
  credential_status: VERIFICADO
  jira:
    base_url: https://tracker.invalid
    project_key: EX
    workflow_mapping:
      PENDING: Open
      DOING: Doing
      DONE: Done
      CANCELLED: Cancelled
  azure_devops:
    organization_url: null
    project: null
    area_path: null
    team: null
    iteration_path: null
    work_item_type: Task
    workflow_mapping:
      PENDING: New
      DOING: Active
      DONE: Closed
      CANCELLED: Removed
functional_documentation: HABILITADA
updated_at: 2026-01-01T00:00:00Z
---
# Perfil legado
"""


class WorkspaceMigrationV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        requirements = self.root / "context/requirements"
        requirements.mkdir(parents=True)
        (self.root / "AGENTS.md").write_text(LEGACY_AGENTS, encoding="utf-8")
        (self.root / "context/README.md").write_text("# Index\n\nOriginal index.\n", encoding="utf-8")
        (requirements / "project-profile.md").write_text(LEGACY_PROFILE, encoding="utf-8")
        (self.root / "context/faro-workspace.json").write_text(json.dumps({
            "schemaVersion": 1,
            "contractVersion": "1.13.0",
            "contractSource": "faro/templates/faro-workspace-config.json",
            "managedArtifacts": [
                "AGENTS.md", "context/faro-workspace.json", "context/stats.json",
                "context/README.md", "context/requirements/project-profile.md",
            ],
        }), encoding="utf-8")
        (self.root / "context/stats.json").write_text(json.dumps({
            "schemaVersion": 1,
            "contractVersion": "1.13.0",
            "faro": {"name": "ED_INSTANCE", "version": "1.13.0"},
            "project": {"name": "Example", "type": "Laravel", "repositories": []},
            "state": "available",
            "updatedAt": "2026-01-01T00:00:00Z",
        }), encoding="utf-8")
        (self.root / "context/workflow.json").write_text(json.dumps({
            "schemaVersion": 1,
            "updatedAt": "2026-01-01T00:00:00Z",
            "active": "RM-0001",
            "phase": "analysis",
            "authorization": {"status": "approved", "source": "human", "artifactVersion": "1.0", "scope": "RM-0001"},
            "currentUnit": {"id": "RM-0001", "status": "DOING"},
            "waitingOn": None,
            "nextRoute": "faro-req-analisis-tecnico",
            "notes": ["continue from evidence"],
        }), encoding="utf-8")
        (requirements / "functional-documents-catalog.md").write_text(
            "# Legacy DF catalog\n\n"
            "## Reservas\n\n"
            "| ID | Fuente | Fecha |\n| --- | --- | --- |\n"
            "| DF-002 | human:future | 2026-01-02T00:00:00Z |\n\n"
            "## Documentos\n\n"
            "| ID | Nombre |\n| --- | --- |\n| DF-001 | Orders |\n",
            encoding="utf-8",
        )
        self.rm_primary = requirements / "RM-0001-checkout.md"
        self.rm_primary.write_text(
            "---\nrm_id: \"RM-0001\"\nartifact_type: \"REQUIREMENT_SPEC\"\n---\n# RM original\n",
            encoding="utf-8",
        )
        (requirements / "RM-0001-plan-tecnico.md").write_text(
            "---\nwork_item_id: \"RM-0001\"\nartifact_type: \"TECHNICAL_PLAN\"\n---\n# Plan\n",
            encoding="utf-8",
        )
        self.rm_screenshot = requirements / "RM-0001-screenshot.png"
        self.rm_screenshot.write_bytes(b"\x89PNG\r\n\x1a\nlegacy-evidence")
        self.bug_primary = requirements / "BUG-0001.md"
        self.bug_primary.write_bytes(b"# Historical BUG without front matter\n\x00bytes-preserved\n")
        self.df_primary = requirements / "DF-001-orders.md"
        self.df_primary.write_text(
            "---\ndf_id: \"DF-001\"\nartifact_type: \"FUNCTIONAL_DOCUMENT\"\n---\n# Orders\n",
            encoding="utf-8",
        )
        (requirements / "DF-001-orders-investigacion-interna.md").write_text(
            "---\ndf_id: \"DF-001\"\nartifact_type: \"FUNCTIONAL_INVESTIGATION\"\n---\n# Internal\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def snapshot(self) -> dict[str, bytes]:
        return {
            path.relative_to(self.root).as_posix(): path.read_bytes()
            for path in self.root.rglob("*") if path.is_file() and not path.is_symlink()
        }

    def test_dry_run_writes_nothing(self) -> None:
        before = self.snapshot()
        plan = MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        self.assertEqual(plan.classification, "legacy-migratable")
        self.assertEqual(self.snapshot(), before)
        self.assertEqual(len(plan.moves), 6)
        self.assertIn("context/faro-migration-v2.json", plan.writes)

    def test_apply_preserves_bytes_groups_files_and_is_idempotent(self) -> None:
        rm_bytes = self.rm_primary.read_bytes()
        screenshot_bytes = self.rm_screenshot.read_bytes()
        bug_bytes = self.bug_primary.read_bytes()
        df_bytes = self.df_primary.read_bytes()
        plan = MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        result = MIGRATION.apply_plan(plan)
        self.assertEqual(result["mode"], "applied")
        rm_target = self.root / "context/requirements/work-items/RM-0001/RM-0001-checkout.md"
        bug_target = self.root / "context/requirements/work-items/BUG-0001/BUG-0001.md"
        df_target = self.root / "context/requirements/functional/DF-001/DF-001-orders.md"
        self.assertEqual(rm_target.read_bytes(), rm_bytes)
        self.assertEqual(
            (self.root / "context/requirements/work-items/RM-0001/RM-0001-screenshot.png").read_bytes(),
            screenshot_bytes,
        )
        self.assertEqual(bug_target.read_bytes(), bug_bytes)
        self.assertEqual(df_target.read_bytes(), df_bytes)
        self.assertFalse(self.rm_primary.exists())
        catalog = (self.root / "context/requirements/requirements-catalog.md").read_text(encoding="utf-8")
        self.assertIn("RM-0001-checkout.md", catalog)
        self.assertIn("BUG-0001.md", catalog)
        self.assertNotIn("| Estado |", catalog)
        functional_catalog = (self.root / "context/requirements/functional-documents-catalog.md").read_text(encoding="utf-8")
        self.assertIn("DF-001-orders.md", functional_catalog)
        self.assertIn("DF-002", functional_catalog)
        self.assertIn("migration:1.13.0:DF-001:", functional_catalog)
        self.assertIn("migration:1.13.0:RM-0001:", catalog)
        workflow = json.loads((self.root / "context/workflow.json").read_text(encoding="utf-8"))
        self.assertEqual(workflow["workItemRef"]["id"], "RM-0001")
        self.assertNotIn("active", workflow)
        self.assertNotIn("currentUnit", workflow)
        record = json.loads((self.root / "context/faro-migration-v2.json").read_text(encoding="utf-8"))
        self.assertEqual(record["legacyPrimaryExceptions"][0]["id"], "BUG-0001")
        self.assertEqual(record["mappingReconciliation"], "PENDING")
        self.assertIn("contentBase64", record["snapshots"]["context/workflow.json"])
        report = MIGRATION.contract.validate_layout(self.root)
        self.assertEqual(report.errors, [])
        self.assertIn("legacy-primary-exception", {issue.code for issue in report.issues if issue.severity == "info"})
        self.assertNotIn("legacy-primary-exception", {issue.code for issue in report.warnings})
        stats = json.loads((self.root / "context/stats.json").read_text(encoding="utf-8"))
        self.assertEqual(stats["faro"]["version"], MIGRATION.suite_package_version())
        repeated = MIGRATION.build_plan(self.root, "2026-11-17T12:10:00-03:00")
        self.assertEqual(repeated.classification, "current")
        self.assertEqual(MIGRATION.apply_plan(repeated)["mode"], "already-current")
        stats["contractVersion"] = "1.13.0"
        (self.root / "context/stats.json").write_text(json.dumps(stats), encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "parcial/incoherente"):
            MIGRATION.build_plan(self.root)

    def test_ambiguous_primary_blocks_without_changes(self) -> None:
        ambiguous = self.root / "context/requirements/RM-0001-other.md"
        ambiguous.write_text(
            "---\nwork_item_id: \"RM-0001\"\nartifact_type: \"REQUIREMENT_SPEC\"\n---\n# Other\n",
            encoding="utf-8",
        )
        before = self.snapshot()
        with self.assertRaisesRegex(MIGRATION.MigrationError, "múltiples primarios"):
            MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        self.assertEqual(self.snapshot(), before)

    def test_mixed_layout_and_future_contract_are_rejected(self) -> None:
        mixed = self.root / "context/requirements/work-items/RM-9999"
        mixed.mkdir(parents=True)
        (mixed / "RM-9999.md").write_text("x", encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "layout mixto"):
            MIGRATION.build_plan(self.root)
        (mixed / "RM-9999.md").unlink()
        mixed.rmdir()
        (mixed.parent).rmdir()
        manifest = self.root / "context/faro-workspace.json"
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        payload["contractVersion"] = "9.0.0"
        manifest.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "no migrable/no degradable"):
            MIGRATION.build_plan(self.root)

    def test_case_collision_is_rejected(self) -> None:
        collision = self.root / "context/requirements/bug-0001.md"
        try:
            collision.write_text("collision", encoding="utf-8")
        except OSError:
            self.skipTest("case-insensitive filesystem cannot create collision fixture")
        if collision.samefile(self.bug_primary):
            self.skipTest("case-insensitive filesystem")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "case-insensitive"):
            MIGRATION.build_plan(self.root)

    def test_lowercase_recognizable_artifact_is_not_silently_ignored(self) -> None:
        lower = self.root / "context/requirements/tec-0001.md"
        lower.write_text("# legacy lower\n", encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "no canónico"):
            MIGRATION.build_plan(self.root)

    def test_lowercase_df_reservation_and_flat_directory_block_without_changes(self) -> None:
        catalog = self.root / "context/requirements/functional-documents-catalog.md"
        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace("DF-002", "df-002"),
            encoding="utf-8",
        )
        before = self.snapshot()
        with self.assertRaisesRegex(MIGRATION.MigrationError, "inválido/no canónico"):
            MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        self.assertEqual(self.snapshot(), before)

        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace("df-002", "DF-002"),
            encoding="utf-8",
        )
        orphan = self.root / "context/requirements/RM-9999"
        orphan.mkdir()
        before = self.snapshot()
        with self.assertRaisesRegex(MIGRATION.MigrationError, "no es archivo regular"):
            MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        self.assertEqual(self.snapshot(), before)

    def test_workflow_operational_dict_and_profile_overlay_block_preflight(self) -> None:
        workflow = self.root / "context/workflow.json"
        payload = json.loads(workflow.read_text(encoding="utf-8"))
        payload["waitingOn"] = {"nested": {"assigned_to": "someone"}}
        workflow.write_text(json.dumps(payload), encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "clave operativa"):
            MIGRATION.build_plan(self.root)
        payload["waitingOn"] = None
        workflow.write_text(json.dumps(payload), encoding="utf-8")
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_text(profile.read_text(encoding="utf-8").replace(
            "  mode: REQUIRED", "  mode: REQUIRED\n  operational_state_authority: EXTERNAL_WORK_TRACKER",
        ), encoding="utf-8")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "overlay v2"):
            MIGRATION.build_plan(self.root)

    def test_active_incident_workflow_is_preserved_as_registered_pointer(self) -> None:
        incidents = self.root / "context/incidents"
        incidents.mkdir()
        incident_path = "context/incidents/INC-0001-timeout.md"
        (self.root / incident_path).write_text("# INC-0001 — Timeout\n", encoding="utf-8")
        (incidents / "README.md").write_text(
            "# Incidentes\n\n## Registros\n\n"
            "| ID | Expediente estable | Fuente de reserva serializada | Seguimiento remoto y último readback | Conclusión / impacto | Derivados y relaciones |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| INC-0001 | {incident_path} | legacy:incident | JIRA EX-7 | pendiente | — |\n\n"
            "## Reservas\n\n| ID | Alcance | Fuente de reserva serializada |\n"
            "| --- | --- | --- |\n",
            encoding="utf-8",
        )
        workflow = self.root / "context/workflow.json"
        payload = json.loads(workflow.read_text(encoding="utf-8"))
        payload["active"] = "INC-0001"
        payload["currentUnit"] = {"id": "INC-0001", "status": "DOING"}
        workflow.write_text(json.dumps(payload), encoding="utf-8")

        plan = MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        projected = json.loads(plan.writes["context/workflow.json"].decode("utf-8"))
        self.assertEqual(
            projected["workItemRef"], {"id": "INC-0001", "path": incident_path},
        )
        MIGRATION.apply_plan(plan)
        report = MIGRATION.contract.validate_layout(self.root)
        self.assertEqual(report.errors, [])
        self.assertNotIn("INC-0001", report.work_items)

    def test_profile_tokens_in_body_are_not_rewritten_as_frontmatter(self) -> None:
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_text(
            profile.read_text(encoding="utf-8")
            + "\nLiteral body evidence: profile_version: 1 and updated_at: never.\n",
            encoding="utf-8",
        )
        plan = MIGRATION.build_plan(self.root, "2026-11-17T12:00:00-03:00")
        migrated = plan.writes["context/requirements/project-profile.md"].decode("utf-8")
        self.assertIn("Literal body evidence: profile_version: 1 and updated_at: never.", migrated)
        self.assertEqual(migrated.split("---", 2)[1].count("profile_version: 2"), 1)

    def test_invalid_utf8_profile_is_reported_as_migration_error(self) -> None:
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_bytes(b"---\nprofile_version: 1\n---\n\xff")
        with self.assertRaisesRegex(MIGRATION.MigrationError, "no es UTF-8"):
            MIGRATION.build_plan(self.root)


if __name__ == "__main__":
    unittest.main()
