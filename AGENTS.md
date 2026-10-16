# Repository guidance

This repository distributes the FARO runtime suite in `faro/` and a guided installer in `bootstrap/`.

- Preserve every file below `faro/` byte-for-byte when packaging an existing FARO release unless an explicit FARO maintenance change is requested.
- Keep `manifest.json` and `checksums.sha256` synchronized with the actual distributable `faro/` tree.
- The bootstrap installs or replaces the complete `faro/` tree only; when an existing target is found, it must inspect, compare, and obtain explicit user confirmation before replacement.
- Do not add credentials, `.env` files, personal data, application source code, or generated runtime state.
- Run `python3 tests/validate_package.py` before committing.
- Changes to runtime skills require reviewing their source, related skill references, and supporting files together.
