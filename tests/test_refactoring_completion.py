"""Contract regression tests for complete, evidenced FARO refactors."""
from pathlib import Path
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"


class RefactoringCompletionTests(unittest.TestCase):
    def test_shared_gate_is_loaded_by_analysis_development_and_validation(self):
        for skill in ("faro-req-analisis-tecnico", "faro-req-desarrollo", "faro-req-validacion"):
            with self.subTest(skill=skill):
                text = (FARO / skill / "SKILL.md").read_text()
                self.assertIn("(../references/refactoring-completion.md)", text)
        development = (FARO / "faro-req-desarrollo/SKILL.md").read_text()
        self.assertLess(development.index("## Cierre de refactorizaciones"), development.index("## Procedimiento"))
        self.assertIn("no marcar `done`", development)
        validation = (FARO / "faro-req-validacion/SKILL.md").read_text()
        self.assertIn("NO_CONFORME", validation)
        self.assertIn("NO_VERIFICADO", validation)

    def test_gate_rejects_unused_extractions_and_preserves_dynamic_consumers(self):
        text = (FARO / "references/refactoring-completion.md").read_text()
        for rule in ("consumidores reales", "sólo desde tests", "implementación anterior",
                     "delegación", "caracterización", "Livewire", "reflexión",
                     "revisión independiente", "no demuestra ausencia de uso",
                     "NO_CONFORME", "NO_VERIFICADO", "sin ampliar el alcance",
                     "no ejecutar `clean`", "no instalar", "dirty diff"):
            with self.subTest(rule=rule):
                self.assertIn(rule.casefold(), text.casefold())

    def test_external_sources_and_safe_fallbacks_are_explicit(self):
        text = (FARO / "references/refactoring-completion.md").read_text()
        for source in ("event4u-app/agent-config", "edulazaro/laraclaude", "obra/superpowers",
                       "requesting-code-review", "verification-before-completion", "lc:dead-code"):
            self.assertIn(source, text)
        self.assertIn("sólo como referencia metodológica", text)
        self.assertIn("Si no hay revisor independiente", text)
        catalog = json.loads((FARO / "references/laravel-external-skills.json").read_text())
        source = next(s for s in catalog["sources"] if s["repository"].endswith("edulazaro/laraclaude"))
        self.assertIn("lc:dead-code", source["skills"])
        self.assertIn("sólo lectura", " ".join(source["uses"]))

    def test_existing_artifacts_capture_wiring_retirement_and_review(self):
        for path in ("faro-req-analisis-tecnico/assets/technical-plan.md",
                     "faro-req-analisis-tecnico/assets/tasks.md",
                     "faro-req-validacion/assets/validation-report.md"):
            with self.subTest(path=path):
                text = (FARO / path).read_text()
                self.assertIn("Consumidor", text)
                self.assertIn("Retiro", text)
                self.assertIn("Revisor", text)

    def test_missing_shared_gate_fails_suite_validation(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            suite = Path(directory) / "faro"
            shutil.copytree(FARO, suite)
            gate = suite / "references/refactoring-completion.md"
            self.assertTrue(gate.is_file())
            gate.unlink()
            result = subprocess.run([sys.executable, "-B", str(suite / "scripts/suite_validation.py"),
                                     "--suite-root", str(suite)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("refactoring-completion.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
