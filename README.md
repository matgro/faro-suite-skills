<p align="center">
  <img src="assets/faro-hero.svg" alt="FARO — a lighthouse guiding governed delivery for AI agents" width="100%" />
</p>

<h1 align="center">FARO Suite Skills</h1>

<p align="center">
  A governed path from request to verified delivery for AI agents.
</p>

<p align="center">
  <strong>15 skills</strong> · Complete lifecycle · Integrity checked · Agent-portable
</p>

---

## Why FARO

AI agents can write code quickly. FARO gives that work a clear operating path: establish context, formalize the request, inspect the real codebase, plan, implement, test, validate, and deliver with evidence.

It is designed for teams that want an agent to move autonomously without losing traceability, scope control, or a clear human approval boundary.

| FARO provides | So your agent can |
| --- | --- |
| A single entry point | Route work to the right specialist instead of improvising phases |
| Explicit project contracts | Know what is observed, authorized, pending, or out of scope |
| Requirements-to-delivery traceability | Keep decisions, plans, QA evidence, and validation connected |
| Controlled handoffs | Move forward only when the current phase is genuinely complete |
| A portable skill suite | Run the same delivery discipline across compatible agents |

## The path

```text
Request → Context → Requirements → Technical plan → Build → QA → Validation → Delivery
```

FARO does not collapse those stages into paperwork. Each specialist skill exists to make one transition clear, evidence-based, and reversible when the facts do not support moving forward.

## Quick start

Clone a reviewed release or commit:

```bash
git clone https://github.com/matgro/faro-suite-skills.git
cd faro-suite-skills
```

Then give an agent the bootstrap skill and the local checkout, tag, or commit:

```text
Load this skill and use it to install or update FARO:
/path/to/faro-suite-skills/bootstrap/SKILL.md

Install from this reviewed checkout: /path/to/faro-suite-skills
Use the target agent's configured skills directory. If FARO is already installed,
show me the destination and comparison, then ask before replacing it.
```

The bootstrap skill installs the complete `faro/` tree. When an existing installation is found, it must inspect it, compare it with the incoming release, and obtain explicit user confirmation before replacement.

> There is no universal skill directory. FARO intentionally lets the target agent determine its own configured skills root instead of assuming a vendor-specific path.

### Manual installation

Copy the complete `faro/` directory into the target agent's skills root, preserving every nested path:

```text
<agent-skills-root>/faro/
├── SKILL.md
├── faro-inicializacion/
├── faro-doctor/
├── faro-req-ingenieria/
├── faro-qa-ejecucion/
└── ...
```

Do not install only `faro/SKILL.md`. FARO routes work to its specialist skills and several of them depend on templates, references, assets, and validation scripts.

## What is included

```text
faro/                         Runtime suite
├── SKILL.md                  Router and lifecycle contract
├── faro-inicializacion/      Safe project contract initialization
├── faro-doctor/              Read-only workspace diagnosis
├── faro-arq-*/               Evidence-based architecture routes
├── faro-req-*/               Requirements, analysis, implementation, validation
├── faro-qa-ejecucion/        QA cases and evidence
├── faro-ux/                  Visible-flow and interface design
├── faro-entrega/             Explicit commit, PR, release, and deployment handoff
└── faro-int-jira/            Optional governed Jira integration

bootstrap/SKILL.md            Agent-guided installation and safe update
manifest.json                 Suite contract and complete skill inventory
checksums.sha256              SHA-256 integrity inventory for the runtime tree
tests/validate_package.py     Dependency-free package validator
```

## Verify a release

Validate the repository before distribution:

```bash
python3 tests/validate_package.py
```

Validate an installed copy against the release:

```bash
python3 tests/validate_package.py --installed-at /path/to/your-agent/skills/faro
```

The validator checks the 15 runtime skills, package manifest, bootstrap contract, file inventory, SHA-256 checksums, and common secret patterns.

## Hermes Agent location

For Hermes Agent, the active profile normally stores skills in `$HERMES_HOME/skills`, with `~/.hermes/skills` as the default-profile fallback:

```text
${HERMES_HOME:-$HOME/.hermes}/skills/faro/
```

The runtime may require a new session or a skill-index refresh before it discovers a newly copied suite.

## Release and security policy

Use a tagged release or pinned commit. When updating an existing installation, compare first and replace the entire `<skills-root>/faro/` tree only after explicit user approval. This avoids a mixed suite assembled from different releases.

Do not add API keys, tokens, passwords, private certificates, cookies, `.env` files, client data, or production exports. See [SECURITY.md](SECURITY.md) for the full policy.

## License

MIT — see [LICENSE](LICENSE).
