# WP-4223 recommendation engine validation report

## Preflight and classification

The inspected baseline was merge `d9e9519`. WP-4220, WP-4221, and WP-4222 were present and
compatible. An earlier assignment already used WP-4223 for operator-surface installation, while
this request names WP-4223 for a recommendation engine. The implementation is therefore
classified as a new, isolated advisory consumer with an identifier collision noted, not as a
replacement or modification of the installed surface or any authoritative package.

## Validation

* Focused engine tests: 20 passed.
* Engine plus WP-4220/WP-4221/WP-4222 regression suites: 49 passed.
* Manifest composition through the real WP-4222 registry produced valid deterministic JSON.
* Compilation, JSON parsing, and Git whitespace checks passed.
* Repeated execution and deep-copy tests prove stable content/hash and unchanged input objects.
* Scenario coverage: healthy, blocked, dependency cycle, merge-heavy, validation-heavy, empty,
  stale, and conflicting-priority campaigns.

The tests cover explanations/provenance, score arithmetic, stable tie breaking, optional-provider
degradation, missing duration, missing Git readiness, malformed/duplicate rows, unsupported
integration/snapshot versions, all four CLI commands, and consumption of the existing WP-4222
example.

## Authority audit

All delivered files are below this removable workstream boundary. The program contains no write,
worker, scheduler, seat, lifecycle, repository-discovery, or Git operation. Provider files are
read by WP-4222 and recommendations are returned as values or stdout. No authoritative queue,
dashboard, registry, work package, Parking Lot, WIP, lifecycle, or Git state is modified by the
engine.
