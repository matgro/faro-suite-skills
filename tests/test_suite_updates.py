"""Offline regression tests for suite updates and renamed workflow routes."""
from __future__ import annotations

import json
import hashlib
import os
from pathlib import Path
import subprocess
import shutil
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR = ROOT / "faro/scripts/suite_validation.py"


class SuiteUpdateTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.suite = self.root / "faro"
        self.write("SKILL.md", "---\nname: faro\nmetadata:\n  hermes:\n    related_skills: [faro-req-desarrollo]\n---\nRouter: `faro-req-desarrollo`.\n")
        self.write("faro-req-desarrollo/SKILL.md", "---\nname: faro-req-desarrollo\nmetadata:\n  hermes:\n    related_skills: [faro]\n---\nDesarrollo.\n")
        self.write("references/suite-provenance.json", json.dumps({"packageVersion": "1.3.0"}))
        self.write("references/suite-changelog.json", json.dumps({
            "schemaVersion": 1,
            "releases": [{
                "version": "1.3.0",
                "changes": ["Rename the development skill."],
                "renamedSkills": {"faro-req-implementacion": "faro-req-desarrollo"},
            }],
        }))

    def write(self, relative, text):
        path = self.suite / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
        return path

    def validate(self, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(VALIDATOR), "--suite-root", str(self.suite), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def test_consistent_suite_is_accepted(self):
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_stale_related_skill_is_rejected(self):
        path = self.suite / "faro-req-desarrollo/SKILL.md"
        self.write("faro-req-desarrollo/SKILL.md", path.read_text().replace("[faro]", "[faro-req-implementacion]"))
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("related_skills apunta a skill ausente", result.stdout)

    def test_external_capability_is_not_mistaken_for_missing_suite_skill(self):
        path = self.suite / "faro-req-desarrollo/SKILL.md"
        self.write("faro-req-desarrollo/SKILL.md", path.read_text().replace("[faro]", "[faro, jira-rest-v3]"))
        result = self.validate()
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_stale_handoff_in_reference_is_rejected(self):
        self.write("references/handoff.md", "Siguiente ruta: `faro-req-implementacion`.\n")
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("referencia a skill ausente", result.stdout)

    def test_old_directory_with_new_name_is_rejected(self):
        (self.suite / "faro-req-desarrollo").rename(self.suite / "faro-req-implementacion")
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("nombre/ruta no coincide", result.stdout)

    def test_extra_obsolete_skill_is_rejected(self):
        self.write("faro-req-implementacion/SKILL.md", "---\nname: faro-req-implementacion\nmetadata:\n  hermes:\n    related_skills: [faro]\n---\nObsoleta.\n")
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("skill retirada todavía instalada", result.stdout)

    def test_changelog_version_mismatch_is_rejected(self):
        self.write("references/suite-provenance.json", json.dumps({"packageVersion": "2.0.0"}))
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("primera release no coincide", result.stdout)

    def test_missing_changelog_is_rejected(self):
        (self.suite / "references/suite-changelog.json").unlink()
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("changelog/provenance inválido", result.stdout)

    def test_rename_cycle_is_rejected(self):
        path = self.suite / "references/suite-changelog.json"
        changelog = json.loads(path.read_text())
        changelog["releases"][0]["renamedSkills"]["faro-req-desarrollo"] = "faro-req-implementacion"
        self.write("references/suite-changelog.json", json.dumps(changelog))
        result = self.validate()
        self.assertEqual(result.returncode, 1)
        self.assertIn("ciclo de renombres", result.stdout)

    def test_renamed_workflow_route_has_actionable_diagnostic_without_writes(self):
        workflow = self.root / "workflow.json"
        workflow.write_text(json.dumps({"nextRoute": "faro-req-implementacion", "authorization": {"status": "approved"}}))
        before = workflow.read_bytes()
        result = self.validate("--workflow", workflow)
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("faro-req-implementacion -> faro-req-desarrollo", result.stdout)
        self.assertIn("autorización", result.stdout)
        self.assertEqual(workflow.read_bytes(), before)

    def test_current_workflow_route_is_accepted(self):
        workflow = self.root / "workflow.json"
        workflow.write_text(json.dumps({"nextRoute": "faro-req-desarrollo"}))
        result = self.validate("--workflow", workflow)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_unknown_workflow_route_is_rejected(self):
        workflow = self.root / "workflow.json"
        workflow.write_text(json.dumps({"nextRoute": "faro-inexistente"}))
        result = self.validate("--workflow", workflow)
        self.assertEqual(result.returncode, 1)
        self.assertIn("nextRoute apunta a skill ausente", result.stdout)

    def test_malformed_workflow_is_reported_without_writes(self):
        workflow = self.root / "workflow.json"
        workflow.write_bytes(b'{"nextRoute":')
        result = self.validate("--workflow", workflow)
        self.assertEqual(result.returncode, 1)
        self.assertIn("workflow/changelog inválido", result.stdout)
        self.assertEqual(workflow.read_bytes(), b'{"nextRoute":')


class UpdateIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR"))
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.suite = self.root / "faro"
        shutil.copytree(ROOT / "faro", self.suite)
        self.workspace = self.root / "workspace"
        for source, destination in {
            "AGENTS.md": "AGENTS.md",
            "faro-workspace-manifest.json": "context/faro-workspace.json",
            "stats.json": "context/stats.json",
            "context-README.md": "context/README.md",
            "project-profile.md": "context/requirements/project-profile.md",
        }.items():
            path = self.workspace / destination
            path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(self.suite / "templates" / source, path)

    def run_script(self, relative, *arguments):
        return subprocess.run(
            [sys.executable, "-B", str(self.root / relative), *map(str, arguments)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONIOENCODING": "utf-8"},
        )

    def test_doctor_blocks_stale_route_and_preserves_entire_workspace(self):
        workflow = self.workspace / "context/workflow.json"
        workflow.write_text(json.dumps({"nextRoute": "faro-req-implementacion", "authorization": {"status": "approved", "artifactVersion": "1"}}))
        before = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        result = self.run_script("faro/faro-doctor/scripts/doctor.py", "--root", self.workspace, "--strict")
        self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
        self.assertIn("faro-req-implementacion -> faro-req-desarrollo", result.stdout)
        after = {path.relative_to(self.root): path.read_bytes() for path in self.root.rglob("*") if path.is_file()}
        self.assertEqual(after, before)

    def test_package_rejects_broken_reference_even_with_valid_checksums(self):
        path = self.suite / "faro-req-desarrollo/SKILL.md"
        path.write_text(path.read_text(encoding="utf-8").replace("[faro,", "[faro-inexistente,"), encoding="utf-8")
        self.prepare_package()
        result = self.run_script("tests/validate_package.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("faro-inexistente", result.stdout + result.stderr)

    def prepare_package(self):
        shutil.copyfile(ROOT / "manifest.json", self.root / "manifest.json")
        shutil.copytree(ROOT / "bootstrap", self.root / "bootstrap")
        (self.root / "tests").mkdir()
        shutil.copyfile(ROOT / "tests/validate_package.py", self.root / "tests/validate_package.py")
        checksums = "".join(hashlib.sha256(path.read_bytes()).hexdigest() + "  " + path.relative_to(self.root).as_posix() + "\n" for path in sorted(self.suite.rglob("*")) if path.is_file())
        (self.root / "checksums.sha256").write_text(checksums, encoding="utf-8")

    def test_duplicate_manifest_skill_is_rejected(self):
        self.prepare_package()
        path = self.root / "manifest.json"
        manifest = json.loads(path.read_text())
        manifest["skills"].append(manifest["skills"][0])
        path.write_text(json.dumps(manifest))
        result = self.run_script("tests/validate_package.py")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("duplicate", result.stdout + result.stderr)

    def test_clean_install_and_initialized_workspace_pass(self):
        self.prepare_package()
        installed = self.root / "installed/faro"
        shutil.copytree(self.suite, installed)
        result = self.run_script("tests/validate_package.py", "--installed-at", installed)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertTrue((installed / "faro-req-desarrollo/SKILL.md").is_file())
        self.assertFalse((installed / "faro-req-implementacion").exists())
        result = self.run_script("installed/faro/faro-doctor/scripts/doctor.py", "--root", self.workspace, "--strict")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_release_normalization_generates_portable_checksums(self):
        path = self.suite / "faro-req-desarrollo/SKILL.md"
        path.write_bytes(path.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8"))
        result = subprocess.run(
            [sys.executable, "-B", str(ROOT / "tools/update_checksums.py"), "--package-root", str(self.root), "--normalize-line-endings"],
            capture_output=True, text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn(b"\r\n", path.read_bytes())
        for line in (self.root / "checksums.sha256").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256((self.root / relative).read_bytes()).hexdigest())

    def test_published_tag_roundtrip_with_windows_git_conversion(self):
        self.prepare_package()
        provenance_path = self.suite / "references/suite-provenance.json"
        provenance = json.loads(provenance_path.read_text())
        provenance["repository"] = self.root.as_posix()
        provenance_path.write_text(json.dumps(provenance), encoding="utf-8")
        shutil.copyfile(ROOT / ".gitattributes", self.root / ".gitattributes")
        subprocess.run([sys.executable, "-B", str(ROOT / "tools/update_checksums.py"), "--package-root", str(self.root), "--normalize-line-endings"], check=True, capture_output=True)

        def git(*arguments):
            result = subprocess.run(
                ["git", "-c", "user.name=FARO test", "-c", "user.email=faro-test@example.invalid", "-C", str(self.root), *arguments],
                capture_output=True, text=True, check=True,
            )
            return result.stdout.strip()

        git("init", "--quiet")
        git("add", "faro", "checksums.sha256", ".gitattributes")
        git("commit", "--quiet", "-m", "Offline release fixture")
        git("tag", "-a", "v1.3.0", "-m", "Offline annotated release")
        commit = git("rev-parse", "HEAD")
        result = self.run_script("faro/faro-doctor/scripts/doctor.py", "--root", self.workspace, "--strict", "--verify-suite-origin")
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn(f"({commit})", result.stdout)

        cloned = self.root / "clean-checkout"
        git("-c", "core.autocrlf=true", "clone", "--quiet", "--no-hardlinks", str(self.root), str(cloned))
        checksums = (cloned / "checksums.sha256").read_text().splitlines()
        for line in checksums:
            digest, relative = line.split("  ", 1)
            self.assertEqual(digest, hashlib.sha256((cloned / relative).read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main()
