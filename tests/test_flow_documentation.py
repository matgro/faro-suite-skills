"""Documentation coverage/link checks, not execution of agent decision-making.

Mermaid syntax is checked separately with a parser; this test suite does not
claim browser layout review, live integrations, or automatic skill execution.
"""
from pathlib import Path
import json
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
GUIDE = ROOT / "docs/flujo-faro"
PAGES = (
    "README.md",
    "01-inicio-y-doctor.md",
    "02-arquitectura-y-decisiones.md",
    "03-solicitudes-y-desarrollo.md",
    "04-incidentes.md",
    "05-integraciones-y-entrega.md",
)


class FlowDocumentationTests(unittest.TestCase):
    def test_root_readme_links_the_unified_guide(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        self.assertIn("(docs/flujo-faro/README.md)", readme)

    def test_each_guide_page_exists_has_a_diagram_and_balanced_fences(self):
        for name in PAGES:
            path = GUIDE / name
            with self.subTest(page=name):
                self.assertTrue(path.is_file(), str(path))
                content = path.read_text(encoding="utf-8")
                fences = re.findall(r"^```.*$", content, re.MULTILINE)
                self.assertEqual(len(fences) % 2, 0, "Unbalanced code fences")
                self.assertRegex(content, r"(?m)^```mermaid\s*$")
                if name != "README.md":
                    self.assertRegex(content, r"\]\((?:\./)?README\.md(?:#[^)]*)?\)")

    def test_overview_covers_the_complete_manifest_inventory(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        overview = (GUIDE / "README.md").read_text(encoding="utf-8")
        documented = re.findall(
            r"^\| `(faro(?:-[a-z0-9]+)*|azure-devops-rest-v7)` \|",
            overview, re.MULTILINE,
        )
        self.assertEqual(len(documented), len(set(documented)), "Duplicate inventory rows")
        self.assertEqual(set(documented), set(manifest["skills"]))

    def test_relative_links_resolve_and_each_runtime_skill_has_a_source(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        linked_files = set()
        for name in PAGES:
            page = GUIDE / name
            content = page.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)", content):
                parsed = urlsplit(target)
                if parsed.scheme or target.startswith("#"):
                    continue
                destination = (page.parent / unquote(parsed.path)).resolve()
                with self.subTest(page=name, link=target):
                    self.assertTrue(destination.exists(), str(destination))
                linked_files.add(destination)
        for name in manifest["skills"]:
            source = ROOT / "faro/SKILL.md" if name == "faro" else ROOT / "faro" / name / "SKILL.md"
            with self.subTest(skill=name):
                self.assertIn(source.resolve(), linked_files, "Missing source link in guide")
        self.assertIn((ROOT / "bootstrap/SKILL.md").resolve(), linked_files)

    def test_guide_preserves_authority_and_separates_state_vocabularies(self):
        overview = (GUIDE / "README.md").read_text(encoding="utf-8")
        for guard in (
            "no un motor que ejecute automáticamente",
            "no agrega reglas, estados ni permisos",
            "sin crear flujo artificial",
            "no es el mismo vocabulario",
            "no demuestra instalación",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, overview)

    def test_local_heading_fragments_resolve(self):
        for name in PAGES:
            page = GUIDE / name
            content = page.read_text(encoding="utf-8")
            for target in re.findall(r"(?<!!)\[[^\]]+\]\(([^)\s]+)\)", content):
                parsed = urlsplit(target)
                if parsed.scheme or not parsed.fragment:
                    continue
                destination = (page.parent / unquote(parsed.path)).resolve() if parsed.path else page
                source = destination.read_text(encoding="utf-8")
                source = re.sub(r"^```[^\n]*\n.*?^```\s*$", "", source, flags=re.MULTILINE | re.DOTALL)
                anchors = set()
                occurrences = {}
                for heading in re.findall(r"^#{1,6}\s+(.+)$", source, re.MULTILINE):
                    heading = re.sub(r"[`*_]", "", heading).lower()
                    slug = re.sub(r"[^\w -]", "", heading).replace(" ", "-")
                    count = occurrences.get(slug, 0)
                    occurrences[slug] = count + 1
                    anchors.add(f"{slug}-{count}" if count else slug)
                with self.subTest(page=name, link=target):
                    self.assertIn(unquote(parsed.fragment), anchors)


if __name__ == "__main__":
    unittest.main()
