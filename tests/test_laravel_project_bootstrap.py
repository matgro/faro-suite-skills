"""Contract tests for bootstrapping a new Laravel project under FARO."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SKILL_NAME = "faro-bootstrap-laravel"


class LaravelProjectBootstrapContractTests(unittest.TestCase):
    def test_new_laravel_project_has_an_explicit_bootstrap_route(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn(SKILL_NAME, manifest["skills"])

        router = (ROOT / "faro/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(f"`{SKILL_NAME}`", router)
        self.assertIn("Laravel/API nuevo autorizado", router)

        initialization = (ROOT / "faro/faro-inicializacion/SKILL.md").read_text(encoding="utf-8")
        self.assertIn(SKILL_NAME, initialization)
        procedure = initialization.split("## Procedimiento", 1)[1]
        self.assertLess(
            procedure.index(SKILL_NAME),
            procedure.index("materializar `context/`"),
            "A new Laravel project must be routed to the bootstrap before FARO writes its contract.",
        )

        skill = (ROOT / f"faro/{SKILL_NAME}/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("composer create-project laravel/laravel", skill)
        self.assertIn("destino vacío", skill)
        self.assertIn("faro-inicializacion", skill)
        self.assertIn("faro-arq-laravel", skill)


if __name__ == "__main__":
    unittest.main()
