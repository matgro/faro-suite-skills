"""Offline contract checks for delivery versioning and tag authorization."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class DeliveryVersioningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.skill = (ROOT / "faro/faro-entrega/SKILL.md").read_text(encoding="utf-8")
        cls.reference = (ROOT / "faro/faro-entrega/references/versionado-y-tags.md").read_text(encoding="utf-8")

    def test_delivery_requires_version_and_tag_decision(self):
        self.assertIn("Antes de commit, push, PR o release", self.skill)
        self.assertIn("preguntar en una sola confirmación", self.skill)
        self.assertIn("references/versionado-y-tags.md", self.skill)
        self.assertIn("antes de modificar la versión o ejecutar la entrega", self.skill)

    def test_confirmation_does_not_repeat_or_infer_authorization(self):
        self.assertIn("No repetir decisiones ya autorizadas", self.reference)
        self.assertIn("preguntar sólo por crear/publicar el tag", self.reference)
        self.assertIn("no autoriza por sí sola versionar ni taguear", self.reference)
        self.assertIn("sin incrementar o sin tag cuando el usuario lo decide explícitamente", self.reference)
        self.assertIn("Si sólo se autoriza crear un tag local, no publicarlo", self.reference)

    def test_semver_is_based_on_accumulated_public_impact(self):
        self.assertIn("alcance acumulado desde la última versión publicada", self.reference)
        self.assertIn("Respetar primero la política de versionado explícita del proyecto", self.reference)
        for rule in (
            "| PATCH | Corrección compatible",
            "| MINOR | Funcionalidad nueva compatible o deprecación",
            "| MAJOR | Cambio incompatible",
            "Aplicar el mayor impacto del conjunto",
            "el prefijo no prueba compatibilidad",
            "Para `0.y.z` o prereleases",
        ):
            with self.subTest(rule=rule):
                self.assertIn(rule, self.reference)

    def test_release_metadata_and_validated_commit_stay_together(self):
        for field in ("manifest.json.version", "suite-provenance.json.packageVersion/ref", "suite-changelog.json", "CHANGELOG.md", "checksums.sha256"):
            with self.subTest(field=field):
                self.assertIn(field, self.reference)
        self.assertIn("No cambiar `contractVersion`", self.reference)
        self.assertIn("tag anotado sobre el SHA validado", self.reference)
        self.assertIn("Si el tag ya existe y coincide, verificarlo en vez de recrearlo", self.reference)

    def test_remote_tag_publication_is_explicit_and_verified(self):
        self.assertIn("Nunca mover, sobrescribir, borrar ni reutilizar un tag publicado", self.reference)
        self.assertIn("No usar `--tags` ni force push", self.reference)
        self.assertIn("git push --atomic", self.reference)
        self.assertIn("git ls-remote", self.reference)
        self.assertIn("refs/tags/<tag>^{}", self.reference)
        self.assertIn("no el SHA del objeto tag", self.reference)
        self.assertIn("Un push de rama no publica automáticamente el tag", self.reference)
        self.assertIn("No abrir PR, crear una release en la plataforma ni desplegar", self.reference)

    def test_primary_sources_are_documented(self):
        for source in ("https://semver.org/", "https://www.conventionalcommits.org/", "https://git-scm.com/docs/git-tag"):
            with self.subTest(source=source):
                self.assertIn(source, self.reference)


if __name__ == "__main__":
    unittest.main()
