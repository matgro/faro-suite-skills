"""Offline checks for the agent-guided bootstrap release-selection contract."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]


class BootstrapContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bootstrap = (ROOT / "bootstrap/SKILL.md").read_text(encoding="utf-8")
        pattern_match = re.search(
            r"Eligible tags must match `([^`]+)`", cls.bootstrap
        )
        assert pattern_match is not None, "Bootstrap must declare its stable tag pattern"
        cls.tag_pattern = pattern_match.group(1)

    def test_stable_tag_pattern_excludes_nonrelease_refs(self):
        for ref in ("refs/tags/v0.0.0", "refs/tags/v1.3.0", "refs/tags/v12.10.20"):
            with self.subTest(ref=ref):
                self.assertIsNotNone(re.fullmatch(self.tag_pattern, ref))
        for ref in (
            "refs/heads/main", "refs/tags/v1.3.0-rc.1", "refs/tags/v1.3.0+build",
            "refs/tags/v1.3.0^{}", "refs/tags/v01.3.0", "refs/tags/v1.3",
        ):
            with self.subTest(ref=ref):
                self.assertIsNone(re.fullmatch(self.tag_pattern, ref))

    def test_documented_numeric_order_handles_double_digits(self):
        self.assertIn("components as integers, not alphabetically", self.bootstrap)
        versions = []
        for ref in ("refs/tags/v1.9.0", "refs/tags/v1.10.0", "refs/tags/v1.3.0"):
            version_match = re.fullmatch(self.tag_pattern, ref)
            assert version_match is not None
            versions.append(tuple(map(int, version_match.groups())))
        self.assertEqual(max(versions), (1, 10, 0))

    def test_explicit_sources_and_failure_guards_remain_documented(self):
        for rule in (
            "honor that source exactly",
            "use the repository recorded in the installed",
            "Do not fall back to branch HEAD, an older release, or the installed version",
            "stop without downgrading",
            "If the tag changes during retrieval, stop",
            "using its peeled `^{}` commit for an annotated tag",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.bootstrap)

    def test_replacement_and_integrity_checks_remain_required(self):
        for rule in (
            "ask the user for one explicit confirmation",
            "if the same version is already installed and the trees match",
            "compare the staged runtime inventory and hashes",
            "A missing tag, different tree or unresolved reference blocks installation",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.bootstrap)


if __name__ == "__main__":
    unittest.main()
