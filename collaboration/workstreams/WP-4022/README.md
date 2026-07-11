# WP-4022 Staged Resident Capability and Tool Access Integration

This staged workstream implements resident-specific capability and tool-access resolution without touching active runtime integration targets.

## Contents

- `src/wp4022_resident_capabilities/resolver.py` — isolated resolver for resident capabilities, approved/denied/unavailable tool states, approval metadata, and resident/Office display payloads.
- `tests/test_resolver.py` — focused staged tests for Alfred, Helen, Grace candidate, unknown residents, and display payloads.
- `install_manifest.json` — install handoff for WP-4031.

## Isolation Boundary

The implementation remains under `collaboration/workstreams/WP-4022/` and does not modify active targets such as `src/estate/core/resident_interaction.py`, `src/estate/core/resident_authority.py`, `src/estate/cli/main.py`, or Office resident/status surfaces.
