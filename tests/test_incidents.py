"""Offline governance contracts and executable catalog/workflow validation.

These tests check documented agent instructions; they do not prove that an LLM
investigates correctly, that external skills were installed, or that an incident
occurred in production.
"""
from __future__ import annotations

import copy
import json
import os
from pathlib import Path
import runpy
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"
VALIDATION = runpy.run_path(str(FARO / "scripts/suite_validation.py"))


def text(relative: str) -> str:
    return (FARO / relative).read_text(encoding="utf-8")


class IncidentContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = text("faro-incidentes/SKILL.md")
        cls.capabilities = text("faro-incidentes/references/capacidades-externas.md")
        cls.router = text("SKILL.md")

    def test_route_is_registered_and_intake_precedes_bug_without_expected(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("faro-incidentes", manifest["skills"])
        rows = self.router.split("## Tabla de ruteo", 1)[1].split("## Continuidad", 1)[0]
        self.assertLess(rows.index("`faro-incidentes`"), rows.index("BUG sin esperado"))
        self.assertIn("Tiene prioridad", rows)
        self.assertIn("SOL/RM/BUG/TEC/INC", self.router)
        self.assertIn("sin exigir uno artificial", rows)

    def test_incident_is_on_demand_and_does_not_migrate_workspace(self):
        config = json.loads(text("templates/faro-workspace-config.json"))
        self.assertEqual(config["contractVersion"], "1.13.0")
        self.assertFalse(any("incidents" in item for item in config["requiredDirectories"] + config["requiredFiles"]))
        self.assertIn("No crear esta estructura durante inicialización", self.skill)
        self.assertIn("sin reserva serializada", self.skill)
        self.assertIn("no reemplazar `workflow.json` sin decisión humana", self.skill)
        self.assertTrue((FARO / "faro-incidentes/assets/incident-index.md").is_file())

    def test_investigation_does_not_authorize_fix_or_remote_side_effects(self):
        for guard in (
            "Registrar no autoriza instrumentación",
            "Una propuesta de corrección no es autorización",
            "sólo con autorización explícita",
            "`fix` describe la implementación/commit, no un tercer artefacto",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, self.skill)
        self.assertIn("No fase 4", self.capabilities)
        self.assertIn("No ejecutar código de ejemplo", self.capabilities)
        self.assertIn("no confirma un BUG", self.router)

    def test_all_outcomes_and_uncertainty_have_explicit_paths(self):
        for outcome in (
            "Defecto propio", "Proveedor o dependencia externa",
            "Comportamiento de negocio esperado", "Configuración, datos u operación",
            "Evidencia insuficiente o no reproducido",
        ):
            with self.subTest(outcome=outcome):
                self.assertIn(outcome, self.skill)
        self.assertIn("pueden coexistir", self.skill)
        self.assertIn("no equivale a «no es bug»", self.skill)
        self.assertIn("No crear una corrección especulativa", self.skill)

    def test_closure_distinguishes_investigation_impact_and_correction(self):
        for guard in (
            "`ABIERTO`, `EN_INVESTIGACION`, `CERRADO`",
            "Causa conocida no significa servicio recuperado",
            "Un cierre sin BUG es válido si se justifica con evidencia",
            "Si persiste impacto activo o no verificado",
            "decisión humana explícita y ausencia de impacto activo pendiente",
            "Reabrir el mismo INC ante nueva evidencia",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, self.skill)

    def test_template_preserves_provenance_hypotheses_limits_and_history(self):
        template = text("faro-incidentes/assets/incident.md")
        for section in (
            "## Evidencias", "## Cronología", "## Investigación", "## Causa y conclusión",
            "## Decisión y acciones derivadas", "## Cierre o continuidad", "## Historial",
        ):
            with self.subTest(section=section):
                self.assertIn(section, template)
        for field in ("Hipótesis", "Comprobación autorizada", "Esperado y fuente", "Situación actual del impacto", "Límites", "sin duplicarla"):
            with self.subTest(field=field):
                self.assertIn(field, template)
        self.assertNotIn("Status: Resolved", template)

    def test_external_stages_are_pinned_gated_and_do_not_replace_local_skills(self):
        for guard in (
            "Si falta, está modificada, tiene otro origen o el escaneo la bloqueó",
            "ni reconstruir silenciosamente", "directorio completo fijado", "No sustituir la `incident-postmortem` local",
        ):
            self.assertIn(guard, self.capabilities)
        self.assertIn("`requiredFiles`", self.capabilities)
        bootstrap = (ROOT / "bootstrap/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("incident-external-skills.json", bootstrap)
        self.assertIn("obtain explicit installation/replacement authorization", bootstrap)
        self.assertIn("raw `SKILL.md`-only install", bootstrap)
        self.assertIn("takes precedence over the mutable update procedure", bootstrap)

    def test_tracking_is_neutral_and_separate_from_correction(self):
        for adapter in ("faro-int-jira/SKILL.md", "faro-int-azure-devops/SKILL.md"):
            content = text(adapter)
            with self.subTest(adapter=adapter):
                for guard in ("faro-incidentes", "tipo neutral", "ni usar Bug por defecto", "sin autorización explícita", "Verificar por lectura toda escritura", "no cierra automáticamente el incidente"):
                    self.assertIn(guard, content)
        self.assertIn("`OFF`: no crear tickets remotos", self.skill)
        self.assertIn("no avanzar de fase ni declarar el cierre remoto", self.skill)
        self.assertIn("sin confirmar BUG por el tipo remoto", text("faro-int-jira/SKILL.md"))
        self.assertIn("No exigir INC para fallos conocidos contra CA", text("faro-qa-ejecucion/SKILL.md"))

    def test_received_bug_item_does_not_force_reclassification_or_duplication(self):
        self.assertIn("Exigir tipo neutral sólo para items nuevos", self.skill)
        self.assertIn("Vincular el item recibido aunque sea de tipo Bug", self.skill)
        self.assertIn("no exigir otro item neutral ni bloquear sólo por su tipo", self.skill)
        for adapter in ("faro-int-jira/SKILL.md", "faro-int-azure-devops/SKILL.md"):
            content = text(adapter)
            with self.subTest(adapter=adapter):
                self.assertIn("exigir tipo neutral sólo para items nuevos", content)
                self.assertIn("Conservar el item recibido aunque sea de tipo Bug", content)
                self.assertIn("su tipo remoto no confirma un defecto", content)
                self.assertIn("crear un item neutral separado requiere decisión explícita", content)

    def test_workflow_can_resume_incident_without_mutating_it(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            workflow = Path(directory) / "workflow.json"
            payload = '{"active": {"id": "INC-0001"}, "nextRoute": "faro-incidentes"}'
            workflow.write_text(payload, encoding="utf-8")
            self.assertEqual(VALIDATION["validate_workflow"](workflow, FARO), [])
            self.assertEqual(workflow.read_text(encoding="utf-8"), payload)


class IncidentCatalogValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.catalog = json.loads(text("references/incident-external-skills.json"))

    def validate(self, catalog):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            suite = Path(directory)
            path = suite / "references/incident-external-skills.json"
            path.parent.mkdir()
            path.write_text(json.dumps(catalog), encoding="utf-8")
            return VALIDATION["validate_incident_capabilities"](suite)

    def test_reviewed_catalog_is_accepted(self):
        self.assertEqual(self.validate(self.catalog), [])
        names = [name for source in self.catalog["sources"] for name in source["skills"]]
        self.assertEqual(names, ["systematic-debugging", "incident-postmortem"])

    def test_mutable_or_malformed_pins_are_rejected(self):
        for revision in ("main", "latest", "2ce8aa1", None):
            catalog = copy.deepcopy(self.catalog)
            catalog["sources"][0]["revision"] = revision
            with self.subTest(revision=revision):
                self.assertTrue(self.validate(catalog))

    def test_missing_supporting_reference_or_invalid_hash_is_rejected(self):
        catalog = copy.deepcopy(self.catalog)
        del catalog["sources"][0]["requiredFiles"]["root-cause-tracing.md"]
        self.assertTrue(self.validate(catalog))
        catalog = copy.deepcopy(self.catalog)
        catalog["sources"][0]["requiredFiles"]["SKILL.md"] = "not-a-sha256"
        self.assertTrue(self.validate(catalog))
        catalog = copy.deepcopy(self.catalog)
        catalog["sources"][0]["licenseSha256"] = ""
        self.assertTrue(self.validate(catalog))

    def test_unsafe_paths_missing_roles_and_malformed_catalog_are_rejected(self):
        for value in ("../other", "/absolute", "C:/absolute", "a\\b", "a//b", "a/./b"):
            catalog = copy.deepcopy(self.catalog)
            catalog["sources"][0]["path"] = value
            with self.subTest(path=value):
                self.assertTrue(self.validate(catalog))
        for value in (None, [], {}, {"schemaVersion": 1, "sources": []}):
            with self.subTest(catalog=value):
                self.assertTrue(self.validate(value))
        catalog = copy.deepcopy(self.catalog)
        catalog["sources"].pop()
        self.assertTrue(self.validate(catalog))


if __name__ == "__main__":
    unittest.main()
