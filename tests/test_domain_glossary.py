"""Contract and offline workspace checks for the shared domain glossary."""
from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"


class DomainGlossaryTests(unittest.TestCase):
    def test_glossary_is_optional_and_does_not_migrate_existing_contracts(self):
        config = json.loads((FARO / "templates/faro-workspace-config.json").read_text())
        self.assertEqual(config["contractVersion"], "1.13.0")
        self.assertNotIn("context/glossary.md", config["requiredFiles"])
        self.assertIn("context/glossary.md", [item["path"] for item in config["conditionalFiles"]])
        self.assertEqual(config["workspace"]["glossaryPath"], "context/glossary.md")
        self.assertTrue((ROOT / config["templateSources"]["glossary"]).is_file())

    def test_every_lifecycle_skill_loads_the_shared_policy(self):
        manifest = json.loads((ROOT / "manifest.json").read_text())
        for name in manifest["skills"]:
            if name == "azure-devops-rest-v7":
                continue  # Technical capability, not a FARO lifecycle entry point.
            path = FARO / ("SKILL.md" if name == "faro" else f"{name}/SKILL.md")
            with self.subTest(skill=name):
                text = path.read_text()
                self.assertIn("context/glossary.md", text)
                self.assertIn("domain-glossary.md", text)
                self.assertIn("cada interacción", text)

    def test_policy_preserves_evidence_scope_and_read_only_boundaries(self):
        text = (FARO / "references/domain-glossary.md").read_text()
        for rule in (
            "CONFIRMADA", "OBSERVADA", "PENDIENTE", "CONFLICTO",
            "no equivale a aprobación funcional", "no crear RM, BUG, TEC",
            "sin reinicializar", "sólo lectura", "disabled", "scaffold",
            "no normalizar siglas", "no copiar a memoria global",
            "no reescribir baselines", "sin cambios no escribir",
            "fuente localizable", "alias", "ámbito",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, text)

    def test_template_is_generic_and_has_traceability_and_history(self):
        text = (FARO / "templates/glossary.md").read_text()
        for field in ("Término", "Significado", "Ámbito", "Alias", "Estado", "Fuente", "Fecha", "Historial"):
            self.assertIn(field, text)
        self.assertNotIn("ERGOSOFT", text)
        self.assertNotIn("REI", text)
        self.assertNotIn("RAE", text)
        policy = (FARO / "references/domain-glossary.md").read_text()
        self.assertIn("context/README.md", policy)
        self.assertIn("No modificar `AGENTS.md` existente", policy)

    def test_documentation_keeps_business_glossary_and_baselines_distinct(self):
        text = (FARO / "faro-documentacion-funcional/SKILL.md").read_text()
        self.assertIn("vocabulario de negocio", text)
        self.assertIn("no reescribir baselines", text)

    def test_doctor_accepts_old_workspace_and_reports_glossary_without_writing(self):
        config = json.loads((FARO / "templates/faro-workspace-config.json").read_text())
        templates = ["AGENTS.md", "faro-workspace-manifest.json", "stats.json", "context-README.md", "project-profile.md"]
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            root = Path(directory)
            for destination, template in zip(config["requiredFiles"], templates):
                path = root / destination
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes((FARO / "templates" / template).read_bytes())
            for present in (False, True):
                with self.subTest(glossary_present=present):
                    if present:
                        (root / "context/glossary.md").write_bytes((FARO / "templates/glossary.md").read_bytes())
                    before = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                    result = subprocess.run(
                        [sys.executable, "-B", str(FARO / "faro-doctor/scripts/doctor.py"), "--root", str(root), "--strict"],
                        capture_output=True, text=True, check=False,
                    )
                    self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                    expected = "presente" if present else "no creado (opcional)"
                    self.assertIn(f"Glosario de dominio: {expected}", result.stdout)
                    after = {str(p.relative_to(root)): p.read_bytes() for p in root.rglob("*") if p.is_file()}
                    self.assertEqual(before, after)


if __name__ == "__main__":
    unittest.main()
