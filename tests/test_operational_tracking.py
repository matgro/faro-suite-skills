"""Contract tests for remote operational authority and delivery/closure separation.

These checks are deliberately offline. They verify the FARO instructions and
Azure REST capability contract; they do not claim a live Jira/Azure mutation.
"""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
FARO = ROOT / "faro"


def runtime_text(relative: str) -> str:
    return (FARO / relative).read_text(encoding="utf-8")


class WorkTrackingAuthorityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.adapters = {
            "jira": runtime_text("faro-int-jira/SKILL.md"),
            "azure": runtime_text("faro-int-azure-devops/SKILL.md"),
        }

    def test_every_work_class_has_a_type_workflow_and_relationship_contract(self):
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                for local_type in ("`RM`", "`BUG`", "`TEC`", "`INC`", "`TASK`"):
                    self.assertIn(local_type, adapter)
                self.assertIn("mapeo", adapter.lower())
                self.assertIn("workflow", adapter)
                self.assertIn("padre/hijo", adapter)
                self.assertIn("origen", adapter)
                self.assertIn("derivado", adapter)

    def test_remote_state_is_canonical_and_every_mutation_is_read_back(self):
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                self.assertIn("estado operativo remoto es canónico", adapter)
                self.assertIn("Después de crear", adapter)
                self.assertIn("releer", adapter)
                self.assertIn("una respuesta http exitosa o", adapter.lower())
                self.assertIn("No persistir un segundo estado operativo", adapter)

    def test_direct_and_derived_work_keep_independent_items(self):
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                self.assertIn("BUG y TEC", adapter)
                self.assertIn("BUG derivado de INC requiere autorización explícita", adapter)
                self.assertIn("Nunca convertir", adapter)
                self.assertIn("vínculos bidireccionales", adapter)
                self.assertIn("TASK", adapter)
                self.assertIn("hija", adapter)

    def test_delivery_evidence_never_implies_done(self):
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                self.assertIn("Push, PR, merge, release, tag o despliegue", adapter)
                self.assertIn("no autorizan ni implican `DONE`", adapter)
                self.assertIn("operación explícita de cierre", adapter)

    def test_migrated_entries_link_one_read_back_item_without_overwrite(self):
        expected_provider = {"jira": "JIRA", "azure": "AZURE_DEVOPS"}
        for name, adapter in self.adapters.items():
            with self.subTest(adapter=name):
                self.assertIn("work_item_contract.py link-external", adapter)
                self.assertIn(f"--external-provider {expected_provider[name]}", adapter)
                self.assertIn("triple totalmente vacío", adapter)
                self.assertIn("nunca se sobrescribe", adapter)
                self.assertIn("releer", adapter)


class AzureRestContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.capability = runtime_text("azure-devops-rest-v7/SKILL.md")

    def test_discovery_and_readback_are_per_type_and_relation(self):
        for guard in (
            "workitemrelationtypes", "cada tipo remoto mapeado",
            "Estados por tipo", "/relations/-", "$expand=Relations",
            "Leer después ambos items", "System.State",
        ):
            with self.subTest(guard=guard):
                self.assertIn(guard, self.capability)

    def test_capability_does_not_classify_or_close_by_delivery(self):
        self.assertIn("sin decidir su clasificación", self.capability)
        self.assertIn("no implican `DONE`", self.capability)
        self.assertIn("operación explícita de cierre", self.capability)
        self.assertIn("nunca lo infiere", self.capability)


class DeliverySeparationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.delivery = runtime_text("faro-entrega/SKILL.md")
        cls.record = runtime_text("faro-entrega/assets/delivery-record.md")

    def test_delivery_records_evidence_but_never_closes_the_item(self):
        self.assertIn("Entrega no es cierre", self.delivery)
        self.assertIn("no solicitar `DONE` ni `CANCELLED` desde esta skill", self.delivery)
        self.assertIn("operación explícita de cierre", self.delivery)
        self.assertIn("Releer después el comentario/vínculo", self.delivery)
        self.assertNotIn("Al completar el alcance autorizado, transicionar al estado remoto `DONE`", self.delivery)

    def test_external_success_and_tracking_failure_are_reported_separately(self):
        self.assertIn("entrega realizada y seguimiento bloqueado", self.delivery)
        self.assertIn("No repetir ni revertir automáticamente", self.delivery)
        self.assertIn("sin declarar la unidad completa", self.delivery)

    def test_delivery_uses_the_resolved_mutable_dossier_and_one_evidence_record(self):
        self.assertIn("work_item_contract.py resolve", self.delivery)
        self.assertIn("expediente congelado", self.delivery)
        self.assertIn("<ID>-entrega.md", self.delivery)
        self.assertIn("assets/delivery-record.md", self.delivery)
        self.assertIn('artifact_type: "DELIVERY_EVIDENCE"', self.record)
        self.assertIn("Historial de intentos", self.record)
        self.assertIn("no representa el estado operativo", self.record)


if __name__ == "__main__":
    unittest.main()
