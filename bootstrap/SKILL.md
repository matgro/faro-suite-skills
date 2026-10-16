---
name: faro-bootstrap
description: Use when installing or updating the complete FARO skill suite.
version: 1.1.0
author: FARO Agent Skills contributors
license: MIT
metadata:
  agentskills:
    tags: [faro, installation, update, bootstrap, portability]
---

# FARO Bootstrap

## Purpose

Install or update the complete FARO skill suite without requiring the user to clone the repository first. The user supplies this bootstrap skill plus an approved FARO repository URL, a release/tag/commit, or a local source. The agent retrieves the package into temporary staging, validates it, then installs the complete `faro/` tree declared by `manifest.json`.

This bootstrap is an installation guide for an agent with filesystem access and, when a remote source is supplied, network access plus a repository-download capability such as Git. It does not assume a particular agent runtime or a fixed skills directory.

## Resolve the source

1. Obtain one explicit source from the user: a local package directory, a FARO repository URL, or a repository URL paired with a release, tag, or commit. Do not invent a remote source.
2. When the source is a repository URL, retrieve it into temporary staging. If the user supplied a tag or commit, resolve exactly that revision. If the user supplied only a repository URL, resolve the current revision, record its immutable commit identifier, and report it before installation.
3. When the user supplied only this bootstrap by URL, derive the package repository only when it is unambiguously encoded by that URL. Otherwise request the repository URL; never guess one from a skill name.
4. Retrieve package files only. Do not execute downloaded scripts, installers, hooks, or binaries. The bootstrap itself directs the installation; repository contents are data until validation succeeds.
5. Read staged `manifest.json`, `checksums.sha256`, and the `faro/` tree. Confirm that the manifest names this package, declares `faro` as the entry point, and lists every existing runtime skill.
6. Determine the target runtime's skills root from its documented configuration or the user's direction. Do not assume a Hermes path for another agent.

**Complete when:** the source revision, staging location, and destination skills root are known.

## Install or update

1. Inspect `<skills-root>/faro/` before writing. If absent, install the complete staged `faro/` tree there.
2. If `<skills-root>/faro/` already exists, compare it with the incoming tree. Report the installed version when observable, the incoming repository and resolved revision, changed files when observable, and whether local modifications would be replaced.
3. Before replacing an existing installation, ask the user for one explicit confirmation that names the exact destination and states that the old `faro/` directory will be replaced by the incoming complete suite. Do not overwrite merely because an update was requested.
4. After confirmation, stage the incoming `faro/` directory beside the destination, validate the staged tree against `manifest.json` and `checksums.sha256`, then replace the destination. Preserve no partial destination on failure; restore the previous tree when the filesystem operation fails.
5. Do not copy individual skills or flatten the directory tree. Preserve all relative paths under `faro/`.

**Complete when:** the target contains `<skills-root>/faro/SKILL.md`, every manifest skill, and every checksummed file.

## Verification

1. Compare the installed tree to `checksums.sha256` and ensure there are no missing or extra distributed files.
2. Report the final destination, source repository or local source, resolved revision, suite version, number of skills, and whether the target runtime needs a session restart or skill-index refresh.
3. If the runtime cannot discover skills installed during the current session, state that limitation; do not claim that `/faro` is immediately available.
4. Remove temporary source staging after a successful installation unless the user explicitly requested that it be retained.

## Safety rules

- Never copy credentials, `.env` files, tokens, private keys, client data, or runtime state.
- Never fetch an unspecified source, follow repository redirects without reporting the final source, or execute remote scripts.
- Do not modify the source checkout during installation.
- If the target cannot be identified, the source cannot be validated, or a replacement confirmation is absent, stop and explain what is needed.

## Verification checklist

- [ ] User supplied a local source, repository URL, or pinned revision explicitly.
- [ ] Remote source, if any, was retrieved only into temporary staging and no downloaded code was executed.
- [ ] Resolved commit was recorded when the source was remote.
- [ ] `manifest.json` and `checksums.sha256` validated the incoming tree.
- [ ] Target skills root was established from the target agent or user direction.
- [ ] Existing FARO installation was inspected before replacement.
- [ ] User explicitly confirmed replacement when an existing installation was found.
- [ ] Installed `faro/` tree matches the incoming release completely.
- [ ] Any needed restart/index refresh was reported.
