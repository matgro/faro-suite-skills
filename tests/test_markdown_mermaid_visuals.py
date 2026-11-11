"""Regression tests for readable FARO visual documentation in Markdown/Mermaid."""
from __future__ import annotations

from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FUNCTIONAL_SKILL = ROOT / "faro/faro-documentacion-funcional/SKILL.md"
DF_TEMPLATE = ROOT / "faro/faro-documentacion-funcional/assets/functional-document.md"
RM_TEMPLATE = ROOT / "faro/faro-req-ingenieria/assets/rm-standard.md"
TECHNICAL_PLAN = ROOT / "faro/faro-req-analisis-tecnico/assets/technical-plan.md"
UX_SKILL = ROOT / "faro/faro-ux/SKILL.md"
VERIFIER = ROOT / "faro/faro-documentacion-funcional/scripts/verify-functional-documentation.py"


class MarkdownMermaidVisualTests(unittest.TestCase):
    def test_functional_visual_contract_is_markdown_mermaid_and_traceable(self):
        skill = FUNCTIONAL_SKILL.read_text(encoding="utf-8")
        template = DF_TEMPLATE.read_text(encoding="utf-8")

        self.assertIn("Markdown/Mermaid", skill)
        self.assertIn("legible sin renderizado", skill)
        self.assertIn("RF/RN/CA/PD", skill)
        self.assertIn("```mermaid", template)
        self.assertIn("flowchart", template)
        self.assertIn("stateDiagram-v2", template)

    def test_requirement_technical_and_ux_routes_use_the_same_visual_contract(self):
        self.assertIn("Markdown/Mermaid", RM_TEMPLATE.read_text(encoding="utf-8"))
        self.assertIn("```mermaid", TECHNICAL_PLAN.read_text(encoding="utf-8"))
        ux = UX_SKILL.read_text(encoding="utf-8")
        self.assertIn("Markdown/Mermaid", ux)
        self.assertIn("artefacto FARO existente", ux)

    def test_verifier_rejects_unclosed_mermaid_fence_in_a_deliverable_df(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requirements = root / "context/requirements"
            requirements.mkdir(parents=True)
            (root / "AGENTS.md").write_text(
                "Con documentación funcional `HABILITADA`\n", encoding="utf-8"
            )
            (requirements / "project-profile.md").write_text(
                "## Documentación funcional\n**Estado:** `HABILITADA`\n", encoding="utf-8"
            )
            (requirements / "functional-documents-catalog.md").write_text(
                "## Reservas\n\n## Documentos\n| DF-001 | Proceso |\n", encoding="utf-8"
            )
            (requirements / "DF-001-proceso.md").write_text(
                "---\ndf_id: \"DF-001\"\n---\n# Proceso\n```mermaid\nflowchart TD\nA[Inicio] --> B[Fin]\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "-B", str(VERIFIER), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Mermaid sin cierre", result.stdout)

    def test_verifier_accepts_a_closed_supported_mermaid_diagram(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requirements = root / "context/requirements"
            requirements.mkdir(parents=True)
            (root / "AGENTS.md").write_text(
                "Con documentación funcional `HABILITADA`\n", encoding="utf-8"
            )
            (requirements / "project-profile.md").write_text(
                "## Documentación funcional\n**Estado:** `HABILITADA`\n", encoding="utf-8"
            )
            (requirements / "functional-documents-catalog.md").write_text(
                "## Reservas\n\n## Documentos\n| DF-001 | Proceso |\n", encoding="utf-8"
            )
            (requirements / "DF-001-proceso.md").write_text(
                "---\ndf_id: \"DF-001\"\n---\n# Proceso\n"
                "Trazabilidad: RF-001, CA-001.\n"
                "```mermaid\nflowchart TD\nA[Inicio] --> B[Fin]\n```\n",
                encoding="utf-8",
            )

            result = subprocess.run(
                [sys.executable, "-B", str(VERIFIER), str(root)],
                capture_output=True,
                text=True,
                encoding="utf-8",
            )

        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("PASS", result.stdout)


if __name__ == "__main__":
    unittest.main()
