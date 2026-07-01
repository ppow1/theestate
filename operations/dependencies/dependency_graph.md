# Estate Dependency Graph

Machine-readable output: `runtime/dependencies/dependency_graph.json`.

## Summary
- Generated: 2026-07-01T22:39:59+00:00
- Nodes: 28
- Edges: 0
- Orphaned items: 28
- Warnings: 31

## Supported dependency sources
- JSON fields: `dependencies`, `depends_on`, `dependency_ids`, `dependency_id`, `blocked_by`, `requires`, `required_capabilities`, `required_services`, `work_package_dependencies`.
- Markdown front matter or lines using those same field names.
- Markdown sections clearly headed `Dependencies`, `Depends On`, `Blocked By`, `Requires`, `Required Capabilities`, or `Required Services`.

## Graph schema
- `nodes`: `{id, type, label, source_artifact}`.
- `edges`: `{source, target, dependency_type, source_artifact}`.
- `warnings`: missing optional inputs, malformed JSON, malformed references, and artifacts without explicit dependency fields.
- `orphaned_items`: nodes with no incoming or outgoing explicit dependency edges.

## CLI usage
- `python -m estate.cli.main dependency-graph` writes JSON and Markdown and prints a summary.
- `python -m estate.cli.main dependency-graph --json` writes outputs and prints the JSON graph.

## Limitations
- Only explicit fields and clearly labelled dependency sections are captured.
- The generator does not infer hidden dependencies from wording, similarity, order, or proximity.
- Missing inputs produce warnings rather than failures.

## Edges
- No explicit dependency edges found.

## Orphaned items
- `Active Work Board` (operation) — operations/boards/active_work.md
- `Active Work Item Template` (operation) — operations/templates/active_work_item.md
- `CAP-000001` (capability) — data/registry/capabilities.json
- `CAP-000002` (capability) — data/registry/capabilities.json
- `CAP-000003` (capability) — data/registry/capabilities.json
- `CAP-000004` (capability) — data/registry/capabilities.json
- `CAP-000005` (capability) — data/registry/capabilities.json
- `CAP-000006` (capability) — data/registry/capabilities.json
- `Daily Task Board` (operation) — operations/boards/daily_board.md
- `Daily Task Template` (operation) — operations/templates/daily_task.md
- `EC-000086: Add Estate Operations Board` (operation) — operations/history/EC-000086.md
- `Estate Capability Lifecycle Status` (capability) — operations/capabilities/lifecycle_status.md
- `Estate Operations Board` (operation) — operations/README.md
- `Estate Steward Dashboard` (operation) — operations/steward/dashboard.md
- `Operations Board Implementation Recommendation` (operation) — operations/implementation_recommendation.md
- `Parking Lot` (operation) — operations/boards/parking_lot.md
- `Parking Lot Item` (operation) — operations/templates/parking_item.md
- `Review Cadence` (operation) — operations/boards/review_cadence.md
- `SVC-000001` (service) — data/registry/services.json
- `SVC-000002` (service) — data/registry/services.json
- `SVC-000003` (service) — data/registry/services.json
- `Strategic Roadmap` (operation) — operations/boards/roadmap.md
- `Work Package WP-LEAP-001` (work_package) — collaboration/work_packages/open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md
- `msg_20260701_000000_example_routing` (message) — collaboration/messages/example_alfred_routing_engine_v1.json
- `msg_ca3_20260701_0001_alfred_capability_brief` (message) — collaboration/messages/msg_ca3_20260701_0001_alfred_capability_brief.json
- `msg_ca3_20260701_0002_audit_malformed_json_review` (message) — collaboration/messages/msg_ca3_20260701_0002_audit_malformed_json_review.json
- `msg_ca3_20260701_0003_operations_board_review` (message) — collaboration/messages/msg_ca3_20260701_0003_operations_board_review.json
- `msg_ca3_20260701_0004_capability_lifecycle_review` (message) — collaboration/messages/msg_ca3_20260701_0004_capability_lifecycle_review.json

## Warnings
- missing_dependency_field: collaboration/messages/example_alfred_routing_engine_v1.json — msg_20260701_000000_example_routing has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0001_alfred_capability_brief.json — msg_ca3_20260701_0001_alfred_capability_brief has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0002_audit_malformed_json_review.json — msg_ca3_20260701_0002_audit_malformed_json_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0003_operations_board_review.json — msg_ca3_20260701_0003_operations_board_review has no explicit dependency field.
- missing_dependency_field: collaboration/messages/msg_ca3_20260701_0004_capability_lifecycle_review.json — msg_ca3_20260701_0004_capability_lifecycle_review has no explicit dependency field.
- missing_optional_artifact: runtime/operations/operations_board.json — Optional input artifact is unavailable.
- missing_optional_artifact: runtime/capabilities/capability_lifecycle_report.json — Optional input artifact is unavailable.
- missing_dependency_field: data/registry/capabilities.json — CAP-000001 has no explicit dependency field.
- missing_dependency_field: data/registry/capabilities.json — CAP-000002 has no explicit dependency field.
- missing_dependency_field: data/registry/capabilities.json — CAP-000003 has no explicit dependency field.
- missing_dependency_field: data/registry/capabilities.json — CAP-000004 has no explicit dependency field.
- missing_dependency_field: data/registry/capabilities.json — CAP-000005 has no explicit dependency field.
- missing_dependency_field: data/registry/capabilities.json — CAP-000006 has no explicit dependency field.
- missing_dependency_field: data/registry/services.json — SVC-000001 has no explicit dependency field.
- missing_dependency_field: data/registry/services.json — SVC-000002 has no explicit dependency field.
- missing_dependency_field: data/registry/services.json — SVC-000003 has no explicit dependency field.
- missing_dependency_field: collaboration/work_packages/open/WP-LEAP-001_Audit_Worker_v1_Local_Ollama.md — Work Package WP-LEAP-001 has no clearly labelled dependency section or field.
- missing_dependency_field: operations/README.md — Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/board/latest.md — Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/active_work.md — Active Work Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/daily_board.md — Daily Task Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/parking_lot.md — Parking Lot has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/review_cadence.md — Review Cadence has no clearly labelled dependency section or field.
- missing_dependency_field: operations/boards/roadmap.md — Strategic Roadmap has no clearly labelled dependency section or field.
- missing_dependency_field: operations/capabilities/lifecycle_status.md — Estate Capability Lifecycle Status has no clearly labelled dependency section or field.
- missing_dependency_field: operations/history/EC-000086.md — EC-000086: Add Estate Operations Board has no clearly labelled dependency section or field.
- missing_dependency_field: operations/implementation_recommendation.md — Operations Board Implementation Recommendation has no clearly labelled dependency section or field.
- missing_dependency_field: operations/steward/dashboard.md — Estate Steward Dashboard has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/active_work_item.md — Active Work Item Template has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/daily_task.md — Daily Task Template has no clearly labelled dependency section or field.
- missing_dependency_field: operations/templates/parking_item.md — Parking Lot Item has no clearly labelled dependency section or field.
