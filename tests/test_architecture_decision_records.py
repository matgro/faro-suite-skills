"""Contract tests for FARO ADR/RFC architecture-decision governance."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parent.parent
FARO = ROOT / "faro"


class ArchitectureDecisionRecordTests(unittest.TestCase):
    def test_adr_and_rfc_are_routed_and_preserve_their_distinct_lifecycle(self) -> None:
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertTrue({"faro-arq-adr", "faro-arq-rfc"}.issubset(manifest["skills"]))

        adr = (FARO / "faro-arq-adr" / "SKILL.md").read_text(encoding="utf-8")
        rfc = (FARO / "faro-arq-rfc" / "SKILL.md").read_text(encoding="utf-8")
        router = (FARO / "SKILL.md").read_text(encoding="utf-8")
        analysis = (FARO / "faro-req-analisis-tecnico" / "SKILL.md").read_text(encoding="utf-8")
        development = (FARO / "faro-req-desarrollo" / "SKILL.md").read_text(encoding="utf-8")

        self.assertIn("costosa de revertir", adr)
        self.assertIn("proposed", adr)
        self.assertIn("accepted", adr)
        self.assertIn("deprecated", adr)
        self.assertIn("superseded", adr)
        self.assertIn("context/decisions/adr/ADR-NNN-<slug>.md", adr)
        self.assertIn("context/decisions/adr/README.md", adr)
        self.assertIn("acuerdo de personas fuera", rfc)
        self.assertIn("Nada dependiente de un RFC abierto", rfc)
        self.assertIn("context/decisions/rfc/RFC-NNN-<slug>.md", rfc)
        self.assertIn("faro-arq-adr", router)
        self.assertIn("faro-arq-rfc", router)
        self.assertIn("faro-arq-adr", analysis)
        self.assertIn("faro-arq-rfc", analysis)
        self.assertIn("RFC abierto", development)
        self.assertIn("ADRs relevantes", development)
        self.assertIn("contradice", development)

    def test_templates_and_nzt_reference_keep_rationale_traceable(self) -> None:
        for path in (
            FARO / "faro-arq-adr" / "assets" / "adr.md",
            FARO / "faro-arq-adr" / "assets" / "adr-index.md",
            FARO / "faro-arq-rfc" / "assets" / "rfc.md",
            FARO / "references" / "nzt-architecture-decisions.md",
            FARO / "references" / "adr-ai-memory.md",
        ):
            self.assertTrue(path.is_file(), path)

        reference = (FARO / "references" / "nzt-architecture-decisions.md").read_text(encoding="utf-8")
        self.assertIn("nzt-architecture-adr", reference)
        self.assertIn("nzt-architecture-rfc", reference)
        self.assertIn("RFC pregunta; ADR registra", reference)
        self.assertIn("2094543", reference)

        ai_reference = (FARO / "references" / "adr-ai-memory.md").read_text(encoding="utf-8")
        self.assertIn("https://medium.com/all-you-need-is-clean-code/adr-la-memoria-arquitect", ai_reference)
        self.assertIn("Miguel Ángel Sánchez", ai_reference)
        self.assertIn("MADR", ai_reference)
        self.assertIn("ADRs relevantes", ai_reference)

        template = (FARO / "faro-arq-adr" / "assets" / "adr.md").read_text(encoding="utf-8")
        for field in ("status:", "date:", "decision-makers:", "supersedes:", "superseded-by:", "## Contexto y problema", "## Consecuencias"):
            self.assertIn(field, template)


if __name__ == "__main__":
    unittest.main()
