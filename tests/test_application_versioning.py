"""Contract checks for application-version delivery policy, not live deploys."""
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"


class ApplicationVersioningTests(unittest.TestCase):
    def test_architecture_and_delivery_load_the_shared_policy(self):
        for name in ("faro-arq-laravel", "faro-arq-dotnet", "faro-arq-mobile", "faro-arq-generica", "faro-entrega"):
            with self.subTest(skill=name):
                self.assertIn("(../references/application-versioning.md)", (FARO / name / "SKILL.md").read_text())
        router = (FARO / "SKILL.md").read_text()
        self.assertIn("(references/application-versioning.md)", router)

    def test_sources_are_architecture_specific_and_laravel_has_no_env_dependency(self):
        policy = (FARO / "references/application-versioning.md").read_text()
        for phrase in ("config/app.php", "config('app.version')", "literal", "no leer ni escribir `.env`",
                       "no crear `VERSION`", "Directory.Build.props", "AssemblyVersion", "InformationalVersion",
                       "MSBuild", "Blazor", "mecanismo existente", "no inventar comandos"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, policy)

    def test_profile_captures_per_component_policy_without_forcing_migration(self):
        text = (FARO / "templates/project-profile.md").read_text()
        for phrase in ("## Versionado de aplicaciones", "CONFIRMAR_POR_ENTREGA", "AUTOMATICA",
                       "Componente", "Fuente", "Derivados", "Permisos", "Autorización", "PENDIENTE"):
            self.assertIn(phrase, text)
        policy = (FARO / "references/application-versioning.md").read_text()
        self.assertIn("sin reinicializar", policy)
        self.assertIn("no bloquea la inicialización", policy)
        self.assertIn("no modificar `contractVersion`", policy)

    def test_release_identity_is_idempotent_and_not_a_per_commit_bump(self):
        text = (FARO / "references/application-versioning.md").read_text()
        for phrase in ("reintento", "promoción", "rollback", "mismo artefacto", "no incrementar por cada commit",
                       "versión objetivo", "SHA", "digest", "colisión", "NO_VERIFICADO", "no reconstruir",
                       "CI", "escritor", "sin tag", "AUTOMATICA", "ambiente"):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase.casefold(), text.casefold())

    def test_delivery_authority_and_legacy_tag_policy_are_consistent(self):
        text = (FARO / "faro-entrega/references/versionado-y-tags.md").read_text()
        self.assertIn("application-versioning.md", text)
        self.assertIn("política AUTOMATICA", text)
        self.assertIn("no autoriza por sí sola versionar ni taguear", text)
        policy = (FARO / "references/application-versioning.md").read_text()
        self.assertIn("desarrollo autorizado", policy)
        self.assertIn("no implementa lectores", policy.casefold())
        self.assertIn("no autoriza desplegar", policy)
        development = (FARO / "faro-req-desarrollo/SKILL.md").read_text()
        self.assertIn("application-versioning.md", development)

    def test_missing_shared_policy_is_detected(self):
        with tempfile.TemporaryDirectory(dir=os.environ.get("TMPDIR")) as directory:
            suite = Path(directory) / "faro"
            shutil.copytree(FARO, suite)
            policy = suite / "references/application-versioning.md"
            self.assertTrue(policy.is_file())
            policy.unlink()
            result = subprocess.run([sys.executable, "-B", str(suite / "scripts/suite_validation.py"),
                                     "--suite-root", str(suite)], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stdout + result.stderr)
            self.assertIn("application-versioning.md", result.stdout)


if __name__ == "__main__":
    unittest.main()
