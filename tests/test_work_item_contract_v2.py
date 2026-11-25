from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "faro/scripts/work_item_contract.py"
TEMPLATES = ROOT / "faro/templates"
SPEC = importlib.util.spec_from_file_location("work_item_contract_v2", SCRIPT)
assert SPEC and SPEC.loader
CONTRACT = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = CONTRACT
SPEC.loader.exec_module(CONTRACT)


class WorkItemContractV2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        requirements = self.root / "context/requirements"
        (requirements / "functional").mkdir(parents=True)
        (requirements / "work-items").mkdir()
        shutil.copyfile(TEMPLATES / "requirements-catalog.md", requirements / "requirements-catalog.md")
        shutil.copyfile(TEMPLATES / "functional-documents-catalog.md", requirements / "functional-documents-catalog.md")
        shutil.copyfile(TEMPLATES / "project-profile.md", requirements / "project-profile.md")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def create_primary(self, identifier: str, *, extra_identity: bool = False) -> Path:
        dossier = self.root / f"context/requirements/work-items/{identifier}"
        dossier.mkdir()
        extra = f"\n{identifier.split('-', 1)[0].lower()}_id: \"{identifier}\"" if extra_identity else ""
        primary = dossier / f"{identifier}.md"
        primary.write_text(
            f"---\nwork_item_id: \"{identifier}\"{extra}\n"
            "artifact_type: \"REQUIREMENT_SPEC\"\n"
            "document_version: \"1.0\"\n"
            f"---\n# {identifier}\n\n"
            "### CA-001 — Resultado verificable\n"
            "- Origen: RF-001\n"
            "- Resultado esperado: returns 200\n"
            "- Método previsto: automated test\n\n"
            "## Impacto en conocimiento durable\n"
            "| Destino | Delta autorizado | Resolución requerida | Fuente / autorización |\n"
            "| --- | --- | --- | --- |\n"
            "| FUNCTIONAL | — | NO_APLICA | Alcance aprobado sin cambio funcional durable. |\n"
            "| ARCHITECTURE | — | NO_APLICA | Alcance aprobado sin decisión arquitectónica. |\n"
            "| OPERATIONS | — | NO_APLICA | Alcance aprobado sin cambio operativo. |\n"
            "| REFERENCE | — | NO_APLICA | Alcance aprobado sin cambio de referencia. |\n\n"
            "## Operaciones de entrega requeridas\n"
            "| Operación | Origen del alcance |\n"
            "| --- | --- |\n",
            encoding="utf-8",
        )
        return primary

    def write_valid_validation(self, primary: Path, *, delivery: bool = False) -> Path:
        identifier = primary.parent.name
        if delivery and "| commit | Solicitud autorizada de commit. |" not in primary.read_text(encoding="utf-8"):
            primary.write_text(
                primary.read_text(encoding="utf-8").replace(
                    "| Operación | Origen del alcance |\n| --- | --- |\n",
                    "| Operación | Origen del alcance |\n| --- | --- |\n"
                    "| commit | Solicitud autorizada de commit. |\n",
                ),
                encoding="utf-8",
            )
        evidence = primary.parent / "evidence-ca-001.txt"
        evidence.write_text("verified execution output\n", encoding="utf-8")
        delivery_value = "SATISFIED" if delivery else "NOT_APPLICABLE"
        validation = primary.parent / f"{identifier}-validacion.md"
        validation.write_text(
            "---\n"
            f"work_item_id: \"{identifier}\"\n"
            "artifact_type: \"VALIDATION_REPORT\"\n"
            f"canonical_path: \"context/requirements/work-items/{identifier}/{identifier}-validacion.md\"\n"
            "document_version: \"1.0\"\n"
            "validated_primary_version: \"1.0\"\n"
            f"validated_primary_sha256: {CONTRACT.sha256(primary)}\n"
            "validation_outcome: VERIFIED\n"
            "impact_functional: NOT_APPLICABLE\n"
            "impact_architecture: NOT_APPLICABLE\n"
            "impact_operations: NOT_APPLICABLE\n"
            "impact_reference: NOT_APPLICABLE\n"
            f"required_delivery_evidence: {delivery_value}\n"
            "---\n# Validación\n\n"
            "## Resultado por criterio\n"
            "| CA | Origen | Resultado esperado | Método | Resultado observado | Evidencia local | Estado |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| CA-001 | RF-001 | returns 200 | automated test | returned 200 | evidence-ca-001.txt | CONFORME |\n\n"
            "## Ejecuciones verificadas\n"
            "| Ejecución | Entorno | Resultado | Evidencia local | Fecha y zona |\n"
            "| --- | --- | --- | --- | --- |\n\n"
            "## Hallazgos de validación\n"
            "| Hallazgo | Tipo | Descripción | Elementos | Evidencia local | Acción | Bloquea |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n\n"
            "## Promoción de conocimiento durable\n"
            "| Destino | Delta validado | Resultado | Ruta durable | Versión / baseline | Evidencia | Justificación |\n"
            "| --- | --- | --- | --- | --- | --- | --- |\n"
            "| FUNCTIONAL | — | NO_APLICA | — | — | — | No cambia comportamiento funcional. |\n"
            "| ARCHITECTURE | — | NO_APLICA | — | — | — | No hay decisión arquitectónica durable. |\n"
            "| OPERATIONS | — | NO_APLICA | — | — | — | No cambia la operación vigente. |\n"
            "| REFERENCE | — | NO_APLICA | — | — | — | No cambia contratos ni referencia. |\n\n"
            "## Operaciones de entrega requeridas\n"
            "| Operación | Origen del alcance |\n"
            "| --- | --- |\n"
            + ("| commit | Solicitud autorizada de commit. |\n" if delivery else "")
            + "\n"
            "## Decisión de entrega\n"
            "| Resultado | Justificación |\n"
            "| --- | --- |\n"
            f"| {delivery_value} | "
            + ("La entrega requerida está acreditada." if delivery else "El alcance no requiere operación de entrega.")
            + " |\n",
            encoding="utf-8",
        )
        if delivery:
            delivery_evidence = primary.parent / "delivery-proof.txt"
            delivery_evidence.write_text("commit abc123 verified\n", encoding="utf-8")
            (primary.parent / f"{identifier}-entrega.md").write_text(
                "---\n"
                f"work_item_id: \"{identifier}\"\n"
                "artifact_type: \"DELIVERY_EVIDENCE\"\n"
                f"canonical_path: \"context/requirements/work-items/{identifier}/{identifier}-entrega.md\"\n"
                "document_version: \"1.0\"\n"
                "delivery_outcome: SATISFIED\n"
                "---\n# Entrega\n\n"
                "## Operaciones verificadas\n"
                "| Operación | Resultado | Referencia | Evidencia local | Fecha y zona |\n"
                "| --- | --- | --- | --- | --- |\n"
                "| commit | SATISFIED | abc123 | delivery-proof.txt | 2026-11-17T14:00:00Z |\n",
                encoding="utf-8",
            )
        return validation

    @staticmethod
    def fake_readback(_root: Path, entry: CONTRACT.WorkItemEntry) -> dict:
        project = (entry.external_id or "").split("-", 1)[0]
        raw = json.dumps({
            "key": entry.external_id,
            "fields": {
                "issuetype": {"name": "Story"},
                "status": {"name": "Done", "statusCategory": {"key": "done"}},
                "project": {"key": project},
            },
        }, separators=(",", ":")).encode("utf-8")
        return {
            "provider": entry.provider,
            "externalId": entry.external_id,
            "externalUrl": entry.external_url,
            "remoteType": "Story",
            "observedState": "Done",
            "remoteProject": project,
            "mappedRemoteType": "Story",
            "mappedDoneState": "Done",
            "mappedProject": project,
            "canonicalState": "DONE",
            "observedAt": "2026-11-17T15:00:00Z",
            "requestUrl": f"https://tracker.invalid/rest/api/3/issue/{entry.external_id}",
            "responseSha256": CONTRACT.hashlib.sha256(raw).hexdigest(),
            "responseBodyBase64": CONTRACT.base64.b64encode(raw).decode("ascii"),
        }

    def reserve_and_register(self, identifier: str = "RM-0001") -> Path:
        kind = identifier.split("-", 1)[0]
        reservation, mode = CONTRACT.reserve_identifier(
            self.root, kind, f"test:{identifier}", identifier=identifier,
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        self.assertEqual(mode, "applied")
        self.assertEqual(reservation["id"], identifier)
        primary = self.create_primary(identifier)
        entry, mode = CONTRACT.register_identifier(
            self.root, identifier, primary.relative_to(self.root).as_posix(),
            reservation_source=f"test:{identifier}", provider="JIRA",
            external_id=identifier, external_url=f"https://tracker.invalid/browse/{identifier}",
            apply=True,
        )
        self.assertEqual(mode, "applied")
        self.assertEqual(entry["primaryDocument"], primary.name)
        profile = self.root / "context/requirements/project-profile.md"
        text = profile.read_text(encoding="utf-8")
        text = text.replace("  mode: PENDIENTE", "  mode: REQUIRED")
        text = text.replace("  provider: null", "  provider: JIRA")
        text = text.replace("  credential_status: NO_VERIFICADO", "  credential_status: VERIFICADO")
        text = text.replace("    base_url: null", "    base_url: https://tracker.invalid")
        text = text.replace("    project_key: null", f"    project_key: {identifier.split('-', 1)[0]}")
        kind = identifier.split("-", 1)[0]
        text = text.replace(f"      {kind}: null", f"      {kind}: Story", 1)
        text = text.replace(
            f"      {kind}: {{PENDING: null, DOING: null, DONE: null, CANCELLED: null}}",
            f"      {kind}: {{PENDING: Open, DOING: In Progress, DONE: Done, CANCELLED: Cancelled}}",
            1,
        )
        profile.write_text(text, encoding="utf-8")
        return primary

    def test_empty_v2_layout_is_valid(self) -> None:
        report = CONTRACT.validate_layout(self.root)
        self.assertEqual(report.layout, "current")
        self.assertEqual(report.errors, [])

    def test_reserve_register_resolve_and_idempotence_use_basename_storage(self) -> None:
        primary = self.reserve_and_register()
        entry, dossier, frozen = CONTRACT.resolve_work_item(self.root, "RM-0001")
        self.assertEqual(entry.primary, "RM-0001.md")
        self.assertEqual(dossier / entry.primary, primary.resolve())
        self.assertFalse(frozen)
        repeated, mode = CONTRACT.register_identifier(
            self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
            reservation_source="test:RM-0001", provider="JIRA", external_id="RM-0001",
            external_url="https://tracker.invalid/browse/RM-0001", apply=True,
        )
        self.assertEqual(mode, "already-registered")
        self.assertEqual(repeated["primaryDocument"], "RM-0001.md")
        with self.assertRaises(CONTRACT.ContractError):
            CONTRACT.register_identifier(
                self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
                reservation_source="test:RM-0001", provider="JIRA", external_id="OTHER",
                external_url="https://tracker.invalid/browse/OTHER", apply=True,
            )

    def test_register_rejects_ambiguous_frontmatter_and_wrong_reservation_source(self) -> None:
        CONTRACT.reserve_identifier(
            self.root, "RM", "source-a", identifier="RM-0001",
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        primary = self.create_primary("RM-0001", extra_identity=True)
        with self.assertRaisesRegex(CONTRACT.ContractError, "un solo campo"):
            CONTRACT.register_identifier(
                self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
                reservation_source="source-a", provider="JIRA", external_id="FARO-1",
                external_url="https://tracker.invalid/browse/FARO-1", apply=True,
            )
        primary.write_text(
            "---\nwork_item_id: \"RM-0001\"\nartifact_type: \"REQUIREMENT_SPEC\"\n---\n# RM-0001\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "fuente"):
            CONTRACT.register_identifier(
                self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
                reservation_source="source-b", provider="JIRA", external_id="FARO-1",
                external_url="https://tracker.invalid/browse/FARO-1", apply=True,
            )

    def test_concurrent_reservations_are_unique_and_idempotent(self) -> None:
        processes = []
        for number in range(8):
            processes.append(subprocess.Popen(
                [
                    sys.executable, "-B", str(SCRIPT), "reserve", "--root", str(self.root),
                    "--kind", "RM", "--source", f"parallel-{number}", "--apply", "--json",
                ],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
            ))
        results = [process.communicate(timeout=20) for process in processes]
        for process, (_stdout, stderr) in zip(processes, results):
            self.assertEqual(process.returncode, 0, stderr)
        identifiers = {json.loads(stdout)["reservation"]["id"] for stdout, _stderr in results}
        self.assertEqual(len(identifiers), 8)
        repeated, mode = CONTRACT.reserve_identifier(self.root, "RM", "parallel-0", apply=True)
        self.assertEqual(mode, "already-reserved")
        self.assertIn(repeated["id"], identifiers)

    def test_reservation_source_is_case_insensitively_idempotent_and_corruption_blocks_writes(self) -> None:
        first, mode = CONTRACT.reserve_identifier(
            self.root, "RM", "Human:Request", reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        self.assertEqual(mode, "applied")
        repeated, mode = CONTRACT.reserve_identifier(self.root, "RM", "human:request", apply=True)
        self.assertEqual(mode, "already-reserved")
        self.assertEqual(repeated["id"], first["id"])
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace("2026-11-17T10:00:00-03:00", "not-a-date"),
            encoding="utf-8",
        )
        before = catalog.read_bytes()
        with self.assertRaisesRegex(CONTRACT.ContractError, "ISO-8601"):
            CONTRACT.reserve_identifier(self.root, "BUG", "another", apply=True)
        self.assertEqual(catalog.read_bytes(), before)

    def test_df_reservation_and_registration_are_idempotent(self) -> None:
        reservation, _ = CONTRACT.reserve_identifier(
            self.root, "DF", "functional-source", reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        self.assertEqual(reservation["id"], "DF-001")
        directory = self.root / "context/requirements/functional/DF-001"
        directory.mkdir()
        primary = directory / "DF-001.md"
        primary.write_text("---\ndf_id: \"DF-001\"\nartifact_type: \"FUNCTIONAL_DOCUMENT\"\n---\n# DF\n", encoding="utf-8")
        _entry, mode = CONTRACT.register_identifier(
            self.root, "DF-001", primary.relative_to(self.root).as_posix(),
            reservation_source="functional-source", domain="Payments", baseline="1.0", apply=True,
        )
        self.assertEqual(mode, "applied")
        report = CONTRACT.validate_layout(self.root)
        self.assertEqual(report.errors, [])
        self.assertEqual(report.functional_documents["DF-001"].primary, "DF-001.md")

    def test_link_external_only_fills_empty_reference(self) -> None:
        dossier = self.root / "context/requirements/work-items/BUG-0001"
        dossier.mkdir()
        primary = dossier / "BUG-0001.md"
        primary.write_text("---\nwork_item_id: \"BUG-0001\"\nartifact_type: \"BUG_ASSESSMENT_OR_TECHNICAL_MAINTENANCE\"\n---\n# BUG\n", encoding="utf-8")
        catalog = self.root / "context/requirements/requirements-catalog.md"
        text = CONTRACT._replace_table(
            catalog.read_text(encoding="utf-8"), "Expedientes", CONTRACT.WORK_ENTRY_HEADERS,
            [["BUG-0001", "BUG", "context/requirements/work-items/BUG-0001", "BUG-0001.md", "legacy:BUG-0001", "—", "—", "—", "—"]],
        )
        text = CONTRACT._replace_table(
            text, "Reservas", CONTRACT.WORK_RESERVATION_HEADERS,
            [["BUG-0001", "BUG", "legacy:BUG-0001", "2026-11-17T10:00:00Z"]],
        )
        catalog.write_text(text, encoding="utf-8")
        _result, mode = CONTRACT.link_external(
            self.root, "BUG-0001", "AZURE_DEVOPS", "42",
            "https://dev.azure.com/acme/Project/_workitems/edit/42", apply=True,
        )
        self.assertEqual(mode, "applied")
        _result, mode = CONTRACT.link_external(
            self.root, "BUG-0001", "AZURE_DEVOPS", "42",
            "https://dev.azure.com/acme/Project/_workitems/edit/42", apply=True,
        )
        self.assertEqual(mode, "already-linked")
        with self.assertRaises(CONTRACT.ContractError):
            CONTRACT.link_external(
                self.root, "BUG-0001", "JIRA", "FARO-99",
                "https://tracker.invalid/browse/FARO-99", apply=True,
            )

    def test_link_external_rejects_corrupt_primary_and_invalid_provider_url(self) -> None:
        dossier = self.root / "context/requirements/work-items/BUG-0001"
        dossier.mkdir()
        primary = dossier / "BUG-0001.md"
        primary.write_text("---\nwork_item_id: \"OTHER-0001\"\n---\n# bad\n", encoding="utf-8")
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(CONTRACT._replace_table(
            catalog.read_text(encoding="utf-8"), "Expedientes", CONTRACT.WORK_ENTRY_HEADERS,
            [["BUG-0001", "BUG", "context/requirements/work-items/BUG-0001", "BUG-0001.md", "legacy:BUG-0001", "—", "—", "—", "—"]],
        ), encoding="utf-8")
        catalog.write_text(CONTRACT._replace_table(
            catalog.read_text(encoding="utf-8"), "Reservas", CONTRACT.WORK_RESERVATION_HEADERS,
            [["BUG-0001", "BUG", "legacy:BUG-0001", "2026-11-17T10:00:00Z"]],
        ), encoding="utf-8")
        with self.assertRaisesRegex(CONTRACT.ContractError, "layout inválido"):
            CONTRACT.link_external(
                self.root, "BUG-0001", "JIRA", "FARO-1",
                "https://tracker.invalid/browse/FARO-1", apply=True,
            )
        with self.assertRaisesRegex(CONTRACT.ContractError, "proveedor"):
            CONTRACT.link_external(self.root, "BUG-0001", "OTHER", "1", "https://tracker.invalid/1")
        with self.assertRaisesRegex(CONTRACT.ContractError, "http"):
            CONTRACT.link_external(self.root, "BUG-0001", "JIRA", "1", "file:///tmp/item")

    def test_freeze_requires_machine_gates_and_remote_readback_then_detects_mutation(self) -> None:
        primary = self.reserve_and_register()
        self.write_valid_validation(primary)
        preview, mode = CONTRACT.freeze_work_item(self.root, "RM-0001")
        self.assertEqual(mode, "dry-run")
        self.assertIsNone(preview["remoteReadback"])
        with self.assertRaisesRegex(CONTRACT.ContractError, "readback Jira exige"):
            CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        with mock.patch.object(CONTRACT, "perform_provider_readback", side_effect=self.fake_readback):
            with mock.patch.object(CONTRACT, "utc_now", return_value="2026-11-17T15:01:00Z"):
                closure, mode = CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        self.assertEqual(mode, "applied")
        self.assertEqual(closure["validationGate"]["outcome"], "VERIFIED")
        self.assertEqual(closure["schemaVersion"], 3)
        self.assertEqual(closure["remoteReadback"]["canonicalState"], "DONE")
        report = CONTRACT.validate_layout(self.root)
        self.assertEqual(report.errors, [])
        primary.write_text(primary.read_text(encoding="utf-8") + "mutated\n", encoding="utf-8")
        report = CONTRACT.validate_layout(self.root)
        self.assertIn("frozen-dossier-mutated", {issue.code for issue in report.errors})

    def test_delivery_satisfied_requires_typed_delivery_artifact(self) -> None:
        primary = self.reserve_and_register()
        self.write_valid_validation(primary, delivery=True)
        delivery = primary.parent / "RM-0001-entrega.md"
        delivery.unlink()
        with self.assertRaisesRegex(CONTRACT.ContractError, "artefacto regular"):
            CONTRACT.freeze_work_item(self.root, "RM-0001")
        self.write_valid_validation(primary, delivery=True)
        _payload, mode = CONTRACT.freeze_work_item(self.root, "RM-0001")
        self.assertEqual(mode, "dry-run")

    def test_traversal_and_symlink_escape_are_rejected(self) -> None:
        primary = self.reserve_and_register()
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(catalog.read_text(encoding="utf-8").replace("RM-0001.md", "../RM-0001.md"), encoding="utf-8")
        report = CONTRACT.validate_layout(self.root)
        self.assertIn("primary-path-invalid", {issue.code for issue in report.errors})
        catalog.write_text(catalog.read_text(encoding="utf-8").replace("../RM-0001.md", "RM-0001.md"), encoding="utf-8")
        linked_root = self.root.parent / f"{self.root.name}-link"
        try:
            linked_root.symlink_to(self.root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        try:
            with self.assertRaisesRegex(CONTRACT.ContractError, "root no puede"):
                CONTRACT.validate_layout(linked_root)
        finally:
            linked_root.unlink()

    def test_workflow_types_nested_state_and_profile_duplicates_are_rejected(self) -> None:
        workflow = self.root / "context/workflow.json"
        workflow.write_text(json.dumps({
            "schemaVersion": 2,
            "updatedAt": "no-zone",
            "phase": 42,
            "authorization": {"status": "none", "source": None, "artifactVersion": None, "scope": None},
            "workItemRef": None,
            "waitingOn": {"detail": {"assigned_to": "someone"}},
            "nextRoute": 7,
            "checkpoint": None,
            "notes": [],
        }), encoding="utf-8")
        profile = self.root / "context/requirements/project-profile.md"
        profile.write_text(profile.read_text(encoding="utf-8").replace(
            "  operational_state_authority: EXTERNAL_WORK_TRACKER",
            "  operational_state_authority: EXTERNAL_WORK_TRACKER\n  operational_state_authority: EXTERNAL_WORK_TRACKER",
        ), encoding="utf-8")
        codes = {issue.code for issue in CONTRACT.validate_layout(self.root).errors}
        self.assertTrue({"workflow-updated-at", "workflow-phase", "workflow-next-route", "workflow-operational-state"} <= codes)
        self.assertIn("profile-v2-missing", codes)

    def test_profile_mappings_cannot_be_shifted_between_providers(self) -> None:
        profile = self.root / "context/requirements/project-profile.md"
        text = profile.read_text(encoding="utf-8")
        mapping = (
            "    type_mapping:\n"
            "      RM: null\n      BUG: null\n      TEC: null\n"
            "      INC: null\n      TASK: null\n"
        )
        jira, azure = text.split("  azure_devops:\n", 1)
        self.assertEqual(jira.count(mapping), 1)
        self.assertEqual(azure.count(mapping), 1)
        profile.write_text(
            jira.replace(mapping, mapping + mapping, 1)
            + "  azure_devops:\n"
            + azure.replace(mapping, "", 1),
            encoding="utf-8",
        )
        self.assertIn(
            "profile-kind-mapping",
            {issue.code for issue in CONTRACT.validate_layout(self.root).errors},
        )

    def test_workflow_incident_reference_uses_separate_registry_and_safe_file(self) -> None:
        incidents = self.root / "context/incidents"
        incidents.mkdir(parents=True)
        incident_path = "context/incidents/INC-0001-payment-timeout.md"
        (self.root / incident_path).write_text(
            "# INC-0001 — Payment timeout\n\nEvidence.\n", encoding="utf-8",
        )
        (incidents / "README.md").write_text(
            "# Incidentes\n\n## Registros\n\n"
            "| ID | Expediente estable | Fuente de reserva serializada | Seguimiento remoto y último readback | Conclusión / impacto | Derivados y relaciones |\n"
            "| --- | --- | --- | --- | --- | --- |\n"
            f"| INC-0001 | {incident_path} | test:timeout | JIRA EX-1 | PENDIENTE | — |\n\n"
            "## Reservas\n\n"
            "| ID | Alcance | Fuente de reserva serializada |\n"
            "| --- | --- | --- |\n",
            encoding="utf-8",
        )
        workflow = self.root / "context/workflow.json"
        workflow.write_text(json.dumps({
            "schemaVersion": 2,
            "updatedAt": "2026-11-17T10:00:00-03:00",
            "phase": "incident-investigation",
            "authorization": {
                "status": "approved", "source": "human",
                "artifactVersion": "1", "scope": "INC-0001",
            },
            "workItemRef": {"id": "INC-0001", "path": incident_path},
            "waitingOn": {"dependency": "vendor evidence"},
            "nextRoute": "faro-incidentes",
            "checkpoint": {"evidence": "context/incidents/INC-0001-payment-timeout.md"},
            "notes": ["Local pointer only; remote tracker owns operational state."],
        }), encoding="utf-8")

        report = CONTRACT.validate_layout(self.root)
        self.assertEqual(report.errors, [])
        self.assertNotIn("INC-0001", report.work_items)

        bad_path = "context/incidents/INC-0001-Payment-Timeout.md"
        payload = json.loads(workflow.read_text(encoding="utf-8"))
        payload["workItemRef"]["path"] = bad_path
        workflow.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn(
            "workflow-reference",
            {issue.code for issue in CONTRACT.validate_layout(self.root).errors},
        )

    def test_df_symlink_and_manual_rm_legacy_exception_are_rejected(self) -> None:
        directory = self.root / "context/requirements/functional/DF-001"
        directory.mkdir()
        primary = directory / "DF-001.md"
        primary.write_text("---\ndf_id: \"DF-001\"\n---\n# DF\n", encoding="utf-8")
        outside = self.root / "outside.md"
        outside.write_text("outside", encoding="utf-8")
        try:
            (directory / "evidence.md").symlink_to(outside)
        except (OSError, NotImplementedError):
            self.skipTest("symlinks unavailable")
        functional_catalog = self.root / "context/requirements/functional-documents-catalog.md"
        functional_catalog.write_text(CONTRACT._replace_table(
            functional_catalog.read_text(encoding="utf-8"), "Documentos", CONTRACT.DF_ENTRY_HEADERS,
            [["DF-001", "context/requirements/functional/DF-001", "DF-001.md", "test:DF-001", "Domain", "1", "—"]],
        ), encoding="utf-8")
        self.assertIn("functional-artifact-symlink", {issue.code for issue in CONTRACT.validate_layout(self.root).errors})

        (directory / "evidence.md").unlink()
        dossier = self.root / "context/requirements/work-items/RM-0001"
        dossier.mkdir()
        rm = dossier / "RM-0001.md"
        rm.write_text("# no front matter\n", encoding="utf-8")
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(CONTRACT._replace_table(
            catalog.read_text(encoding="utf-8"), "Expedientes", CONTRACT.WORK_ENTRY_HEADERS,
            [["RM-0001", "RM", "context/requirements/work-items/RM-0001", "RM-0001.md", "test:RM-0001", "—", "—", "—", "—"]],
        ), encoding="utf-8")
        record = {
            "legacyPrimaryExceptions": [{
                "id": "RM-0001", "kind": "RM", "primary": "context/requirements/work-items/RM-0001/RM-0001.md",
                "sha256": CONTRACT.sha256(rm), "reason": "legacy-primary-without-frontmatter",
            }],
        }
        (self.root / "context/faro-migration-v2.json").write_text(json.dumps(record), encoding="utf-8")
        report = CONTRACT.validate_layout(self.root)
        self.assertIn("migration-record-invalid", {issue.code for issue in report.errors})
        self.assertIn("primary-frontmatter", {issue.code for issue in report.errors})

    def test_published_source_remains_idempotent(self) -> None:
        self.reserve_and_register("RM-0001")
        repeated, mode = CONTRACT.reserve_identifier(
            self.root, "RM", "test:RM-0001", apply=True,
        )
        self.assertEqual(mode, "already-registered")
        self.assertEqual(repeated["id"], "RM-0001")
        catalog = self.root / "context/requirements/requirements-catalog.md"
        _headers, rows = CONTRACT._table(catalog, "Expedientes")
        self.assertEqual(CONTRACT.cell(rows[0], "Fuente de reserva serializada"), "test:RM-0001")

    def test_reserve_blocks_orphan_and_any_flat_legacy_artifact(self) -> None:
        orphan = self.root / "context/requirements/work-items/RM-0001"
        orphan.mkdir()
        with self.assertRaisesRegex(CONTRACT.ContractError, "layout inválido"):
            CONTRACT.reserve_identifier(self.root, "RM", "orphan", apply=True)
        orphan.rmdir()
        legacy = self.root / "context/requirements/RM-0001-screenshot.png"
        legacy.write_bytes(b"png")
        with self.assertRaisesRegex(CONTRACT.ContractError, "layout inválido"):
            CONTRACT.reserve_identifier(self.root, "RM", "legacy", apply=True)

    def test_repeat_register_revalidates_published_primary(self) -> None:
        primary = self.reserve_and_register("RM-0001")
        primary.unlink()
        with self.assertRaisesRegex(CONTRACT.ContractError, "layout inválido"):
            CONTRACT.register_identifier(
                self.root, "RM-0001",
                "context/requirements/work-items/RM-0001/RM-0001.md",
                reservation_source="test:RM-0001", provider="JIRA",
                external_id="RM-0001", external_url="https://tracker.invalid/browse/RM-0001",
                apply=True,
            )

    def test_remote_reference_cannot_be_shared(self) -> None:
        self.reserve_and_register("RM-0001")
        CONTRACT.reserve_identifier(
            self.root, "BUG", "test:BUG-0001", identifier="BUG-0001",
            reserved_at="2026-11-17T10:01:00-03:00", apply=True,
        )
        bug = self.create_primary("BUG-0001")
        with self.assertRaisesRegex(CONTRACT.ContractError, "item remoto duplicado"):
            CONTRACT.register_identifier(
                self.root, "BUG-0001", bug.relative_to(self.root).as_posix(),
                reservation_source="test:BUG-0001", provider="JIRA",
                external_id="RM-0001", external_url="https://tracker.invalid/browse/RM-0001",
                apply=True,
            )
        _headers, reservations = CONTRACT._table(
            self.root / "context/requirements/requirements-catalog.md", "Reservas",
        )
        self.assertEqual([CONTRACT.cell(row, "ID") for row in reservations], ["BUG-0001", "RM-0001"])

    def test_df_ids_and_basenames_are_strictly_uppercase(self) -> None:
        with self.assertRaisesRegex(CONTRACT.ContractError, "mayúsculas"):
            CONTRACT.reserve_identifier(self.root, "df", "lowercase")
        CONTRACT.reserve_identifier(
            self.root, "DF", "functional", identifier="DF-001",
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        directory = self.root / "context/requirements/functional/DF-001"
        directory.mkdir()
        primary = directory / "df-001.md"
        primary.write_text(
            "---\ndf_id: DF-001\nartifact_type: FUNCTIONAL_DOCUMENT\n---\n# DF\n",
            encoding="utf-8",
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "mayúsculas|basename"):
            CONTRACT.register_identifier(
                self.root, "DF-001", primary.relative_to(self.root).as_posix(),
                reservation_source="functional", domain="Orders", baseline="1", apply=True,
            )

    def test_freeze_rejects_nonconforming_criterion_even_with_verified_frontmatter(self) -> None:
        primary = self.reserve_and_register("RM-0001")
        validation = self.write_valid_validation(primary)
        validation.write_text(
            validation.read_text(encoding="utf-8").replace("| CONFORME |", "| NO_CONFORME |"),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "no está CONFORME"):
            CONTRACT.freeze_work_item(self.root, "RM-0001")

    def test_live_jira_readback_derives_state_from_raw_response(self) -> None:
        self.reserve_and_register("RM-0001")
        profile = self.root / "context/requirements/project-profile.md"
        text = profile.read_text(encoding="utf-8")
        text = text.replace("  mode: PENDIENTE", "  mode: REQUIRED")
        text = text.replace("  provider: null", "  provider: JIRA")
        text = text.replace("  credential_status: NO_VERIFICADO", "  credential_status: VERIFICADO")
        text = text.replace("    base_url: null", "    base_url: https://tracker.invalid")
        text = text.replace("      RM: null", "      RM: Story", 1)
        text = text.replace(
            "      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}",
            "      RM: {PENDING: Open, DOING: In Progress, DONE: Done, CANCELLED: Cancelled}",
            1,
        )
        profile.write_text(text, encoding="utf-8")
        entry = CONTRACT.validate_layout(self.root).work_items["RM-0001"]
        raw = b'{"key":"RM-0001","fields":{"issuetype":{"name":"Story"},"status":{"name":"Done","statusCategory":{"key":"done"}},"project":{"key":"RM"}}}'
        payload = json.loads(raw)
        with mock.patch.dict("os.environ", {
            "JIRA_BASE_URL": "https://tracker.invalid",
            "JIRA_EMAIL": "agent@example.invalid",
            "JIRA_API_TOKEN": "secret",
        }, clear=False):
            with mock.patch.object(CONTRACT, "_http_get_json", return_value=(raw, payload)):
                readback = CONTRACT.perform_provider_readback(self.root, entry)
        self.assertEqual(readback["canonicalState"], "DONE")
        self.assertEqual(readback["responseSha256"], CONTRACT.hashlib.sha256(raw).hexdigest())

    def test_primary_mutated_after_validation_blocks_before_network(self) -> None:
        primary = self.reserve_and_register()
        self.write_valid_validation(primary)
        primary.write_text(primary.read_text(encoding="utf-8") + "changed after validation\n", encoding="utf-8")
        with mock.patch.object(CONTRACT, "perform_provider_readback") as readback:
            with self.assertRaisesRegex(CONTRACT.ContractError, "validated_primary_sha256"):
                CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        readback.assert_not_called()
        self.assertFalse((primary.parent / "RM-0001-cierre.json").exists())

    def test_offline_closure_rejects_marker_tampering_and_missing_primary(self) -> None:
        primary = self.reserve_and_register()
        self.write_valid_validation(primary)
        with mock.patch.object(CONTRACT, "perform_provider_readback", side_effect=self.fake_readback):
            with mock.patch.object(CONTRACT, "utc_now", return_value="2026-11-17T15:01:00Z"):
                CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        marker = primary.parent / "RM-0001-cierre.json"
        original = marker.read_bytes()

        payload = json.loads(original)
        payload["validationGate"]["criteria"][0]["id"] = "CA-999"
        payload["validationGate"]["criteria"][0]["origin"] = ""
        marker.write_text(json.dumps(payload), encoding="utf-8")
        codes = {issue.code for issue in CONTRACT.validate_layout(self.root).errors}
        self.assertIn("closure-validation-gate", codes)

        marker.write_bytes(original)
        payload = json.loads(original)
        payload["remoteReadback"]["observedState"] = "Open"
        marker.write_text(json.dumps(payload), encoding="utf-8")
        codes = {issue.code for issue in CONTRACT.validate_layout(self.root).errors}
        self.assertIn("closure-readback", codes)

        marker.write_bytes(original)
        primary.unlink()
        report = CONTRACT.validate_layout(self.root)
        self.assertTrue(report.errors)
        self.assertIn("primary-missing", {issue.code for issue in report.errors})

    def test_delivery_scope_and_marker_operations_are_exact(self) -> None:
        primary = self.reserve_and_register()
        validation = self.write_valid_validation(primary, delivery=True)
        validation.write_text(
            validation.read_text(encoding="utf-8").replace(
                "| commit | Solicitud autorizada de commit. |",
                "| commit | Solicitud autorizada de commit. |\n| deploy | Alcance autorizado. |",
            ),
            encoding="utf-8",
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "no coinciden exactamente"):
            CONTRACT.freeze_work_item(self.root, "RM-0001")

        self.write_valid_validation(primary, delivery=True)
        with mock.patch.object(CONTRACT, "perform_provider_readback", side_effect=self.fake_readback):
            with mock.patch.object(CONTRACT, "utc_now", return_value="2026-11-17T15:01:00Z"):
                CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        marker = primary.parent / "RM-0001-cierre.json"
        payload = json.loads(marker.read_text(encoding="utf-8"))
        payload["validationGate"]["delivery"]["operations"] = [{"result": "FAILED"}]
        marker.write_text(json.dumps(payload), encoding="utf-8")
        self.assertIn(
            "closure-validation-gate",
            {issue.code for issue in CONTRACT.validate_layout(self.root).errors},
        )

    def test_reservation_source_is_global_for_work_items_and_frozen(self) -> None:
        CONTRACT.reserve_identifier(
            self.root, "RM", "request:shared", identifier="RM-0001",
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        with self.assertRaisesRegex(CONTRACT.ContractError, "clasificada como RM"):
            CONTRACT.reserve_identifier(self.root, "BUG", "request:shared", apply=True)

        primary = self.create_primary("RM-0001")
        CONTRACT.register_identifier(
            self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
            reservation_source="request:shared", provider="JIRA", external_id="RM-0001",
            external_url="https://tracker.invalid/browse/RM-0001", apply=True,
        )
        profile = self.root / "context/requirements/project-profile.md"
        profile_text = profile.read_text(encoding="utf-8")
        profile_text = profile_text.replace("  mode: PENDIENTE", "  mode: REQUIRED")
        profile_text = profile_text.replace("  provider: null", "  provider: JIRA")
        profile_text = profile_text.replace("  credential_status: NO_VERIFICADO", "  credential_status: VERIFICADO")
        profile_text = profile_text.replace("    base_url: null", "    base_url: https://tracker.invalid")
        profile_text = profile_text.replace("    project_key: null", "    project_key: RM")
        profile_text = profile_text.replace("      RM: null", "      RM: Story", 1)
        profile_text = profile_text.replace(
            "      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}",
            "      RM: {PENDING: Open, DOING: In Progress, DONE: Done, CANCELLED: Cancelled}",
            1,
        )
        profile.write_text(profile_text, encoding="utf-8")
        self.write_valid_validation(primary)
        with mock.patch.object(CONTRACT, "perform_provider_readback", side_effect=self.fake_readback):
            with mock.patch.object(CONTRACT, "utc_now", return_value="2026-11-17T15:01:00Z"):
                CONTRACT.freeze_work_item(self.root, "RM-0001", apply=True)
        catalog = self.root / "context/requirements/requirements-catalog.md"
        catalog.write_text(
            catalog.read_text(encoding="utf-8").replace("request:shared", "request:tampered"),
            encoding="utf-8",
        )
        self.assertIn(
            "closure-reservation-source",
            {issue.code for issue in CONTRACT.validate_layout(self.root).errors},
        )

    def test_full_layout_blocks_missing_hidden_and_invalid_port_without_mutation(self) -> None:
        catalog = self.root / "context/requirements/requirements-catalog.md"
        before = catalog.read_bytes()
        hidden = self.root / "context/requirements/work-items/.RM-0001"
        hidden.mkdir()
        with self.assertRaisesRegex(CONTRACT.ContractError, "entrada oculta"):
            CONTRACT.reserve_identifier(self.root, "RM", "hidden", apply=True)
        self.assertEqual(catalog.read_bytes(), before)
        hidden.rmdir()

        functional = self.root / "context/requirements/functional"
        functional.rmdir()
        with self.assertRaisesRegex(CONTRACT.ContractError, "functional root obligatorio ausente"):
            CONTRACT.reserve_identifier(self.root, "RM", "missing-root", apply=True)
        functional.mkdir()

        profile = self.root / "context/requirements/project-profile.md"
        profile_bytes = profile.read_bytes()
        profile.unlink()
        with self.assertRaisesRegex(CONTRACT.ContractError, "perfil obligatorio ausente"):
            CONTRACT.reserve_identifier(self.root, "RM", "missing-profile", apply=True)
        profile.write_bytes(profile_bytes)

        CONTRACT.reserve_identifier(
            self.root, "RM", "bad-port", identifier="RM-0001",
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        primary = self.create_primary("RM-0001")
        with self.assertRaisesRegex(CONTRACT.ContractError, "puerto inválido"):
            CONTRACT.register_identifier(
                self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
                reservation_source="bad-port", provider="JIRA", external_id="RM-0001",
                external_url="https://tracker.invalid:bad/browse/RM-0001", apply=True,
            )
        _headers, reservations = CONTRACT._table(catalog, "Reservas")
        self.assertEqual([CONTRACT.cell(row, "ID") for row in reservations], ["RM-0001"])

    def test_nonfunctional_promotion_requires_authority_markdown_and_real_version(self) -> None:
        primary = self.reserve_and_register()
        validation = self.write_valid_validation(primary)
        target = self.root / "context/decisions/adr/random.txt"
        target.parent.mkdir(parents=True)
        target.write_text("RM-0001\n", encoding="utf-8")
        validated_sha = CONTRACT.sha256(primary)
        primary.write_text(
            primary.read_text(encoding="utf-8").replace(
                "| ARCHITECTURE | — | NO_APLICA | Alcance aprobado sin decisión arquitectónica. |",
                "| ARCHITECTURE | decisión | INCORPORAR | Decisión arquitectónica autorizada. |",
            ),
            encoding="utf-8",
        )
        text = validation.read_text(encoding="utf-8").replace(
            f"validated_primary_sha256: {validated_sha}",
            f"validated_primary_sha256: {CONTRACT.sha256(primary)}",
        )
        text = text.replace("impact_architecture: NOT_APPLICABLE", "impact_architecture: INCORPORATED")
        text = text.replace(
            "| ARCHITECTURE | — | NO_APLICA | — | — | — | No hay decisión arquitectónica durable. |",
            "| ARCHITECTURE | decisión | INCORPORADO | context/decisions/adr/random.txt | banana | sí | — |",
        )
        validation.write_text(text, encoding="utf-8")
        with self.assertRaisesRegex(CONTRACT.ContractError, "Markdown|versión/baseline"):
            CONTRACT.freeze_work_item(self.root, "RM-0001")

    def test_live_azure_readback_is_bound_to_authorized_organization(self) -> None:
        CONTRACT.reserve_identifier(
            self.root, "RM", "azure", identifier="RM-0001",
            reserved_at="2026-11-17T10:00:00-03:00", apply=True,
        )
        primary = self.create_primary("RM-0001")
        CONTRACT.register_identifier(
            self.root, "RM-0001", primary.relative_to(self.root).as_posix(),
            reservation_source="azure", provider="AZURE_DEVOPS", external_id="42",
            external_url="https://dev.azure.com/acme/Project/_workitems/edit/42", apply=True,
        )
        profile = self.root / "context/requirements/project-profile.md"
        text = profile.read_text(encoding="utf-8")
        text = text.replace("  mode: PENDIENTE", "  mode: REQUIRED")
        text = text.replace("  provider: null", "  provider: AZURE_DEVOPS")
        text = text.replace("  credential_status: NO_VERIFICADO", "  credential_status: VERIFICADO")
        text = text.replace("    organization_url: null", "    organization_url: https://dev.azure.com/acme")
        text = text.replace("    project: null", "    project: Project")
        text = text.replace("      RM: null", "      RM: User Story")
        text = text.replace(
            "      RM: {PENDING: null, DOING: null, DONE: null, CANCELLED: null}",
            "      RM: {PENDING: New, DOING: Active, DONE: Closed, CANCELLED: Removed}",
        )
        profile.write_text(text, encoding="utf-8")
        entry = CONTRACT.validate_layout(self.root).work_items["RM-0001"]
        raw = b'{"id":42,"fields":{"System.WorkItemType":"User Story","System.State":"Closed","System.TeamProject":"Project"}}'
        payload = json.loads(raw)
        with mock.patch.dict("os.environ", {
            "AZDO_ORGANIZATION_URL": "https://dev.azure.com/acme",
            "AZDO_PAT": "secret",
        }, clear=False):
            with mock.patch.object(CONTRACT, "_http_get_json", return_value=(raw, payload)):
                readback = CONTRACT.perform_provider_readback(self.root, entry)
        self.assertEqual(readback["observedState"], "Closed")

        with mock.patch.dict("os.environ", {
            "AZDO_ORGANIZATION_URL": "https://evil.invalid/acme",
            "AZDO_PAT": "secret",
        }, clear=False):
            with mock.patch.object(CONTRACT, "_http_get_json") as http:
                with self.assertRaisesRegex(CONTRACT.ContractError, "no coincide|oficial"):
                    CONTRACT.perform_provider_readback(self.root, entry)
        http.assert_not_called()


if __name__ == "__main__":
    unittest.main()
