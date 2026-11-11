"""Offline contract checks for the documented delivery message format."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeliveryMessageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "faro/faro-entrega/SKILL.md").read_text(encoding="utf-8")
        cls.section = cls.skill.split("## Mensajes de commit y PR\n", 1)[1].split("\n## ", 1)[0]

    def test_commit_and_pr_use_separate_title_and_description(self):
        self.assertIn("primera línea como título breve, línea en blanco", self.section)
        self.assertIn("sin repetir el título", self.section)
        self.assertIn("Preservar los saltos de línea", self.section)
        self.assertIn("Para un PR, usar la primera línea como título y el resto como descripción", self.section)

    def test_description_is_short_and_functional(self):
        self.assertIn("qué funcionalidad cambió, se agregó o se quitó", self.section)
        self.assertIn("Usar una o dos oraciones", self.section)
        self.assertIn("no incluir código, nombres de clases ni detalles internos", self.section)

    def test_task_references_are_verified_and_at_the_end(self):
        self.assertIn("con formato `#<ID>`", self.section)
        self.assertIn("Si hay varias, incluir una por línea", self.section)
        self.assertIn("Usar sólo tareas asociadas verificadas; no inventar IDs", self.section)
        self.assertIn("si no hay tareas asociadas, omitir ese bloque", self.section)
        self.assertIn("No incluir estas referencias en el título", self.section)

    def test_example_has_distinct_description_and_multiple_tasks(self):
        example = re.search(r"```text\n(.*?)\n```", self.section, re.DOTALL)
        if example is None:
            self.fail("Missing commit message example")
        title, description, tasks = example.group(1).split("\n\n")
        self.assertNotEqual(title, description)
        self.assertNotIn("#", title)
        self.assertEqual(tasks.splitlines(), ["#9999", "#10000"])


if __name__ == "__main__":
    unittest.main()
