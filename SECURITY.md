# Security policy

## Never commit

Do not commit or publish:

- API keys, access tokens, passwords, session cookies, authorization headers, or private keys.
- `.env` files or credential stores.
- Private certificates or SSH keys.
- Production database exports, client documents, personal data, clinical data, or logs containing them.
- Configuration values copied from a user application when they contain secrets.

The FARO skills intentionally describe metadata-only integrations. For example, a Jira URL/project key or Azure DevOps organization/project/area can be documented when appropriate; credentials, including Azure DevOps PATs, must remain outside this repository and outside FARO artifacts.

## Bootstrap safety

The bootstrap skill may retrieve a user-approved FARO repository into temporary staging or copy a reviewed local release into an agent's skills root. It must validate `manifest.json` and `checksums.sha256`; it must inspect and compare an existing FARO installation; and it must get explicit user confirmation before replacing that existing installation. It must not download or execute arbitrary remote scripts.

## Before publishing

Run:

```bash
python3 tests/validate_package.py
git diff --check
git status --short
```

Review all staged files before pushing. A secret scanner such as gitleaks is recommended in CI.

## Reporting an exposed secret

If a secret reaches Git history, revoke or rotate it immediately. Removing it from a later commit is not enough. Then contact the repository maintainers through a private channel and rewrite history if required by the affected provider's incident process.
