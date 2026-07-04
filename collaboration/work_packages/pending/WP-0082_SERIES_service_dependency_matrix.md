# SERIES TASK WP-0082 — Service Dependency Matrix

## Codex Command
Read `collaboration/work_packages/pending/WP-0082_SERIES_service_dependency_matrix.md` and do exactly what it says.

## Mission
Create a Service Dependency Matrix that documents operational dependencies between Estate services, enabling impact analysis, startup sequencing, troubleshooting, and future Operations Center visualization.

## Scope
Build on the Estate Service Catalog by identifying service-to-service dependencies, required providers, optional integrations, startup order, and failure impact.

## Behavior Requirements
- Read-only aggregation.
- Do not infer unsupported dependencies.
- Link dependencies to authoritative artifacts.
- Support future visualization and health monitoring.

## Constraints
Do not create duplicate dependency registries. Do not modify governance. Do not edit `estate_ledger/ledger.md` or `development/devlog.md`.

## Tests
Verify dependency mapping, graceful handling of incomplete metadata, startup ordering, and source-link integrity.

## Completion Signal
Create `collaboration/work_packages/completions/WP-0082_codex_done.json` using the standard completion schema.

## Merge Class
Class A.
