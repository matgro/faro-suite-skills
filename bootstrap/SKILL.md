---
name: faro-bootstrap
description: Use when installing or updating the complete FARO skill suite.
version: 1.0.0
author: FARO Agent Skills contributors
license: MIT
metadata:
  agentskills:
    tags: [faro, installation, update, bootstrap, portability]
---

# FARO Bootstrap

## Purpose

Install or update the complete FARO skill suite from a local checkout or a user-approved repository release. The suite is the complete `faro/` tree declared by `manifest.json`; partial installation is invalid.

This bootstrap is an installation guide for an agent with filesystem access. It does not assume a particular agent runtime or a fixed skills directory.

## Preconditions

1. Obtain an explicit source from the user: a local checkout, a repository URL, or a pinned release/tag/commit. Do not invent a remote source or silently use a moving branch when the user supplied a versioned source.
2. Read `manifest.json`, `checksums.sha256`, and the source `faro/` tree. Confirm that `manifest.json` declares `faro` as the entry point and that every listed skill exists.
3. Determine the target runtime's skills root from its documented configuration or the user's direction. Do not assume a Hermes path for another agent.

**Complete when:** source, version/revision, and destination skills root are known.

## Install or update

1. Inspect `<skills-root>/faro/` before writing. If absent, install the complete source `faro/` tree there.
2. If `<skills-root>/faro/` already exists, compare it with the incoming `faro/` tree: report the installed version when observable, the incoming version/revision, changed files when observable, and whether local modifications would be replaced.
3. Before replacing an existing installation, ask the user for one explicit confirmation that names the exact destination and states that the old `faro/` directory will be replaced by the incoming complete suite. Do not overwrite merely because an update was requested.
4. After confirmation, stage the incoming `faro/` directory beside the destination, validate the staged tree against `manifest.json` and `checksums.sha256`, then replace the destination. Preserve no partial destination on failure; restore the previous tree when the filesystem operation fails.
5. Do not copy individual skills or flatten the directory tree. Preserve all relative paths under `faro/`.

**Complete when:** the target contains `<skills-root>/faro/SKILL.md`, every manifest skill, and every checksummed file.

## Verification

1. Compare the installed tree to `checksums.sha256` and ensure there are no missing or extra distributed files.
2. Report the final destination, source revision, suite version, number of skills, and whether the target runtime needs a session restart or skill-index refresh.
3. If the runtime cannot discover skills installed during the current session, state that limitation; do not claim that `/faro` is immediately available.

## Safety rules

- Never copy credentials, `.env` files, tokens, private keys, client data, or runtime state.
- Never fetch or execute an unreviewed remote script as part of installation.
- Do not modify the source checkout during installation.
- If the target cannot be identified or a replacement confirmation is absent, stop and explain what is needed.

## Verification checklist

- [ ] Source revision was provided or explicitly approved by the user.
- [ ] `manifest.json` and `checksums.sha256` validated the incoming tree.
- [ ] Target skills root was established from the target agent or user direction.
- [ ] Existing FARO installation was inspected before replacement.
- [ ] User explicitly confirmed replacement when an existing installation was found.
- [ ] Installed `faro/` tree matches the incoming release completely.
- [ ] Any needed restart/index refresh was reported.
