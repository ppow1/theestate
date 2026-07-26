# WP-4222 — Staged Engineering Campaign Dashboard Integration

- **Status:** Implemented in isolated staging; not installed
- **Depends on:** WP-4220 and WP-4221
- **Implementation root:** `collaboration/workstreams/WP-4222/`
- **Authority:** read-only composition only

## Mission

Wire the published WP-4220 engineering queue to the WP-4221 dashboard projection through a
deterministic provider and panel registry.  The integration validates provider identity,
contract versions and schemas, loads immutable snapshots, composes the existing projection,
and reports compatibility, health, degradation, and provenance.

## Boundaries

This package creates no browser or Office surface and installs no production runtime.  It
does not schedule, dispatch, mutate lifecycle state, or perform Git operations.  Providers
are local immutable artifacts, panels are discovered from the WP-4221 projection contract,
and output is written only to an explicitly selected staging destination.  Production use
requires the separate install handoff in the implementation root.

## Acceptance

Provider and panel discovery, version/schema compatibility, projection and snapshot loading,
missing/degraded provider behavior, deterministic repeated composition, diagnostics, and
source read-only enforcement must pass the staged test suite.  WP-4214, WP-4215, WP-4217,
WP-4220, and WP-4221 contracts are referenced rather than reimplemented.
