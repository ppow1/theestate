# SERIES TASK WP-0077 — Capability Dependency Visualization

## Codex Command
Read `collaboration/work_packages/pending/WP-0077_SERIES_capability_dependency_visualization.md` and do exactly what it says.

## Mission
Create a visualization layer for the Estate Capability Registry that exposes capability dependencies, readiness, and implementation relationships for Mission Control and architectural review.

## Scope
Use the Estate Capability Registry and existing metadata to produce dependency views showing upstream/downstream relationships, implementation state, validation state, and operational readiness.

## Behavior Requirements
- Read-only visualization.
- Link every node back to its authoritative artifact.
- Handle incomplete dependency data gracefully.
- Support future Operations Center integration.

## Constraints
Do not invent dependencies. Do not modify governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify rendering with complete, partial, and missing dependency metadata. Verify links resolve correctly.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0077_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
