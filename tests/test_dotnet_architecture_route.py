"""Contract tests for FARO's .NET bootstrap and architecture route."""
from __future__ import annotations

import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class DotnetArchitectureRouteContractTests(unittest.TestCase):
    def test_dotnet_new_and_existing_projects_have_a_dedicated_evidence_route(self):
        manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.assertIn("faro-bootstrap-dotnet", manifest["skills"])
        self.assertIn("faro-arq-dotnet", manifest["skills"])

        router = (ROOT / "faro/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("`faro-bootstrap-dotnet`", router)
        self.assertIn("`faro-arq-dotnet`", router)
        self.assertIn(".NET nuevo autorizado", router)
        self.assertIn(".NET/C# confirmado", router)

        initialization = (ROOT / "faro/faro-inicializacion/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("faro-bootstrap-dotnet", initialization)
        self.assertIn("faro-arq-dotnet", initialization)
        procedure = initialization.split("## Procedimiento", 1)[1]
        self.assertLess(
            procedure.index("faro-bootstrap-dotnet"),
            procedure.index("materializar `context/`"),
            "A new .NET project must be scaffolded before FARO writes its contract.",
        )

        bootstrap = (ROOT / "faro/faro-bootstrap-dotnet/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("dotnet new", bootstrap)
        self.assertIn("destino vacío", bootstrap)
        self.assertIn("faro-inicializacion", bootstrap)
        self.assertIn("faro-arq-dotnet", bootstrap)

        architecture = (ROOT / "faro/faro-arq-dotnet/SKILL.md").read_text(encoding="utf-8")
        self.assertIn("global.json", architecture)
        self.assertIn("Directory.Packages.props", architecture)
        self.assertIn(".csproj", architecture)
        self.assertIn("context/architecture-dotnet.md", architecture)
        self.assertIn("proyecto nuevo", architecture)
        self.assertIn("proyecto existente", architecture)
        self.assertIn("No leer ni copiar secretos", architecture)

        template = (ROOT / "faro/faro-arq-dotnet/templates/architecture-dotnet.md").read_text(encoding="utf-8")
        for heading in ("Plataforma y comandos", "Componentes y límites observados", "Entradas, persistencia, contratos e integraciones"):
            self.assertIn(heading, template)


if __name__ == "__main__":
    unittest.main()
