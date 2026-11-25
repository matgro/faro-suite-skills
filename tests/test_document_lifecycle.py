"""Regression tests for the FARO v2 documentary lifecycle contract."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"


def read(relative: str) -> str:
    return (FARO / relative).read_text(encoding="utf-8")


class DocumentaryLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skills = {
            "functional": read("faro-documentacion-funcional/SKILL.md"),
            "engineering": read("faro-req-ingenieria/SKILL.md"),
            "analysis": read("faro-req-analisis-tecnico/SKILL.md"),
            "ux": read("faro-ux/SKILL.md"),
            "development": read("faro-req-desarrollo/SKILL.md"),
            "qa": read("faro-qa-ejecucion/SKILL.md"),
            "validation": read("faro-req-validacion/SKILL.md"),
            "closure": read("faro-cierre/SKILL.md"),
        }

    def test_every_phase_reads_the_shared_lifecycle_contract(self):
        for name, skill in self.skills.items():
            with self.subTest(skill=name):
                self.assertIn("../references/work-item-lifecycle.md", skill)

    def test_only_closure_invokes_the_freeze_operation(self):
        self.assertIn("work_item_contract.py freeze", self.skills["closure"])
        self.assertIn("--apply", self.skills["closure"])
        self.assertIn("--apply --json", self.skills["closure"])
        self.assertIn("GET HTTPS autenticado", self.skills["closure"])
        for name in ("engineering", "analysis", "ux", "development", "qa", "validation"):
            with self.subTest(skill=name):
                self.assertNotIn("work_item_contract.py freeze", self.skills[name])

    def test_closure_promotes_knowledge_before_done_and_freeze(self):
        closure = self.skills["closure"]
        promotion = closure.index("## Promoción de conocimiento")
        remote_done = closure.index("transicionar el item remoto al estado mapeado como `DONE`")
        freeze_apply = closure.index("--id <ID> --apply --json")
        self.assertLess(promotion, remote_done)
        self.assertLess(remote_done, freeze_apply)
        self.assertIn("faro-int-jira", closure)
        self.assertIn("faro-int-azure-devops", closure)
        self.assertIn("no construir una API paralela", closure)

    def test_new_units_are_canonical_but_migrated_primaries_are_resolved(self):
        lifecycle = read("references/work-item-lifecycle.md")
        self.assertIn("Documento principal", lifecycle)
        self.assertIn("basename histórico con slug", lifecycle)
        for name in ("functional", "engineering", "analysis", "qa"):
            with self.subTest(skill=name):
                self.assertIn("Documento principal", self.skills[name])
                self.assertIn("migrad", self.skills[name].lower())
        for catalog in ("templates/requirements-catalog.md", "templates/functional-documents-catalog.md"):
            with self.subTest(catalog=catalog):
                self.assertIn("almacena sólo el basename", read(catalog))

    def test_local_assets_use_one_canonical_id_and_no_operational_state_field(self):
        assets = [
            "faro-req-ingenieria/assets/rm-lite.md",
            "faro-req-ingenieria/assets/rm-standard.md",
            "faro-req-analisis-tecnico/assets/maintenance-record.md",
            "faro-req-analisis-tecnico/assets/technical-plan.md",
            "faro-req-analisis-tecnico/assets/tasks.md",
            "faro-qa-ejecucion/assets/qa-report.md",
            "faro-req-validacion/assets/validation-report.md",
        ]
        for relative in assets:
            text = read(relative)
            with self.subTest(asset=relative):
                self.assertEqual(text.count("\nwork_item_id:"), 1)
                self.assertNotIn("\nrm_id:", text)
                self.assertNotIn("\nrequirement_status:", text)
                self.assertNotIn("\ndelivery_status:", text)

    def test_validation_exposes_machine_readable_freeze_gates(self):
        report = read("faro-req-validacion/assets/validation-report.md")
        for field in (
            "impact_functional",
            "impact_architecture",
            "impact_operations",
            "impact_reference",
            "required_delivery_evidence",
        ):
            with self.subTest(field=field):
                self.assertIn(f"\n{field}: PENDING", report)
                self.assertIn(field, self.skills["validation"])
        self.assertIn("validationGate", self.skills["closure"])
        self.assertIn("artifact_type: DELIVERY_EVIDENCE", self.skills["closure"])
        self.assertIn("<ID>-entrega.md", self.skills["validation"])

    def test_new_units_use_serialized_reserve_and_register(self):
        for name in ("functional", "engineering", "analysis", "qa"):
            with self.subTest(skill=name):
                self.assertIn("reserve --root <root>", self.skills[name])
                self.assertIn("register --root <root>", self.skills[name])
                self.assertIn("--reservation-source <misma-evidencia>", self.skills[name])

    def test_ux_resolves_the_same_mutable_dossier(self):
        ux = self.skills["ux"]
        self.assertIn("work_item_contract.py resolve", ux)
        self.assertIn("workflow.workItemRef", ux)
        self.assertIn("expediente congelado", ux)
        self.assertIn("estado, prioridad, asignación o backlog", ux)

    def test_documented_flags_exist_in_the_central_cli(self):
        helper = FARO / "scripts/work_item_contract.py"
        expected = {
            "reserve": ("--kind", "--source", "--reserved-at", "--apply", "--json"),
            "register": (
                "--primary", "--reservation-source", "--external-provider",
                "--external-id", "--external-url", "--related", "--domain",
                "--baseline", "--apply", "--json",
            ),
            "freeze": (
                "--apply", "--json",
            ),
            "link-external": (
                "--external-provider", "--external-id", "--external-url", "--apply", "--json",
            ),
        }
        for command, flags in expected.items():
            with self.subTest(command=command):
                result = subprocess.run(
                    [sys.executable, "-B", str(helper), command, "--help"],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                for flag in flags:
                    self.assertIn(flag, result.stdout)
                if command == "freeze":
                    for removed in (
                        "--remote-state", "--readback-at", "--readback-evidence", "--frozen-at",
                    ):
                        self.assertNotIn(removed, result.stdout)

    def test_cli_lifecycle_reserves_registers_freezes_and_detects_mutation(self):
        helper = FARO / "scripts/work_item_contract.py"

        def invoke(root: Path, *arguments: str) -> subprocess.CompletedProcess[str]:
            return subprocess.run(
                [sys.executable, "-B", str(helper), *arguments, "--root", str(root), "--json"],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requirements = root / "context/requirements"
            dossier = requirements / "work-items/RM-0001"
            (requirements / "functional").mkdir(parents=True)
            (requirements / "work-items").mkdir()
            (requirements / "project-profile.md").write_text(
                read("templates/project-profile.md"), encoding="utf-8"
            )
            (requirements / "requirements-catalog.md").write_text(
                read("templates/requirements-catalog.md"), encoding="utf-8"
            )
            (requirements / "functional-documents-catalog.md").write_text(
                read("templates/functional-documents-catalog.md"), encoding="utf-8"
            )

            reserved = invoke(
                root, "reserve", "--kind", "RM", "--source", "test:request:1",
                "--id", "RM-0001", "--reserved-at", "2026-01-01T00:00:00Z", "--apply",
            )
            self.assertEqual(reserved.returncode, 0, reserved.stdout + reserved.stderr)
            self.assertEqual(json.loads(reserved.stdout)["reservation"]["id"], "RM-0001")

            dossier.mkdir()
            primary = dossier / "RM-0001.md"
            primary.write_text(
                "---\n"
                "work_item_id: RM-0001\n"
                "artifact_type: REQUIREMENT_SPEC\n"
                "canonical_path: context/requirements/work-items/RM-0001/RM-0001.md\n"
                "document_version: 1.0\n"
                "---\n"
                "# RM-0001\n\n"
                "### CA-001\n"
                "- Origen: RF-001\n"
                "- Resultado esperado: El comportamiento solicitado queda disponible.\n\n"
                "## Impacto en conocimiento durable\n"
                "| Destino | Delta autorizado | Resolución requerida | Fuente / autorización |\n"
                "| --- | --- | --- | --- |\n"
                "| FUNCTIONAL | — | NO_APLICA | Sin cambio durable. |\n"
                "| ARCHITECTURE | — | NO_APLICA | Sin cambio durable. |\n"
                "| OPERATIONS | — | NO_APLICA | Sin cambio durable. |\n"
                "| REFERENCE | — | NO_APLICA | Sin cambio durable. |\n\n"
                "## Operaciones de entrega requeridas\n"
                "| Operación | Origen del alcance |\n"
                "| --- | --- |\n",
                encoding="utf-8",
            )
            registered = invoke(
                root, "register", "--id", "RM-0001", "--primary",
                "context/requirements/work-items/RM-0001/RM-0001.md",
                "--reservation-source", "test:request:1", "--external-provider", "JIRA",
                "--external-id", "FARO-1", "--external-url", "https://tracker.example/browse/FARO-1",
                "--apply",
            )
            self.assertEqual(registered.returncode, 0, registered.stdout + registered.stderr)
            entry = json.loads(registered.stdout)["entry"]
            self.assertEqual(entry["primaryDocument"], "RM-0001.md")
            self.assertEqual(
                entry["primaryPath"], "context/requirements/work-items/RM-0001/RM-0001.md"
            )

            validation = dossier / "RM-0001-validacion.md"
            (dossier / "evidence-ca-001.txt").write_text("evidencia verificable\n", encoding="utf-8")
            validation.write_text(
                "---\n"
                "work_item_id: RM-0001\n"
                "artifact_type: VALIDATION_REPORT\n"
                "canonical_path: context/requirements/work-items/RM-0001/RM-0001-validacion.md\n"
                "document_version: 1.0\n"
                "validated_primary_version: 1.0\n"
                f"validated_primary_sha256: {hashlib.sha256(primary.read_bytes()).hexdigest()}\n"
                "validation_outcome: VERIFIED\n"
                "impact_functional: NOT_APPLICABLE\n"
                "impact_architecture: NOT_APPLICABLE\n"
                "impact_operations: NOT_APPLICABLE\n"
                "impact_reference: NOT_APPLICABLE\n"
                "required_delivery_evidence: NOT_APPLICABLE\n"
                "---\n"
                "# Validación\n\n"
                "## Resultado por criterio\n\n"
                "| CA | Origen | Resultado esperado | Método | Resultado observado | Evidencia local | Estado |\n"
                "|---|---|---|---|---|---|---|\n"
                "| CA-001 | RF-001 | El comportamiento solicitado queda disponible. | Prueba automatizada | El comportamiento solicitado queda disponible. | evidence-ca-001.txt | CONFORME |\n\n"
                "## Ejecuciones verificadas\n\n"
                "| Ejecución | Entorno | Resultado | Evidencia local | Fecha y zona |\n"
                "|---|---|---|---|---|\n\n"
                "## Hallazgos de validación\n\n"
                "| Hallazgo | Tipo | Descripción | Elementos | Evidencia local | Acción | Bloquea |\n"
                "|---|---|---|---|---|---|---|\n\n"
                "## Promoción de conocimiento durable\n\n"
                "| Destino | Delta validado | Resultado | Ruta durable | Versión / baseline | Evidencia | Justificación |\n"
                "|---|---|---|---|---|---|---|\n"
                "| FUNCTIONAL | — | NO_APLICA | — | — | — | No modifica el contrato funcional. |\n"
                "| ARCHITECTURE | — | NO_APLICA | — | — | — | No introduce decisiones arquitectónicas. |\n"
                "| OPERATIONS | — | NO_APLICA | — | — | — | No modifica la operación. |\n"
                "| REFERENCE | — | NO_APLICA | — | — | — | No requiere referencia durable adicional. |\n\n"
                "## Operaciones de entrega requeridas\n\n"
                "| Operación | Origen del alcance |\n"
                "|---|---|\n\n"
                "## Decisión de entrega\n\n"
                "| Resultado | Justificación |\n"
                "|---|---|\n"
                "| NOT_APPLICABLE | La prueba no requiere una operación externa. |\n",
                encoding="utf-8",
            )

            preview = invoke(root, "freeze", "--id", "RM-0001")
            self.assertEqual(preview.returncode, 0, preview.stdout + preview.stderr)
            self.assertEqual(json.loads(preview.stdout)["mode"], "dry-run")
            marker = dossier / "RM-0001-cierre.json"
            self.assertFalse(marker.exists())

            missing_readback = invoke(root, "freeze", "--id", "RM-0001", "--apply")
            self.assertNotEqual(missing_readback.returncode, 0)
            self.assertIn("required", missing_readback.stderr.lower())

            declarative_readback = invoke(
                root, "freeze", "--id", "RM-0001", "--remote-state", "DONE", "--apply",
            )
            self.assertNotEqual(declarative_readback.returncode, 0)
            self.assertIn("unrecognized arguments", declarative_readback.stderr.lower())
            self.assertFalse(marker.exists())

    def test_default_branch_supports_rm_bug_and_tec(self):
        development = self.skills["development"]
        self.assertIn("feature/<ID>-<descripcion-kebab-case>", development)
        self.assertIn("prefijo RM, BUG o TEC", development)
        self.assertNotIn("feature/<RM-ID>-<descripcion-kebab-case>", development)

    def test_closed_dossiers_require_successors_instead_of_reopening(self):
        closure = self.skills["closure"]
        self.assertIn("expediente congelado", closure)
        self.assertIn("sucesor", closure)
        self.assertIn("No existe cierre local bajo seguimiento `OFF`", closure)


if __name__ == "__main__":
    unittest.main()
