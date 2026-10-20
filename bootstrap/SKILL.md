---
name: faro-bootstrap
description: Use when installing or updating the complete FARO skill suite.
version: 1.4.0
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

1. Establish one source: a local package directory, a FARO repository URL, or a repository URL paired with a release, tag, or commit supplied by the user. For an update without a new source, reuse the installed provenance repository as described below. Do not invent a remote source.
2. Select the revision using the release selection rules below, then retrieve it into temporary staging without changing its bytes. For Git use `git -c core.autocrlf=false clone ...` (and disable conversion on subsequent checkouts). Record the selected tag and its immutable commit identifier, and report them before installation.
3. When the user supplied only this bootstrap by URL, derive the package repository only when it is unambiguously encoded by that URL. Otherwise request the repository URL; never guess one from a skill name.
4. Retrieve package files only. Do not execute downloaded scripts, installers, hooks, or binaries. The bootstrap itself directs the installation; repository contents are data until validation succeeds.
5. Read staged `manifest.json`, `checksums.sha256`, `faro/references/suite-provenance.json`, `faro/references/suite-changelog.json`, and the `faro/` tree. Confirm that the manifest names this package, declares `faro` as the entry point, lists every existing runtime skill exactly once, and that each skill's folder matches its frontmatter name. Validate all internal `related_skills`, router entries and Markdown handoffs against that inventory; external capabilities such as Jira REST are not bundled skills. The first changelog release must match the package version, and rename mappings must resolve without cycles to present skills while their old names are absent. These are read-only data checks, not permission to run downloaded validators.
6. Confirm that provenance declares the same repository plus an immutable `refs/tags/v*` reference matching the package version. Resolve that tag remotely to its commit (peel annotated tags), retrieve that exact revision without line-ending conversion, and compare the staged runtime inventory and hashes against the release's published checksums. A missing tag, different tree or unresolved reference blocks installation, including local maintenance sources that are not published yet. Do not regenerate checksums, normalize downloaded files or relabel an old tag to bypass a failure.
7. Determine the target runtime's skills root from its documented configuration or the user's direction. Do not assume a Hermes path for another agent.

**Complete when:** the source revision, staging location, and destination skills root are known.

### Release selection

- If the user supplied an explicit release, tag, commit, or local package directory, honor that source exactly. Do not silently substitute a newer release. An explicit commit or local package must still match its published provenance tag during validation.
- For a repository URL without an explicit revision, select the newest published stable version, not the default branch HEAD or the version declared by the installed suite. For an update without a new source, use the repository recorded in the installed `faro/references/suite-provenance.json`; report that source before querying it. If it is absent or invalid, request the repository URL instead of guessing.
- List remote tags with `git ls-remote --tags <repository>`. Eligible tags must match `refs/tags/v(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)` in full. Exclude prereleases, build suffixes and peeled `^{}` entries from the candidate names. Compare the major, minor and patch components as integers, not alphabetically or by commit/tag date; for example, `v1.10.0` is newer than `v1.9.0`.
- Resolve the selected tag to its commit, using its peeled `^{}` commit for an annotated tag. Keep that exact commit fixed throughout staging and verification. Its manifest version and provenance ref must match the selected tag. If the tag changes during retrieval, stop rather than installing a moving target.
- If no eligible stable tag exists, remote discovery fails, or the selected release fails validation, stop and explain the blocker. Do not fall back to branch HEAD, an older release, or the installed version. Prereleases are used only when explicitly requested.

## Install or update

1. Inspect `<skills-root>/faro/` before writing. If absent, install the complete staged `faro/` tree there.
2. If `<skills-root>/faro/` already exists, compare it with the incoming tree. Report the installed package version separately from the workspace contract version, the incoming repository and resolved revision, added/removed/changed files and skills, and whether local modifications would be replaced. Read the incoming changelog entries newer than the installed version and report affected renames and required workspace actions. If the installed version is unknown, do not guess the migration range: compare the full inventories and report all potentially applicable entries. A changelog mapping explains a rename; it is not an executable alias or authorization to migrate.
   For automatic release selection, if the same version is already installed and the trees match, report that FARO is up to date without replacing it. If that version has local differences, report them and require replacement confirmation before restoring published bytes. If the installed version is newer than the selected stable release, report it and stop without downgrading; a downgrade requires an explicitly requested revision and replacement confirmation.
3. Before replacing an existing installation, ask the user for one explicit confirmation that names the exact destination and states that the old `faro/` directory will be replaced by the incoming complete suite. Identify customized development guidelines under `faro-req-desarrollo/references/` in the comparison and agree whether to retain a recoverable copy, reapply selected rules, or discard them. Do not overwrite merely because an update was requested. Reapplied customizations must be reported as a locally modified suite, not a byte-identical published release; verify the unmodified installed release before any separately authorized customization.
4. After confirmation, stage the incoming `faro/` directory beside the destination, validate the staged tree against `manifest.json` and `checksums.sha256`, then replace the destination. Preserve no partial destination on failure; restore the previous tree when the filesystem operation fails.
5. Do not copy individual skills, overlay the new tree onto the old one, or flatten the directory tree. Preserve all relative paths under `faro/`. Removed or renamed directories must not remain installed. Retain the recoverable previous tree until verification succeeds; restore it if verification fails too.
6. Installing skills does not migrate projects. Do not search for or rewrite arbitrary workspaces. Explain that each workspace to be resumed must run doctor after the runtime refresh; old `nextRoute` values require a specific authorized correction, not reinitialization or a blanket text replacement. Preserve requirement IDs, versions, approvals, tasks and historical documents.
7. After the FARO tree is installed and verified, read `faro/references/laravel-external-skills.json`. For a Hermes runtime, install every configured direct skill with `hermes skills install <url> --yes`. For a `repository_skill_tree`, clone the declared public repository into temporary staging, enumerate only `<path>/**/<entrypoint>`, inspect each file and install each direct raw URL with the same official command. Do not execute repository scripts. Run `hermes skills audit <name>` after each successful install. Never pass `--force`: retain and report a security-blocked skill instead of bypassing the scanner.
8. Refresh approved external skills only after their status is checked with `hermes skills check <name>` and an update is explicitly authorized. Then run `hermes skills update <name>` followed by `hermes skills audit <name>`. A runtime without Hermes must report external capabilities as unavailable rather than copying repository contents by hand.

**Complete when:** the target contains `<skills-root>/faro/SKILL.md`, every manifest skill, and every checksummed file.

## Verification

1. Compare the installed tree to `checksums.sha256` and ensure there are no missing or extra distributed files. Repeat the name/folder/reference/changelog consistency checks on the exact destination, including absence of retired skills.
2. Report the final destination, source repository, immutable tag, resolved commit, suite version, number of skills, and whether the target runtime needs a session restart or skill-index refresh.
3. If the runtime cannot discover skills installed during the current session, state that limitation; do not claim that `/faro` is immediately available.
4. Remove temporary source staging after a successful installation unless the user explicitly requested that it be retained.

## Safety rules

- Never copy credentials, `.env` files, tokens, private keys, client data, or runtime state.
- Never fetch an unspecified source, follow repository redirects without reporting the final source, or execute remote scripts.
- Do not modify the source checkout during installation.
- If the target cannot be identified, the source cannot be validated, or a replacement confirmation is absent, stop and explain what is needed.

## Verification checklist

- [ ] Source was supplied explicitly or recovered from installed provenance for an update.
- [ ] Remote source, if any, was retrieved only into temporary staging and no downloaded code was executed.
- [ ] Resolved commit was recorded when the source was remote.
- [ ] An unpinned install/update selected the numerically newest published stable tag; explicit sources were honored and no branch fallback or implicit downgrade occurred.
- [ ] The installed suite provenance names the same remote and immutable release tag; the install report includes its resolved commit.
- [ ] `manifest.json` and `checksums.sha256` validated the incoming tree.
- [ ] Skill names, folders, references, changelog version and rename destinations are coherent; staged bytes match the published tag.
- [ ] Target skills root was established from the target agent or user direction.
- [ ] Existing FARO installation was inspected before replacement.
- [ ] User explicitly confirmed replacement when an existing installation was found.
- [ ] Installed `faro/` tree matches the incoming release completely.
- [ ] Any needed restart/index refresh was reported.
- [ ] Applicable changelog entries and authorized workspace migration steps were explained without editing projects.
- [ ] The Laravel external-skill catalog was processed after FARO verification; each allowed skill was installed and audited through the target runtime's official installer, while any blocked skill was reported without `--force`.
