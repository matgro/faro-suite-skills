"""Contract tests for safe Azure DevOps agent-global configuration."""
from __future__ import annotations

from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
AZURE_ADAPTER = ROOT / "faro/faro-int-azure-devops/SKILL.md"
AZURE_CAPABILITY = ROOT / "faro/azure-devops-rest-v7/SKILL.md"
PROFILE = ROOT / "faro/templates/project-profile.md"


class AzureDevOpsGlobalEnvironmentContractTests(unittest.TestCase):
    def test_agent_global_azure_defaults_are_explicit_and_never_read_from_an_application_env(self):
        expected = {
            "AZDO_ORGANIZATION_URL",
            "AZDO_DEFAULT_PROJECT",
            "AZDO_DEFAULT_AREA_PATH",
            "AZDO_DEFAULT_TEAM",
        }
        for path in (AZURE_ADAPTER, AZURE_CAPABILITY, PROFILE):
            text = path.read_text(encoding="utf-8")
            self.assertTrue(expected <= set(item for item in expected if item in text), path)

        adapter = AZURE_ADAPTER.read_text(encoding="utf-8")
        capability = AZURE_CAPABILITY.read_text(encoding="utf-8")
        self.assertIn(".env` global perteneciente a un agente", adapter)
        self.assertIn("nunca busca ni lee `.env` de una aplicación", adapter.lower())
        self.assertIn(".env` global de un agente", capability)
        self.assertIn("nunca leer `.env` del workspace", capability.lower())
        self.assertIn("confirmación humana", adapter)


if __name__ == "__main__":
    unittest.main()
