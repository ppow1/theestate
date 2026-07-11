# WP-4030 — Estate Backup, Restore, and Resident Continuity Recovery

This staged workstream implements an isolated local backup/restore service. It is
not installed into the estate runtime; WP-4031 is responsible for approved CLI,
Office, service-status, and lifecycle integrations.

## Scope coverage

The service supports declared relative backup scopes for resident identity,
continuity, journal, mail, session, task, lifecycle, knowledge metadata, and
configuration records. Scope entries reject absolute paths, parent traversal,
secrets, caches, protected material, and unrestricted external paths.

## Backup behavior

- Deterministic manifests with source links, checksums, retention metadata, and
  truthful partial-failure reporting.
- Full backup plans copy all included files.
- Incremental backup plans require a base manifest and copy only changed files.
- Large model binaries and generated outputs are inventoried by reference unless
  the scope explicitly opts into large inclusion.

## Restore behavior

- Selective restore accepts a list of manifest-relative paths.
- Dry-run mode reports collisions without writing.
- Existing records are never overwritten unless `approve_overwrite=True`.
- Disaster-recovery rehearsal verifies the backup, restores to an isolated root,
  and checks restored checksums.
