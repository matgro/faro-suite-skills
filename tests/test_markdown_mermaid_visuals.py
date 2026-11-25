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
DF_INVESTIGATION = ROOT / "faro/faro-documentacion-funcional/assets/functional-investigation.md"
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
            dossier = requirements / "functional/DF-001"
            dossier.mkdir(parents=True)
            (root / "AGENTS.md").write_text(
                "# Instrucciones locales sin directiva funcional duplicada\n", encoding="utf-8"
            )
            (requirements / "project-profile.md").write_text(
                "---\nfunctional_documentation: HABILITADA\n---\n", encoding="utf-8"
            )
            (requirements / "functional-documents-catalog.md").write_text(
                "## Reservas\n\n"
                "| ID | Fuente de reserva serializada | Fecha y zona |\n"
                "| --- | --- | --- |\n\n"
                "| DF-001 | test:df:1 | 2026-11-17T10:00:00Z |\n\n"
                "## Documentos\n"
                "| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| DF-001 | context/requirements/functional/DF-001 | DF-001-proceso.md | test:df:1 | Proceso | 1.0 | — |\n",
                encoding="utf-8",
            )
            (dossier / "DF-001-proceso.md").write_text(
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
            dossier = requirements / "functional/DF-001"
            dossier.mkdir(parents=True)
            (root / "AGENTS.md").write_text(
                "# Instrucciones locales sin directiva funcional duplicada\n", encoding="utf-8"
            )
            (requirements / "project-profile.md").write_text(
                "---\nfunctional_documentation: HABILITADA\n---\n", encoding="utf-8"
            )
            (requirements / "functional-documents-catalog.md").write_text(
                "## Reservas\n\n"
                "| ID | Fuente de reserva serializada | Fecha y zona |\n"
                "| --- | --- | --- |\n"
                "| DF-001 | test:df:1 | 2026-11-17T10:00:00Z |\n\n"
                "## Documentos\n"
                "| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| DF-001 | context/requirements/functional/DF-001 | DF-001-proceso.md | test:df:1 | Proceso | 1.0 | — |\n",
                encoding="utf-8",
            )
            (dossier / "DF-001-proceso.md").write_text(
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

    def test_verifier_rejects_symlinked_catalog_root_and_primary(self):
        for linked in ("catalog", "functional-root", "primary"):
            with self.subTest(linked=linked), tempfile.TemporaryDirectory() as temporary:
                root = Path(temporary)
                requirements = root / "context/requirements"
                requirements.mkdir(parents=True)
                (requirements / "project-profile.md").write_text(
                    "---\nfunctional_documentation: HABILITADA\n---\n", encoding="utf-8"
                )

                if linked == "functional-root":
                    functional = root / "real-functional"
                    functional.mkdir()
                    try:
                        (requirements / "functional").symlink_to(functional, target_is_directory=True)
                    except (OSError, NotImplementedError) as error:
                        self.skipTest(f"symlinks are unavailable: {error}")
                else:
                    functional = requirements / "functional"
                    functional.mkdir()
                dossier = functional / "DF-001"
                dossier.mkdir()

                catalog_text = (
                    "## Reservas\n\n"
                    "| ID | Fuente de reserva serializada | Fecha y zona |\n"
                    "| --- | --- | --- |\n\n"
                    "## Documentos\n"
                    "| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |\n"
                    "| --- | --- | --- | --- | --- | --- | --- |\n"
                    "| DF-001 | context/requirements/functional/DF-001 | "
                    "DF-001.md | test:df:1 | Proceso | 1.0 | — |\n"
                )
                catalog = requirements / "functional-documents-catalog.md"
                if linked == "catalog":
                    catalog_target = root / "catalog-target.md"
                    catalog_target.write_text(catalog_text, encoding="utf-8")
                    try:
                        catalog.symlink_to(catalog_target)
                    except (OSError, NotImplementedError) as error:
                        self.skipTest(f"symlinks are unavailable: {error}")
                else:
                    catalog.write_text(catalog_text, encoding="utf-8")

                primary = dossier / "DF-001.md"
                primary_text = "---\ndf_id: DF-001\n---\n# Documento\n"
                if linked == "primary":
                    primary_target = root / "primary-target.md"
                    primary_target.write_text(primary_text, encoding="utf-8")
                    try:
                        primary.symlink_to(primary_target)
                    except (OSError, NotImplementedError) as error:
                        self.skipTest(f"symlinks are unavailable: {error}")
                else:
                    primary.write_text(primary_text, encoding="utf-8")

                result = subprocess.run(
                    [sys.executable, "-B", str(VERIFIER), str(root)],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                )

                self.assertNotEqual(result.returncode, 0)
                self.assertIn("symlink", result.stdout.lower())

    def test_verifier_enforces_uppercase_df_without_rewriting_historical_slug(self):
        self.assertTrue(DF_INVESTIGATION.read_text(encoding="utf-8").startswith("---\ndf_id:"))
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            requirements = root / "context/requirements"
            dossier = requirements / "functional/DF-001"
            dossier.mkdir(parents=True)
            (root / "AGENTS.md").write_text("# FARO\n", encoding="utf-8")
            (requirements / "project-profile.md").write_text(
                "---\nfunctional_documentation: HABILITADA\n---\n", encoding="utf-8",
            )
            catalog = requirements / "functional-documents-catalog.md"
            catalog.write_text(
                "## Reservas\n\n"
                "| ID | Fuente de reserva serializada | Fecha y zona |\n"
                "| --- | --- | --- |\n"
                "| DF-001 | request:orders | 2026-11-17T10:00:00Z |\n\n"
                "## Documentos\n\n"
                "| ID | Ruta canónica | Documento principal | Fuente de reserva serializada | Dominio o proceso | Versión / baseline | Relacionados |\n"
                "| --- | --- | --- | --- | --- | --- | --- |\n"
                "| DF-001 | context/requirements/functional/DF-001 | DF-001-Orders.md | request:orders | Orders | 1.0 | — |\n",
                encoding="utf-8",
            )
            (dossier / "DF-001-Orders.md").write_text(
                "---\ndf_id: DF-001\n---\n# Orders\nRF-001 CA-001\n", encoding="utf-8",
            )
            accepted = subprocess.run(
                [sys.executable, "-B", str(VERIFIER), str(root)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertEqual(accepted.returncode, 0, accepted.stdout + accepted.stderr)

            secondary = dossier / "DF-001-NOTES.md"
            secondary.write_text("---\ndf_id: df-001\n---\n# Notes\n", encoding="utf-8")
            rejected = subprocess.run(
                [sys.executable, "-B", str(VERIFIER), str(root)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("declares 'df-001'", rejected.stdout)
            secondary.unlink()

            catalog.write_text(
                catalog.read_text(encoding="utf-8").replace(
                    "| DF-001 | request:orders | 2026-11-17T10:00:00Z |\n\n## Documentos",
                    "| DF-001 | request:orders | 2026-11-17T10:00:00Z |\n| df-002 | request:lower | 2026-11-17T10:00:00Z |\n\n## Documentos",
                ),
                encoding="utf-8",
            )
            rejected = subprocess.run(
                [sys.executable, "-B", str(VERIFIER), str(root)],
                capture_output=True, text=True, encoding="utf-8",
            )
            self.assertNotEqual(rejected.returncode, 0)
            self.assertIn("non-canonical DF reservation ID", rejected.stdout)


if __name__ == "__main__":
    unittest.main()
