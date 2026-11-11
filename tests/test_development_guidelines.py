"""Contract tests for editable development guidelines, not their wording."""
from __future__ import annotations

import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
DEVELOPMENT = ROOT / "faro/faro-req-desarrollo"
GUIDELINES = ("lineamientos-comunes.md", "lineamientos-dotnet.md", "lineamientos-laravel.md", "lineamientos-blazor.md")


class DevelopmentGuidelineTests(unittest.TestCase):
    def test_existing_changes_require_explicit_human_validation(self):
        skill = (DEVELOPMENT / "SKILL.md").read_text(encoding="utf-8")
        for rule in (
            "detenerse y esperar validación humana explícita",
            "archivos afectados, su atribución y la acción propuesta",
            "El silencio, la autorización general de implementar o una aprobación anterior",
            "volver a comprobar Git",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)

    def test_repository_duplication_is_not_an_automatic_escape(self):
        skill = (DEVELOPMENT / "SKILL.md").read_text(encoding="utf-8")
        for rule in (
            "repositorio y directorio de código actuales",
            "No crear clones, copias del repositorio ni worktrees",
            "autorización humana explícita previa para esa operación y su destino",
            "No hacer stash, descartar, mover ni incluir cambios ajenos en un commit",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, skill)

    def test_skill_links_nonempty_guidelines_inside_its_directory(self):
        skill = (DEVELOPMENT / "SKILL.md").read_text(encoding="utf-8")
        for filename in GUIDELINES:
            with self.subTest(filename=filename):
                relative = "references/" + filename
                self.assertIn("(" + relative + ")", skill)
                self.assertTrue((DEVELOPMENT / relative).is_file())
                self.assertTrue((DEVELOPMENT / relative).read_text(encoding="utf-8").strip())

    def test_edits_do_not_require_skill_changes_or_fail_local_validation(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temporary:
            suite = Path(temporary) / "faro"
            shutil.copytree(ROOT / "faro", suite)
            development = suite / "faro-req-desarrollo"
            before = (development / "SKILL.md").read_bytes()
            for filename in GUIDELINES:
                path = development / "references" / filename
                self.assertTrue(path.is_file(), str(path))
                path.write_text("# Lineamientos personalizados\n\n- Respetar las convenciones del equipo.\n", encoding="utf-8")
            result = self.validate(suite)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertEqual((development / "SKILL.md").read_bytes(), before)

    def test_local_validation_reports_missing_blazor_guidelines(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temporary:
            suite = Path(temporary) / "faro"
            shutil.copytree(ROOT / "faro", suite)
            reference = suite / "faro-req-desarrollo/references/lineamientos-blazor.md"
            self.assertTrue(reference.is_file(), str(reference))
            reference.unlink()
            result = self.validate(suite)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("lineamientos-blazor.md", result.stdout)

    def test_local_validation_reports_missing_reference_file(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temporary:
            suite = Path(temporary) / "faro"
            shutil.copytree(ROOT / "faro", suite)
            path = suite / "faro-req-desarrollo/SKILL.md"
            text = path.read_text(encoding="utf-8")
            path.write_text(text + "\n[Guía requerida](references/guia-ausente.md)\n", encoding="utf-8")
            result = self.validate(suite)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("guia-ausente.md", result.stdout)

    def validate(self, suite):
        return subprocess.run(
            [sys.executable, "-B", str(suite / "scripts/suite_validation.py"), "--suite-root", str(suite)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def test_local_validation_reports_empty_reference_file(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as temporary:
            suite = Path(temporary) / "faro"
            shutil.copytree(ROOT / "faro", suite)
            development = suite / "faro-req-desarrollo"
            reference = development / "references/guia-vacia.md"
            reference.parent.mkdir(parents=True, exist_ok=True)
            reference.write_text(" \n\t\n", encoding="utf-8")
            path = development / "SKILL.md"
            path.write_text(path.read_text(encoding="utf-8") + "\n[Guía requerida](references/guia-vacia.md)\n", encoding="utf-8")
            result = self.validate(suite)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("archivo de referencia vacío: references/guia-vacia.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
